from django.views.generic import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.urls import reverse_lazy
from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse

from ..models import (
    SalesQuotation, SalesOrder, SalesOrderLine,
    Delivery, DeliveryLine, Return, ReturnLine,
    ARInvoice, ARInvoiceLine
)
from ..forms.arinvoice_forms import copy_from_sales_order, copy_from_delivery

# class ConvertQuotationToOrderView(LoginRequiredMixin, View):
#     """
#     Converts a SalesQuotation to a SalesOrder.
#     Only remaining (unconverted) quantities will be transferred.
#     Prevents duplicate or over-quantity conversion.
#     """

#     def dispatch(self, request, *args, **kwargs):
#         # Permission check
#         if not (request.user.has_perm('Sales.view_salesquotation') and
#                 request.user.has_perm('Sales.add_salesorder')):
#             return self.handle_no_permission()
#         return super().dispatch(request, *args, **kwargs)

#     def get(self, request, pk):
#         # Get the Quotation
#         quotation = get_object_or_404(SalesQuotation, pk=pk)

#         # Block conversion if quotation is already converted or cancelled
#         if quotation.status in ['Expired', 'Cancelled', 'Converted']:
#             messages.error(request, f"Quotation {quotation.pk} cannot be converted because it is {quotation.status}.")
#             return redirect('Sales:sales_quotation_detail', pk=pk)

#         # Step 1: Calculate already ordered quantities from previous SalesOrders
#         existing_orders = SalesOrder.objects.filter(quotation=quotation)

#         # item_key: (item_code, uom) → total ordered qty
#         ordered_quantities = {}

#         for order in existing_orders:
#             for line in order.lines.all():
#                 key = (line.item_code, line.uom)
#                 ordered_quantities[key] = ordered_quantities.get(key, 0) + line.quantity

#         # Step 2: Determine which quotation lines still have remaining quantities
#         remaining_lines = []
#         for q_line in quotation.lines.all():
#             key = (q_line.item_code, q_line.uom)
#             already_ordered = ordered_quantities.get(key, 0)
#             remaining_qty = q_line.quantity - already_ordered

#             if remaining_qty > 0:
#                 # There is still something to convert for this item
#                 remaining_lines.append({
#                     'source': q_line,
#                     'remaining_qty': remaining_qty
#                 })

#         # Step 3: Block conversion if all items are already ordered
#         if not remaining_lines:
#             messages.error(request, f"All items in Quotation {quotation.pk} have already been converted to Sales Orders.")
#             return redirect('Sales:sales_quotation_detail', pk=pk)

#         # Step 4: Begin conversion
#         with transaction.atomic():
#             try:
#                 order = SalesOrder.objects.create(
#                     document_date=quotation.document_date,
#                     delivery_date=quotation.valid_until,
#                     customer=quotation.customer,
#                     contact_person=quotation.contact_person,
#                     billing_address=quotation.billing_address,
#                     shipping_address=quotation.shipping_address,
#                     currency=quotation.currency,
#                     payment_terms=quotation.payment_terms,
#                     remarks=quotation.remarks,
#                     sales_employee=quotation.sales_employee,
#                     status='Open',
#                     discount_amount=quotation.discount_amount,
#                     tax_amount=quotation.tax_amount,
#                     total_amount=0,  # will be calculated below
#                     payable_amount=0,
#                     paid_amount=0,
#                     due_amount=0,
#                     payment_method=quotation.payment_method,
#                     payment_reference=quotation.payment_reference,
#                     payment_date=quotation.payment_date
#                 )

#                 # Step 5: Create Order Lines only for remaining quantities
#                 total_amount = 0
#                 for item in remaining_lines:
#                     q_line = item['source']
#                     quantity = item['remaining_qty']
#                     line_total = quantity * q_line.unit_price
#                     total_amount += line_total

#                     SalesOrderLine.objects.create(
#                         order=order,
#                         item_code=q_line.item_code,
#                         item_name=q_line.item_name,
#                         quantity=quantity,
#                         unit_price=q_line.unit_price,
#                         total_amount=line_total,
#                         uom=q_line.uom,
#                         remarks=q_line.remarks,
#                         is_active=True
#                     )

#                 # Update order financials
#                 order.total_amount = total_amount
#                 order.payable_amount = total_amount - order.discount_amount
#                 order.due_amount = order.payable_amount - order.paid_amount
#                 order.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])

#                 # Optional: Update quotation status to Converted if fully converted
#                 fully_converted = all(
#                     (q.quantity - ordered_quantities.get((q.item_code, q.uom), 0) - q.quantity) >= 0
#                     for q in quotation.lines.all()
#                 )
#                 if fully_converted:
#                     quotation.status = 'Converted'
#                     quotation.save(update_fields=['status'])

#                 messages.success(request, f"Quotation {quotation.pk} successfully converted to Sales Order {order.pk}.")
#                 return redirect('Sales:sales_order_detail', pk=order.pk)

#             except Exception as e:
#                 print(f"Error: {e}")
#                 messages.error(request, f"Error creating Sales Order: {str(e)}")
#                 return redirect('Sales:sales_quotation_detail', pk=pk)

