from django.views.generic import FormView, TemplateView
from django.db.models import Sum, Count, Avg, F, DecimalField, Q, ExpressionWrapper, FloatField
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from collections import defaultdict


from ..forms.sales_report_forms import SalesReportForm
from ..models import SalesOrder, SalesOrderLine, SalesEmployee
from BusinessPartnerMasterData.models import BusinessPartner
from Inventory.models import Item

class SalesReportView(FormView):
    """View for the sales report form"""
    template_name = 'sales/reports/sales_report_form.html'
    form_class = SalesReportForm
    
    def form_valid(self, form):
        # Get form data
        from_date = form.cleaned_data['from_date']
        to_date = form.cleaned_data['to_date']
        business_partner = form.cleaned_data.get('business_partner')
        sales_employee = form.cleaned_data.get('sales_employee')
        product = form.cleaned_data.get('product')
        report_type = form.cleaned_data.get('report_type', 'detail')
        
        # Redirect to results view with parameters
        url = reverse('Sales:sales_report_results')
        params = f'?from_date={from_date}&to_date={to_date}&report_type={report_type}'
        
        if business_partner:
            params += f'&business_partner={business_partner.id}'
        
        if sales_employee:
            params += f'&sales_employee={sales_employee.id}'
            
        if product:
            params += f'&product={product.id}'
            
        return redirect(f'{url}{params}')

