from django.core.validators import MinValueValidator
from django.db import models


class PantryItem(models.Model):
	name = models.CharField(max_length=120)
	category = models.CharField(max_length=80, blank=True)
	quantity = models.DecimalField(
		max_digits=8,
		decimal_places=2,
		validators=[MinValueValidator(0)],
	)
	unit = models.CharField(max_length=40, blank=True)
	expiry_date = models.DateField(null=True, blank=True)
	purchase_date = models.DateField(null=True, blank=True)
	notes = models.TextField(blank=True)
	location = models.CharField(max_length=60, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['expiry_date', 'name']

	def __str__(self) -> str:
		return self.name