class ConvertQuotationToOrderView(LoginRequiredMixin, View):
    """
    Prefills sales order form using quotation data.
    Does not create order directly, instead redirects to order creation view.
    """
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.has_perm('Sales.view_salesquotation') and request.user.has_perm('Sales.add_salesorder')):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        quotation = get_object_or_404(SalesQuotation, pk=pk)

        if quotation.status in ['Expired', 'Cancelled', 'Converted']:
            messages.error(request, f"Quotation {quotation.pk} cannot be converted because it is {quotation.status}.")
            return redirect('Sales:sales_quotation_detail', pk=pk)

        ordered_quantities = {}
        for order in SalesOrder.objects.filter(quotation=quotation):
            for line in order.lines.all():
                key = (line.item_code, line.uom)
                ordered_quantities[key] = ordered_quantities.get(key, 0) + line.quantity

        remaining_lines = []
        for q_line in quotation.lines.all():
            key = (q_line.item_code, q_line.uom)
            already_ordered = ordered_quantities.get(key, 0)
            remaining_qty = q_line.quantity - already_ordered
            if remaining_qty > 0:
                remaining_lines.append({
                    'item_code': q_line.item_code,
                    'item_name': q_line.item_name,
                    'quantity': float(remaining_qty),
                    'unit_price': float(q_line.unit_price),
                    'uom': q_line.uom,
                    'remarks': q_line.remarks,
                    'is_active': True
                })

        if not remaining_lines:
            messages.error(request, f"All items in Quotation {quotation.pk} have already been converted.")
            return redirect('Sales:sales_quotation_detail', pk=pk)

        # Pass data through session to prefill in SalesOrderCreateView
        request.session['prefill_order_data'] = {
            'document_date': str(quotation.document_date),
            'delivery_date': str(quotation.valid_until),
            'customer': quotation.customer_id,
            'contact_person': quotation.contact_person_id,
            'billing_address': quotation.billing_address_id,
            'shipping_address': quotation.shipping_address_id,
            'currency': quotation.currency_id,
            'payment_terms': quotation.payment_terms_id,
            'remarks': quotation.remarks,
            'sales_employee': quotation.sales_employee_id,
            'discount_amount': float(quotation.discount_amount),
            'total_amount': float(quotation.total_amount),
            'payable_amount': float(quotation.payable_amount),
            'paid_amount': float(quotation.paid_amount),
            'due_amount': float(quotation.due_amount),
            'payment_method': quotation.payment_method,
            'payment_reference': quotation.payment_reference,
            'payment_date': str(quotation.payment_date) if quotation.payment_date else None,
            'quotation_id': quotation.id,
            'lines': remaining_lines
        }

        # Redirect to the sales order create form with prefilled data from session
        return redirect(reverse('Sales:sales_order_create'))

# class ConvertOrderToDeliveryView(LoginRequiredMixin, View):
#     """Convert a sales order to a delivery"""
    
#     def dispatch(self, request, *args, **kwargs):
#         if not (request.user.has_perm('Sales.view_salesorder') and 
#                 request.user.has_perm('Sales.add_delivery')):
#             return self.handle_no_permission()
#         return super().dispatch(request, *args, **kwargs)
    
#     def get(self, request, pk):
#         order = get_object_or_404(SalesOrder, pk=pk)
        
#         # Check if order can be converted
#         if order.status in ['Cancelled', 'Closed']:
#             messages.error(request, f"Sales Order {order.pk} cannot be converted because it is {order.status}.")
#             return redirect('Sales:sales_order_detail', pk=pk)
        
#         # Check if there are existing deliveries for this order
#         existing_deliveries = Delivery.objects.filter(sales_order=order, status__in=['Open', 'Partially Delivered', 'Delivered'])
        
#         # Calculate already delivered quantities for each line item
#         delivered_quantities = {}
#         for delivery in existing_deliveries:
#             for line in delivery.lines.all():
#                 if line.sales_order_line_id in delivered_quantities:
#                     delivered_quantities[line.sales_order_line_id] += line.quantity
#                 else:
#                     delivered_quantities[line.sales_order_line_id] = line.quantity
        
#         # Check if all items are fully delivered
#         all_delivered = True
#         any_to_deliver = False
        
#         for order_line in order.lines.all():
#             delivered_qty = delivered_quantities.get(order_line.id, 0)
#             if delivered_qty < order_line.quantity:
#                 all_delivered = False
#                 any_to_deliver = True
#                 break
        
#         if all_delivered:
#             messages.error(request, f"All items in Sales Order {order.pk} have already been fully delivered.")
#             return redirect('Sales:sales_order_detail', pk=pk)
        
#         if not any_to_deliver:
#             messages.error(request, f"No items in Sales Order {order.pk} are available for delivery.")
#             return redirect('Sales:sales_order_detail', pk=pk)
        
#         with transaction.atomic():
#             # Create delivery
#             try:
#                 # Set deliveryemployee based on user type
#                 deliveryemployee = None
#                 if request.user.is_authenticated:
#                     if not request.user.is_superuser:
#                         deliveryemployee = request.user.username
            
