from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .graph import build_shopping
from .views import plan_week


class WeeklyPlannerShoppingTests(SimpleTestCase):
    def test_shopping_is_built_from_meal_missing_ingredients(self):
        meals = {
            'cook_today': [
                {
                    'title': 'Tomato pasta',
                    'missing_ingredients': ['tomato', 'cheese'],
                }
            ],
            'cook_this_week': [
                {
                    'title': 'Grain bowl',
                    'missing_ingredients': ['yogurt', 'tomato'],
                }
            ],
            'possible_later': [],
        }

        result = build_shopping({'meals': meals, 'budget_model': None})

        self.assertEqual(
            [item['name'] for item in result['shopping_items']],
            ['tomato', 'cheese', 'yogurt'],
        )
        self.assertEqual(result['shopping_totals']['total_estimated_cost'], '11.50')
        self.assertEqual(result['shopping_totals']['currency'], 'USD')

    def test_shopping_respects_budget_without_reordering_meal_needs(self):
        meals = {
            'cook_today': [
                {
                    'title': 'Tomato pasta',
                    'missing_ingredients': ['tomato', 'cheese'],
                }
            ],
            'cook_this_week': [
                {
                    'title': 'Rice bowl',
                    'missing_ingredients': ['rice'],
                }
            ],
            'possible_later': [],
        }
        budget = type(
            'Budget',
            (),
            {
                'weekly_budget_amount': Decimal('6.00'),
                'currency': 'USD',
            },
        )()

        result = build_shopping({'meals': meals, 'budget_model': budget})

        self.assertEqual([item['name'] for item in result['shopping_items']], ['tomato', 'rice'])
        self.assertEqual(result['shopping_totals']['total_estimated_cost'], '6.00')
        self.assertEqual(result['shopping_totals']['budget_remaining'], '0.00')


class WeeklyPlannerSavedPlanTests(SimpleTestCase):
    def test_get_plan_week_returns_saved_plan_without_generating(self):
        saved_plan = {
            'generated_at': '2026-05-12T12:00:00Z',
            'tasks': ['meals', 'shopping'],
            'warnings': [],
            'budget': None,
            'urgent_items': [],
            'meals': {
                'cook_today': [],
                'cook_this_week': [],
                'possible_later': [],
            },
            'substitutions': [],
            'shopping': {
                'items': [],
                'totals': {
                    'total_estimated_cost': '0.00',
                    'budget_amount': None,
                    'budget_remaining': None,
                    'currency': 'USD',
                },
            },
            'explanation': {'message': 'Saved plan', 'source': 'test', 'fallback': False},
        }

        factory = APIRequestFactory()
        request = factory.get('/api/plan-week/')
        force_authenticate(request, user=SimpleNamespace(is_authenticated=True))

        with (
            patch('planner.views.AIPlanSession.objects') as session_manager,
            patch('planner.views.run_weekly_plan') as run_weekly_plan,
        ):
            session_manager.filter.return_value.order_by.return_value.first.return_value = (
                SimpleNamespace(budget_snapshot={'plan_snapshot': saved_plan})
            )

            response = plan_week(request)

        self.assertEqual(response.data['plan'], saved_plan)
        run_weekly_plan.assert_not_called()
