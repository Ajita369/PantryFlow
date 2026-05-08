from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from pantry.models import PantryItem

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


def build_meal_groups(pantry_items, urgent_names):
	cook_today = []
	cook_this_week = []
	possible_later = []

	for template in MEAL_TEMPLATES:
		matched = []
		missing = []
		substitutions = {}

		for ingredient in template['ingredients']:
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

		match_score = len(matched) / len(template['ingredients'])
		if any(name in urgent_names for name in matched):
			match_score = min(1.0, match_score + 0.1)

		meal_payload = {
			'id': template['id'],
			'title': template['title'],
			'description': template['description'],
			'cuisine_type': template['cuisine_type'],
			'estimated_cost': template['estimated_cost'],
			'estimated_time_minutes': template['estimated_time_minutes'],
			'matched_ingredients': matched,
			'missing_ingredients': missing,
			'substitutions': substitutions,
			'match_score': round(match_score, 2),
		}

		if match_score >= 0.75 and len(missing) <= 1:
			cook_today.append(meal_payload)
		elif match_score >= 0.5:
			cook_this_week.append(meal_payload)
		else:
			possible_later.append(meal_payload)

	return {
		'cook_today': cook_today,
		'cook_this_week': cook_this_week,
		'possible_later': possible_later,
	}


@api_view(['GET'])
def meal_suggestions(request):
	pantry_items = PantryItem.objects.all()
	urgent_items = build_urgent_items(pantry_items)
	urgent_names = {normalize(item['name']) for item in urgent_items if item['urgency_score'] >= 60}

	pantry_payload = [
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

	meals = build_meal_groups(pantry_payload, urgent_names)

	return Response(
		{
			'urgent_items': urgent_items,
			'meals': meals,
			'generated_at': timezone.now().isoformat(),
		}
	)
