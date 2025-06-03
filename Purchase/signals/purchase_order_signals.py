# purchase_order_signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal

from Purchase.models import PurchaseOrderLine  # PurchaseOrderLine মডেল
from Inventory.models import InventoryTransaction, Item, ItemWarehouseInfo

@receiver(post_save, sender=PurchaseOrderLine)
def create_purchase_order_transaction(sender, instance, created, **kwargs):
    """Create or update inventory transaction when a PurchaseOrderLine is saved."""
    if instance.order.status != 'Open':  # Ensure order is 'Open'
        return
        
    try:
        item_instance = Item.objects.get(code=instance.item_code)  # Get the item instance
        warehouse = item_instance.default_warehouse  # Use warehouse from the Item instance
        
        if not warehouse:
            return  # Exit if no warehouse is available
            
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
                    reference=f"PO-{instance.order.id}",
                    item_code=instance.item_code
                ).first()
                
                if old_transaction:
                    old_quantity = old_transaction.quantity
                    
                    # Delete existing transaction for this line if updating
                    InventoryTransaction.objects.filter(
                        reference=f"PO-{instance.order.id}",
                        item_code=instance.item_code
                    ).delete()
            
            # Update in_stock (subtract old quantity and add new quantity)
            warehouse_info.in_stock = warehouse_info.in_stock - old_quantity + instance.quantity
            
            # Update ordered quantity
            warehouse_info.ordered = max(0, warehouse_info.ordered + instance.quantity)
            
            warehouse_info.save()  # This will also update available field
            
            # Create new transaction
            InventoryTransaction.objects.create(
                item_code=instance.item_code,
                item_name=instance.item_name,
                warehouse=warehouse,
                transaction_type="ORDER",
                quantity=instance.quantity,
                unit_price=instance.unit_price,
                reference=f"PO-{instance.order.id}"
            )
    except Item.DoesNotExist:
        pass



@receiver(post_delete, sender=PurchaseOrderLine)
def delete_purchase_order_transaction(sender, instance, **kwargs):
    """Delete inventory transaction when a PurchaseOrderLine is deleted."""
    if instance.order.status != 'Open':  # `purchase_order` -> `order`
        return
        
    try:
        item_instance = Item.objects.get(code=instance.item_code)
        warehouse = instance.order.warehouse or item_instance.default_warehouse  # `purchase_order` -> `order`
        
        if not warehouse:
            return
            
        with transaction.atomic():
            # Get transaction to determine quantity
            transaction = InventoryTransaction.objects.filter(
                reference=f"PO-{instance.order.id}",  # `purchase_order` -> `order`
                item_code=instance.item_code
            ).first()
            
            if transaction:
                # Update warehouse info
                warehouse_info = ItemWarehouseInfo.objects.filter(
                    item=item_instance,
                    warehouse=warehouse
                ).first()
                
                if warehouse_info:
                    # Subtract the deleted quantity from in_stock
                    warehouse_info.in_stock -= transaction.quantity
                    
                    # Update ordered quantity
                    warehouse_info.ordered -= transaction.quantity
                        
                    warehouse_info.save()  # This will also update available field
                
                # Delete the transaction
                transaction.delete()
    except Item.DoesNotExist:
        pass
