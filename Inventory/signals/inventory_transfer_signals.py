from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction

from Inventory.models import InventoryTransferLine, InventoryTransaction, Item

@receiver(post_save, sender=InventoryTransferLine)
def create_transfer_transactions(sender, instance, created, **kwargs):
    """Create or update inventory transactions when an InventoryTransferLine is saved."""
    if instance.inventory_transfer.status != 'Posted':
        return  # Only process posted documents
        
    try:
        item_instance = Item.objects.get(code=instance.item_code)
        
        with transaction.atomic():
            # Delete existing transactions for this line if updating
            if not created:
                InventoryTransaction.objects.filter(
                    reference=f"IT-{instance.inventory_transfer.id}",
                    item_code=instance.item_code
                ).delete()
            
            # Create outgoing transaction (negative quantity)
            InventoryTransaction.objects.create(
                item_code=instance.item_code,
                item_name=instance.item_name,
                warehouse=instance.from_warehouse,
                transaction_type="TRANSFER",
                quantity=-instance.quantity,  # Negative for outgoing
                unit_price=instance.unit_price,
                reference=f"IT-{instance.inventory_transfer.id}-OUT"
            )
            
            # Create incoming transaction (positive quantity)
            InventoryTransaction.objects.create(
                item_code=instance.item_code,
                item_name=instance.item_name,
                warehouse=instance.to_warehouse,
                transaction_type="TRANSFER",
                quantity=instance.quantity,  # Positive for incoming
                unit_price=instance.unit_price,
                reference=f"IT-{instance.inventory_transfer.id}-IN"
            )
    except Item.DoesNotExist:
        pass


@receiver(post_delete, sender=InventoryTransferLine)
def delete_transfer_transactions(sender, instance, **kwargs):
    """Delete inventory transactions when an InventoryTransferLine is deleted."""
    InventoryTransaction.objects.filter(
        reference__startswith=f"IT-{instance.inventory_transfer.id}",
        item_code=instance.item_code
    ).delete()