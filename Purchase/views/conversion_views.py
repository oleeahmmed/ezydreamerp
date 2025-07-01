from django.views.generic import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.urls import reverse_lazy
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import models

from ..models import (
    PurchaseQuotation, PurchaseQuotationLine, 
    PurchaseOrder, PurchaseOrderLine,
    GoodsReceiptPo, GoodsReceiptPoLine, 
    GoodsReturn, GoodsReturnLine,
    APInvoice, APInvoiceLine
)

class ConvertQuotationToOrderView(LoginRequiredMixin, View):
    """Convert a purchase quotation to a purchase order"""
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.has_perm('Purchase.view_purchasequotation') and 
                request.user.has_perm('Purchase.add_purchaseorder')):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, pk):
        quotation = get_object_or_404(PurchaseQuotation, pk=pk)
        
        # Check if quotation can be converted
        if quotation.status in ['Expired', 'Cancelled', 'Converted']:
            messages.error(request, f"Quotation {quotation.pk} cannot be converted because it is {quotation.status}.")
            return redirect('Purchase:purchase_quotation_detail', pk=pk)
        
        with transaction.atomic():
            # Create purchase order
            try:
                order = PurchaseOrder.objects.create(
                    document_date=quotation.document_date,
                    delivery_date=quotation.valid_until,
                    vendor=quotation.vendor,
                    contact_person=quotation.contact_person,
                    billing_address=quotation.billing_address,
                    shipping_address=quotation.shipping_address,
                    currency=quotation.currency,
                    payment_terms=quotation.payment_terms,
                    remarks=quotation.remarks,
                    purchasing_employee=quotation.purchasing_employee,
                    status='Draft',
                    # Financial fields
                    discount_amount=quotation.discount_amount,
                    tax_amount=quotation.tax_amount,
                    total_amount=quotation.total_amount,
                    payable_amount=quotation.payable_amount,
                    # Payment information fields
                    paid_amount=quotation.paid_amount,
                    due_amount=quotation.due_amount,
                    payment_method=quotation.payment_method,
                    payment_reference=quotation.payment_reference,
                    payment_date=quotation.payment_date
                )
            except Exception as e:
                print(f"Error creating order: {e}")
                messages.error(request, f"Error creating order: {e}")
                return redirect('Purchase:purchase_quotation_detail', pk=pk)
            
            # Create order lines from quotation lines
            total_amount = 0
            for q_line in quotation.lines.all():
                try:
                    line_total = Decimal(q_line.quantity * q_line.unit_price).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    order_line = PurchaseOrderLine.objects.create(
                        order=order,
                        item_code=q_line.item_code,
                        item_name=q_line.item_name,
                        quantity=q_line.quantity,
                        unit_price=q_line.unit_price,
                        total_amount=line_total,
                        uom=q_line.uom,
                        remarks=q_line.remarks,
                        is_active=True
                    )
                    total_amount += line_total
                except Exception as e:
                    print(f"Error creating order line: {e}")
                    messages.error(request, f"Error creating order line: {e}")
                    return redirect('Purchase:purchase_quotation_detail', pk=pk)
            
            # Update order totals
            order.total_amount = total_amount
            order.payable_amount = total_amount - order.discount_amount
            order.due_amount = order.payable_amount - order.paid_amount
            order.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])
            
            # Update quotation status
            quotation.status = 'Converted'
            quotation.save(update_fields=['status'])
            
            messages.success(request, f"Quotation {quotation.pk} successfully converted to Purchase Order {order.pk}.")
            return redirect('Purchase:purchase_order_detail', pk=order.pk)

