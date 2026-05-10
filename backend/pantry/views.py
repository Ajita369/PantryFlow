from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import PantryItem
from .serializers import PantryItemSerializer


class PantryItemViewSet(viewsets.ModelViewSet):
	serializer_class = PantryItemSerializer

	def get_queryset(self):
		queryset = PantryItem.objects.filter(user=self.request.user)
		category = self.request.query_params.get('category')
		search = self.request.query_params.get('search')

		if category:
			queryset = queryset.filter(category__iexact=category.strip())

		if search:
			term = search.strip()
			queryset = queryset.filter(
				Q(name__icontains=term) | Q(category__icontains=term)
			)

		return queryset.order_by('expiry_date', 'name')

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)

	@action(detail=False, methods=['get'], url_path='expired')
	def expired(self, request):
		today = timezone.localdate()
		queryset = self.get_queryset().filter(expiry_date__lt=today)
		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data)

	@action(detail=False, methods=['get'], url_path='expiring-soon')
	def expiring_soon(self, request):
		today = timezone.localdate()
		days_param = request.query_params.get('days', '7')

		try:
			days = max(1, int(days_param))
		except ValueError:
			days = 7

		cutoff = today + timedelta(days=days)
		queryset = self.get_queryset().filter(
			expiry_date__gte=today, expiry_date__lte=cutoff
		)
		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data)

	@action(detail=False, methods=['get'], url_path='search')
	def search(self, request):
		term = request.query_params.get('q', '').strip()
		if not term:
			return Response([])

		queryset = self.get_queryset().filter(
			Q(name__icontains=term) | Q(category__icontains=term)
		).order_by('expiry_date', 'name')
		serializer = self.get_serializer(queryset, many=True)
		return Response(serializer.data)
