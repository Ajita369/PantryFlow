from django.urls import path

from .views import meal_explanation, shopping_notes, substitution_explanation

urlpatterns = [
    path('ai/meal-explanation/', meal_explanation, name='meal-explanation'),
    path('ai/substitution/', substitution_explanation, name='substitution-explanation'),
    path('ai/shopping-notes/', shopping_notes, name='shopping-notes'),
]