class ConvertOrderToGoodsReceiptView(LoginRequiredMixin, View):
    """Convert a purchase order to a goods receipt"""
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.has_perm('Purchase.view_purchaseorder') and 
                request.user.has_perm('Purchase.add_goodsreceiptpo')):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, pk):
        order = get_object_or_404(PurchaseOrder, pk=pk)
        
        # Check if order can be converted
        if order.status in ['Cancelled', 'Closed']:
            messages.error(request, f"Purchase Order {order.pk} cannot be converted because it is {order.status}.")
            return redirect('Purchase:purchase_order_detail', pk=pk)
        
        # Check if there are existing goods receipts for this order
        existing_receipts = GoodsReceiptPo.objects.filter(purchase_order=order, status__in=['Open', 'Partially Received', 'Received'])
        
        # Calculate already received quantities for each line item
        received_quantities = {}
        for receipt in existing_receipts:
            for line in receipt.lines.all():
                if line.purchase_order_line_id in received_quantities:
                    received_quantities[line.purchase_order_line_id] += line.quantity
                else:
                    received_quantities[line.purchase_order_line_id] = line.quantity
        
        # Check if all items are fully received
        all_received = True
        any_to_receive = False
        
        for order_line in order.lines.all():
            received_qty = received_quantities.get(order_line.id, 0)
            if received_qty < order_line.quantity:
                all_received = False
                any_to_receive = True
                break
        
        if all_received:
            messages.error(request, f"All items in Purchase Order {order.pk} have already been fully received.")
            return redirect('Purchase:purchase_order_detail', pk=pk)
        
        if not any_to_receive:
            messages.error(request, f"No items in Purchase Order {order.pk} are available for receipt.")
            return redirect('Purchase:purchase_order_detail', pk=pk)
        
        with transaction.atomic():
            # Create goods receipt
            try:
                # Set warehouse based on user if available
                warehouse = None
                if hasattr(request.user, 'default_warehouse'):
                    warehouse = request.user.default_warehouse
                
                goods_receipt = GoodsReceiptPo.objects.create(
                    document_date=timezone.now().date(),
                    posting_date=timezone.now().date(),
                    vendor=order.vendor,
                    contact_person=order.contact_person,
                    shipping_address=order.shipping_address,
                    purchase_order=order,
                    warehouse=warehouse,
                    currency=order.currency,
                    payment_terms=order.payment_terms,
                    discount_amount=order.discount_amount,
                    tax_amount=order.tax_amount,
                    total_amount=0,  # Will calculate after adding lines
                    payable_amount=0,  # Will calculate after adding lines
                    paid_amount=order.paid_amount,
                    due_amount=0,  # Will calculate after adding lines
                    payment_method=order.payment_method,
                    payment_reference=order.payment_reference,
                    payment_date=order.payment_date,
                    remarks=order.remarks,
                    status='Draft',
                    purchasing_employee=order.purchasing_employee
                )
            except Exception as e:
                print(f"Error creating goods receipt: {e}")
                messages.error(request, f"Error creating goods receipt: {e}")
                return redirect('Purchase:purchase_order_detail', pk=pk)
            
            # Create goods receipt lines from order lines for remaining quantities
            total_receipt_amount = 0
            lines_created = 0
            
            for o_line in order.lines.all():
                received_qty = received_quantities.get(o_line.id, 0)
                remaining_qty = o_line.quantity - received_qty
                
                if remaining_qty > 0:
                    try:
                        line_total = Decimal(remaining_qty * o_line.unit_price).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                        receipt_line = GoodsReceiptPoLine.objects.create(
                            goods_receipt=goods_receipt,
                            purchase_order_line=o_line,
                            item_code=o_line.item_code,
                            item_name=o_line.item_name,
                            quantity=remaining_qty,
                            unit_price=o_line.unit_price,
                            total_amount=line_total,
                            uom=o_line.uom,
                            remarks=o_line.remarks,
                            is_active=True
                        )
                        total_receipt_amount += line_total
                        lines_created += 1
                    except Exception as e:
                        print(f"Error creating goods receipt line: {e}")
                        messages.error(request, f"Error creating goods receipt line: {e}")
                        return redirect('Purchase:purchase_order_detail', pk=pk)
            
            if lines_created == 0:
                # Rollback if no lines were created
                messages.error(request, f"No items in Purchase Order {order.pk} are available for receipt.")
                return redirect('Purchase:purchase_order_detail', pk=pk)
            
            # Update goods receipt total amount and calculate payable and due amounts
            goods_receipt.total_amount = total_receipt_amount
            goods_receipt.payable_amount = total_receipt_amount - goods_receipt.discount_amount
            goods_receipt.due_amount = goods_receipt.payable_amount - goods_receipt.paid_amount
            goods_receipt.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])
            
            # Update order status
            if all(received_quantities.get(line.id, 0) + (line.quantity - received_quantities.get(line.id, 0)) >= line.quantity for line in order.lines.all()):
                order.status = 'Received'
            else:
                order.status = 'Partially Received'
            
            order.save(update_fields=['status'])
            
            messages.success(request, f"Purchase Order {order.pk} successfully converted to Goods Receipt {goods_receipt.pk}.")
            return redirect('Purchase:goods_receipt_detail', pk=goods_receipt.pk)

