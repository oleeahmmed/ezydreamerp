from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal

from Sales.models import ReturnLine
from Inventory.models import InventoryTransaction, Item, ItemWarehouseInfo

@receiver(post_save, sender=ReturnLine)
def create_return_transaction(sender, instance, created, **kwargs):
    """
    Create or update inventory transaction when a ReturnLine is saved.
    - Increases in_stock in ItemWarehouseInfo (does not affect committed).
    - Records a RETURN transaction in InventoryTransaction.
    """
    if instance.return_doc.status != "Open":
        return  # Only process returns with status 'Open'

    try:
        item_instance = Item.objects.get(code=instance.item_code)
        warehouse = item_instance.default_warehouse
        if not warehouse:
            return  # If no warehouse found, exit

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
                    'max_stock': item_instance.maximum_stock,
                    'reorder_point': item_instance.reorder_point
                }
            )

            # Handle existing transaction if updating
            old_quantity = Decimal('0')
            if not created:
                old_transaction = InventoryTransaction.objects.filter(
                    reference=f"RET-{instance.return_doc.id}-{instance.pk}",
                    item_code=instance.item_code,
                    transaction_type="RETURN"
                ).first()
                if old_transaction:
                    old_quantity = old_transaction.quantity
                    old_transaction.delete()

            # Adjust in_stock (add back old quantity, then add new quantity)
            warehouse_info.in_stock += old_quantity
            warehouse_info.in_stock += instance.quantity
            warehouse_info.save(update_fields=['in_stock', 'available', 'updated_at'])  # Updates available field automatically

            # Create new RETURN transaction
            InventoryTransaction.objects.create(
                item_code=instance.item_code,
                item_name=instance.item_name,
                warehouse=warehouse,
                transaction_type="RETURN",
                quantity=instance.quantity,
                unit_price=instance.unit_price,
                reference=f"RET-{instance.return_doc.id}-{instance.pk}",
                notes="Auto created from ReturnLine Save"
            )

    except Item.DoesNotExist:
        pass

@receiver(post_delete, sender=ReturnLine)
def delete_return_transaction(sender, instance, **kwargs):
    """
    Delete inventory transaction and reverse stock adjustments when a ReturnLine is deleted.
    - Reduces in_stock in ItemWarehouseInfo (does not affect committed).
    - Deletes the corresponding RETURN transaction.
    """
    if instance.return_doc.status != "Open":
        return  # Only process returns with status 'Open'

    try:
        item_instance = Item.objects.get(code=instance.item_code)
        warehouse = item_instance.default_warehouse
        if not warehouse:
            return  # If no warehouse found, exit

        with transaction.atomic():
            # Get ItemWarehouseInfo
            warehouse_info = ItemWarehouseInfo.objects.get(item=item_instance, warehouse=warehouse)

            # Find and delete the transaction
            transaction = InventoryTransaction.objects.filter(
                reference=f"RET-{instance.return_doc.id}-{instance.pk}",
                item_code=instance.item_code,
                transaction_type="RETURN"
            ).first()

            if transaction:
                # Reverse the stock adjustment (subtract the returned quantity from in_stock)
                warehouse_info.in_stock -= transaction.quantity
                if warehouse_info.in_stock < 0:
                    warehouse_info.in_stock = 0
                warehouse_info.save(update_fields=['in_stock', 'available', 'updated_at'])  # Updates available field

                # Delete the transaction
                transaction.delete()

    except (Item.DoesNotExist, ItemWarehouseInfo.DoesNotExist):
        pass
