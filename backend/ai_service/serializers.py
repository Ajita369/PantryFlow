from rest_framework import serializers


class MealExplanationRequestSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    matched_ingredients = serializers.ListField(child=serializers.CharField())
    missing_ingredients = serializers.ListField(child=serializers.CharField())
    substitutions = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()), required=False
    )


class SubstitutionRequestSerializer(serializers.Serializer):
    missing_ingredients = serializers.ListField(child=serializers.CharField())
    substitutions = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()), required=False
    )


class ShoppingNotesRequestSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.DictField())
    totals = serializers.DictField()