class ConvertGoodsReceiptToReturnView(LoginRequiredMixin, View):
    """Convert a goods receipt to a goods return"""
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.has_perm('Purchase.view_goodsreceiptpo') and 
                request.user.has_perm('Purchase.add_goodsreturn')):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, pk):
        goods_receipt = get_object_or_404(GoodsReceiptPo, pk=pk)
        
        # Check if goods receipt can be converted
        if goods_receipt.status in ['Cancelled', 'Closed', 'Draft']:
            messages.error(request, f"Goods Receipt {goods_receipt.pk} cannot be converted because it is {goods_receipt.status}.")
            return redirect('Purchase:goods_receipt_detail', pk=pk)
        
        # Check if there are existing returns for this goods receipt
        existing_returns = GoodsReturn.objects.filter(goods_receipt=goods_receipt)
        
        # Calculate already returned quantities for each line item
        returned_quantities = {}
        for return_doc in existing_returns:
            for line in return_doc.lines.all():
                if line.goods_receipt_line_id in returned_quantities:
                    returned_quantities[line.goods_receipt_line_id] += line.quantity
                else:
                    returned_quantities[line.goods_receipt_line_id] = line.quantity
        
        # Check if all items are fully returned
        all_returned = True
        any_to_return = False
        
        for receipt_line in goods_receipt.lines.all():
            returned_qty = returned_quantities.get(receipt_line.id, 0)
            if returned_qty < receipt_line.quantity:
                all_returned = False
                any_to_return = True
                break
        
        if all_returned:
            messages.error(request, f"All items in Goods Receipt {goods_receipt.pk} have already been fully returned.")
            return redirect('Purchase:goods_receipt_detail', pk=pk)
        
        if not any_to_return:
            messages.error(request, f"No items in Goods Receipt {goods_receipt.pk} are available for return.")
            return redirect('Purchase:goods_receipt_detail', pk=pk)
        
        with transaction.atomic():
            # Create return
            try:
                goods_return = GoodsReturn.objects.create(
                    document_date=timezone.now().date(),
                    posting_date=timezone.now().date(),
                    vendor=goods_receipt.vendor,
                    contact_person=goods_receipt.contact_person,
                    return_address=goods_receipt.shipping_address,
                    goods_receipt=goods_receipt,
                    warehouse=goods_receipt.warehouse,
                    currency=goods_receipt.currency,
                    payment_terms=goods_receipt.payment_terms,
                    discount_amount=goods_receipt.discount_amount,
                    tax_amount=goods_receipt.tax_amount,
                    total_amount=0,  # Will calculate after adding lines
                    payable_amount=0,  # Will calculate after adding lines
                    paid_amount=goods_receipt.paid_amount,
                    due_amount=0,  # Will calculate after adding lines
                    payment_method=goods_receipt.payment_method,
                    payment_reference=goods_receipt.payment_reference,
                    payment_date=goods_receipt.payment_date,
                    return_reason=f"Return for goods receipt {goods_receipt.pk}",
                    remarks=goods_receipt.remarks,
                    purchasing_employee=goods_receipt.purchasing_employee,
                    status='Draft',
                )
            except Exception as e:
                print(f"Error creating goods return: {e}")
                messages.error(request, f"Error creating goods return: {e}")
                return redirect('Purchase:goods_receipt_detail', pk=pk)
            
            # Create return lines from goods receipt lines for remaining quantities
            total_return_amount = 0
            lines_created = 0
            
            for gr_line in goods_receipt.lines.all():
                returned_qty = returned_quantities.get(gr_line.id, 0)
                remaining_qty = gr_line.quantity - returned_qty
                
                if remaining_qty > 0:
                    try:
                        line_total = Decimal(remaining_qty * gr_line.unit_price).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                        return_line = GoodsReturnLine.objects.create(
                            goods_return=goods_return,
                            goods_receipt_line=gr_line,
                            purchase_order_line=gr_line.purchase_order_line,
                            item_code=gr_line.item_code,
                            item_name=gr_line.item_name,
                            quantity=remaining_qty,
                            unit_price=gr_line.unit_price,
                            total_amount=line_total,
                            uom=gr_line.uom,
                            remarks=gr_line.remarks,
                            is_active=True
                        )
                        total_return_amount += line_total
                        lines_created += 1
                    except Exception as e:
                        print(f"Error creating goods return line: {e}")
                        messages.error(request, f"Error creating goods return line: {e}")
                        return redirect('Purchase:goods_receipt_detail', pk=pk)
            
            if lines_created == 0:
                # Rollback if no lines were created
                messages.error(request, f"No items in Goods Receipt {goods_receipt.pk} are available for return.")
                return redirect('Purchase:goods_receipt_detail', pk=pk)
            
            # Update return total amount and calculate payable and due amounts
            goods_return.total_amount = total_return_amount
            goods_return.payable_amount = total_return_amount - goods_return.discount_amount
            goods_return.due_amount = goods_return.payable_amount - goods_return.paid_amount
            goods_return.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])
            
            messages.success(request, f"Goods Receipt {goods_receipt.pk} successfully converted to Goods Return {goods_return.pk}.")
            return redirect('Purchase:goods_return_detail', pk=goods_return.pk)

