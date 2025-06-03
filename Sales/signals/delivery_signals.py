from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from Sales.models import DeliveryLine
from Inventory.models import ItemWarehouseInfo, Item, InventoryTransaction
from django.db import transaction
from decimal import Decimal

@receiver(post_save, sender=DeliveryLine)
def handle_delivery_line_save(sender, instance, created, **kwargs):
    """
    যখন DeliveryLine তৈরি বা আপডেট হবে:
    - in_stock কমবে
    - committed কমবে
    - InventoryTransaction আপডেট হবে
    """
    if instance.delivery.status != "Open":
        return

    try:
        item = Item.objects.get(code=instance.item_code)
        warehouse = item.default_warehouse
        if not warehouse:
            return

        with transaction.atomic():
            item_warehouse, created_info = ItemWarehouseInfo.objects.get_or_create(
                item=item,
                warehouse=warehouse,
                defaults={
                    'in_stock': 0,
                    'committed': 0,
                    'ordered': 0,
                    'available': 0
                }
            )

            # ✅ প্রথমে Old Transaction খুঁজবো
            old_transaction = InventoryTransaction.objects.filter(
                item_code=instance.item_code,
                warehouse=warehouse,
                transaction_type="DELIVERY",
                reference=f"DEL-{instance.delivery.id}-{instance.pk}"
            ).first()

            old_quantity = Decimal('0')
            if old_transaction:
                old_quantity = old_transaction.quantity
                old_transaction.delete()

            # ✅ in_stock এবং committed থেকে আগের quantity ফেরত আনবো
            item_warehouse.in_stock += old_quantity
            item_warehouse.committed += old_quantity

            # ✅ তারপর নতুন quantity মাইনাস করবো
            item_warehouse.in_stock -= instance.quantity
            if item_warehouse.in_stock < 0:
                item_warehouse.in_stock = 0

            item_warehouse.committed -= instance.quantity
            if item_warehouse.committed < 0:
                item_warehouse.committed = 0

            item_warehouse.save(update_fields=["in_stock", "committed", "available", "updated_at"])

            # ✅ নতুন InventoryTransaction Save করবো
            InventoryTransaction.objects.create(
                item_code=instance.item_code,
                item_name=instance.item_name,
                warehouse=warehouse,
                transaction_type="DELIVERY",
                quantity=instance.quantity,
                unit_price=instance.unit_price,
                reference=f"DEL-{instance.delivery.id}-{instance.pk}",
                notes="Auto created from DeliveryLine Save"
            )

    except Item.DoesNotExist:
        pass

@receiver(post_delete, sender=DeliveryLine)
def handle_delivery_line_delete(sender, instance, **kwargs):
    """
    যখন DeliveryLine delete হবে:
    - in_stock বাড়বে
    - committed বাড়বে
    - InventoryTransaction delete হবে
    """
    if instance.delivery.status != "Open":
        return

    try:
        item = Item.objects.get(code=instance.item_code)
        warehouse = item.default_warehouse
        if not warehouse:
            return

        with transaction.atomic():
            item_warehouse = ItemWarehouseInfo.objects.get(item=item, warehouse=warehouse)

            # ✅ in_stock এবং committed quantity ফেরত আনবো
            item_warehouse.in_stock += instance.quantity
            item_warehouse.committed += instance.quantity
            item_warehouse.save(update_fields=["in_stock", "committed", "available", "updated_at"])

            # ✅ Inventory Transaction delete করবো
            InventoryTransaction.objects.filter(
                item_code=instance.item_code,
                warehouse=warehouse,
                reference=f"DEL-{instance.delivery.id}-{instance.pk}",
                transaction_type="DELIVERY"
            ).delete()

    except (Item.DoesNotExist, ItemWarehouseInfo.DoesNotExist):
        pass