#                 delivery = Delivery.objects.create(
#                     document_date=timezone.now().date(),
#                     posting_date=timezone.now().date(),
#                     customer=order.customer,
#                     contact_person=order.contact_person,
#                     shipping_address=order.shipping_address,
#                     sales_order=order,
#                     currency=order.currency,
#                     payment_terms=order.payment_terms,
#                     total_amount=0,  # Will calculate after adding lines
#                     discount_amount=order.discount_amount,
#                     remarks=order.remarks,
#                     sales_employee=order.sales_employee,
#                     deliveryemployee=deliveryemployee,
#                     status='Open',
#                     # Payment information fields
#                     paid_amount=order.paid_amount,
#                     payment_method=order.payment_method,
#                     payment_reference=order.payment_reference,
#                     payment_date=order.payment_date
#                 )
#             except Exception as e:
#                 print(f"Error creating delivery: {e}")
#                 messages.error(request, f"Error creating delivery: {e}")
#                 return redirect('Sales:sales_order_detail', pk=pk)
            
#             # Create delivery lines from order lines for remaining quantities
#             total_delivery_amount = 0
#             lines_created = 0
            
#             for o_line in order.lines.all():
#                 delivered_qty = delivered_quantities.get(o_line.id, 0)
#                 remaining_qty = o_line.quantity - delivered_qty
                
#                 if remaining_qty > 0:
#                     try:
#                         delivery_line = DeliveryLine.objects.create(
#                             delivery=delivery,
#                             sales_order_line=o_line,
#                             item_code=o_line.item_code,
#                             item_name=o_line.item_name,
#                             quantity=remaining_qty,
#                             unit_price=o_line.unit_price,
#                             uom=o_line.uom,
#                             remarks=o_line.remarks,
#                             is_active=True
#                         )
#                         total_delivery_amount += delivery_line.quantity * delivery_line.unit_price
#                         lines_created += 1
#                     except Exception as e:
#                         print(f"Error creating delivery line: {e}")
#                         messages.error(request, f"Error creating delivery line: {e}")
#                         return redirect('Sales:sales_order_detail', pk=pk)
            
#             if lines_created == 0:
#                 # Rollback if no lines were created
#                 messages.error(request, f"No items in Sales Order {order.pk} are available for delivery.")
#                 return redirect('Sales:sales_order_detail', pk=pk)
            
#             # Update delivery total amount and calculate payable and due amounts
#             delivery.total_amount = total_delivery_amount
#             delivery.payable_amount = delivery.total_amount - delivery.discount_amount
#             delivery.due_amount = delivery.payable_amount - delivery.paid_amount
#             delivery.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])
            
#             # Update order status
#             if all(delivered_quantities.get(line.id, 0) + (line.quantity - delivered_quantities.get(line.id, 0)) >= line.quantity for line in order.lines.all()):
#                 order.status = 'Delivered'
#             else:
#                 order.status = 'Partially Delivered'
            
#             order.save(update_fields=['status'])
            
#             messages.success(request, f"Sales Order {order.pk} successfully converted to Delivery {delivery.pk}.")
#             return redirect('Sales:delivery_detail', pk=delivery.pk)


class ConvertOrderToDeliveryView(LoginRequiredMixin, View):
    """
    Prefills delivery form using sales order data.
    Does not create delivery directly, instead redirects to delivery creation view.
    """
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.has_perm('Sales.view_salesorder') and request.user.has_perm('Sales.add_delivery')):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        order = get_object_or_404(SalesOrder, pk=pk)

        if order.status in ['Cancelled', 'Closed']:
            messages.error(request, f"Sales Order {order.pk} cannot be converted because it is {order.status}.")
            return redirect('Sales:sales_order_detail', pk=pk)

        delivered_quantities = {}
        for delivery in order.deliveries.all():
            for line in delivery.lines.all():
                key = (line.item_code, line.uom)
                delivered_quantities[key] = delivered_quantities.get(key, 0) + line.quantity

        remaining_lines = []
        for o_line in order.lines.all():
            key = (o_line.item_code, o_line.uom)
            already_delivered = delivered_quantities.get(key, 0)
            remaining_qty = o_line.quantity - already_delivered
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

        if not remaining_lines:
            messages.error(request, f"All items in Sales Order {order.pk} have already been delivered.")
            return redirect('Sales:sales_order_detail', pk=pk)

        # Pass data through session to prefill in DeliveryCreateView
        request.session['prefill_delivery_data'] = {
            'document_date': str(order.document_date),
            'posting_date': str(order.document_date),
            'customer': order.customer_id,
            'contact_person': order.contact_person_id,
            'shipping_address': order.shipping_address_id,
            'sales_employee': order.sales_employee_id,
            'discount_amount': float(order.discount_amount),
            'total_amount': float(order.total_amount),
            'payable_amount': float(order.payable_amount),
            'paid_amount': float(order.paid_amount),
            'due_amount': float(order.due_amount),
            'payment_method': order.payment_method,
            'payment_reference': order.payment_reference,
            'payment_date': str(order.payment_date) if order.payment_date else None,
            'remarks': f"Delivery for Sales Order #{order.pk}",
            'sales_order': order.id,
            'lines': remaining_lines
        }

        # Redirect to the delivery create view with prefilled data from session
        return redirect(reverse('Sales:delivery_create'))



