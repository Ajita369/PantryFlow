from decimal import Decimal

from django.test import SimpleTestCase

from .models import ShoppingListItem
from .views import apply_budget, build_meal_shopping_candidates


class MealShoppingCandidateTests(SimpleTestCase):
    def test_candidates_follow_recommended_meal_order_and_dedupe_items(self):
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
            'possible_later': [
                {
                    'title': 'Breakfast bowl',
                    'missing_ingredients': ['berries'],
                }
            ],
        }

        candidates = build_meal_shopping_candidates(meals)

        self.assertEqual([item.name for item in candidates], ['tomato', 'cheese', 'yogurt', 'berries'])
        self.assertEqual(candidates[0].priority, ShoppingListItem.Priority.HIGH)
        self.assertEqual(candidates[2].priority, ShoppingListItem.Priority.MEDIUM)
        self.assertEqual(candidates[3].priority, ShoppingListItem.Priority.LOW)
        self.assertIn('cook today', candidates[0].reason)

    def test_apply_budget_can_preserve_candidate_order(self):
        items = [
            ShoppingListItem(
                name='tomato',
                estimated_price=Decimal('3.50'),
                quantity=Decimal('1.00'),
                priority=ShoppingListItem.Priority.HIGH,
            ),
            ShoppingListItem(
                name='cheese',
                estimated_price=Decimal('4.00'),
                quantity=Decimal('1.00'),
                priority=ShoppingListItem.Priority.HIGH,
            ),
            ShoppingListItem(
                name='rice',
                estimated_price=Decimal('2.50'),
                quantity=Decimal('1.00'),
                priority=ShoppingListItem.Priority.MEDIUM,
            ),
        ]
        budget = type('Budget', (), {'weekly_budget_amount': Decimal('6.00')})()

        selected = apply_budget(items, budget, preserve_order=True)

        self.assertEqual([item.name for item in selected], ['tomato', 'rice'])
