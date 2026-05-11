from django.test import SimpleTestCase

from .views import build_meal_groups


class MealGroupingTests(SimpleTestCase):
    def test_groups_are_balanced_and_possible_later_is_capped(self):
        pantry_items = [
            {'name': 'rice', 'name_norm': 'rice', 'category': 'grains'},
            {'name': 'bread', 'name_norm': 'bread', 'category': 'grains'},
        ]
        meal_candidates = [
            {
                'id': 1,
                'title': 'Rice toast',
                'estimated_time_minutes': 10,
                'ingredients': ['rice', 'bread'],
            },
            {
                'id': 2,
                'title': 'Rice bowl',
                'estimated_time_minutes': 15,
                'ingredients': ['rice', 'beans'],
            },
            {
                'id': 3,
                'title': 'Bread plate',
                'estimated_time_minutes': 12,
                'ingredients': ['bread', 'cheese'],
            },
            {
                'id': 4,
                'title': 'Soup',
                'estimated_time_minutes': 20,
                'ingredients': ['tomato', 'onion'],
            },
            {
                'id': 5,
                'title': 'Pasta',
                'estimated_time_minutes': 25,
                'ingredients': ['pasta', 'milk'],
            },
            {
                'id': 6,
                'title': 'Salad',
                'estimated_time_minutes': 8,
                'ingredients': ['lettuce', 'cucumber'],
            },
            {
                'id': 7,
                'title': 'Curry',
                'estimated_time_minutes': 30,
                'ingredients': ['potato', 'peas'],
            },
        ]

        groups = build_meal_groups(
            pantry_items,
            urgent_names=set(),
            meal_candidates=meal_candidates,
            source='llm',
        )

        self.assertGreaterEqual(len(groups['cook_today']), 1)
        self.assertGreaterEqual(len(groups['cook_this_week']), 2)
        self.assertLessEqual(len(groups['possible_later']), 3)
