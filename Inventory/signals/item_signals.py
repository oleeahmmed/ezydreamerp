from django.db.models.signals import post_save
from django.dispatch import receiver
import django.db.transaction as db_transaction  # ✅ fixed here

from Inventory.models import Item, ItemWarehouseInfo, Warehouse

@receiver(post_save, sender=Item)
def create_or_update_item_warehouse_info(sender, instance, created, **kwargs):
    """
    Create or update ItemWarehouseInfo records for an Item.
    This ensures every Item has warehouse information for its default warehouse
    and synchronizes the min_stock, max_stock, and reorder_point values.
    """
    # Skip if no default warehouse is set
    if not instance.default_warehouse:
        return
        
    # Check if ItemWarehouseInfo already exists for this item and warehouse
    warehouse_info, created = ItemWarehouseInfo.objects.get_or_create(
        item=instance,
        warehouse=instance.default_warehouse,
        defaults={
            'in_stock': 0,
            'committed': 0,
            'ordered': 0,
            'available': 0,
            'min_stock': instance.minimum_stock,
            'max_stock': instance.maximum_stock,
            'reorder_point': instance.reorder_point
        }
    )
    
    # If record already exists, update the min_stock, max_stock, and reorder_point values
    if not created:
        with db_transaction.atomic():  
            warehouse_info.min_stock = instance.minimum_stock
            warehouse_info.max_stock = instance.maximum_stock
            warehouse_info.reorder_point = instance.reorder_point
            warehouse_info.save(update_fields=['min_stock', 'max_stock', 'reorder_point', 'updated_at'])