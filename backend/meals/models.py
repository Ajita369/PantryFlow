from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class GeneratedMealSet(models.Model):
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='generated_meal_sets',
	)
	source = models.CharField(max_length=20)
	pantry_hash = models.CharField(max_length=64)
	week_start = models.DateField()
	created_at = models.DateTimeField(auto_now_add=True)
	is_active = models.BooleanField(default=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self) -> str:
		return f'Meal set {self.id} ({self.source})'


class GeneratedMeal(models.Model):
	meal_set = models.ForeignKey(
		GeneratedMealSet,
		on_delete=models.CASCADE,
		related_name='meals',
	)
	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	cuisine_type = models.CharField(max_length=60, blank=True)
	estimated_cost = models.DecimalField(
		max_digits=8,
		decimal_places=2,
		validators=[MinValueValidator(0)],
	)
	estimated_time_minutes = models.IntegerField()
	ingredients = models.JSONField(default=list)
	steps = models.JSONField(default=list)
	category = models.CharField(max_length=30)
	match_score = models.FloatField(default=0.0)
	matched_ingredients = models.JSONField(default=list)
	missing_ingredients = models.JSONField(default=list)
	substitutions = models.JSONField(default=dict)

	class Meta:
		ordering = ['-match_score', 'title']

	def __str__(self) -> str:
		return self.title
