from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from pantry.models import PantryItem

from .cache import compute_pantry_hash, get_cached_meals, invalidate_meals
from .generator import generate_meal_candidates
from .models import GeneratedMeal, GeneratedMealSet

MEAL_TEMPLATES = [
	{
		'id': 1,
		'title': 'Lemon herb chicken with greens',
		'description': 'Quick skillet chicken with a bright herb finish.',
		'cuisine_type': 'American',
		'estimated_cost': 12.0,
		'estimated_time_minutes': 25,
		'ingredients': ['chicken', 'spinach', 'lemon', 'garlic', 'olive oil'],
	},
	{
		'id': 2,
		'title': 'Chickpea grain bowl',
		'description': 'Protein-rich bowl with grains and roasted veg.',
		'cuisine_type': 'Mediterranean',
		'estimated_cost': 9.0,
		'estimated_time_minutes': 30,
		'ingredients': ['chickpeas', 'brown rice', 'cucumber', 'tomato', 'yogurt'],
	},
	{
		'id': 3,
		'title': 'Veggie stir-fry',
		'description': 'Colorful vegetables with a simple soy glaze.',
		'cuisine_type': 'Asian',
		'estimated_cost': 8.0,
		'estimated_time_minutes': 20,
		'ingredients': ['broccoli', 'carrot', 'bell pepper', 'soy sauce', 'rice'],
	},
	{
		'id': 4,
		'title': 'Creamy pasta bake',
		'description': 'Comforting pasta with a creamy herb sauce.',
		'cuisine_type': 'Italian',
		'estimated_cost': 10.0,
		'estimated_time_minutes': 35,
		'ingredients': ['pasta', 'milk', 'cheese', 'spinach', 'onion'],
	},
	{
		'id': 5,
		'title': 'Breakfast yogurt parfaits',
		'description': 'Layered yogurt with fruit and crunchy toppings.',
		'cuisine_type': 'American',
		'estimated_cost': 6.0,
		'estimated_time_minutes': 10,
		'ingredients': ['yogurt', 'berries', 'oats', 'honey'],
	},
]

HIGH_USE_CATEGORIES = {
	'produce',
	'dairy',
	'protein',
	'grains',
	'eggs',
}

SUBSTITUTION_MAP = {
	'spinach': ['kale', 'chard'],
	'milk': ['oat milk', 'almond milk'],
	'yogurt': ['sour cream'],
	'rice': ['quinoa', 'couscous'],
	'pasta': ['noodles'],
	'chickpeas': ['white beans', 'lentils'],
	'broccoli': ['cauliflower', 'green beans'],
	'berries': ['apple', 'banana'],
}

INGREDIENT_CATEGORY_MAP = {
	'spinach': 'produce',
	'broccoli': 'produce',
	'carrot': 'produce',
	'bell pepper': 'produce',
	'tomato': 'produce',
	'cucumber': 'produce',
	'berries': 'produce',
	'apple': 'produce',
	'banana': 'produce',
	'yogurt': 'dairy',
	'milk': 'dairy',
	'cheese': 'dairy',
	'chicken': 'protein',
	'eggs': 'eggs',
	'rice': 'grains',
	'brown rice': 'grains',
	'pasta': 'grains',
	'oats': 'grains',
}

MIN_COOK_TODAY = 1
MIN_COOK_THIS_WEEK = 2
MAX_POSSIBLE_LATER = 3


def normalize(text: str) -> str:
	return text.strip().lower()


def ingredient_matches(ingredient: str, pantry_name: str) -> bool:
	ingredient_norm = normalize(ingredient)
	pantry_norm = normalize(pantry_name)
	return ingredient_norm in pantry_norm or pantry_norm in ingredient_norm


def urgency_label(expiry_date) -> str:
	if not expiry_date:
		return 'No expiry'

	days = (expiry_date - timezone.localdate()).days
	if days < 0:
		return 'Expired'
	if days <= 3:
		return 'Urgent'
	if days <= 7:
		return 'Soon'
	return 'OK'


def urgency_score(item: PantryItem) -> int:
	score = 0
	if item.expiry_date:
		days = (item.expiry_date - timezone.localdate()).days
		if days < 0:
			score += 90
		elif days <= 3:
			score += 70
		elif days <= 7:
			score += 50
		else:
			score += 30
	else:
		score += 20

	if item.quantity <= Decimal('1.00'):
		score += 15
	elif item.quantity <= Decimal('2.00'):
		score += 8

	if normalize(item.category or '') in HIGH_USE_CATEGORIES:
		score += 10

	return min(score, 100)


