# views.py
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from ..models import Item, ItemWarehouseInfo
from .serializers import (
    ItemSerializer, 
    ItemCreateUpdateSerializer, 
    ItemWarehouseInfoSerializer,
    ItemListSerializer
)
from .permissions import InventoryHasDynamicModelPermission

class ItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows items to be viewed or edited.
    """
    queryset = Item.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, InventoryHasDynamicModelPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_inventory_item', 'is_sales_item', 'is_purchase_item', 'is_service', 'item_group']
    search_fields = ['code', 'name', 'description', 'barcode']
    ordering_fields = ['code', 'name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    swagger_tags = ['Items']  # Add this line for tag categorization

    def get_serializer_class(self):
        if self.action == 'list':
            return ItemSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ItemCreateUpdateSerializer
        return ItemSerializer

    def get_queryset(self):
        queryset = Item.objects.select_related(
            'item_group', 
            'inventory_uom',
            'purchase_uom',
            'sales_uom',
            'default_warehouse'
        ).prefetch_related('warehouse_info__warehouse')
        
        # Filter by warehouse if provided
        warehouse_id = self.request.query_params.get('warehouse', None)
        if warehouse_id:
            queryset = queryset.filter(warehouse_info__warehouse_id=warehouse_id)
        
        return queryset

    @swagger_auto_schema(
        operation_summary="List all inventory items",
        operation_description="Returns a list of all inventory items the user has access to view.",
        tags=['Items']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create a new inventory item",
        operation_description="Creates a new inventory item with the provided data.",
        tags=['Items']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve a specific inventory item",
        operation_description="Returns the details of a specific inventory item.",
        tags=['Items']
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update an inventory item",
        operation_description="Updates the specified inventory item with the provided data.",
        tags=['Items']
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially update an inventory item",
        operation_description="Partially updates the specified inventory item with the provided data.",
        tags=['Items']
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete an inventory item",
        operation_description="Deletes the specified inventory item.",
        tags=['Items']
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Get warehouse info for an item",
        operation_description="Returns warehouse information for a specific inventory item.",
        tags=['Items']
    )
    @action(detail=True, methods=['get'])
    def warehouse_info(self, request, pk=None):
        """
        Retrieve warehouse info for a specific item
        """
        item = self.get_object()
        warehouse_info = item.warehouse_info.all()
        serializer = ItemWarehouseInfoSerializer(warehouse_info, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Search for inventory items",
        operation_description="Search for inventory items by code or name.",
        tags=['Items']
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search for items by code or name
        """
        query = request.query_params.get('query', '')
        
        if query:
            items = Item.objects.filter(
                Q(code__icontains=query) | 
                Q(name__icontains=query)
            ).filter(is_active=True).select_related(
                'inventory_uom', 
                'default_warehouse'
            ).prefetch_related('warehouse_info__warehouse')[:100]
        else:
            items = Item.objects.filter(is_active=True).select_related(
                'inventory_uom', 
                'default_warehouse'
            ).prefetch_related('warehouse_info__warehouse')[:100]
        
        serializer = ItemSerializer(items, many=True)
        return Response(serializer.data)

