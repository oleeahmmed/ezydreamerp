from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from Inventory.models import ItemWarehouseInfo
from global_settings.models import Notification

@receiver(post_save, sender=ItemWarehouseInfo)
def check_stock_levels_and_notify(sender, instance, **kwargs):
    """
    Monitor stock levels in ItemWarehouseInfo and create notifications when:
    1. In stock quantity is less than minimum stock (low stock alert)
    2. In stock quantity is greater than maximum stock (excess stock alert)
    3. In stock quantity is at or below reorder point (reorder alert)
    """
    # Skip if min_stock, max_stock, or reorder_point are not set
    if instance.min_stock is None and instance.max_stock is None and instance.reorder_point is None:
        return
    
    item_name = f"{instance.item.code} - {instance.item.name}"
    warehouse_name = instance.warehouse.name
    
    # Check for low stock
    if instance.min_stock is not None and instance.in_stock < instance.min_stock:
        create_stock_notification(
            title=_("Low Stock Alert"),
            message=_(f"Item {item_name} is below minimum stock level in {warehouse_name}. "
                     f"Current stock: {instance.in_stock}, Minimum required: {instance.min_stock}"),
            notification_type="warning"
        )
    
    # Check for excess stock
    if instance.max_stock is not None and instance.in_stock > instance.max_stock:
        create_stock_notification(
            title=_("Excess Stock Alert"),
            message=_(f"Item {item_name} exceeds maximum stock level in {warehouse_name}. "
                     f"Current stock: {instance.in_stock}, Maximum allowed: {instance.max_stock}"),
            notification_type="info"
        )
    
    # Check for reorder point
    if instance.reorder_point is not None and instance.in_stock <= instance.reorder_point:
        create_stock_notification(
            title=_("Reorder Point Reached"),
            message=_(f"Item {item_name} has reached reorder point in {warehouse_name}. "
                     f"Current stock: {instance.in_stock}, Reorder point: {instance.reorder_point}"),
            notification_type="warning"
        )

def create_stock_notification(title, message, notification_type):
    """
    Helper function to create a notification for superusers.
    """
    with transaction.atomic():
        # Get all superusers
        superusers = User.objects.filter(is_superuser=True)
        
        if superusers.exists():
            # Create individual notifications for each superuser
            for superuser in superusers:
                Notification.objects.create(
                    recipient=superuser,
                    all_users=False,
                    title=title,
                    message=message,
                    notification_type=notification_type
                )
        else:
            # If no superusers exist, create a notification for all users
            Notification.objects.create(
                all_users=True,
                title=title,
                message=message,
                notification_type=notification_type
            )