def build_urgent_items(pantry_items):
	urgent_items = []
	for item in pantry_items:
		score = urgency_score(item)
		urgent_items.append(
			{
				'id': item.id,
				'name': item.name,
				'category': item.category,
				'quantity': str(item.quantity),
				'unit': item.unit,
				'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None,
				'urgency_score': score,
				'urgency_label': urgency_label(item.expiry_date),
			}
		)

	urgent_items.sort(key=lambda x: x['urgency_score'], reverse=True)
	return urgent_items


def substitution_candidates(missing: str, pantry_items):
	missing_norm = normalize(missing)
	candidates = []

	synonyms = SUBSTITUTION_MAP.get(missing_norm, [])
	category = INGREDIENT_CATEGORY_MAP.get(missing_norm)

	for item in pantry_items:
		item_name = item['name']
		item_norm = item['name_norm']

		for synonym in synonyms:
			if ingredient_matches(synonym, item_name):
				candidates.append(item_name)
				break

		if category and normalize(item['category']) == category:
			candidates.append(item_name)

	unique = []
	for name in candidates:
		if name not in unique:
			unique.append(name)

	return unique


def meal_rank(meal):
	return (
		-meal['match_score'],
		len(meal['missing_ingredients']),
		meal['estimated_time_minutes'],
		meal['title'],
	)


def rebalance_meal_groups(groups):
	cook_today = sorted(groups['cook_today'], key=meal_rank)
	cook_this_week = sorted(groups['cook_this_week'], key=meal_rank)
	possible_later = sorted(groups['possible_later'], key=meal_rank)

	while len(cook_today) < MIN_COOK_TODAY and (cook_this_week or possible_later):
		source = cook_this_week if cook_this_week else possible_later
		cook_today.append(source.pop(0))

	while len(cook_this_week) < MIN_COOK_THIS_WEEK and possible_later:
		cook_this_week.append(possible_later.pop(0))

	while len(cook_this_week) < MIN_COOK_THIS_WEEK and len(cook_today) > MIN_COOK_TODAY:
		cook_this_week.append(cook_today.pop())

	return {
		'cook_today': sorted(cook_today, key=meal_rank),
		'cook_this_week': sorted(cook_this_week, key=meal_rank),
		'possible_later': sorted(possible_later, key=meal_rank)[:MAX_POSSIBLE_LATER],
	}


def build_meal_groups(pantry_items, urgent_names, meal_candidates=None, source: str = 'templates'):
	cook_today = []
	cook_this_week = []
	possible_later = []

	if meal_candidates is None:
		meal_candidates = MEAL_TEMPLATES
		source = 'templates'

	for index, template in enumerate(meal_candidates):
		ingredients = template.get('ingredients') or []
		if not ingredients:
			continue
		matched = []
		missing = []
		substitutions = {}

		for ingredient in ingredients:
			match = None
			for item in pantry_items:
				if ingredient_matches(ingredient, item['name']):
					match = item
					break

			if match:
				matched.append(ingredient)
			else:
				missing.append(ingredient)
				substitutions[ingredient] = substitution_candidates(ingredient, pantry_items)

		match_score = len(matched) / len(ingredients)
		if any(name in urgent_names for name in matched):
			match_score = min(1.0, match_score + 0.1)

		meal_payload = {
			'id': template.get('id', index + 1),
			'title': template.get('title', ''),
			'description': template.get('description', ''),
			'cuisine_type': template.get('cuisine_type', ''),
			'estimated_cost': template.get('estimated_cost', 0),
			'estimated_time_minutes': template.get('estimated_time_minutes', 0),
			'ingredients': ingredients,
			'steps': template.get('steps', []),
			'matched_ingredients': matched,
			'missing_ingredients': missing,
			'substitutions': substitutions,
			'match_score': round(match_score, 2),
			'source': source,
		}

		if match_score >= 0.75 and len(missing) <= 1:
			cook_today.append(meal_payload)
		elif match_score >= 0.5:
			cook_this_week.append(meal_payload)
		else:
			possible_later.append(meal_payload)

	return rebalance_meal_groups({
		'cook_today': cook_today,
		'cook_this_week': cook_this_week,
		'possible_later': possible_later,
	})


def select_meal_candidates(pantry_payload: list[dict]):
	candidates, error = generate_meal_candidates(pantry_payload)
	if candidates:
		return candidates, 'llm', None
	if error:
		error = 'AI meal generation is unavailable right now, so template meals are shown.'
	return MEAL_TEMPLATES, 'templates', error


def build_pantry_payload(pantry_items) -> list[dict]:
	return [
		{
			'id': item.id,
			'name': item.name,
			'name_norm': normalize(item.name),
			'category': item.category or '',
			'quantity': str(item.quantity),
			'unit': item.unit,
			'expiry_date': item.expiry_date,
		}
		for item in pantry_items
	]


