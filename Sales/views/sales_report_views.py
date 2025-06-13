from django.views.generic import ListView, TemplateView
from django.db.models import Sum, Q
from django.utils import timezone
from Sales.models import SalesOrder, SalesEmployee, SalesOrderLine
from BusinessPartnerMasterData.models import BusinessPartner
from config.views import GenericFilterView
from ..forms.sales_report_forms import SalesReportFilterForm


class SalesReportListView(TemplateView):
    template_name = 'sales/reports/sales_report_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Sales Reports'
        return context


class SalesReportView(GenericFilterView):
    model = SalesOrder
    template_name = 'sales/reports/sales_report.html'
    context_object_name = 'sales_orders'
    filter_form_class = SalesReportFilterForm
    permission_required = 'Sales.view_salesorder'

    def get_queryset(self):
        """
        Override to get the queryset and initialize the filter form.
        """
        queryset = SalesOrder.objects.select_related(
            'customer',
            'sales_employee'
        )
        
        # Initialize filter form
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
        else:
            self.filter_form = None
        
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        """Apply custom filtering logic for sales report"""
        filters = self.filter_form.cleaned_data
        
        # Search filter (for Sales Order ID)
        if filters.get('search'):
            search_term = filters['search']
            queryset = queryset.filter(
                Q(id__icontains=search_term)
            )
        
        # Date filters
        if filters.get('start_date'):
            queryset = queryset.filter(document_date__gte=filters['start_date'])
        
        if filters.get('end_date'):
            queryset = queryset.filter(document_date__lte=filters['end_date'])
        
        # Customer filter
        if filters.get('customer'):
            queryset = queryset.filter(customer=filters['customer'])
        
        # Sales Employee filter
        if filters.get('sales_employee'):
            queryset = queryset.filter(sales_employee=filters['sales_employee'])
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter values to context for template
        if hasattr(self, 'filter_form'):
            if self.filter_form and self.filter_form.is_valid():
                context.update({
                    'start_date': self.filter_form.cleaned_data.get('start_date', ''),
                    'end_date': self.filter_form.cleaned_data.get('end_date', ''),
                    'selected_customer': self.filter_form.cleaned_data.get('customer'),
                    'selected_employee': self.filter_form.cleaned_data.get('sales_employee'),
                    'search_term': self.filter_form.cleaned_data.get('search'),
                })
        
        context['page_title'] = 'Sales Report'
        context['all_customers'] = BusinessPartner.objects.filter(bp_type='C')
        context['all_sales_employees'] = SalesEmployee.objects.all()
        
        # Calculate totals for current filtered results
        orders = context['sales_orders']
        total_amount = sum(order.total_amount or 0 for order in orders)
        total_payable = sum(order.payable_amount or 0 for order in orders)
        total_paid = sum(getattr(order, 'paid_amount', 0) or 0 for order in orders)
        total_due = sum(getattr(order, 'due_amount', 0) or 0 for order in orders)
        
        context.update({
            'total_amount': total_amount,
            'total_payable': total_payable,
            'total_paid': total_paid,
            'total_due': total_due,
            'total_orders': len(orders),
            'avg_order_value': total_amount / len(orders) if orders else 0,
        })
        
        # Add filter summary for display
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            
            if filters.get('start_date') and filters.get('end_date'):
                filter_summary.append(f"Period: {filters['start_date']} to {filters['end_date']}")
            elif filters.get('start_date'):
                filter_summary.append(f"From: {filters['start_date']}")
            elif filters.get('end_date'):
                filter_summary.append(f"Until: {filters['end_date']}")
            
            if filters.get('customer'):
                filter_summary.append(f"Customer: {filters['customer'].name}")
            
            if filters.get('sales_employee'):
                filter_summary.append(f"Sales Employee: {filters['sales_employee'].name}")
            
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
        
        context['filter_summary'] = filter_summary
        
        return context

class SalesReportDetailsView(GenericFilterView):
    model = SalesOrder
    template_name = 'sales/reports/sales_report_details.html'
    context_object_name = 'sales_orders'
    filter_form_class = SalesReportFilterForm
    permission_required = 'Sales.view_salesorder'

    def get_queryset(self):
        """
        Override to get the queryset with related lines and initialize the filter form.
        """
        queryset = SalesOrder.objects.select_related(
            'customer',
            'sales_employee'
        ).prefetch_related('lines')
        
        # Initialize filter form
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
        else:
            self.filter_form = None
        
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        """Apply custom filtering logic for detailed sales report"""
        filters = self.filter_form.cleaned_data
        
        # Search filter (for Sales Order ID)
        if filters.get('search'):
            search_term = filters['search']
            queryset = queryset.filter(
                Q(id__icontains=search_term)
            )
        
        # Date filters
        if filters.get('start_date'):
            queryset = queryset.filter(document_date__gte=filters['start_date'])
        
        if filters.get('end_date'):
            queryset = queryset.filter(document_date__lte=filters['end_date'])
        
        # Customer filter
        if filters.get('customer'):
            queryset = queryset.filter(customer=filters['customer'])
        
        # Sales Employee filter
        if filters.get('sales_employee'):
            queryset = queryset.filter(sales_employee=filters['sales_employee'])
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter values to context for template
        if hasattr(self, 'filter_form'):
            if self.filter_form and self.filter_form.is_valid():
                context.update({
                    'start_date': self.filter_form.cleaned_data.get('start_date', ''),
                    'end_date': self.filter_form.cleaned_data.get('end_date', ''),
                    'selected_customer': self.filter_form.cleaned_data.get('customer'),
                    'selected_employee': self.filter_form.cleaned_data.get('sales_employee'),
                    'search_term': self.filter_form.cleaned_data.get('search'),
                })
        
        context['page_title'] = 'Sales Report Details'
        context['all_customers'] = BusinessPartner.objects.filter(bp_type='C')
        context['all_sales_employees'] = SalesEmployee.objects.all()
        
        # Calculate totals for current filtered results
        orders = context['sales_orders']
        total_amount = sum(order.total_amount or 0 for order in orders)
        total_payable = sum(order.payable_amount or 0 for order in orders)
        total_paid = sum(getattr(order, 'paid_amount', 0) or 0 for order in orders)
        total_due = sum(getattr(order, 'due_amount', 0) or 0 for order in orders)
        
        context.update({
            'total_amount': total_amount,
            'total_payable': total_payable,
            'total_paid': total_paid,
            'total_due': total_due,
            'total_orders': len(orders),
            'avg_order_value': total_amount / len(orders) if orders else 0,
        })
        
        # Add filter summary for display
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            
            if filters.get('start_date') and filters.get('end_date'):
                filter_summary.append(f"Period: {filters['start_date']} to {filters['end_date']}")
            elif filters.get('start_date'):
                filter_summary.append(f"From: {filters['start_date']}")
            elif filters.get('end_date'):
                filter_summary.append(f"Until: {filters['end_date']}")
            
            if filters.get('customer'):
                filter_summary.append(f"Customer: {filters['customer'].name}")
            
            if filters.get('sales_employee'):
                filter_summary.append(f"Sales Employee: {filters['sales_employee'].name}")
            
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
        
        context['filter_summary'] = filter_summary
        
        return context