class ConvertOrderToReturnView(LoginRequiredMixin, View):
    """Convert a purchase order directly to a goods return"""
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.has_perm('Purchase.view_purchaseorder') and 
                request.user.has_perm('Purchase.add_goodsreturn')):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, pk):
        order = get_object_or_404(PurchaseOrder, pk=pk)
        
        # Check if order can be converted
        if order.status in ['Cancelled', 'Closed', 'Draft']:
            messages.error(request, f"Purchase Order {order.pk} cannot be converted because it is {order.status}.")
            return redirect('Purchase:purchase_order_detail', pk=pk)
        
        with transaction.atomic():
            # Create goods return
            try:
                goods_return = GoodsReturn.objects.create(
                    document_date=timezone.now().date(),
                    posting_date=timezone.now().date(),
                    vendor=order.vendor,
                    contact_person=order.contact_person,
                    return_address=order.shipping_address,
                    purchase_order=order,
                    currency=order.currency,
                    payment_terms=order.payment_terms,
                    discount_amount=order.discount_amount,
                    tax_amount=order.tax_amount,
                    total_amount=0,  # Will calculate after adding lines
                    payable_amount=0,  # Will calculate after adding lines
                    paid_amount=order.paid_amount,
                    due_amount=0,  # Will calculate after adding lines
                    payment_method=order.payment_method,
                    payment_reference=order.payment_reference,
                    payment_date=order.payment_date,
                    return_reason=f"Return for purchase order {order.pk}",
                    remarks=order.remarks,
                    purchasing_employee=order.purchasing_employee,
                    status='Draft',
                )
            except Exception as e:
                print(f"Error creating goods return: {e}")
                messages.error(request, f"Error creating goods return: {e}")
                return redirect('Purchase:purchase_order_detail', pk=pk)
            
            # Create return lines from order lines
            total_return_amount = 0
            
            for o_line in order.lines.all():
                try:
                    line_total = Decimal(o_line.quantity * o_line.unit_price).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    return_line = GoodsReturnLine.objects.create(
                        goods_return=goods_return,
                        purchase_order_line=o_line,
                        item_code=o_line.item_code,
                        item_name=o_line.item_name,
                        quantity=o_line.quantity,
                        unit_price=o_line.unit_price,
                        total_amount=line_total,
                        uom=o_line.uom,
                        remarks=o_line.remarks,
                        is_active=True
                    )
                    total_return_amount += line_total
                except Exception as e:
                    print(f"Error creating goods return line: {e}")
                    messages.error(request, f"Error creating goods return line: {e}")
                    return redirect('Purchase:purchase_order_detail', pk=pk)
            
            # Update return total amount and calculate payable and due amounts
            goods_return.total_amount = total_return_amount
            goods_return.payable_amount = total_return_amount - goods_return.discount_amount
            goods_return.due_amount = goods_return.payable_amount - goods_return.paid_amount
            goods_return.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])
            
            messages.success(request, f"Purchase Order {order.pk} successfully converted to Goods Return {goods_return.pk}.")
            return redirect('Purchase:goods_return_detail', pk=goods_return.pk)

