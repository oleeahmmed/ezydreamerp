# sales/utils.py
from django.db.models import Sum
from django.db import models # This is for models.Sum, can stay at top

from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Inventory models (Item, Warehouse, ItemWarehouseInfo) are typically in a separate app
# like 'Inventory' and do not cause circular imports with 'Sales.models'.
# So, they can remain at the top.
from Inventory.models import Item, Warehouse, ItemWarehouseInfo


def calculate_delivered_quantities(sales_order):
    """
    Calculate already delivered quantities for each line item in a sales order
    Returns a dictionary with (item_code, uom) as key and delivered quantity as value
    """
    # Local import: DeliveryLine is from Sales.models
    from .models import DeliveryLine
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
    # This function calls calculate_delivered_quantities, which handles its own local import of DeliveryLine.
    # No direct import of DeliveryLine is needed here.
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
                'order_line_id': o_line.id
            })
    return remaining_lines

def validate_sales_order_line_stock(sales_order_line_instance):
    """
    Validates if there is sufficient stock for a given SalesOrderLine instance.
    Raises ValidationError if stock is insufficient.
    """
    # Local import: SalesOrderLine is from Sales.models
    from .models import SalesOrderLine

    try:
        # Item and Warehouse are imported at the top from Inventory.models, which is fine.
        item = Item.objects.get(code=sales_order_line_instance.item_code)
        warehouse = item.default_warehouse

        if not warehouse:
            raise ValidationError(_("Default warehouse not set for item: %(item_name)s"),
                                  params={'item_name': item.name}) # Changed from item.item_name to item.name

        # Get the ItemWarehouseInfo for the item and its default warehouse
        item_warehouse_info = ItemWarehouseInfo.objects.filter(item=item, warehouse=warehouse).first()

        if not item_warehouse_info:
            raise ValidationError(_("Item '%(item_name)s' is not available in the default warehouse."),
                                  params={'item_name': item.name}) # Changed from item.item_name to item.name

        # Determine the quantity to check against
        old_quantity = Decimal('0.000000')
        if sales_order_line_instance.pk:
            try:
                # We need to fetch the old instance to calculate the change in quantity.
                # SalesOrderLine is imported locally above.
                old_instance = SalesOrderLine.objects.get(pk=sales_order_line_instance.pk)
                old_quantity = old_instance.quantity
            except SalesOrderLine.DoesNotExist:
                # This case should ideally not happen if pk exists, but good for robustness.
                pass

        # Calculate the effective quantity needed for this transaction (delta)
        effective_quantity_change = sales_order_line_instance.quantity - old_quantity

        # Only check if effective_quantity_change is positive (i.e., quantity is increasing or a new line)
        if effective_quantity_change > 0 and item_warehouse_info.available < effective_quantity_change:
            raise ValidationError(
                _("Insufficient stock for item '%(item_name)s' in warehouse '%(warehouse_name)s'. Available: %(available_stock)s, Required: %(required_quantity)s"),
                params={
                    'item_name': item.name, # Changed from item.item_name to item.name
                    'warehouse_name': warehouse.name,
                    'available_stock': item_warehouse_info.available,
                    'required_quantity': sales_order_line_instance.quantity # Show the total requested quantity
                }
            )

    except Item.DoesNotExist:
        raise ValidationError(_("Item with code '%(item_code)s' does not exist."),
                              params={'item_code': sales_order_line_instance.item_code})

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
    # django.db.models.Sum is already imported at the top.
    from .models import DeliveryLine # Local import

    # Check if all order lines have been fully delivered
    order_lines = sales_order.lines.all()
    all_delivered = True
    any_delivered = False

    for line in order_lines:
        delivered_qty = sum(dl.quantity for dl in DeliveryLine.objects.filter(
            delivery__sales_order=sales_order, item_code=line.item_code, uom=line.uom
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
    """ Calculate financial totals for a document (order, delivery, etc.)
    Updates total_amount, payable_amount, and due_amount
    """
    if lines:
        obj.total_amount = sum(line.total_amount for line in lines)
    else:
        obj.total_amount = sum(line.total_amount for line in obj.lines.all())

    obj.payable_amount = (obj.total_amount + obj.tax_amount) - obj.discount_amount
    obj.due_amount = obj.payable_amount - obj.paid_amount

    obj.save(update_fields=['total_amount', 'payable_amount', 'due_amount', 'updated_at'])

def adjust_committed_quantity(line):
    """
    Adjusts the committed quantity for an item in ItemWarehouseInfo.
    This function is related to handling free items.
    """
    # Item and ItemWarehouseInfo are imported globally at the top of utils.py.
    # SalesOrderLine is needed for querying, so it's imported locally.
    from .models import SalesOrderLine

    try:
        item = Item.objects.get(code=line.item_code)
        warehouse = item.default_warehouse
        if not warehouse:
            return

        item_warehouse = ItemWarehouseInfo.objects.get(item=item, warehouse=warehouse)

        # Calculate committed quantity based on SalesOrderLines (excluding Free Items)
        paid_qty = line.order.lines.exclude(remarks="Free Item (Auto)").filter(
            item_code=line.item_code
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

        # Calculate free items quantity if they also affect committed stock
        free_qty = line.order.lines.filter(
            item_code=line.item_code,
            remarks="Free Item (Auto)"
        ).aggregate(total=models.Sum('quantity'))['total'] or 0

        item_warehouse.committed = paid_qty + free_qty
        item_warehouse.save()

    except Item.DoesNotExist:
        pass


def apply_free_items(order):
    """
    Applies free items to a SalesOrder based on FreeItemDiscount rules.
    """
    # Local imports for SalesOrderLine and FreeItemDiscount
    from .models import SalesOrderLine, FreeItemDiscount

    if order.status != "Open":
        return
    if hasattr(order, '_applying_free_items'):
        # Prevents infinite recursion if signals/save methods trigger apply_free_items again
        return

    order._applying_free_items = True

    # Remove old auto-added free items before recalculating
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
                    unit_price=0, # Free items typically have 0 unit price
                    total_amount=0,
                    remarks="Free Item (Auto)"
                )
                adjust_committed_quantity(free_line)  # Immediately update committed for this free item

    del order._applying_free_items