from __future__ import annotations

import csv
from decimal import Decimal
from typing import Iterable

from django.http import HttpResponse
from django.db import transaction
from rest_framework import mixins, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from meals.cache import compute_pantry_hash, get_cached_meals
from meals.views import (
	build_pantry_payload,
	build_meal_groups,
	build_urgent_items,
	INGREDIENT_CATEGORY_MAP,
	normalize,
	persist_meal_set,
	select_meal_candidates,
	serialize_meal_set,
)
from pantry.models import PantryItem

from .models import ShoppingListItem, WeeklyBudget
from .serializers import ShoppingListItemSerializer, WeeklyBudgetSerializer

CATEGORY_PRICE_MAP = {
	'produce': Decimal('3.50'),
	'dairy': Decimal('4.00'),
	'protein': Decimal('6.00'),
	'meat': Decimal('7.50'),
	'seafood': Decimal('8.00'),
	'eggs': Decimal('3.00'),
	'grains': Decimal('2.50'),
	'canned': Decimal('2.00'),
	'frozen': Decimal('3.50'),
	'baking': Decimal('2.00'),
	'spices': Decimal('3.00'),
}

PERISHABLE_CATEGORIES = {
	'produce',
	'dairy',
	'protein',
	'meat',
	'seafood',
	'eggs',
}

DEFAULT_PRICE = Decimal('3.00')

MEAL_GROUP_ORDER = ('cook_today', 'cook_this_week', 'possible_later')

MEAL_GROUP_LABELS = {
	'cook_today': 'cook today',
	'cook_this_week': 'cook this week',
	'possible_later': 'possible later',
}

MEAL_GROUP_PRIORITIES = {
	'cook_today': ShoppingListItem.Priority.HIGH,
	'cook_this_week': ShoppingListItem.Priority.MEDIUM,
	'possible_later': ShoppingListItem.Priority.LOW,
}


def current_budget(user) -> WeeklyBudget | None:
	return (
		WeeklyBudget.objects.filter(user=user)
		.order_by('-week_start_date', '-created_at')
		.first()
	)


def estimate_price(category: str) -> Decimal:
	if not category:
		return DEFAULT_PRICE
	return CATEGORY_PRICE_MAP.get(category.strip().lower(), DEFAULT_PRICE)


def estimate_ingredient_price(name: str) -> Decimal:
	category = INGREDIENT_CATEGORY_MAP.get(normalize(name), '')
	return estimate_price(category)


def priority_for_category(category: str) -> int:
	if category.strip().lower() in PERISHABLE_CATEGORIES:
		return ShoppingListItem.Priority.HIGH
	if category.strip().lower() in {'grains', 'canned', 'frozen'}:
		return ShoppingListItem.Priority.MEDIUM
	return ShoppingListItem.Priority.LOW


def calculate_totals(
	items: Iterable[ShoppingListItem], budget: WeeklyBudget | None
) -> dict:
	total = Decimal('0.00')
	for item in items:
		total += item.estimated_price * item.quantity

	total = total.quantize(Decimal('0.01'))

	if budget:
		remaining = (budget.weekly_budget_amount - total).quantize(Decimal('0.01'))
		return {
			'total_estimated_cost': str(total),
			'budget_amount': str(budget.weekly_budget_amount),
			'budget_remaining': str(remaining),
			'currency': budget.currency,
		}

	return {
		'total_estimated_cost': str(total),
		'budget_amount': None,
		'budget_remaining': None,
		'currency': 'USD',
	}


def build_shopping_candidates(pantry_items: Iterable[PantryItem]):
	candidates: list[ShoppingListItem] = []

	for item in pantry_items:
		if item.quantity <= Decimal('1.00'):
			category = item.category or ''
			candidates.append(
				ShoppingListItem(
					name=item.name,
					estimated_price=estimate_price(category),
					quantity=Decimal('1.00'),
					unit=item.unit,
					priority=priority_for_category(category),
					is_needed=True,
					reason='Low stock in pantry.',
					linked_pantry_item=item,
				)
			)

	if candidates:
		return candidates

	return [
		ShoppingListItem(
			name='Seasonal vegetables',
			estimated_price=Decimal('3.50'),
			quantity=Decimal('1.00'),
			unit='bundle',
			priority=ShoppingListItem.Priority.HIGH,
			is_needed=True,
			reason='Keep produce stocked for balanced meals.',
		),
		ShoppingListItem(
			name='Eggs',
			estimated_price=Decimal('3.00'),
			quantity=Decimal('1.00'),
			unit='dozen',
			priority=ShoppingListItem.Priority.HIGH,
			is_needed=True,
			reason='Versatile protein for quick meals.',
		),
		ShoppingListItem(
			name='Whole grains',
			estimated_price=Decimal('2.50'),
			quantity=Decimal('1.00'),
			unit='bag',
			priority=ShoppingListItem.Priority.MEDIUM,
			is_needed=True,
			reason='Staple base for meal planning.',
		),
	]


def apply_budget(
	items: Iterable[ShoppingListItem],
	budget: WeeklyBudget | None,
	preserve_order: bool = False,
) -> list[ShoppingListItem]:
	item_list = list(items)
	if not budget:
		return item_list

	remaining = budget.weekly_budget_amount
	selected: list[ShoppingListItem] = []
	ordered_items = item_list
	if not preserve_order:
		ordered_items = sorted(item_list, key=lambda x: (x.priority, x.estimated_price))

	for item in ordered_items:
		line_cost = item.estimated_price * item.quantity
		if line_cost <= remaining:
			selected.append(item)
			remaining -= line_cost

	return selected