class ConvertOrderToInvoiceView(LoginRequiredMixin, View):
    """Convert a purchase order to an AP invoice"""
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.has_perm('Purchase.view_purchaseorder') and 
                request.user.has_perm('Purchase.add_apinvoice')):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, pk):
        order = get_object_or_404(PurchaseOrder, pk=pk)
        
        # Check if order can be converted
        if order.status in ['Cancelled', 'Closed']:
            messages.error(request, f"Purchase Order {order.pk} cannot be converted because it is {order.status}.")
            return redirect('Purchase:purchase_order_detail', pk=pk)
        
        with transaction.atomic():
            # Create invoice
            try:
                invoice = APInvoice.objects.create(
                    document_date=timezone.now().date(),
                    posting_date=timezone.now().date(),
                    due_date=timezone.now().date() + timezone.timedelta(days=30),  # Default 30 days
                    vendor=order.vendor,
                    contact_person=order.contact_person,
                    billing_address=order.billing_address,
                    purchase_order=order,
                    currency=order.currency,
                    payment_terms=order.payment_terms,
                    status='Draft',
                    purchasing_employee=order.purchasing_employee,
                    # Financial fields
                    discount_amount=order.discount_amount,
                    tax_amount=order.tax_amount,
                    total_amount=order.total_amount,
                    payable_amount=order.payable_amount,
                    # Payment information fields
                    paid_amount=order.paid_amount,
                    due_amount=order.due_amount,
                    payment_method=order.payment_method,
                    payment_reference=order.payment_reference,
                    payment_date=order.payment_date,
                    remarks=order.remarks
                )
                
                # Copy line items from purchase order
                for order_line in order.lines.filter(is_active=True):
                    line_total = Decimal(order_line.quantity * order_line.unit_price).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    APInvoiceLine.objects.create(
                        invoice=invoice,
                        purchase_order_line=order_line,
                        item_code=order_line.item_code,
                        item_name=order_line.item_name,
                        quantity=order_line.quantity,
                        unit_price=order_line.unit_price,
                        total_amount=line_total,
                        uom=order_line.uom,
                        remarks=order_line.remarks,
                        is_active=True
                    )
                
            except Exception as e:
                print(f"Error creating invoice: {e}")
                messages.error(request, f"Error creating invoice: {e}")
                return redirect('Purchase:purchase_order_detail', pk=pk)
            
            # Update order status
            if order.status not in ['Invoiced', 'Partially Invoiced']:
                order.status = 'Partially Invoiced'
                order.save(update_fields=['status'])
            
            messages.success(request, f"Purchase Order {order.pk} successfully converted to AP Invoice {invoice.pk}.")
            return redirect('Purchase:apinvoice_detail', pk=invoice.pk)

