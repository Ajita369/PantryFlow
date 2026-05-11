from django.urls import path

from .views import generate_meals, meal_suggestions

urlpatterns = [
    path('meals/suggestions/', meal_suggestions, name='meal-suggestions'),
    path('meals/generate/', generate_meals, name='meal-generate'),
]
