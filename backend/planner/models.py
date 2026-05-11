from django.conf import settings
from django.db import models


class AIPlanSession(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='ai_plan_sessions',
	)
	week_start = models.DateField()
	pantry_snapshot = models.JSONField(default=list)
	budget_snapshot = models.JSONField(default=dict)
	meal_set = models.ForeignKey(
		'meals.GeneratedMealSet',
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='plan_sessions',
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self) -> str:
		return f'Plan session {self.id}'