class ConvertGoodsReceiptToInvoiceView(LoginRequiredMixin, View):
    """Convert a goods receipt to an AP invoice"""
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.has_perm('Purchase.view_goodsreceiptpo') and 
                request.user.has_perm('Purchase.add_apinvoice')):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, pk):
        goods_receipt = get_object_or_404(GoodsReceiptPo, pk=pk)
        
        # Check if goods receipt can be converted
        if goods_receipt.status in ['Cancelled', 'Closed', 'Draft']:
            messages.error(request, f"Goods Receipt {goods_receipt.pk} cannot be converted because it is {goods_receipt.status}.")
            return redirect('Purchase:goods_receipt_detail', pk=pk)
        
        with transaction.atomic():
            # Create invoice
            try:
                invoice = APInvoice.objects.create(
                    document_date=timezone.now().date(),
                    posting_date=timezone.now().date(),
                    due_date=timezone.now().date() + timezone.timedelta(days=30),  # Default 30 days
                    vendor=goods_receipt.vendor,
                    contact_person=goods_receipt.contact_person,
                    billing_address=goods_receipt.purchase_order.billing_address if goods_receipt.purchase_order else None,
                    goods_receipt=goods_receipt,
                    purchase_order=goods_receipt.purchase_order,
                    currency=goods_receipt.currency,
                    payment_terms=goods_receipt.payment_terms,
                    status='Draft',
                    purchasing_employee=goods_receipt.purchasing_employee,
                    # Financial fields
                    discount_amount=goods_receipt.discount_amount,
                    tax_amount=goods_receipt.tax_amount,
                    total_amount=goods_receipt.total_amount,
                    payable_amount=goods_receipt.payable_amount,
                    # Payment information fields
                    paid_amount=goods_receipt.paid_amount,
                    due_amount=goods_receipt.due_amount,
                    payment_method=goods_receipt.payment_method,
                    payment_reference=goods_receipt.payment_reference,
                    payment_date=goods_receipt.payment_date,
                    remarks=goods_receipt.remarks
                )
                
                # Copy line items from goods receipt
                for receipt_line in goods_receipt.lines.filter(is_active=True):
                    line_total = Decimal(receipt_line.quantity * receipt_line.unit_price).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
                    APInvoiceLine.objects.create(
                        invoice=invoice,
                        goods_receipt_line=receipt_line,
                        purchase_order_line=receipt_line.purchase_order_line,
                        item_code=receipt_line.item_code,
                        item_name=receipt_line.item_name,
                        quantity=receipt_line.quantity,
                        unit_price=receipt_line.unit_price,
                        total_amount=line_total,
                        uom=receipt_line.uom,
                        remarks=receipt_line.remarks,
                        is_active=True
                    )
                
            except Exception as e:
                print(f"Error creating invoice: {e}")
                messages.error(request, f"Error creating invoice: {e}")
                return redirect('Purchase:goods_receipt_detail', pk=pk)
            
            # Update purchase order status if it exists
            if goods_receipt.purchase_order and goods_receipt.purchase_order.status not in ['Invoiced', 'Partially Invoiced']:
                goods_receipt.purchase_order.status = 'Partially Invoiced'
                goods_receipt.purchase_order.save(update_fields=['status'])
            
            messages.success(request, f"Goods Receipt {goods_receipt.pk} successfully converted to AP Invoice {invoice.pk}.")
            return redirect('Purchase:apinvoice_detail', pk=invoice.pk)