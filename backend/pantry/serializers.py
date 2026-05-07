from datetime import date

from rest_framework import serializers

from .models import PantryItem


class PantryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PantryItem
        fields = [
            'id',
            'name',
            'category',
            'quantity',
            'unit',
            'expiry_date',
            'purchase_date',
            'notes',
            'location',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError('Name is required.')
        return cleaned

    def validate(self, attrs):
        purchase_date = attrs.get('purchase_date')
        expiry_date = attrs.get('expiry_date')

        if purchase_date and purchase_date > date.today():
            raise serializers.ValidationError(
                {'purchase_date': 'Purchase date cannot be in the future.'}
            )

        if purchase_date and expiry_date and expiry_date < purchase_date:
            raise serializers.ValidationError(
                {'expiry_date': 'Expiry date cannot be before purchase date.'}
            )

        return attrs