# class ConvertDeliveryToReturnView(LoginRequiredMixin, View):
#     """Convert a delivery to a return"""
    
#     def dispatch(self, request, *args, **kwargs):
#         if not (request.user.has_perm('Sales.view_delivery') and 
#                 request.user.has_perm('Sales.add_return')):
#             return self.handle_no_permission()
#         return super().dispatch(request, *args, **kwargs)
    
#     def get(self, request, pk):
#         delivery = get_object_or_404(Delivery, pk=pk)
        
#         # Check if delivery can be converted
#         if delivery.status in ['Cancelled', 'Closed']:
#             messages.error(request, f"Delivery {delivery.pk} cannot be converted because it is {delivery.status}.")
#             return redirect('Sales:delivery_detail', pk=pk)
        
#         # Check if there are existing returns for this delivery
#         existing_returns = Return.objects.filter(delivery=delivery)
        
#         # Calculate already returned quantities for each line item
#         returned_quantities = {}
#         for return_doc in existing_returns:
#             for line in return_doc.lines.all():
#                 if line.delivery_line_id in returned_quantities:
#                     returned_quantities[line.delivery_line_id] += line.quantity
#                 else:
#                     returned_quantities[line.delivery_line_id] = line.quantity
        
#         # Check if all items are fully returned
#         all_returned = True
#         any_to_return = False
        
#         for delivery_line in delivery.lines.all():
#             returned_qty = returned_quantities.get(delivery_line.id, 0)
#             if returned_qty < delivery_line.quantity:
#                 all_returned = False
#                 any_to_return = True
#                 break
        
#         if all_returned:
#             messages.error(request, f"All items in Delivery {delivery.pk} have already been fully returned.")
#             return redirect('Sales:delivery_detail', pk=pk)
        
#         if not any_to_return:
#             messages.error(request, f"No items in Delivery {delivery.pk} are available for return.")
#             return redirect('Sales:delivery_detail', pk=pk)
        
#         with transaction.atomic():
#             # Create return
#             try:
#                 return_doc = Return.objects.create(
#                     document_date=timezone.now().date(),
#                     posting_date=timezone.now().date(),
#                     customer=delivery.customer,
#                     contact_person=delivery.contact_person,
#                     return_address=delivery.shipping_address,
#                     delivery=delivery,
#                     currency=delivery.currency,
#                     payment_terms=delivery.payment_terms,
#                     total_amount=0,  # Will calculate after adding lines
#                     discount_amount=delivery.discount_amount,
#                     remarks=f"Return for delivery {delivery.pk}",
#                     sales_employee=delivery.sales_employee,
#                     status='Draft',
#                     # Payment information fields
#                     paid_amount=delivery.paid_amount,
#                     payment_method=delivery.payment_method,
#                     payment_reference=delivery.payment_reference,
#                     payment_date=delivery.payment_date
#                 )
#             except Exception as e:
#                 print(f"Error creating return: {e}")
#                 messages.error(request, f"Error creating return: {e}")
#                 return redirect('Sales:delivery_detail', pk=pk)
            
#             # Create return lines from delivery lines for remaining quantities
#             total_return_amount = 0
#             lines_created = 0
            
#             for d_line in delivery.lines.all():
#                 returned_qty = returned_quantities.get(d_line.id, 0)
#                 remaining_qty = d_line.quantity - returned_qty
                
#                 if remaining_qty > 0:
#                     try:
#                         return_line = ReturnLine.objects.create(
#                             return_doc=return_doc,
#                             delivery_line=d_line,
#                             item_code=d_line.item_code,
#                             item_name=d_line.item_name,
#                             quantity=remaining_qty,
#                             unit_price=d_line.unit_price,
#                             uom=d_line.uom,
#                             remarks=d_line.remarks,
#                             is_active=True
#                         )
#                         total_return_amount += return_line.quantity * return_line.unit_price
#                         lines_created += 1
#                     except Exception as e:
#                         print(f"Error creating return line: {e}")
#                         messages.error(request, f"Error creating return line: {e}")
#                         return redirect('Sales:delivery_detail', pk=pk)
            
#             if lines_created == 0:
#                 # Rollback if no lines were created
#                 messages.error(request, f"No items in Delivery {delivery.pk} are available for return.")
#                 return redirect('Sales:delivery_detail', pk=pk)
            
#             # Update return total amount and calculate payable and due amounts
#             return_doc.total_amount = total_return_amount
#             return_doc.payable_amount = return_doc.total_amount - return_doc.discount_amount
#             return_doc.due_amount = return_doc.payable_amount - return_doc.paid_amount
#             return_doc.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])
            
#             messages.success(request, f"Delivery {delivery.pk} successfully converted to Return {return_doc.pk}.")
#             return redirect('Sales:return_detail', pk=return_doc.pk)

