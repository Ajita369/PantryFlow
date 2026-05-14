from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from meals.cache import get_cached_meals
from meals.views import build_meal_groups, build_pantry_payload, build_urgent_items, normalize, serialize_meal_set
from pantry.models import PantryItem
from planning.models import ShoppingListItem
from planning.views import calculate_totals, current_budget


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
	return Response({'status': 'ok'})


@api_view(['GET'])
def dashboard(request):
	pantry_items = PantryItem.objects.filter(user=request.user)
	today = timezone.localdate()
	cutoff = today + timedelta(days=7)

	pantry_count = pantry_items.count()
	expiring_soon_count = pantry_items.filter(
		expiry_date__gte=today, expiry_date__lte=cutoff
	).count()
	expired_count = pantry_items.filter(expiry_date__lt=today).count()

	urgent_items = build_urgent_items(pantry_items)[:5]
	urgent_names = {
		normalize(item['name'])
		for item in urgent_items
		if item.get('urgency_score', 0) >= 60
	}

	meal_set, _pantry_hash, _pantry_changed = get_cached_meals(request.user)
	if meal_set:
		meals = serialize_meal_set(meal_set)
	else:
		pantry_payload = build_pantry_payload(pantry_items)
		meals = build_meal_groups(pantry_payload, urgent_names)

	quick_meals = []
	for meal in meals.get('cook_today', [])[:3]:
		quick_meals.append(
			{
				'id': meal.get('id'),
				'title': meal.get('title'),
				'match_score': meal.get('match_score'),
				'estimated_time_minutes': meal.get('estimated_time_minutes'),
			}
		)

	budget = current_budget(request.user)
	shopping_items = ShoppingListItem.objects.filter(user=request.user, is_needed=True)
	shopping_count = shopping_items.count()
	totals = calculate_totals(shopping_items, budget)

	return Response(
		{
			'pantry_count': pantry_count,
			'expiring_soon_count': expiring_soon_count,
			'expired_count': expired_count,
			'budget_remaining': totals.get('budget_remaining'),
			'budget_total': totals.get('budget_amount'),
			'currency': totals.get('currency', 'USD'),
			'top_urgent_items': urgent_items,
			'quick_meals': quick_meals,
			'shopping_count': shopping_count,
		}
	)
