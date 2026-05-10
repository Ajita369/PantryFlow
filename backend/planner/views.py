from rest_framework.decorators import api_view
from rest_framework.response import Response

from .graph import run_weekly_plan


@api_view(['GET'])
def plan_week(request):
	plan = run_weekly_plan(request.user)
	return Response(plan)