class ConvertDeliveryToReturnView(LoginRequiredMixin, View):
    """
    Prefills return form using delivery data.
    Does not create return directly, instead redirects to return creation view.
    """
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.has_perm('Sales.view_delivery') and request.user.has_perm('Sales.add_return')):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        delivery = get_object_or_404(Delivery, pk=pk)

        if delivery.status in ['Cancelled', 'Closed']:
            messages.error(request, f"Delivery {delivery.pk} cannot be converted because it is {delivery.status}.")
            return redirect('Sales:delivery_detail', pk=pk)

        # Clear any existing prefill data
        if 'prefill_return_data' in request.session:
            del request.session['prefill_return_data']

        # Calculate remaining quantities to return
        from django.db.models import Sum
        
        returned_quantities = {}
        for ret in Return.objects.filter(delivery=delivery):
            for line in ret.lines.all():
                key = (line.item_code, line.uom)
                returned_quantities[key] = returned_quantities.get(key, 0) + line.quantity

        remaining_lines = []
        for d_line in delivery.lines.all():
            key = (d_line.item_code, d_line.uom)
            already_returned = returned_quantities.get(key, 0)
            remaining_qty = d_line.quantity - already_returned
            if remaining_qty > 0:
                remaining_lines.append({
                    'item_code': d_line.item_code,
                    'item_name': d_line.item_name,
                    'quantity': float(remaining_qty),
                    'unit_price': float(d_line.unit_price),
                    'uom': d_line.uom,
                    'remarks': d_line.remarks,
                    'is_active': True,
                    'delivery_line': d_line.id  # Include delivery line ID
                })

        if not remaining_lines:
            messages.error(request, f"All items in Delivery {delivery.pk} have already been returned.")
            return redirect('Sales:delivery_detail', pk=pk)

        # Pass data through session to prefill in ReturnCreateView
        request.session['prefill_return_data'] = {
            'document_date': str(delivery.document_date),  # Use delivery's document date
            'posting_date': str(delivery.posting_date),    # Use delivery's posting date
            'customer': delivery.customer_id,
            'contact_person': delivery.contact_person_id,
            'return_address': delivery.shipping_address_id,
            'sales_employee': delivery.sales_employee_id,
            'discount_amount': float(delivery.discount_amount),
            'total_amount': float(delivery.total_amount),
            'payable_amount': float(delivery.payable_amount),
            'paid_amount': float(delivery.paid_amount),
            'due_amount': float(delivery.due_amount),
            'payment_method': delivery.payment_method,
            'payment_reference': delivery.payment_reference,
            'payment_date': str(delivery.payment_date) if delivery.payment_date else None,
            'remarks': f"Return for Delivery #{delivery.pk}",
            'delivery': delivery.id,
            'sales_order': delivery.sales_order_id if delivery.sales_order else None,
            'lines': remaining_lines
        }

        # Save the session to ensure data is persisted
        request.session.modified = True

        # Redirect to the return create view with prefilled data from session
        return redirect(reverse('Sales:return_create'))
# class ConvertOrderToInvoiceView(LoginRequiredMixin, View):
#     """Convert a Sales Order to an AR Invoice"""

#     def dispatch(self, request, *args, **kwargs):
#         if not (request.user.has_perm('Sales.view_salesorder') and
#                 request.user.has_perm('Sales.add_arinvoice')):
#             return self.handle_no_permission()
#         return super().dispatch(request, *args, **kwargs)

#     def get(self, request, pk):
#         order = get_object_or_404(SalesOrder, pk=pk)

#         if order.status in ['Cancelled', 'Closed']:
#             messages.error(request, f"Sales Order {order.pk} cannot be invoiced because it is {order.status}.")
#             return redirect('Sales:sales_order_detail', pk=pk)

#         # আগের ইনভয়েস থেকে প্রতিটি লাইনের quantity বের করুন
#         invoiced_quantities = {}
#         for line in order.lines.all():
#             total_invoiced = ARInvoiceLine.objects.filter(sales_order_line=line).exclude(invoice__status='Cancelled').aggregate(
#                 total=models.Sum('quantity')
#             )['total'] or 0
#             invoiced_quantities[line.id] = total_invoiced

#         # Check whether there's anything left to invoice
#         all_invoiced = True
#         any_to_invoice = False

#         for line in order.lines.all():
#             remaining_qty = line.quantity - invoiced_quantities.get(line.id, 0)
#             if remaining_qty > 0:
#                 all_invoiced = False
#                 any_to_invoice = True
#                 break

#         if all_invoiced:
#             messages.error(request, f"All items in Sales Order {order.pk} have already been fully invoiced.")
#             return redirect('Sales:sales_order_detail', pk=pk)

#         if not any_to_invoice:
#             messages.error(request, f"No items in Sales Order {order.pk} are available for invoicing.")
#             return redirect('Sales:sales_order_detail', pk=pk)

#         with transaction.atomic():
#             try:
#                 invoice = ARInvoice.objects.create(
#                     document_date=timezone.now().date(),
#                     posting_date=timezone.now().date(),
#                     due_date=timezone.now().date(),
#                     customer=order.customer,
#                     contact_person=order.contact_person,
#                     billing_address=order.billing_address,
#                     sales_order=order,
#                     currency=order.currency,
#                     payment_terms=order.payment_terms,
#                     remarks=order.remarks,
#                     sales_employee=order.sales_employee,
#                     status='Open',
#                     discount_amount=order.discount_amount,
#                     paid_amount=order.paid_amount,
#                     payment_method=order.payment_method,
#                     payment_reference=order.payment_reference,
#                     payment_date=order.payment_date
#                 )
#             except Exception as e:
#                 print(f"Error creating invoice: {e}")
#                 messages.error(request, f"Error creating invoice: {e}")
#                 return redirect('Sales:sales_order_detail', pk=pk)