def serialize_meal_set(meal_set: GeneratedMealSet) -> dict:
	meals = {
		'cook_today': [],
		'cook_this_week': [],
		'possible_later': [],
	}

	for meal in meal_set.meals.all():
		payload = {
			'id': meal.id,
			'title': meal.title,
			'description': meal.description,
			'cuisine_type': meal.cuisine_type,
			'estimated_cost': float(meal.estimated_cost),
			'estimated_time_minutes': meal.estimated_time_minutes,
			'ingredients': meal.ingredients or [],
			'steps': meal.steps or [],
			'matched_ingredients': meal.matched_ingredients or [],
			'missing_ingredients': meal.missing_ingredients or [],
			'substitutions': meal.substitutions or {},
			'match_score': meal.match_score,
			'source': meal_set.source,
		}
		meals.setdefault(meal.category, []).append(payload)

	for key in meals:
		meals[key] = sorted(meals[key], key=meal_rank)

	return meals


def week_start_date(current_date: date | None = None) -> date:
	current_date = current_date or timezone.localdate()
	return current_date - timedelta(days=current_date.weekday())


def persist_meal_set(user, pantry_hash: str, source: str, meals: dict) -> GeneratedMealSet:
	invalidate_meals(user)
	with transaction.atomic():
		meal_set = GeneratedMealSet.objects.create(
			user=user,
			source=source,
			pantry_hash=pantry_hash,
			week_start=week_start_date(),
			is_active=True,
		)
		meal_rows = []
		for category, group in meals.items():
			for meal in group:
				estimated_cost = meal.get('estimated_cost')
				if estimated_cost is None:
					estimated_cost = 0
				estimated_time = meal.get('estimated_time_minutes')
				if estimated_time is None:
					estimated_time = 0
				meal_rows.append(
					GeneratedMeal(
						meal_set=meal_set,
						title=meal.get('title', ''),
						description=meal.get('description', ''),
						cuisine_type=meal.get('cuisine_type', ''),
						estimated_cost=Decimal(str(estimated_cost)),
						estimated_time_minutes=int(estimated_time),
						ingredients=meal.get('ingredients') or [],
						steps=meal.get('steps') or [],
						category=category,
						match_score=meal.get('match_score', 0.0),
						matched_ingredients=meal.get('matched_ingredients') or [],
						missing_ingredients=meal.get('missing_ingredients') or [],
						substitutions=meal.get('substitutions') or {},
					)
				)
		GeneratedMeal.objects.bulk_create(meal_rows)

	return meal_set


@api_view(['GET'])
def meal_suggestions(request):
	pantry_items = PantryItem.objects.filter(user=request.user)
	urgent_items = build_urgent_items(pantry_items)
	urgent_names = {normalize(item['name']) for item in urgent_items if item['urgency_score'] >= 60}

	meal_set, pantry_hash, pantry_changed = get_cached_meals(request.user)
	if meal_set:
		return Response(
			{
				'urgent_items': urgent_items,
				'meals': serialize_meal_set(meal_set),
				'source': meal_set.source,
				'llm_error': None,
				'generated_at': meal_set.created_at.isoformat(),
				'cached': True,
				'pantry_changed': False,
			}
		)

	pantry_payload = build_pantry_payload(pantry_items)
	meal_candidates, source, llm_error = select_meal_candidates(pantry_payload)
	meals = build_meal_groups(pantry_payload, urgent_names, meal_candidates, source)
	meal_set = persist_meal_set(request.user, pantry_hash, source, meals)

	return Response(
		{
			'urgent_items': urgent_items,
			'meals': meals,
			'source': source,
			'llm_error': llm_error,
			'generated_at': meal_set.created_at.isoformat(),
			'cached': False,
			'pantry_changed': pantry_changed,
		}
	)


@api_view(['POST'])
def generate_meals(request):
	pantry_items = PantryItem.objects.filter(user=request.user)
	urgent_items = build_urgent_items(pantry_items)
	urgent_names = {normalize(item['name']) for item in urgent_items if item['urgency_score'] >= 60}

	pantry_payload = build_pantry_payload(pantry_items)
	pantry_hash = compute_pantry_hash(request.user)
	meal_candidates, source, llm_error = select_meal_candidates(pantry_payload)
	meals = build_meal_groups(pantry_payload, urgent_names, meal_candidates, source)
	meal_set = persist_meal_set(request.user, pantry_hash, source, meals)

	return Response(
		{
			'urgent_items': urgent_items,
			'meals': meals,
			'source': source,
			'llm_error': llm_error,
			'generated_at': meal_set.created_at.isoformat(),
			'cached': False,
			'pantry_changed': False,
		}
	)
