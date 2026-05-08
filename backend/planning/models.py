from django.core.validators import MinValueValidator
from django.db import models

from pantry.models import PantryItem


class WeeklyBudget(models.Model):
	weekly_budget_amount = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		validators=[MinValueValidator(0)],
	)
	currency = models.CharField(max_length=10, default='USD')
	week_start_date = models.DateField()
	week_end_date = models.DateField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-week_start_date', '-created_at']

	def __str__(self) -> str:
		return f'{self.week_start_date} budget'


class ShoppingListItem(models.Model):
	class Priority(models.IntegerChoices):
		HIGH = 1, 'High'
		MEDIUM = 2, 'Medium'
		LOW = 3, 'Low'

	name = models.CharField(max_length=120)
	estimated_price = models.DecimalField(
		max_digits=8,
		decimal_places=2,
		validators=[MinValueValidator(0)],
	)
	quantity = models.DecimalField(
		max_digits=8,
		decimal_places=2,
		validators=[MinValueValidator(0)],
	)
	unit = models.CharField(max_length=40, blank=True)
	priority = models.IntegerField(choices=Priority.choices, default=Priority.MEDIUM)
	is_needed = models.BooleanField(default=True)
	reason = models.TextField(blank=True)
	linked_pantry_item = models.ForeignKey(
		PantryItem,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='shopping_list_items',
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['priority', 'name']

	def __str__(self) -> str:
		return self.name