#             total_invoice_amount = 0
#             lines_created = 0

#             for order_line in order.lines.all():
#                 remaining_qty = order_line.quantity - invoiced_quantities.get(order_line.id, 0)

#                 if remaining_qty > 0:
#                     try:
#                         ar_line = ARInvoiceLine.objects.create(
#                             invoice=invoice,
#                             sales_order_line=order_line,
#                             item_code=order_line.item_code,
#                             item_name=order_line.item_name,
#                             quantity=remaining_qty,
#                             unit_price=order_line.unit_price,
#                             uom=order_line.uom,
#                             remarks=order_line.remarks,
#                             is_active=True
#                         )
#                         total_invoice_amount += ar_line.quantity * ar_line.unit_price
#                         lines_created += 1
#                     except Exception as e:
#                         print(f"Error creating invoice line: {e}")
#                         messages.error(request, f"Error creating invoice line: {e}")
#                         return redirect('Sales:sales_order_detail', pk=pk)

#             if lines_created == 0:
#                 messages.error(request, f"No items in Sales Order {order.pk} are available for invoicing.")
#                 return redirect('Sales:sales_order_detail', pk=pk)

#             invoice.total_amount = total_invoice_amount
#             invoice.payable_amount = invoice.total_amount - invoice.discount_amount
#             invoice.due_amount = invoice.payable_amount - invoice.paid_amount
#             invoice.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])

#             # 🔄 Update Order Status
#             fully_invoiced = True
#             for line in order.lines.all():
#                 total_invoiced = ARInvoiceLine.objects.filter(sales_order_line=line).exclude(invoice__status='Cancelled').aggregate(
#                     total=models.Sum('quantity')
#                 )['total'] or 0
#                 if total_invoiced < line.quantity:
#                     fully_invoiced = False
#                     break

#             order.status = 'Invoiced' if fully_invoiced else 'Partially Invoiced'
#             order.save(update_fields=['status'])

#             # 🔄 Update related delivery status
#             related_deliveries = Delivery.objects.filter(sales_order=order)
#             for delivery in related_deliveries:
#                 if not ARInvoice.objects.filter(delivery=delivery).exists():
#                     delivery.status = 'Open'
#                 else:
#                     delivery.status = 'Invoiced'
#                 delivery.save(update_fields=['status'])

#             messages.success(request, f"Sales Order {order.pk} successfully converted to Invoice {invoice.pk}.")
#             return redirect('Sales:arinvoice_detail', pk=invoice.pk)

class ConvertOrderToInvoiceView(LoginRequiredMixin, View):
    """
    Prefills invoice form using sales order data.
    Does not create invoice directly, instead redirects to invoice creation view.
    """
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.has_perm('Sales.view_salesorder') and request.user.has_perm('Sales.add_arinvoice')):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        order = get_object_or_404(SalesOrder, pk=pk)

        if order.status in ['Cancelled', 'Closed']:
            messages.error(request, f"Sales Order {order.pk} cannot be converted because it is {order.status}.")
            return redirect('Sales:sales_order_detail', pk=pk)

        invoiced_quantities = {}
        for invoice in ARInvoice.objects.filter(sales_order=order):
            for line in invoice.lines.all():
                key = (line.item_code, line.uom)
                invoiced_quantities[key] = invoiced_quantities.get(key, 0) + line.quantity

        remaining_lines = []
        for o_line in order.lines.all():
            key = (o_line.item_code, o_line.uom)
            already_invoiced = invoiced_quantities.get(key, 0)
            remaining_qty = o_line.quantity - already_invoiced
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

        if not remaining_lines:
            messages.error(request, f"All items in Sales Order {order.pk} have already been invoiced.")
            return redirect('Sales:sales_order_detail', pk=pk)

        # Pass data through session to prefill in ARInvoiceCreateView
        request.session['prefill_invoice_data'] = {
            'document_date': str(order.document_date),
            'posting_date': str(order.document_date),
            'due_date': str(order.delivery_date) if order.delivery_date else str(order.document_date),
            'customer': order.customer_id,
            'contact_person': order.contact_person_id,
            'billing_address': order.billing_address_id,
            'sales_employee': order.sales_employee_id,
            'discount_amount': float(order.discount_amount),
            'total_amount': float(order.total_amount),
            'payable_amount': float(order.payable_amount),
            'paid_amount': float(order.paid_amount),
            'due_amount': float(order.due_amount),
            'payment_method': order.payment_method,
            'payment_reference': order.payment_reference,
            'payment_date': str(order.payment_date) if order.payment_date else None,
            'remarks': f"Invoice for Sales Order #{order.pk}",
            'sales_order': order.id,
            'lines': remaining_lines
        }

        # Redirect to the invoice create view with prefilled data from session
        return redirect(reverse('Sales:arinvoice_create'))


