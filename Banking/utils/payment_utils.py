from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.apps import apps

def calculate_remaining_balance(sales_order):
    """
    Calculates the remaining balance after the payment.
    """
    if sales_order:
        # Lazy import to avoid circular imports
        Payment = apps.get_model('Banking', 'Payment')
        
        total_paid = Payment.objects.filter(sales_order=sales_order, payment_type='incoming') \
            .aggregate(total_paid=Sum('amount'))['total_paid'] or Decimal(0)
        remaining_balance = sales_order.total_amount - total_paid
        return remaining_balance
    return Decimal(0)

def validate_payment_amount(sales_order, amount):
    """
    Validates that the payment amount does not exceed the sales order total amount.
    """
    if sales_order:
        # Lazy import to avoid circular imports
        Payment = apps.get_model('Banking', 'Payment')
        
        total_paid = Payment.objects.filter(sales_order=sales_order, payment_type='incoming') \
            .aggregate(total_paid=Sum('amount'))['total_paid'] or Decimal(0)

        if total_paid + amount > sales_order.total_amount:
            raise ValidationError('The payment amount exceeds the total amount of the sales order.')

    return True

def set_business_partner(payment_instance):
    """
    Sets the business partner from the associated sales order if it's not set.
    """
    if not payment_instance.business_partner and payment_instance.sales_order:
        payment_instance.business_partner = payment_instance.sales_order.customer
    return payment_instance

def calculate_sales_order_totals_from_lines(sales_order):
    """
    Calculate the total_amount field based on the sum of all active line items.
    """
    from django.db.models import Sum
    from decimal import Decimal

    # Calculate total from active lines
    total = sales_order.lines.filter(is_active=True).aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')
    
    sales_order.total_amount = total
    
    # Update dependent fields
    sales_order.payable_amount = sales_order.total_amount - sales_order.discount_amount
    sales_order.due_amount = sales_order.payable_amount - sales_order.paid_amount
    
    return sales_order

def update_sales_order_payment_info(sales_order):
    """
    Updates the payment information in the sales order based on all associated payments.
    This function is called when a payment is saved, updated, or deleted.
    """
    if not sales_order:
        print("[Warning] No sales order provided to update_sales_order_payment_info")
        return

    print(f"[INFO] Updating SalesOrder #{sales_order.id} Payment Info...")

    # Lazy import to avoid circular imports
    Payment = apps.get_model('Banking', 'Payment')

    payments = Payment.objects.filter(
        sales_order=sales_order, 
        payment_type='incoming'
    ).order_by('-payment_date')

    total_paid = payments.aggregate(total=Sum('amount'))['total'] or Decimal(0)
    due_amount = sales_order.payable_amount - total_paid

    print(f"[INFO] Found Payments: {payments.count()}, Total Paid: {total_paid}")
    print(f"[INFO] SalesOrder Payable: {sales_order.payable_amount}, Due: {due_amount}")

    latest_payment = payments.first()

    sales_order.paid_amount = total_paid
    sales_order.due_amount = due_amount

    if latest_payment:
        sales_order.payment_method = latest_payment.payment_method.name if latest_payment.payment_method else None
        sales_order.payment_reference = latest_payment.reference
        sales_order.payment_date = latest_payment.payment_date

        print(f"[INFO] Latest Payment: #{latest_payment.id}, Method: {sales_order.payment_method}, Date: {sales_order.payment_date}")
    else:
        sales_order.payment_method = None
        sales_order.payment_reference = None
        sales_order.payment_date = None
        print("[INFO] No payments found, cleared payment reference information")

    if total_paid == 0:
        if sales_order.status not in ['Draft', 'Cancelled']:
            sales_order.status = 'Open'
    elif total_paid < sales_order.payable_amount:
        sales_order.status = 'Partially Invoiced'
    elif total_paid >= sales_order.payable_amount:
        sales_order.status = 'Invoiced'

    update_fields = [
        'paid_amount', 'due_amount',
        'payment_method', 'payment_reference', 'payment_date',
        'status', 'total_amount', 'payable_amount'
    ]

    sales_order.save(update_fields=update_fields)
    print(f"[SUCCESS] SalesOrder #{sales_order.id} updated successfully. Status: {sales_order.status}")

