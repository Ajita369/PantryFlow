from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from django.db import transaction
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

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
	items: Iterable[ShoppingListItem], budget: WeeklyBudget | None
) -> list[ShoppingListItem]:
	if not budget:
		return list(items)

	remaining = budget.weekly_budget_amount
	selected: list[ShoppingListItem] = []

	for item in sorted(items, key=lambda x: (x.priority, x.estimated_price)):
		line_cost = item.estimated_price * item.quantity
		if line_cost <= remaining:
			selected.append(item)
			remaining -= line_cost

	return selected


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
		return ShoppingListItem.objects.filter(user=self.request.user)

	def list(self, request, *args, **kwargs):
		items = self.get_queryset()
		serializer = self.get_serializer(items, many=True)
		totals = calculate_totals(items, current_budget(request.user))
		return Response({'items': serializer.data, 'totals': totals})

	@action(detail=False, methods=['post'], url_path='generate')
	def generate(self, request):
		pantry_items = PantryItem.objects.filter(user=request.user)
		budget = current_budget(request.user)
		candidates = build_shopping_candidates(pantry_items)
		selected = apply_budget(candidates, budget)
		for item in selected:
			item.user = request.user

		with transaction.atomic():
			ShoppingListItem.objects.filter(user=request.user).delete()
			ShoppingListItem.objects.bulk_create(selected)

		items = self.get_queryset()
		serializer = self.get_serializer(items, many=True)
		totals = calculate_totals(items, budget)
		return Response({'items': serializer.data, 'totals': totals})
