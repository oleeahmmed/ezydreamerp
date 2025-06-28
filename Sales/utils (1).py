# sales/utils.py
from django.db.models import Sum
from django.db import models

from decimal import Decimal
from django.utils import timezone
from .models import DeliveryLine
def calculate_delivered_quantities(sales_order):
    """
    Calculate already delivered quantities for each line item in a sales order
    Returns a dictionary with (item_code, uom) as key and delivered quantity as value
    """
    delivered_quantities = {}
    for delivery in sales_order.deliveries.all():
        for line in delivery.lines.all():
            key = (line.item_code, line.uom)
            delivered_quantities[key] = delivered_quantities.get(key, 0) + line.quantity
    return delivered_quantities

def get_remaining_order_lines(sales_order):
    """
    Get remaining undelivered quantities from a sales order
    Returns a list of dictionaries with line item data
    """
    delivered_quantities = calculate_delivered_quantities(sales_order)
    
    remaining_lines = []
    for o_line in sales_order.lines.all():
        key = (o_line.item_code, o_line.uom)
        delivered_qty = delivered_quantities.get(key, 0)
        remaining_qty = o_line.quantity - delivered_qty
        
        if remaining_qty > 0:
            remaining_lines.append({
                'item_code': o_line.item_code,
                'item_name': o_line.item_name,
                'quantity': float(remaining_qty),
                'unit_price': float(o_line.unit_price),
                'uom': o_line.uom,
                'remarks': o_line.remarks,
                'is_active': True
            })
    
    return remaining_lines

def prepare_delivery_from_order(sales_order, user=None):
    """
    Prepare delivery data from a sales order
    Returns a dictionary with delivery data
    """
    remaining_lines = get_remaining_order_lines(sales_order)
    
    # Set deliveryemployee based on user
    deliveryemployee = None
    if user and user.is_authenticated:
        deliveryemployee = user.username
    
    delivery_data = {
        'document_date': str(timezone.now().date()),
        'posting_date': str(timezone.now().date()),
        'customer': sales_order.customer_id,
        'sales_order': sales_order.id,
        'contact_person': sales_order.contact_person_id if sales_order.contact_person else None,
        'shipping_address': sales_order.shipping_address_id if sales_order.shipping_address else None,
        'currency': sales_order.currency_id if sales_order.currency else None,
        'payment_terms': sales_order.payment_terms_id if sales_order.payment_terms else None,
        'remarks': sales_order.remarks,
        'sales_employee': sales_order.sales_employee_id if sales_order.sales_employee else None,
        'discount_amount': float(sales_order.discount_amount),
        'paid_amount': float(sales_order.paid_amount),
        'payment_method': sales_order.payment_method,
        'payment_reference': sales_order.payment_reference,
        'payment_date': str(sales_order.payment_date) if sales_order.payment_date else None,
        'deliveryemployee': deliveryemployee,
        'lines': remaining_lines
    }
    
    return delivery_data

def update_order_delivery_status(sales_order):
    """
    Update the sales order status based on delivery status
    """
    from django.db.models import Sum
    
    # Check if all order lines have been fully delivered
    order_lines = sales_order.lines.all()
    all_delivered = True
    any_delivered = False
    
    for line in order_lines:
        delivered_qty = sum(dl.quantity for dl in DeliveryLine.objects.filter(
            delivery__sales_order=sales_order,
            item_code=line.item_code,
            uom=line.uom
        ))
        
        if delivered_qty > 0:
            any_delivered = True
            
        if delivered_qty < line.quantity:
            all_delivered = False
    
    if all_delivered:
        sales_order.status = 'Delivered'
    elif any_delivered:
        sales_order.status = 'Partially Delivered'
    
    sales_order.save(update_fields=['status'])
    
    return sales_order.status

def calculate_financial_totals(obj, lines=None):
    """
    Calculate financial totals for a document (order, delivery, etc.)
    Updates total_amount, payable_amount, and due_amount
    """
    if lines:
        total_amount = sum(line.quantity * line.unit_price for line in lines)
    else:
        total_amount = sum(line.total_amount for line in obj.lines.all())
    
    obj.total_amount = Decimal(total_amount)
    obj.payable_amount = obj.total_amount - obj.discount_amount
    obj.due_amount = obj.payable_amount - obj.paid_amount
    
    return obj
    
    
from Sales.models import SalesOrderLine, FreeItemDiscount
from Inventory.models import Item, ItemWarehouseInfo

def adjust_committed_quantity(line):
    try:
        item = Item.objects.get(code=line.item_code)
        warehouse = item.default_warehouse
        if not warehouse:
            return
        item_warehouse, created = ItemWarehouseInfo.objects.get_or_create(
            item=item,
            warehouse=warehouse,
            defaults={'in_stock': 0, 'committed': 0, 'ordered': 0}
        )

        # ✅ Include both paid & free items
        paid_qty = line.order.lines.filter(
            item_code=line.item_code
        ).exclude(
            remarks="Free Item (Auto)"
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

        free_qty = line.order.lines.filter(
            item_code=line.item_code,
            remarks="Free Item (Auto)"
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

        item_warehouse.committed = paid_qty + free_qty
        item_warehouse.save()

    except Item.DoesNotExist:
        pass


def apply_free_items(order):
    if order.status != "Open":
        return
    if hasattr(order, '_applying_free_items'):
        return

    order._applying_free_items = True

    # Remove old auto-added free items
    order.lines.filter(remarks="Free Item (Auto)").delete()

    for line in order.lines.exclude(remarks="Free Item (Auto)"):
        discounts = FreeItemDiscount.objects.filter(item__code=line.item_code)
        for discount in discounts:
            free_qty = (line.quantity // discount.buy_quantity) * discount.free_quantity
            if free_qty > 0:
                free_line = SalesOrderLine.objects.create(
                    order=order,
                    item_code=discount.free_item.code,
                    item_name=discount.free_item.name,
                    quantity=free_qty,
                    unit_price=0,
                    total_amount=0,
                    remarks="Free Item (Auto)"
                )
                adjust_committed_quantity(free_line)  # ✅ Immediately update committed for free item

    del order._applying_free_items    