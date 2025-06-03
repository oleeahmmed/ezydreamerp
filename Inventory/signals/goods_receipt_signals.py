from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal

from Inventory.models import GoodsReceiptLine, InventoryTransaction, Item, ItemWarehouseInfo

# ------------------------------------------
# ✅ GoodsReceiptLine Create হলে কাজ করবে
# ------------------------------------------
@receiver(post_save, sender=GoodsReceiptLine)
def create_receipt_transaction(sender, instance, created, **kwargs):
    """
    নতুন GoodsReceiptLine তৈরি হলে স্টক বাড়াবে এবং ট্রানজেকশন রেকর্ড করবে
    """
    if not created:
        return  # শুধুমাত্র নতুন তৈরি হলে কাজ করবো
    
    if instance.goods_receipt.status != 'Posted':
        return  # যদি ডকুমেন্ট পোস্টেড না হয়, তাহলে কিছু করবো না

    try:
        # আইটেম এবং ওয়্যারহাউজ বের করবো
        item_instance = Item.objects.get(code=instance.item_code)
        warehouse = item_instance.default_warehouse

        with transaction.atomic():
            # ওয়্যারহাউজ ইনফো খুঁজবো বা নতুন করে বানাবো
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
            
            # নতুন স্টক যোগ করবো
            warehouse_info.in_stock += instance.quantity
            warehouse_info.save()  # Save করলে available ফিল্ড আপডেট হয়ে যাবে

            # ট্রানজেকশন রেকর্ড করবো
            InventoryTransaction.objects.create(
                item_code=instance.item_code,
                item_name=instance.item_name,
                warehouse=warehouse,
                transaction_type="RECEIPT",
                quantity=instance.quantity,
                unit_price=instance.unit_price,
                reference=f"GR-{instance.goods_receipt.id}"
            )
    except Item.DoesNotExist:
        pass

# ------------------------------------------
# ✅ GoodsReceiptLine Update হলে কাজ করবে
# ------------------------------------------
@receiver(post_save, sender=GoodsReceiptLine)
def update_receipt_transaction(sender, instance, created, **kwargs):
    """
    পুরনো GoodsReceiptLine আপডেট হলে স্টক কমিয়ে নতুন করে যোগ করবে এবং নতুন ট্রানজেকশন রেকর্ড করবে
    """
    if created:
        return  # আপডেটের সময় কাজ করবো, নতুন তৈরি হলে না

    if instance.goods_receipt.status != 'Posted':
        return  # যদি ডকুমেন্ট পোস্টেড না হয়, তাহলে কিছু করবো না

    try:
        # আইটেম এবং ওয়্যারহাউজ বের করবো
        item_instance = Item.objects.get(code=instance.item_code)
        warehouse = item_instance.default_warehouse

        with transaction.atomic():
            # ওয়্যারহাউজ ইনফো খুঁজবো
            warehouse_info = ItemWarehouseInfo.objects.get(item=item_instance, warehouse=warehouse)

            # পুরাতন ট্রানজেকশন খুঁজবো
            old_transaction = InventoryTransaction.objects.filter(
                reference=f"GR-{instance.goods_receipt.id}",
                item_code=instance.item_code
            ).first()

            old_quantity = Decimal('0')
            if old_transaction:
                old_quantity = old_transaction.quantity
                old_transaction.delete()  # পুরনো ট্রানজেকশন ডিলিট করবো

            # স্টক থেকে পুরনো quantity বাদ দিয়ে নতুন quantity যোগ করবো
            warehouse_info.in_stock = warehouse_info.in_stock - old_quantity + instance.quantity
            warehouse_info.save()  # Save করলে available আপডেট হবে

            # নতুন ট্রানজেকশন রেকর্ড করবো
            InventoryTransaction.objects.create(
                item_code=instance.item_code,
                item_name=instance.item_name,
                warehouse=warehouse,
                transaction_type="RECEIPT",
                quantity=instance.quantity,
                unit_price=instance.unit_price,
                reference=f"GR-{instance.goods_receipt.id}"
            )
    except Item.DoesNotExist:
        pass

# ------------------------------------------
# ✅ GoodsReceiptLine Delete হলে কাজ করবে
# ------------------------------------------
@receiver(post_delete, sender=GoodsReceiptLine)
def delete_receipt_transaction(sender, instance, **kwargs):
    """
    GoodsReceiptLine ডিলিট হলে স্টক কমাবে এবং ট্রানজেকশন ডিলিট করবে
    """
    if instance.goods_receipt.status != 'Posted':
        return  # যদি ডকুমেন্ট পোস্টেড না হয়, তাহলে কিছু করবো না

    try:
        # আইটেম এবং ওয়্যারহাউজ বের করবো
        item_instance = Item.objects.get(code=instance.item_code)
        warehouse = item_instance.default_warehouse

        with transaction.atomic():
            # ওয়্যারহাউজ ইনফো খুঁজবো
            warehouse_info = ItemWarehouseInfo.objects.get(item=item_instance, warehouse=warehouse)

            # ট্রানজেকশন খুঁজবো
            old_transaction = InventoryTransaction.objects.filter(
                reference=f"GR-{instance.goods_receipt.id}",
                item_code=instance.item_code
            ).first()

            if old_transaction:
                # স্টক থেকে quantity বাদ দেবো
                warehouse_info.in_stock -= old_transaction.quantity
                warehouse_info.save()  # available ফিল্ডও আপডেট হবে

                # ট্রানজেকশন ডিলিট করবো
                old_transaction.delete()
    except Item.DoesNotExist:
        pass
