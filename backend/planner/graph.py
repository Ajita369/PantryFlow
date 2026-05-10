from __future__ import annotations

from datetime import datetime
from typing import Iterable, TypedDict

from django.utils import timezone
from langgraph.graph import END, StateGraph

from ai_service.provider import generate_with_fallback
from meals.views import build_meal_groups, build_urgent_items, normalize
from pantry.models import PantryItem
from planning.models import WeeklyBudget
from planning.views import (
    apply_budget,
    build_shopping_candidates,
    calculate_totals,
    current_budget,
)


class PlanState(TypedDict, total=False):
    user: object
    pantry_models: list[PantryItem]
    pantry_payload: list[dict]
    budget_model: WeeklyBudget | None
    budget: dict | None
    urgent_items: list[dict]
    urgent_names: set[str]
    tasks: list[str]
    meals: dict
    substitutions: list[dict]
    shopping_items: list[dict]
    shopping_totals: dict
    explanation: dict
    warnings: list[str]
    generated_at: str


def serialize_budget(budget: WeeklyBudget | None):
    if not budget:
        return None
    return {
        'id': budget.id,
        'weekly_budget_amount': str(budget.weekly_budget_amount),
        'currency': budget.currency,
        'week_start_date': budget.week_start_date.isoformat(),
        'week_end_date': budget.week_end_date.isoformat(),
        'created_at': budget.created_at.isoformat(),
        'updated_at': budget.updated_at.isoformat(),
    }


def load_data(state: PlanState) -> PlanState:
    user = state.get('user')
    pantry_models = list(PantryItem.objects.filter(user=user))
    budget_model = current_budget(user)
    pantry_payload = [
        {
            'id': item.id,
            'name': item.name,
            'name_norm': normalize(item.name),
            'category': item.category or '',
            'quantity': str(item.quantity),
            'unit': item.unit,
            'expiry_date': item.expiry_date,
        }
        for item in pantry_models
    ]

    return {
        'pantry_models': pantry_models,
        'pantry_payload': pantry_payload,
        'budget_model': budget_model,
        'budget': serialize_budget(budget_model),
        'generated_at': timezone.now().isoformat(),
    }


def compute_urgency(state: PlanState) -> PlanState:
    urgent_items = build_urgent_items(state['pantry_models'])
    urgent_names = {
        normalize(item['name'])
        for item in urgent_items
        if item.get('urgency_score', 0) >= 60
    }
    return {'urgent_items': urgent_items, 'urgent_names': urgent_names}


def decide_tasks(state: PlanState) -> PlanState:
    tasks: list[str] = []
    warnings: list[str] = []

    pantry_models = state['pantry_models']
    urgent_names = state.get('urgent_names', set())

    if not pantry_models:
        warnings.append('Add pantry items to improve meal accuracy.')
        tasks.append('shopping')
    if urgent_names:
        tasks.append('meals')

    low_stock = any(item.quantity <= 1 for item in pantry_models)
    if low_stock:
        tasks.append('shopping')

    if not tasks:
        tasks = ['meals']

    return {'tasks': tasks, 'warnings': warnings}


def summarize_substitutions(meals: dict) -> list[dict]:
    substitution_map: dict[str, list[str]] = {}

    for group in meals.values():
        for meal in group:
            for missing in meal['missing_ingredients']:
                options = meal['substitutions'].get(missing, [])
                if missing not in substitution_map:
                    substitution_map[missing] = []
                for option in options:
                    if option not in substitution_map[missing]:
                        substitution_map[missing].append(option)

    return [
        {'ingredient': ingredient, 'options': options}
        for ingredient, options in substitution_map.items()
    ]


def build_meals(state: PlanState) -> PlanState:
    if 'meals' not in state['tasks']:
        return {
            'meals': {
                'cook_today': [],
                'cook_this_week': [],
                'possible_later': [],
            },
            'substitutions': [],
        }

    meals = build_meal_groups(state['pantry_payload'], state.get('urgent_names', set()))
    substitutions = summarize_substitutions(meals)
    return {'meals': meals, 'substitutions': substitutions}


def serialize_shopping_items(items: Iterable) -> list[dict]:
    payload = []
    for item in items:
        payload.append(
            {
                'name': item.name,
                'estimated_price': str(item.estimated_price),
                'quantity': str(item.quantity),
                'unit': item.unit,
                'priority': item.priority,
                'reason': item.reason,
            }
        )
    return payload


def build_shopping(state: PlanState) -> PlanState:
    if 'shopping' not in state['tasks']:
        return {'shopping_items': [], 'shopping_totals': calculate_totals([], state['budget_model'])}

    candidates = build_shopping_candidates(state['pantry_models'])
    selected = apply_budget(candidates, state['budget_model'])
    totals = calculate_totals(selected, state['budget_model'])
    return {
        'shopping_items': serialize_shopping_items(selected),
        'shopping_totals': totals,
    }


def build_explanation(state: PlanState) -> PlanState:
    urgent_count = len(state.get('urgent_items', []))
    shopping_count = len(state.get('shopping_items', []))
    tasks = ', '.join(state.get('tasks', []))
    fallback = (
        f"Plan focuses on {tasks}."
        f" {urgent_count} urgent items and {shopping_count} shopping items identified."
    )

    prompt = (
        'Write a short weekly plan summary (2-3 sentences).\n'
        f"Tasks: {tasks}\n"
        f"Urgent items: {urgent_count}\n"
        f"Shopping items: {shopping_count}\n"
        f"Budget: {state.get('budget')}\n"
        'Keep it practical and avoid adding new items.'
    )

    message, source, fallback_used = generate_with_fallback(prompt, fallback)
    return {
        'explanation': {
            'message': message,
            'source': source,
            'fallback': fallback_used,
        }
    }


def build_plan_graph():
    graph = StateGraph(PlanState)
    graph.add_node('load_data', load_data)
    graph.add_node('compute_urgency', compute_urgency)
    graph.add_node('decide_tasks', decide_tasks)
    graph.add_node('build_meals', build_meals)
    graph.add_node('build_shopping', build_shopping)
    graph.add_node('build_explanation', build_explanation)

    graph.set_entry_point('load_data')
    graph.add_edge('load_data', 'compute_urgency')
    graph.add_edge('compute_urgency', 'decide_tasks')
    graph.add_edge('decide_tasks', 'build_meals')
    graph.add_edge('build_meals', 'build_shopping')
    graph.add_edge('build_shopping', 'build_explanation')
    graph.add_edge('build_explanation', END)

    return graph.compile()


GRAPH = build_plan_graph()


def run_weekly_plan(user) -> dict:
    result = GRAPH.invoke({'user': user})
    return {
        'generated_at': result.get('generated_at', datetime.utcnow().isoformat()),
        'tasks': result.get('tasks', []),
        'warnings': result.get('warnings', []),
        'budget': result.get('budget'),
        'urgent_items': result.get('urgent_items', []),
        'meals': result.get('meals', {}),
        'substitutions': result.get('substitutions', []),
        'shopping': {
            'items': result.get('shopping_items', []),
            'totals': result.get('shopping_totals', {}),
        },
        'explanation': result.get('explanation', {}),
        'debug': {
            'pantry_count': len(result.get('pantry_models', [])),
            'urgent_count': len(result.get('urgent_items', [])),
            'shopping_count': len(result.get('shopping_items', [])),
        },
    }
