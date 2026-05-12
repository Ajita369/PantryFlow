from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from meals.cache import get_cached_meals
from meals.views import week_start_date
from pantry.models import PantryItem

from .graph import run_weekly_plan
from .models import AIPlanSession


def latest_saved_plan(user):
	session = AIPlanSession.objects.filter(user=user).order_by('-created_at').first()
	if not session:
		return None
	if hasattr(session, 'plan_snapshot'):
		return session.plan_snapshot or None
	return (session.budget_snapshot or {}).get('plan_snapshot')


def pantry_snapshot(user) -> list[dict]:
	items = PantryItem.objects.filter(user=user).order_by('expiry_date', 'name')
	return [
		{
			'id': item.id,
			'name': item.name,
			'category': item.category,
			'quantity': str(item.quantity),
			'unit': item.unit,
			'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None,
		}
		for item in items
	]


def save_plan_session(user, plan: dict) -> None:
	meal_set, _pantry_hash, _pantry_changed = get_cached_meals(user)
	AIPlanSession.objects.create(
		user=user,
		week_start=week_start_date(timezone.localdate()),
		pantry_snapshot=pantry_snapshot(user),
		budget_snapshot={
			'budget': plan.get('budget') or {},
			'plan_snapshot': plan,
		},
		meal_set=meal_set,
	)


@api_view(['GET', 'POST'])
def plan_week(request):
	if request.method == 'GET':
		return Response({'plan': latest_saved_plan(request.user)})

	plan = run_weekly_plan(request.user)
	save_plan_session(request.user, plan)
	return Response({'plan': plan})
