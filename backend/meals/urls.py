from django.urls import path

from .views import meal_suggestions

urlpatterns = [
    path('meals/suggestions/', meal_suggestions, name='meal-suggestions'),
]
