from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from Sales.models import SalesOrder, SalesOrderLine
from Inventory.models import ItemWarehouseInfo, Item

# ------------------------------------------
# ✅ SalesOrderLine Save হওয়ার আগে পুরাতন quantity ধরে রাখবো
# ------------------------------------------
@receiver(pre_save, sender=SalesOrderLine)
def set_old_quantity_before_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = SalesOrderLine.objects.get(pk=instance.pk)
            instance._old_quantity = old_instance.quantity
        except SalesOrderLine.DoesNotExist:
            instance._old_quantity = None
    else:
        instance._old_quantity = None

# ------------------------------------------
# ✅ SalesOrderLine Create বা Update হলে committed আপডেট করবো
# ------------------------------------------
@receiver(post_save, sender=SalesOrderLine)
def handle_sales_orderline_commit_stock(sender, instance, created, **kwargs):
    if instance.order.status != "Open":
        return

    try:
        item = Item.objects.get(code=instance.item_code)
        warehouse = item.default_warehouse
        if not warehouse:
            return

        item_warehouse, _ = ItemWarehouseInfo.objects.get_or_create(
            item=item,
            warehouse=warehouse,
            defaults={'in_stock': 0, 'committed': 0, 'ordered': 0}
        )

        if created:
            item_warehouse.committed += instance.quantity
        else:
            old_quantity = instance._old_quantity or 0
            item_warehouse.committed = item_warehouse.committed - old_quantity + instance.quantity
            if item_warehouse.committed < 0:
                item_warehouse.committed = 0

        item_warehouse.save()

    except (Item.DoesNotExist, ItemWarehouseInfo.DoesNotExist):
        pass

# ------------------------------------------
# ✅ SalesOrderLine ডিলিট হওয়ার সময় committed কমাবো
# ------------------------------------------
@receiver(pre_delete, sender=SalesOrderLine)
def delete_sales_orderline_commit_stock(sender, instance, **kwargs):
    if instance.order.status != "Open":
        return

    try:
        item = Item.objects.get(code=instance.item_code)
        warehouse = item.default_warehouse
        if not warehouse:
            return

        # ItemWarehouseInfo রেকর্ড চেক করি
        try:
            item_warehouse = ItemWarehouseInfo.objects.select_for_update().get(item=item, warehouse=warehouse)
            item_warehouse.committed -= instance.quantity
            if item_warehouse.committed < 0:
                item_warehouse.committed = 0

            # ট্রানজাকশনের মধ্যে save করি
            item_warehouse.save(update_fields=['committed'])
        except ItemWarehouseInfo.DoesNotExist:
            pass  # রেকর্ড না থাকলে উপেক্ষা করি
        except DatabaseError:
            pass  # DatabaseError হলে উপেক্ষা করি যাতে ডিলেট বন্ধ না হয়

    except Item.DoesNotExist:
        pass

# ------------------------------------------
# ✅ SalesOrder ডিলিট হওয়ার সময় সমস্ত লাইনের committed কমাবো
# ------------------------------------------
# @receiver(pre_delete, sender=SalesOrder)
# def delete_sales_order_commit_stock(sender, instance, **kwargs):
#     if instance.status != "Open":
#         return

#     lines = list(instance.lines.all())  # ❗ লাইনের কপি নিচ্ছি

#     for line in lines:
#         try:
#             item = Item.objects.get(code=line.item_code)
#             warehouse = item.default_warehouse
#             if not warehouse:
#                 continue

#             item_warehouse = ItemWarehouseInfo.objects.get(item=item, warehouse=warehouse)

#             item_warehouse.committed -= line.quantity
#             if item_warehouse.committed < 0:
#                 item_warehouse.committed = 0

#             item_warehouse.save()
#         except (Item.DoesNotExist, ItemWarehouseInfo.DoesNotExist):
#             continue