from rest_framework.decorators import api_view
from rest_framework.response import Response

from .provider import generate_with_fallback
from .serializers import (
	MealExplanationRequestSerializer,
	ShoppingNotesRequestSerializer,
	SubstitutionRequestSerializer,
)


def build_meal_fallback(data) -> str:
	matched = ', '.join(data['matched_ingredients']) or 'your pantry staples'
	missing = ', '.join(data['missing_ingredients'])
	note = f"Use {matched} to pull together {data['title']}."
	if missing:
		note += f" Missing: {missing}."
	return note


def build_substitution_fallback(data) -> str:
	missing_items = data['missing_ingredients']
	substitutions = data.get('substitutions', {})
	lines = []
	for item in missing_items:
		options = substitutions.get(item, [])
		if options:
			lines.append(f"{item}: try {', '.join(options)}.")
		else:
			lines.append(f"{item}: no pantry swaps found.")
	return ' '.join(lines)


def build_shopping_fallback(data) -> str:
	totals = data.get('totals', {})
	total = totals.get('total_estimated_cost', '0.00')
	currency = totals.get('currency', 'USD')
	remaining = totals.get('budget_remaining')
	note = f"Estimated total is {total} {currency}."
	if remaining not in (None, ''):
		note += f" Budget remaining: {remaining} {currency}."
	note += ' Focus on the highest-priority items first.'
	return note


def meal_prompt(data) -> str:
	return (
		'Write a short, friendly meal note (2-3 sentences).\n'
		f"Meal: {data['title']}\n"
		f"Description: {data.get('description', '')}\n"
		f"Matched ingredients: {', '.join(data['matched_ingredients'])}\n"
		f"Missing ingredients: {', '.join(data['missing_ingredients'])}\n"
		f"Substitutions: {data.get('substitutions', {})}\n"
		'Keep it practical and avoid inventing new ingredients.'
	)


def substitution_prompt(data) -> str:
	return (
		'Explain substitution options briefly (1-2 sentences).\n'
		f"Missing ingredients: {', '.join(data['missing_ingredients'])}\n"
		f"Possible substitutions: {data.get('substitutions', {})}\n"
		'Use only the provided substitutions.'
	)


def shopping_prompt(data) -> str:
	return (
		'Write a short shopping note (2 sentences).\n'
		f"Items: {data.get('items', [])}\n"
		f"Totals: {data.get('totals', {})}\n"
		'Highlight budget awareness and priorities.'
	)


@api_view(['POST'])
def meal_explanation(request):
	serializer = MealExplanationRequestSerializer(data=request.data)
	serializer.is_valid(raise_exception=True)
	payload = serializer.validated_data
	fallback = build_meal_fallback(payload)
	prompt = meal_prompt(payload)
	message, source, fallback_used = generate_with_fallback(prompt, fallback)
	return Response({'message': message, 'source': source, 'fallback': fallback_used})


@api_view(['POST'])
def substitution_explanation(request):
	serializer = SubstitutionRequestSerializer(data=request.data)
	serializer.is_valid(raise_exception=True)
	payload = serializer.validated_data
	fallback = build_substitution_fallback(payload)
	prompt = substitution_prompt(payload)
	message, source, fallback_used = generate_with_fallback(prompt, fallback)
	return Response({'message': message, 'source': source, 'fallback': fallback_used})


@api_view(['POST'])
def shopping_notes(request):
	serializer = ShoppingNotesRequestSerializer(data=request.data)
	serializer.is_valid(raise_exception=True)
	payload = serializer.validated_data
	fallback = build_shopping_fallback(payload)
	prompt = shopping_prompt(payload)
	message, source, fallback_used = generate_with_fallback(prompt, fallback)
	return Response({'message': message, 'source': source, 'fallback': fallback_used})
