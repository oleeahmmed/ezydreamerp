from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from Sales.models import SalesOrderLine
from Inventory.models import ItemWarehouseInfo, Item, InventoryTransaction
from django.db import transaction
from decimal import Decimal

# ------------------------------------------
# ✅ SalesOrderLine Save বা Update হলে স্টক এবং ট্রানজেকশন আপডেট হবে
# ------------------------------------------
@receiver(post_save, sender=SalesOrderLine)
def handle_sales_orderline_commit_stock(sender, instance, created, **kwargs):
    """
    যখন SalesOrderLine তৈরি বা আপডেট হবে:
    - in_stock এবং committed আপডেট হবে
    - InventoryTransaction তৈরি বা আপডেট হবে
    """
    try:
        item = Item.objects.get(code=instance.item_code)
        warehouse = item.default_warehouse
        if not warehouse:
            return  # যদি warehouse না থাকে, কাজ করবে না

        with transaction.atomic():
            # ItemWarehouseInfo রেকর্ড তৈরি বা পাওয়া
            item_warehouse, created_info = ItemWarehouseInfo.objects.get_or_create(
                item=item,
                warehouse=warehouse,
                defaults={'in_stock': 0, 'committed': 0, 'ordered': 0, 'available': 0}
            )

            # ✅ পুরানো ট্রানজেকশন খুঁজে বের করা
            old_transaction = InventoryTransaction.objects.filter(
                item_code=instance.item_code,
                warehouse=warehouse,
                transaction_type="SALE",
                reference=f"SO-{instance.order.id}-{instance.pk}"
            ).first()

            old_quantity = Decimal('0')
            if old_transaction:
                old_quantity = old_transaction.quantity  # পুরানো পরিমাণ ধরে রাখবো
                old_transaction.delete()  # পুরানো ট্রানজেকশন মুছে ফেলবো

            # ✅ পূর্ববর্তী স্টক আপডেট (আগের পরিমাণ ফিরিয়ে আনবো)
            item_warehouse.in_stock += old_quantity
            item_warehouse.committed += old_quantity

            # ✅ নতুন স্টক কমানো হবে (এই সেলস অর্ডারের পরিমাণ অনুসারে)
            item_warehouse.in_stock -= instance.quantity
            if item_warehouse.in_stock < 0:
                item_warehouse.in_stock = 0  # in_stock যদি নেতিবাচক হয়ে যায়, তবে সেটিকে 0 করে দিবো

            item_warehouse.committed -= instance.quantity
            if item_warehouse.committed < 0:
                item_warehouse.committed = 0  # committed স্টক কমানো হবে

            # ✅ WarehouseInfo আপডেট করা
            item_warehouse.save(update_fields=["in_stock", "committed", "available", "updated_at"])

            # ✅ নতুন InventoryTransaction রেকর্ড তৈরি করা
            InventoryTransaction.objects.create(
                item_code=instance.item_code,
                item_name=instance.item_name,
                warehouse=warehouse,
                transaction_type="SALE",  # Transaction type is SALE
                quantity=instance.quantity,
                unit_price=instance.unit_price,
                total_amount=instance.quantity * instance.unit_price,
                reference=f"SO-{instance.order.id}-{instance.pk}",  # SalesOrder reference
                notes="Auto created from SalesOrderLine Save"
            )

    except (Item.DoesNotExist, ItemWarehouseInfo.DoesNotExist):
        pass

# ------------------------------------------
# ✅ SalesOrderLine ডিলিট হলে স্টক এবং ট্রানজেকশন পুনরুদ্ধার হবে
# ------------------------------------------
@receiver(pre_delete, sender=SalesOrderLine)
def delete_sales_orderline_commit_stock(sender, instance, **kwargs):
    """
    যখন SalesOrderLine ডিলিট হবে:
    - in_stock বাড়বে
    - committed বাড়বে
    - InventoryTransaction ডিলিট হবে
    """
    try:
        item = Item.objects.get(code=instance.item_code)
        warehouse = item.default_warehouse
        if not warehouse:
            return  # যদি warehouse না থাকে, কাজ করবে না

        with transaction.atomic():
            # ItemWarehouseInfo রেকর্ড খুঁজে পাওয়া
            item_warehouse = ItemWarehouseInfo.objects.get(item=item, warehouse=warehouse)

            # ✅ in_stock এবং committed স্টক পুনরুদ্ধার করা (যেহেতু ডিলিট হচ্ছে)
            item_warehouse.in_stock += instance.quantity
            item_warehouse.committed += instance.quantity
            item_warehouse.save(update_fields=["in_stock", "committed", "available", "updated_at"])

            # ✅ পূর্বের Inventory Transaction ডিলিট করা
            InventoryTransaction.objects.filter(
                item_code=instance.item_code,
                warehouse=warehouse,
                reference=f"SO-{instance.order.id}-{instance.pk}",
                transaction_type="SALE"
            ).delete()

    except (Item.DoesNotExist, ItemWarehouseInfo.DoesNotExist):
        pass
