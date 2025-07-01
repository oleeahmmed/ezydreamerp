# signals/payment_signals.py

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.core.exceptions import ValidationError
from django.apps import apps
from Banking.utils.payment_utils import (
    validate_payment_amount, 
    calculate_remaining_balance, 
    update_sales_order_payment_info,
    calculate_sales_order_totals_from_lines
)
from Banking.models import Payment

# Use lazy loading for models to avoid circular imports
def get_sales_order_model():
    return apps.get_model('Sales', 'SalesOrder')

def get_sales_order_line_model():
    return apps.get_model('Sales', 'SalesOrderLine')


@receiver(pre_save, sender=Payment)
def payment_pre_save(sender, instance, **kwargs):
    """
    Validate payment amount before saving
    """
    try:
        validate_payment_amount(instance.sales_order, instance.amount)
    except ValidationError as e:
        raise e

    remaining_balance = calculate_remaining_balance(instance.sales_order)
    print(f"[Pre-save] Remaining balance for sales order: {remaining_balance}")


@receiver(post_save, sender=Payment)
def payment_post_save(sender, instance, created, **kwargs):
    """
    Update sales order payment information after payment is saved
    """
    print(f"[SIGNAL] Payment post_save called. Created: {created}")
    print(f"Payment ID: {instance.id}, Type: {instance.payment_type}, Amount: {instance.amount}")
    
    if instance.sales_order and instance.payment_type == 'incoming':
        print(f"Linked to Sales Order ID: {instance.sales_order.id}")
        transaction.on_commit(lambda: update_sales_order_payment_info(instance.sales_order))
    else:
        print("Not linked to a sales order or not an incoming payment. Skipping update.")


@receiver(post_delete, sender=Payment)
def payment_post_delete(sender, instance, **kwargs):
    """
    Update sales order payment information after payment is deleted
    """
    print(f"[SIGNAL] Payment post_delete called.")
    print(f"Deleted Payment ID: {instance.id}, Type: {instance.payment_type}")
    
    if instance.sales_order and instance.payment_type == 'incoming':
        print(f"Was linked to Sales Order ID: {instance.sales_order.id}")
        transaction.on_commit(lambda: update_sales_order_payment_info(instance.sales_order))
    else:
        print("Was not linked to a sales order or not an incoming payment. Skipping update.")


def register_sales_order_line_signals():
    """
    Register signals for SalesOrderLine model.
    This function is called from apps.ready() to ensure models are loaded.
    """
    SalesOrderLine = get_sales_order_line_model()
    
    @receiver(post_save, sender=SalesOrderLine)
    def sales_order_line_post_save(sender, instance, **kwargs):
        """
        Update sales order totals when a line item is saved
        """
        print(f"[SIGNAL] SalesOrderLine post_save called.")
        print(f"SalesOrderLine ID: {instance.id}, Order ID: {instance.order.id if instance.order else 'None'}")
        
        if instance.order:
            calculate_sales_order_totals_from_lines(instance.order)
            update_fields = ['total_amount', 'payable_amount', 'due_amount']
            instance.order.save(update_fields=update_fields)
            transaction.on_commit(lambda: update_sales_order_payment_info(instance.order))

    @receiver(post_delete, sender=SalesOrderLine)
    def sales_order_line_post_delete(sender, instance, **kwargs):
        """
        Update sales order totals when a line item is deleted
        """
        print(f"[SIGNAL] SalesOrderLine post_delete called.")
        
        if instance.order:
            calculate_sales_order_totals_from_lines(instance.order)
            update_fields = ['total_amount', 'payable_amount', 'due_amount']
            instance.order.save(update_fields=update_fields)
            transaction.on_commit(lambda: update_sales_order_payment_info(instance.order))
