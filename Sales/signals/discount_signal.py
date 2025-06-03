from django.db.models.signals import post_save
from django.dispatch import receiver
from Sales.models import SalesOrder, SalesOrderLine
from Sales.utils import apply_free_items, adjust_committed_quantity

@receiver(post_save, sender=SalesOrder)
def handle_sales_order_update(sender, instance, created, **kwargs):
    if instance.status == "Open":
        apply_free_items(instance)
        for line in instance.lines.all():
            adjust_committed_quantity(line)

@receiver(post_save, sender=SalesOrderLine)
def handle_sales_order_line_change(sender, instance, created, **kwargs):
    if instance.remarks == "Free Item (Auto)":  # ✅ Prevent infinite recursion
        return
    if instance.order.status == "Open":
        apply_free_items(instance.order)
        adjust_committed_quantity(instance)