class ConvertOrderToReturnView(LoginRequiredMixin, View):
    """
    Prefills return form using sales order data.
    Does not create return directly, instead redirects to return creation view.
    """
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.has_perm('Sales.view_salesorder') and request.user.has_perm('Sales.add_return')):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        order = get_object_or_404(SalesOrder, pk=pk)

        if order.status in ['Cancelled', 'Closed']:
            messages.error(request, f"Sales Order {order.pk} cannot be converted because it is {order.status}.")
            return redirect('Sales:sales_order_detail', pk=pk)

        # Check if there are deliveries for this order
        if not order.deliveries.exists():
            messages.error(request, f"Sales Order {order.pk} has no deliveries to return.")
            return redirect('Sales:sales_order_detail', pk=pk)

        returned_quantities = {}
        for delivery in order.deliveries.all():
            for ret in Return.objects.filter(delivery=delivery):
                for line in ret.lines.all():
                    key = (line.item_code, line.uom)
                    returned_quantities[key] = returned_quantities.get(key, 0) + line.quantity

        # Get delivered quantities
        delivered_quantities = {}
        for delivery in order.deliveries.all():
            for line in delivery.lines.all():
                key = (line.item_code, line.uom)
                delivered_quantities[key] = delivered_quantities.get(key, 0) + line.quantity

        remaining_lines = []
        for o_line in order.lines.all():
            key = (o_line.item_code, o_line.uom)
            delivered_qty = delivered_quantities.get(key, 0)
            already_returned = returned_quantities.get(key, 0)
            remaining_qty = delivered_qty - already_returned
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

        if not remaining_lines:
            messages.error(request, f"No delivered items from Sales Order {order.pk} are available for return.")
            return redirect('Sales:sales_order_detail', pk=pk)

        # Get the latest delivery for this order
        latest_delivery = order.deliveries.order_by('-document_date').first()

        # Pass data through session to prefill in ReturnCreateView
        request.session['prefill_return_data'] = {
            'document_date': str(timezone.now().date()),
            'posting_date': str(timezone.now().date()),
            'customer': order.customer_id,
            'contact_person': order.contact_person_id,
            'return_address': order.shipping_address_id,
            'sales_employee': order.sales_employee_id,
            'discount_amount': float(order.discount_amount),
            'total_amount': float(order.total_amount),
            'payable_amount': float(order.payable_amount),
            'paid_amount': float(order.paid_amount),
            'due_amount': float(order.due_amount),
            'payment_method': order.payment_method,
            'payment_reference': order.payment_reference,
            'payment_date': str(order.payment_date) if order.payment_date else None,
            'remarks': f"Return for Sales Order #{order.pk}",
            'delivery': latest_delivery.id if latest_delivery else None,
            'lines': remaining_lines
        }

        # Redirect to the return create view with prefilled data from session
        return redirect(reverse('Sales:return_create'))        
# class ConvertDeliveryToInvoiceView(LoginRequiredMixin, View):
#     """Convert a delivery to an AR Invoice"""

#     def dispatch(self, request, *args, **kwargs):
#         if not (request.user.has_perm('Sales.view_delivery') and 
#                 request.user.has_perm('Sales.add_arinvoice')):
#             return self.handle_no_permission()
#         return super().dispatch(request, *args, **kwargs)

#     def get(self, request, pk):
#         delivery = get_object_or_404(Delivery, pk=pk)

#         # Check if delivery can be invoiced
#         if delivery.status in ['Cancelled', 'Closed']:
#             messages.error(request, f"Delivery {delivery.pk} cannot be invoiced because it is {delivery.status}.")
#             return redirect('Sales:delivery_detail', pk=pk)

#         # Check previous invoices and calculate already invoiced quantities
#         invoiced_quantities = {}
#         existing_invoices = ARInvoice.objects.filter(delivery=delivery)

#         for invoice in existing_invoices:
#             for line in invoice.lines.all():
#                 dl_id = line.delivery_line_id
#                 if dl_id in invoiced_quantities:
#                     invoiced_quantities[dl_id] += line.quantity
#                 else:
#                     invoiced_quantities[dl_id] = line.quantity

#         # Check if all delivery items are already invoiced
#         all_invoiced = True
#         any_to_invoice = False

#         for d_line in delivery.lines.all():
#             invoiced_qty = invoiced_quantities.get(d_line.id, 0)
#             if invoiced_qty < d_line.quantity:
#                 all_invoiced = False
#                 any_to_invoice = True
#                 break

#         if all_invoiced:
#             messages.error(request, f"All items in Delivery {delivery.pk} have already been fully invoiced.")
#             return redirect('Sales:delivery_detail', pk=pk)

#         if not any_to_invoice:
#             messages.error(request, f"No items in Delivery {delivery.pk} are available for invoicing.")
#             return redirect('Sales:delivery_detail', pk=pk)

