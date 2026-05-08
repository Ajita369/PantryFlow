from datetime import date, timedelta

from rest_framework import serializers

from .models import ShoppingListItem, WeeklyBudget


def default_week_range(today: date) -> tuple[date, date]:
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


class WeeklyBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyBudget
        fields = [
            'id',
            'weekly_budget_amount',
            'currency',
            'week_start_date',
            'week_end_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'currency': {'required': False},
            'week_start_date': {'required': False},
            'week_end_date': {'required': False},
        }

    def validate_currency(self, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            raise serializers.ValidationError('Currency is required.')
        return cleaned

    def validate(self, attrs):
        week_start = attrs.get('week_start_date')
        week_end = attrs.get('week_end_date')

        if not week_start or not week_end:
            if self.instance:
                attrs.setdefault('week_start_date', self.instance.week_start_date)
                attrs.setdefault('week_end_date', self.instance.week_end_date)
            else:
                default_start, default_end = default_week_range(date.today())
                attrs.setdefault('week_start_date', default_start)
                attrs.setdefault('week_end_date', default_end)

            week_start = attrs.get('week_start_date')
            week_end = attrs.get('week_end_date')

        if week_start and week_end and week_start > week_end:
            raise serializers.ValidationError(
                {'week_end_date': 'Week end must be on or after week start.'}
            )

        return attrs


class ShoppingListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingListItem
        fields = [
            'id',
            'name',
            'estimated_price',
            'quantity',
            'unit',
            'priority',
            'is_needed',
            'reason',
            'linked_pantry_item',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Name is required.')
        return cleaned