def get_or_generate_meals_for_shopping(user, pantry_items: list[PantryItem]) -> dict:
	meal_set, pantry_hash, _pantry_changed = get_cached_meals(user)
	if meal_set:
		return serialize_meal_set(meal_set)

	urgent_items = build_urgent_items(pantry_items)
	urgent_names = {
		normalize(item['name'])
		for item in urgent_items
		if item['urgency_score'] >= 60
	}
	pantry_payload = build_pantry_payload(pantry_items)
	meal_candidates, source, _llm_error = select_meal_candidates(pantry_payload)
	meals = build_meal_groups(pantry_payload, urgent_names, meal_candidates, source)

	persist_meal_set(user, pantry_hash or compute_pantry_hash(user), source, meals)
	return meals


def build_meal_shopping_candidates(meals: dict) -> list[ShoppingListItem]:
	candidates: list[ShoppingListItem] = []
	seen_names: set[str] = set()

	for group_name in MEAL_GROUP_ORDER:
		priority = MEAL_GROUP_PRIORITIES[group_name]
		group_label = MEAL_GROUP_LABELS[group_name]
		for meal in meals.get(group_name, []):
			title = meal.get('title') or 'recommended meal'
			for ingredient in meal.get('missing_ingredients') or []:
				name = str(ingredient).strip()
				normalized = normalize(name)
				if not name or normalized in seen_names:
					continue

				seen_names.add(normalized)
				candidates.append(
					ShoppingListItem(
						name=name,
						estimated_price=estimate_ingredient_price(name),
						quantity=Decimal('1.00'),
						unit='item',
						priority=priority,
						is_needed=True,
						reason=f'Needed for {group_label}: {title}.',
					)
				)

	return candidates


class BudgetView(APIView):
	def get(self, request):
		budget = current_budget(request.user)
		if not budget:
			return Response({'budget': None})

		serializer = WeeklyBudgetSerializer(budget)
		return Response({'budget': serializer.data})

	def post(self, request):
		budget = current_budget(request.user)
		serializer = WeeklyBudgetSerializer(
			instance=budget,
			data=request.data,
			partial=budget is not None,
		)
		serializer.is_valid(raise_exception=True)
		saved = serializer.save(user=request.user)
		return Response({'budget': WeeklyBudgetSerializer(saved).data})

	def put(self, request):
		return self.post(request)


class ShoppingListViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
	serializer_class = ShoppingListItemSerializer
	queryset = ShoppingListItem.objects.all()

	def get_queryset(self):
		return ShoppingListItem.objects.filter(user=self.request.user).order_by('priority', 'id')

	def list(self, request, *args, **kwargs):
		items = self.get_queryset()
		serializer = self.get_serializer(items, many=True)
		totals = calculate_totals(items, current_budget(request.user))
		return Response({'items': serializer.data, 'totals': totals})

	@action(detail=False, methods=['post'], url_path='generate')
	def generate(self, request):
		pantry_items = list(PantryItem.objects.filter(user=request.user))
		budget = current_budget(request.user)
		meals = get_or_generate_meals_for_shopping(request.user, pantry_items)
		candidates = build_meal_shopping_candidates(meals)
		selected = apply_budget(candidates, budget, preserve_order=True)
		for item in selected:
			item.user = request.user

		with transaction.atomic():
			ShoppingListItem.objects.filter(user=request.user).delete()
			ShoppingListItem.objects.bulk_create(selected)

		items = self.get_queryset()
		serializer = self.get_serializer(items, many=True)
		totals = calculate_totals(items, budget)
		return Response({'items': serializer.data, 'totals': totals})

	@action(detail=False, methods=['post'], url_path='add-items')
	def add_items(self, request):
		raw_items = request.data.get('items', [])
		if not isinstance(raw_items, list):
			raw_items = []

		names = []
		for item in raw_items:
			name = str(item).strip()
			if name and name.lower() not in {entry.lower() for entry in names}:
				names.append(name)

		for name in names:
			existing = ShoppingListItem.objects.filter(
				user=request.user,
				name__iexact=name,
			).first()
			if existing:
				if not existing.is_needed:
					existing.is_needed = True
					existing.reason = 'Needed for a selected meal.'
					existing.save(update_fields=['is_needed', 'reason', 'updated_at'])
				continue

			ShoppingListItem.objects.create(
				user=request.user,
				name=name,
				estimated_price=DEFAULT_PRICE,
				quantity=Decimal('1.00'),
				unit='item',
				priority=ShoppingListItem.Priority.MEDIUM,
				is_needed=True,
				reason='Needed for a selected meal.',
			)

		items = self.get_queryset()
		serializer = self.get_serializer(items, many=True)
		totals = calculate_totals(items, current_budget(request.user))
		return Response({'items': serializer.data, 'totals': totals})


@api_view(['GET'])
def export_shopping_list(request):
	format_param = request.query_params.get('format', 'csv').strip().lower()
	items = ShoppingListItem.objects.filter(user=request.user).order_by('priority', 'id')

	if format_param == 'text':
		lines = []
		for item in items:
			status = 'needed' if item.is_needed else 'bought'
			lines.append(
				f"- {item.name} ({item.quantity} {item.unit}) "
				f"{item.estimated_price} [{status}]"
			)
		payload = '\n'.join(lines) if lines else 'No shopping items yet.'
		return HttpResponse(payload, content_type='text/plain')

	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="shopping-list.csv"'
	writer = csv.writer(response)
	writer.writerow(
		['Item', 'Quantity', 'Unit', 'Priority', 'Estimated', 'Needed', 'Reason']
	)
	for item in items:
		writer.writerow(
			[
				item.name,
				str(item.quantity),
				item.unit,
				item.priority,
				str(item.estimated_price),
				'yes' if item.is_needed else 'no',
				item.reason,
			]
		)

	return response