#         with transaction.atomic():
#             try:
#                 invoice = ARInvoice.objects.create(
#                     document_date=timezone.now().date(),
#                     posting_date=timezone.now().date(),
#                     due_date=timezone.now().date(),
#                     customer=delivery.customer,
#                     contact_person=delivery.contact_person,
#                     billing_address=delivery.customer.default_billing_address(),
#                     delivery=delivery,
#                     sales_order=delivery.sales_order,
#                     currency=delivery.currency,
#                     payment_terms=delivery.payment_terms,
#                     remarks=delivery.remarks,
#                     sales_employee=delivery.sales_employee,
#                     status='Open',
#                     discount_amount=delivery.discount_amount,
#                     paid_amount=delivery.paid_amount,
#                     payment_method=delivery.payment_method,
#                     payment_reference=delivery.payment_reference,
#                     payment_date=delivery.payment_date
#                 )
#             except Exception as e:
#                 print(f"Error creating invoice: {e}")
#                 messages.error(request, f"Error creating invoice: {e}")
#                 return redirect('Sales:delivery_detail', pk=pk)

#             total_invoice_amount = 0
#             lines_created = 0

#             for d_line in delivery.lines.all():
#                 invoiced_qty = invoiced_quantities.get(d_line.id, 0)
#                 remaining_qty = d_line.quantity - invoiced_qty

#                 if remaining_qty > 0:
#                     try:
#                         ar_line = ARInvoiceLine.objects.create(
#                             invoice=invoice,
#                             delivery_line=d_line,
#                             sales_order_line=d_line.sales_order_line,
#                             item_code=d_line.item_code,
#                             item_name=d_line.item_name,
#                             quantity=remaining_qty,
#                             unit_price=d_line.unit_price,
#                             uom=d_line.uom,
#                             remarks=d_line.remarks,
#                             is_active=True
#                         )
#                         total_invoice_amount += ar_line.quantity * ar_line.unit_price
#                         lines_created += 1
#                     except Exception as e:
#                         print(f"Error creating invoice line: {e}")
#                         messages.error(request, f"Error creating invoice line: {e}")
#                         return redirect('Sales:delivery_detail', pk=pk)

#             if lines_created == 0:
#                 messages.error(request, f"No items in Delivery {delivery.pk} are available for invoicing.")
#                 return redirect('Sales:delivery_detail', pk=pk)

#             invoice.total_amount = total_invoice_amount
#             invoice.payable_amount = invoice.total_amount - invoice.discount_amount
#             invoice.due_amount = invoice.payable_amount - invoice.paid_amount
#             invoice.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])

#             messages.success(request, f"Delivery {delivery.pk} successfully converted to Invoice {invoice.pk}.")
#             return redirect('Sales:arinvoice_detail', pk=invoice.pk)



class ConvertDeliveryToInvoiceView(LoginRequiredMixin, View):
    """
    Prefills invoice form using delivery data.
    Does not create invoice directly, instead redirects to invoice creation view.
    """
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.has_perm('Sales.view_delivery') and request.user.has_perm('Sales.add_arinvoice')):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        delivery = get_object_or_404(Delivery, pk=pk)

        if delivery.status in ['Cancelled', 'Closed']:
            messages.error(request, f"Delivery {delivery.pk} cannot be converted because it is {delivery.status}.")
            return redirect('Sales:delivery_detail', pk=pk)

        invoiced_quantities = {}
        for invoice in ARInvoice.objects.filter(delivery=delivery):
            for line in invoice.lines.all():
                key = (line.item_code, line.uom)
                invoiced_quantities[key] = invoiced_quantities.get(key, 0) + line.quantity

        remaining_lines = []
        for d_line in delivery.lines.all():
            key = (d_line.item_code, d_line.uom)
            already_invoiced = invoiced_quantities.get(key, 0)
            remaining_qty = d_line.quantity - already_invoiced
            if remaining_qty > 0:
                remaining_lines.append({
                    'item_code': d_line.item_code,
                    'item_name': d_line.item_name,
                    'quantity': float(remaining_qty),
                    'unit_price': float(d_line.unit_price),
                    'uom': d_line.uom,
                    'remarks': d_line.remarks,
                    'is_active': True
                })

        if not remaining_lines:
            messages.error(request, f"All items in Delivery {delivery.pk} have already been invoiced.")
            return redirect('Sales:delivery_detail', pk=pk)

        # Pass data through session to prefill in ARInvoiceCreateView
        request.session['prefill_invoice_data'] = {
            'document_date': str(delivery.document_date),
            'posting_date': str(delivery.posting_date),
            'due_date': str(delivery.posting_date),
            'customer': delivery.customer_id,
            'contact_person': delivery.contact_person_id,
            'billing_address': delivery.shipping_address_id,
            'sales_employee': delivery.sales_employee_id,
            'discount_amount': float(delivery.discount_amount),
            'total_amount': float(delivery.total_amount),
            'payable_amount': float(delivery.payable_amount),
            'paid_amount': float(delivery.paid_amount),
            'due_amount': float(delivery.due_amount),
            'payment_method': delivery.payment_method,
            'payment_reference': delivery.payment_reference,
            'payment_date': str(delivery.payment_date) if delivery.payment_date else None,
            'remarks': f"Invoice for Delivery #{delivery.pk}",
            'delivery': delivery.id,
            'sales_order': delivery.sales_order_id if delivery.sales_order else None,
            'lines': remaining_lines
        }

        # Redirect to the invoice create view with prefilled data from session
        return redirect(reverse('Sales:arinvoice_create'))