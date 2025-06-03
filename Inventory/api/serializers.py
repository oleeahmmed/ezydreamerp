# serializers.py
from rest_framework import serializers
from ..models import Item, ItemWarehouseInfo, UnitOfMeasure, Warehouse, ItemGroup

class UnitOfMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = ['id', 'code', 'name']

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ['id', 'code', 'name']

class ItemGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemGroup
        fields = ['id', 'code', 'name']

class ItemWarehouseInfoSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    
    class Meta:
        model = ItemWarehouseInfo
        fields = ['id', 'warehouse', 'warehouse_name', 'in_stock', 'committed', 
                  'ordered', 'available', 'min_stock', 'max_stock', 'reorder_point']

class ItemListSerializer(serializers.ModelSerializer):
    """Serializer for list view with limited fields"""
    item_group_name = serializers.CharField(source='item_group.name', read_only=True)
    inventory_uom_name = serializers.CharField(source='inventory_uom.name', read_only=True)
    default_warehouse_name = serializers.CharField(source='default_warehouse.name', read_only=True, allow_null=True)
    image = serializers.SerializerMethodField()
    in_stock = serializers.SerializerMethodField()
    committed = serializers.SerializerMethodField()
    ordered = serializers.SerializerMethodField()
    available = serializers.SerializerMethodField()
    
    class Meta:
        model = Item
        fields = [
            'id', 'code', 'name', 
            'item_group_name', 'inventory_uom_name', 'default_warehouse_name',
            'minimum_stock', 'maximum_stock', 'reorder_point', 'unit_price',
            'image', 'in_stock', 'committed', 'ordered', 'available'
        ]


    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            image_url = obj.image.url
            if request is not None:
                return request.build_absolute_uri(image_url)
            return image_url
        return None
    
    def get_in_stock(self, obj):
        warehouse_info = obj.warehouse_info.filter(warehouse=obj.default_warehouse).first()
        return warehouse_info.in_stock if warehouse_info else 0
    
    def get_committed(self, obj):
        warehouse_info = obj.warehouse_info.filter(warehouse=obj.default_warehouse).first()
        return warehouse_info.committed if warehouse_info else 0
    
    def get_ordered(self, obj):
        warehouse_info = obj.warehouse_info.filter(warehouse=obj.default_warehouse).first()
        return warehouse_info.ordered if warehouse_info else 0
    
    def get_available(self, obj):
        warehouse_info = obj.warehouse_info.filter(warehouse=obj.default_warehouse).first()
        return warehouse_info.available if warehouse_info else 0
 
class ItemSerializer(serializers.ModelSerializer):
    item_group_name = serializers.CharField(source='item_group.name', read_only=True)
    inventory_uom_name = serializers.CharField(source='inventory_uom.name', read_only=True)
    purchase_uom_name = serializers.CharField(source='purchase_uom.name', read_only=True, allow_null=True)
    sales_uom_name = serializers.CharField(source='sales_uom.name', read_only=True, allow_null=True)
    default_warehouse_name = serializers.CharField(source='default_warehouse.name', read_only=True, allow_null=True)
    warehouse_info = ItemWarehouseInfoSerializer(many=True, read_only=True, source='warehouse_info.all')
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Item
        fields = [
            'id', 'code', 'name', 'description', 'item_group', 'item_group_name',
            'inventory_uom', 'inventory_uom_name', 'purchase_uom', 'purchase_uom_name',
            'sales_uom', 'sales_uom_name', 'is_inventory_item', 'is_sales_item',
            'is_purchase_item', 'is_service', 'default_warehouse', 'default_warehouse_name',
            'minimum_stock', 'maximum_stock', 'reorder_point', 'barcode', 'weight',
            'volume', 'image','image_url', 'unit_price', 'item_cost', 'purchase_price',
            'selling_price', 'markup_percentage', 'discount_percentage',
            'created_at', 'updated_at', 'is_active', 'warehouse_info'
        ]
    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            image_url = obj.image.url
            if request is not None:
                return request.build_absolute_uri(image_url)
            return image_url
        return None

class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = [
            'code', 'name', 'description', 'item_group', 'inventory_uom',
            'purchase_uom', 'sales_uom', 'is_inventory_item', 'is_sales_item',
            'is_purchase_item', 'is_service', 'default_warehouse',
            'minimum_stock', 'maximum_stock', 'reorder_point', 'barcode', 'weight',
            'volume', 'image_url', 'unit_price', 'item_cost', 'purchase_price',
            'selling_price', 'markup_percentage', 'discount_percentage', 'is_active'
        ]