class SalesReportResultsView(TemplateView):
    """View for displaying sales report results"""
    template_name = 'sales/reports/sales_report_results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get query parameters
        from_date = self.request.GET.get('from_date')
        to_date = self.request.GET.get('to_date')
        business_partner_id = self.request.GET.get('business_partner')
        sales_employee_id = self.request.GET.get('sales_employee')
        product_id = self.request.GET.get('product')
        report_type = self.request.GET.get('report_type', 'detail')
        
        # Convert string dates to datetime objects
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            # Default to current month if dates are invalid
            to_date = timezone.now().date()
            from_date = to_date.replace(day=1)
        
        # Base queryset for sales orders
        orders_queryset = SalesOrder.objects.filter(
            document_date__gte=from_date,
            document_date__lte=to_date
        ).order_by('-document_date')
        
        # Apply additional filters if provided
        if business_partner_id:
            orders_queryset = orders_queryset.filter(customer_id=business_partner_id)
        
        if sales_employee_id:
            orders_queryset = orders_queryset.filter(sales_employee_id=sales_employee_id)
        
        # Get all order lines for the filtered orders
        order_lines_queryset = SalesOrderLine.objects.filter(
            order__in=orders_queryset
        ).select_related('order', 'order__customer', 'order__sales_employee')
        
        # Apply product filter if provided
        if product_id:
            order_lines_queryset = order_lines_queryset.filter(item_code=product_id)
            # We also need to update orders_queryset to only include orders with this product
            order_ids = order_lines_queryset.values_list('order_id', flat=True).distinct()
            orders_queryset = orders_queryset.filter(id__in=order_ids)
        
        # Get all unique products from the order lines
        product_ids = order_lines_queryset.values_list('item_code', flat=True).distinct()
        products = Item.objects.filter(code__in=product_ids)
        
        # Calculate summary data
        # Assuming SalesOrder has a total_amount field that's a direct field, not an aggregate
        total_amount = orders_queryset.aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders = orders_queryset.count()
        
        # Assuming SalesOrderLine has a quantity field and we need to calculate line total as quantity * unit_price
        total_items = order_lines_queryset.aggregate(total=Sum('quantity'))['total'] or 0
        
        summary_data = {
            'total_orders': total_orders,
            'total_amount': total_amount,
            'total_items': total_items,
            'avg_order_value': total_amount / total_orders if total_orders > 0 else 0,
        }
        
        # Calculate product summary data
        # Assuming SalesOrderLine has unit_price and quantity fields, and we calculate total_amount as unit_price * quantity
        product_summary = order_lines_queryset.values('item_code', 'item_name').annotate(
            total_quantity=Sum('quantity'),
            # Calculate total amount as quantity * unit_price
            total_amount=Sum(F('quantity') * F('unit_price')),
            # Calculate average price
            avg_price=ExpressionWrapper(
                Sum(F('quantity') * F('unit_price')) / Sum('quantity'),
                output_field=DecimalField()
            )
        ).order_by('-total_amount')
        
        # Calculate daily sales data for chart
        daily_sales = orders_queryset.annotate(
            date=TruncDate('document_date')
        ).values('date').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('date')
        
        # Calculate date-wise summary
        date_summary = orders_queryset.annotate(
            date=TruncDate('document_date')
        ).values('date').annotate(
            order_count=Count('id'),
            total_amount=Sum('total_amount')
        ).order_by('date')
        
        # Add avg_order_value to date_summary
        for item in date_summary:
            item['avg_order_value'] = item['total_amount'] / item['order_count'] if item['order_count'] > 0 else 0
        
        # Calculate sales employee summary
        employee_summary = orders_queryset.values(
            'sales_employee__id', 
            'sales_employee__name'
        ).annotate(
            order_count=Count('id'),
            total_amount=Sum('total_amount')
        ).order_by('-total_amount')
        
        # Add avg_order_value to employee_summary
        for employee in employee_summary:
            employee['avg_order_value'] = employee['total_amount'] / employee['order_count'] if employee['order_count'] > 0 else 0
        
        # Calculate date-wise sales employee summary
        employee_date_summary = orders_queryset.annotate(
            date=TruncDate('document_date')
        ).values(
            'date', 
            'sales_employee__id', 
            'sales_employee__name'
        ).annotate(
            order_count=Count('id'),
            total_amount=Sum('total_amount')
        ).order_by('date', '-total_amount')
        
        # Calculate employee order details
        employee_order_details = order_lines_queryset.values(
            'order__sales_employee__name',
            'order__id',
            'order__document_date',
            'order__customer__name',
            'item_name',
            'quantity',
            'unit_price'
        ).annotate(
            line_total=F('quantity') * F('unit_price')
        ).order_by('order__sales_employee__name', 'order__document_date')
        
        # Calculate customer summary
        customer_summary = orders_queryset.values(
            'customer__id', 
            'customer__name'
        ).annotate(
            order_count=Count('id'),
            total_amount=Sum('total_amount')
        ).order_by('-total_amount')
        
        # Add avg_order_value to customer_summary
        for customer in customer_summary:
            customer['avg_order_value'] = customer['total_amount'] / customer['order_count'] if customer['order_count'] > 0 else 0
        
        # Calculate date-wise customer summary
        customer_date_summary = orders_queryset.annotate(
            date=TruncDate('document_date')
        ).values(
            'date', 
            'customer__id', 
            'customer__name'
        ).annotate(
            order_count=Count('id'),
            total_amount=Sum('total_amount')
        ).order_by('date', '-total_amount')
        
        # Calculate customer order details
        customer_order_details = order_lines_queryset.values(
            'order__customer__name',
            'order__id',
            'order__document_date',
            'order__sales_employee__name',
            'item_name',
            'quantity',
            'unit_price'
        ).annotate(
            line_total=F('quantity') * F('unit_price')
        ).order_by('order__customer__name', 'order__document_date')
        
        # Calculate product date-wise summary
        product_date_summary = order_lines_queryset.annotate(
            date=TruncDate('order__document_date')
        ).values(
            'date', 
            'item_code', 
            'item_name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_amount=Sum(F('quantity') * F('unit_price'))
        ).order_by('date', '-total_amount')
        
        # Calculate product order details
        product_order_details = order_lines_queryset.values(
            'item_name',
            'order__id',
            'order__document_date',
            'order__customer__name',
            'order__sales_employee__name',
            'quantity',
            'unit_price'
        ).annotate(
            line_total=F('quantity') * F('unit_price')
        ).order_by('item_name', 'order__document_date')
        
        # Get all sales employees and customers for filtering
        all_sales_employees = SalesEmployee.objects.all()
        all_customers = BusinessPartner.objects.filter(bp_type='C',)
        all_products = Item.objects.all()
        
        # Create filter descriptions for the report header
        filter_descriptions = [
            f"{_('Period')}: {from_date.strftime('%b %d, %Y')} - {to_date.strftime('%b %d, %Y')}"
        ]
        
        if business_partner_id:
            customer_name = BusinessPartner.objects.get(id=business_partner_id).name
            filter_descriptions.append(f"{_('Customer')}: {customer_name}")
            
        if sales_employee_id:
            employee_name = SalesEmployee.objects.get(id=sales_employee_id).name
            filter_descriptions.append(f"{_('Sales Employee')}: {employee_name}")
            
        if product_id:
            product_name = Item.objects.get(code=product_id).name
            filter_descriptions.append(f"{_('Product')}: {product_name}")
            
        filter_descriptions.append(f"{_('Report Type')}: {_('Detailed') if report_type == 'detail' else _('Summary')}")
        
        # Add all data to context
        context.update({
            'from_date': from_date,
            'to_date': to_date,
            'orders': orders_queryset,
            'order_lines': order_lines_queryset,
            'products': products,
            'product_summary': product_summary,
            'summary_data': summary_data,
            'daily_sales': daily_sales,
            'report_type': report_type,
            'date_summary': date_summary,
            'employee_summary': employee_summary,
            'employee_date_summary': employee_date_summary,
            'employee_order_details': employee_order_details,
            'customer_summary': customer_summary,
            'customer_date_summary': customer_date_summary,
            'customer_order_details': customer_order_details,
            'product_date_summary': product_date_summary,
            'product_order_details': product_order_details,
            'all_sales_employees': all_sales_employees,
            'all_customers': all_customers,
            'all_products': all_products,
            'selected_employee_id': sales_employee_id,
            'selected_customer_id': business_partner_id,
            'selected_product_id': product_id,
            'filter_descriptions': filter_descriptions,
            'unique_products': product_summary.count(),
        })
        
        return context