from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal

from Purchase.models import GoodsReturnLine
from Inventory.models import InventoryTransaction, Item, ItemWarehouseInfo

@receiver(post_save, sender=GoodsReturnLine)
def create_goods_return_transaction(sender, instance, created, **kwargs):
    """Create or update inventory transaction when a GoodsReturnLine is saved."""
    # Only process if the goods return is in Open status
    if instance.goods_return.status != 'Open':
        return
        
    try:
        item_instance = Item.objects.get(code=instance.item_code)
        warehouse = instance.goods_return.warehouse or item_instance.default_warehouse
        
        if not warehouse:
            return
            
        with transaction.atomic():
            # Get or create ItemWarehouseInfo
            warehouse_info, created_info = ItemWarehouseInfo.objects.get_or_create(
                item=item_instance,
                warehouse=warehouse,
                defaults={
                    'in_stock': 0,
                    'committed': 0,
                    'ordered': 0,
                    'available': 0,
                    'min_stock': item_instance.minimum_stock,
                    'max_stock': item_instance.maximum_stock
                }
            )
            
            # Calculate quantity change
            old_quantity = Decimal('0')
            if not created:
                # Find existing transaction to determine quantity change
                old_transaction = InventoryTransaction.objects.filter(
                    reference=f"GR-{instance.goods_return.id}",
                    item_code=instance.item_code
                ).first()
                
                if old_transaction:
                    old_quantity = old_transaction.quantity
                    
                    # Delete existing transaction for this line if updating
                    InventoryTransaction.objects.filter(
                        reference=f"GR-{instance.goods_return.id}",
                        item_code=instance.item_code
                    ).delete()
            
            # Update in_stock (add old quantity and subtract new quantity since this is a return)
            warehouse_info.in_stock = warehouse_info.in_stock + old_quantity - instance.quantity
            warehouse_info.save()  # This will also update available field
            
            # Create new transaction
            InventoryTransaction.objects.create(
                item_code=instance.item_code,
                item_name=instance.item_name,
                warehouse=warehouse,
                transaction_type="RETURN",
                quantity=instance.quantity,
                unit_price=instance.unit_price,
                reference=f"GR-{instance.goods_return.id}"
            )
    except Item.DoesNotExist:
        pass


@receiver(post_delete, sender=GoodsReturnLine)
def delete_goods_return_transaction(sender, instance, **kwargs):
    """Delete inventory transaction when a GoodsReturnLine is deleted."""
    # Only process if the goods return is in Open status
    if instance.goods_return.status != 'Open':
        return
        
    try:
        item_instance = Item.objects.get(code=instance.item_code)
        warehouse = instance.goods_return.warehouse or item_instance.default_warehouse
        
        if not warehouse:
            return
            
        with transaction.atomic():
            # Get transaction to determine quantity
            transaction = InventoryTransaction.objects.filter(
                reference=f"GR-{instance.goods_return.id}",
                item_code=instance.item_code
            ).first()
            
            if transaction:
                # Update warehouse info
                warehouse_info = ItemWarehouseInfo.objects.filter(
                    item=item_instance,
                    warehouse=warehouse
                ).first()
                
                if warehouse_info:
                    # Add the deleted quantity back to in_stock (since this was a return)
                    warehouse_info.in_stock += transaction.quantity
                    warehouse_info.save()  # This will also update available field
                
                # Delete the transaction
                transaction.delete()
    except Item.DoesNotExist:
        pass