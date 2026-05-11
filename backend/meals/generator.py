from __future__ import annotations

from datetime import date
from typing import Any

from django.utils import timezone

from ai_service.provider import get_default_provider

REQUIRED_KEYS = {
    'title',
    'estimated_cost',
    'estimated_time_minutes',
    'ingredients',
}


def build_meal_prompt(pantry_items: list[dict]) -> str:
    lines = []
    for item in pantry_items:
        expiry_date = item.get('expiry_date')
        days_until = None
        if isinstance(expiry_date, date):
            days_until = (expiry_date - timezone.localdate()).days
        lines.append(
            f"- {item.get('name')} | category: {item.get('category') or 'n/a'} | "
            f"qty: {item.get('quantity')} {item.get('unit') or ''} | "
            f"days_until_expiry: {days_until if days_until is not None else 'n/a'}"
        )

    pantry_section = '\n'.join(lines) if lines else '- (no pantry items)'

    return (
        'You are a meal generator. Return ONLY valid JSON with no markdown.\n'
        'Return a strict JSON array of 8-12 meal objects.\n'
        'Each meal object must include: title, description, cuisine_type, '
        'estimated_cost, estimated_time_minutes, ingredients, steps.\n'
        'ingredients and steps must be arrays of strings.\n'
        'estimated_cost and estimated_time_minutes must be numbers.\n'
        'Rules: use at least 2 pantry items per meal when possible, '
        'keep ingredients to 5-7 items, keep steps to 3-5 steps.\n'
        'Use pantry item names as written when possible.\n'
        'Example format: [{"title":"Potato sandwich","description":"...",'
        '"cuisine_type":"Global","estimated_cost":4.5,'
        '"estimated_time_minutes":15,"ingredients":["bread","potato"],'
        '"steps":["Toast bread","Cook potato","Assemble"]}]\n'
        f'Pantry items:\n{pantry_section}'
    )


def _coerce_string_list(value: Any) -> list[str] | None:
    if isinstance(value, str):
        raw = [chunk.strip() for chunk in value.replace('\n', ',').split(',')]
        cleaned = [item for item in raw if item]
        return cleaned or None
    if not isinstance(value, list):
        return None
    cleaned = [str(item).strip() for item in value if str(item).strip()]
    return cleaned if cleaned else None


def _coerce_number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace('$', '')
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _sanitize_meal(item: dict) -> dict | None:
    if not REQUIRED_KEYS.issubset(item.keys()):
        # Allow relaxed keys when LLM uses synonyms.
        if 'title' not in item or 'ingredients' not in item:
            return None

    title = str(item.get('title', '')).strip()
    description = str(item.get('description', '')).strip()
    cuisine_type = str(item.get('cuisine_type', '')).strip()
    ingredients = _coerce_string_list(item.get('ingredients') or item.get('ingredient_list'))
    steps = _coerce_string_list(item.get('steps'))
    estimated_cost = _coerce_number(
        item.get('estimated_cost')
        or item.get('cost')
        or item.get('estimated_price')
    )
    estimated_time = _coerce_number(
        item.get('estimated_time_minutes')
        or item.get('estimated_time')
        or item.get('cook_time_minutes')
        or item.get('cook_time')
    )

    if not title or not ingredients:
        return None

    if estimated_cost is None:
        estimated_cost = 0.0

    if estimated_time is None:
        estimated_time = 0.0

    return {
        'title': title,
        'description': description,
        'cuisine_type': cuisine_type,
        'estimated_cost': float(estimated_cost),
        'estimated_time_minutes': int(round(estimated_time)),
        'ingredients': ingredients,
        'steps': steps or [],
    }


def validate_meal_json(data: Any) -> list[dict]:
    if isinstance(data, dict):
        data = data.get('meals') or data.get('items') or data.get('candidates') or []
    if not isinstance(data, list):
        return []

    valid: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        sanitized = _sanitize_meal(item)
        if sanitized:
            valid.append(sanitized)

    return valid[:12]


def generate_meal_candidates(pantry_items: list[dict]) -> tuple[list[dict], str | None]:
    provider = get_default_provider()
    if not provider:
        return [], 'Gemini API key not configured.'

    prompt = build_meal_prompt(pantry_items)

    try:
        data = provider.generate_json(
            prompt,
            temperature=0.7,
            max_output_tokens=4096,
        )
    except RuntimeError as exc:
        return [], str(exc)

    candidates = validate_meal_json(data)
    if not candidates:
        return [], 'LLM response did not contain valid meal objects.'

    return candidates, None
