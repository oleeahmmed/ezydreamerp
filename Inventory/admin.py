from django.contrib import admin
from .models import (
    UnitOfMeasure,
    Warehouse,
    ItemGroup,
    Item,
    ItemWarehouseInfo,
    InventoryTransaction,
    GoodsReceipt,
    GoodsReceiptLine,
    GoodsIssue,
    GoodsIssueLine,
    InventoryTransfer,
    InventoryTransferLine,
)

@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_default', 'contact_person', 'contact_phone', 'is_active')

@admin.register(ItemGroup)
class ItemGroupAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'parent', 'is_active')

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'item_group', 'inventory_uom', 'default_warehouse', 'is_inventory_item', 'is_sales_item', 'is_active')

@admin.register(ItemWarehouseInfo)
class ItemWarehouseInfoAdmin(admin.ModelAdmin):
    list_display = ('item', 'warehouse', 'in_stock', 'committed', 'ordered', 'available')

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'item_code', 'item_name', 'warehouse', 'quantity', 'total_amount', 'transaction_date')

@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'document_date', 'posting_date', 'supplier', 'status', 'total_amount', 'payable_amount')

@admin.register(GoodsReceiptLine)
class GoodsReceiptLineAdmin(admin.ModelAdmin):
    list_display = ('goods_receipt', 'item_code', 'item_name', 'quantity', 'unit_price', 'total_amount')

@admin.register(GoodsIssue)
class GoodsIssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'document_date', 'posting_date', 'recipient', 'status', 'total_amount', 'payable_amount')

@admin.register(GoodsIssueLine)
class GoodsIssueLineAdmin(admin.ModelAdmin):
    list_display = ('goods_issue', 'item_code', 'item_name', 'quantity', 'unit_price', 'total_amount')

@admin.register(InventoryTransfer)
class InventoryTransferAdmin(admin.ModelAdmin):
    list_display = ('id', 'document_date', 'posting_date', 'from_warehouse', 'to_warehouse', 'status', 'total_amount')

@admin.register(InventoryTransferLine)
class InventoryTransferLineAdmin(admin.ModelAdmin):
    list_display = ('inventory_transfer', 'item_code', 'item_name', 'quantity', 'from_warehouse', 'to_warehouse', 'total_amount')
