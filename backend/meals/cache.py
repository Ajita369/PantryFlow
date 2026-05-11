from __future__ import annotations

import hashlib
import json

from pantry.models import PantryItem

from .models import GeneratedMealSet


def compute_pantry_hash(user) -> str:
	items = (
		PantryItem.objects.filter(user=user)
		.order_by('name', 'id')
		.values_list('name', 'quantity', 'expiry_date')
	)
	payload = []
	for name, quantity, expiry_date in items:
		payload.append(
			{
				'name': (name or '').strip().lower(),
				'quantity': str(quantity),
				'expiry_date': expiry_date.isoformat() if expiry_date else '',
			}
		)
	raw = json.dumps(payload, sort_keys=True, separators=(',', ':'))
	return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def get_cached_meals(user):
	current_hash = compute_pantry_hash(user)
	meal_set = (
		GeneratedMealSet.objects.filter(user=user, is_active=True)
		.order_by('-created_at')
		.first()
	)
	if meal_set and meal_set.pantry_hash == current_hash:
		return meal_set, current_hash, False

	pantry_changed = meal_set is not None
	return None, current_hash, pantry_changed


def invalidate_meals(user) -> None:
	GeneratedMealSet.objects.filter(user=user, is_active=True).update(is_active=False)
