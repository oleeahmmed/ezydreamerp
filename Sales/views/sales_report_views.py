from django.views.generic import ListView, TemplateView
from django.db.models import Sum, Q, Count
from decimal import Decimal
from django.utils import timezone
from Sales.models import SalesQuotation, SalesQuotationLine, SalesOrder, SalesEmployee, SalesOrderLine, Delivery, DeliveryLine, Return, ReturnLine, ARInvoice, ARInvoiceLine
from BusinessPartnerMasterData.models import BusinessPartner
from Inventory.models import Item
from config.views import GenericFilterView
from ..forms.sales_report_forms import SalesReportFilterForm
import logging

logger = logging.getLogger(__name__)

class SalesReportListView(TemplateView):
    template_name = 'sales/reports/sales_report_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Sales Reports'
        return context

class SalesQuotationReportView(GenericFilterView):
    model = SalesQuotation
    template_name = 'sales/reports/sales_quotation_report.html'
    context_object_name = 'sales_quotations'
    filter_form_class = SalesReportFilterForm
    permission_required = 'Sales.view_salesquotation'
    paginate_by = 10  # Default to 10 items

    def get_paginate_by(self, queryset):
        """Show 10 records by default, all records when filters are applied"""
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            # Check if any filter is applied
            if any(cleaned_data.get(key) for key in ['search', 'start_date', 'end_date', 'customer', 'sales_employee', 'valid_from', 'valid_until']):
                logger.debug("Filters applied, showing all records")
                return None  # Show all records
        logger.debug("No filters applied, using default pagination of 10")
        return self.paginate_by

    def get_queryset(self):
        queryset = SalesQuotation.objects.select_related('customer', 'sales_employee')
        logger.debug(f"Initial Sales Quotation queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Sales Quotation count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
                # Show default 10 records if no valid filters
                pass
        else:
            self.filter_form = None
            logger.info("No filter form class provided")
            
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('start_date'):
            try:
                queryset = queryset.filter(document_date__gte=filters['start_date'])
                applied_filters.append(f"start_date={filters['start_date']}")
            except Exception as e:
                logger.error(f"Error applying start_date filter: {e}")
                
        if filters.get('end_date'):
            try:
                queryset = queryset.filter(document_date__lte=filters['end_date'])
                applied_filters.append(f"end_date={filters['end_date']}")
            except Exception as e:
                logger.error(f"Error applying end_date filter: {e}")
                
        if filters.get('valid_from'):
            try:
                queryset = queryset.filter(valid_until__gte=filters['valid_from'])
                applied_filters.append(f"valid_from={filters['valid_from']}")
            except Exception as e:
                logger.error(f"Error applying valid_from filter: {e}")
                
        if filters.get('valid_until'):
            try:
                queryset = queryset.filter(valid_until__lte=filters['valid_until'])
                applied_filters.append(f"valid_until={filters['valid_until']}")
            except Exception as e:
                logger.error(f"Error applying valid_until filter: {e}")
                
        if filters.get('customer'):
            queryset = queryset.filter(customer=filters['customer'])
            applied_filters.append(f"customer={filters['customer'].id}")
            
        if filters.get('sales_employee'):
            queryset = queryset.filter(sales_employee=filters['sales_employee'])
            applied_filters.append(f"sales_employee={filters['sales_employee'].id}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'start_date': self.filter_form.cleaned_data.get('start_date', ''),
                'end_date': self.filter_form.cleaned_data.get('end_date', ''),
                'valid_from': self.filter_form.cleaned_data.get('valid_from', ''),
                'valid_until': self.filter_form.cleaned_data.get('valid_until', ''),
                'selected_customer': self.filter_form.cleaned_data.get('customer'),
                'selected_employee': self.filter_form.cleaned_data.get('sales_employee'),
                'search_term': self.filter_form.cleaned_data.get('search'),
            })
            
        context['page_title'] = 'Sales Quotation Report'
        context['all_customers'] = BusinessPartner.objects.filter(bp_type='C')
        context['all_sales_employees'] = SalesEmployee.objects.all()
        
        quotations = context['sales_quotations']
        total_amount = sum(quotation.total_amount or 0 for quotation in quotations)
        total_payable = sum(quotation.payable_amount or 0 for quotation in quotations)
        total_paid = sum(quotation.paid_amount or 0 for quotation in quotations)
        total_due = sum(quotation.due_amount or 0 for quotation in quotations)
        
        context.update({
            'total_amount': "{:.2f}".format(total_amount),
            'total_payable': "{:.2f}".format(total_payable),
            'total_paid': "{:.2f}".format(total_paid),
            'total_due': "{:.2f}".format(total_due),
            'total_quotations': len(quotations),
            'avg_quotation_value': "{:.2f}".format(total_amount / len(quotations)) if quotations else "0.00",
        })
        
        # Build filter summary
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('start_date') and filters.get('end_date'):
                filter_summary.append(f"Period: {filters['start_date']} to {filters['end_date']}")
            elif filters.get('start_date'):
                filter_summary.append(f"From: {filters['start_date']}")
            elif filters.get('end_date'):
                filter_summary.append(f"Until: {filters['end_date']}")
            if filters.get('valid_from') and filters.get('valid_until'):
                filter_summary.append(f"Valid Period: {filters['valid_from']} to {filters['valid_until']}")
            elif filters.get('valid_from'):
                filter_summary.append(f"Valid From: {filters['valid_from']}")
            elif filters.get('valid_until'):
                filter_summary.append(f"Valid Until: {filters['valid_until']}")
            if filters.get('customer'):
                filter_summary.append(f"Customer: {filters['customer'].name}")
            if filters.get('sales_employee'):
                filter_summary.append(f"Sales Employee: {filters['sales_employee'].name}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Sales Quotation context: {len(quotations)} quotations, Total Amount: {context['total_amount']}")
        return context

class SalesQuotationReportDetailsView(GenericFilterView):
    model = SalesQuotation
    template_name = 'sales/reports/sales_quotation_report_details.html'
    context_object_name = 'sales_quotations'
    filter_form_class = SalesReportFilterForm
    permission_required = 'Sales.view_salesquotation'
    paginate_by = 10  # Default to 10 items

    def get_paginate_by(self, queryset):
        """Show 10 records by default, all records when filters are applied"""
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'start_date', 'end_date', 'customer', 'sales_employee', 'valid_from', 'valid_until']):
                logger.debug("Filters applied, showing all records")
                return None  # Show all records
        logger.debug("No filters applied, using default pagination of 10")
        return self.paginate_by

    def get_queryset(self):
        queryset = SalesQuotation.objects.select_related('customer', 'sales_employee').prefetch_related('lines')
        logger.debug(f"Initial Sales Quotation Details queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Sales Quotation Details count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        else:
            self.filter_form = None
            logger.info("No filter form class provided")
            
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('start_date'):
            try:
                queryset = queryset.filter(document_date__gte=filters['start_date'])
                applied_filters.append(f"start_date={filters['start_date']}")
            except Exception as e:
                logger.error(f"Error applying start_date filter: {e}")
                
        if filters.get('end_date'):
            try:
                queryset = queryset.filter(document_date__lte=filters['end_date'])
                applied_filters.append(f"end_date={filters['end_date']}")
            except Exception as e:
                logger.error(f"Error applying end_date filter: {e}")
                
        if filters.get('valid_from'):
            try:
                queryset = queryset.filter(valid_until__gte=filters['valid_from'])
                applied_filters.append(f"valid_from={filters['valid_from']}")
            except Exception as e:
                logger.error(f"Error applying valid_from filter: {e}")
                
        if filters.get('valid_until'):
            try:
                queryset = queryset.filter(valid_until__lte=filters['valid_until'])
                applied_filters.append(f"valid_until={filters['valid_until']}")
            except Exception as e:
                logger.error(f"Error applying valid_until filter: {e}")
                
        if filters.get('customer'):
            queryset = queryset.filter(customer=filters['customer'])
            applied_filters.append(f"customer={filters['customer'].id}")
            
        if filters.get('sales_employee'):
            queryset = queryset.filter(sales_employee=filters['sales_employee'])
            applied_filters.append(f"sales_employee={filters['sales_employee'].id}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'start_date': self.filter_form.cleaned_data.get('start_date', ''),
                'end_date': self.filter_form.cleaned_data.get('end_date', ''),
                'valid_from': self.filter_form.cleaned_data.get('valid_from', ''),
                'valid_until': self.filter_form.cleaned_data.get('valid_until', ''),
                'selected_customer': self.filter_form.cleaned_data.get('customer'),
                'selected_employee': self.filter_form.cleaned_data.get('sales_employee'),
                'search_term': self.filter_form.cleaned_data.get('search'),
            })
            
        context['page_title'] = 'Sales Quotation Report Details'
        context['all_customers'] = BusinessPartner.objects.filter(bp_type='C')
        context['all_sales_employees'] = SalesEmployee.objects.all()
        
        quotations = context['sales_quotations']
        total_amount = sum(quotation.total_amount or 0 for quotation in quotations)
        total_payable = sum(quotation.payable_amount or 0 for quotation in quotations)
        total_paid = sum(quotation.paid_amount or 0 for quotation in quotations)
        total_due = sum(quotation.due_amount or 0 for quotation in quotations)
        
        # Format line items
        for quotation in quotations:
            for line in quotation.lines.all():
                line.quantity = "{:.2f}".format(line.quantity) if line.quantity else "0.00"
                line.unit_price = "{:.2f}".format(line.unit_price) if line.unit_price else "0.00"
                line.total_amount = "{:.2f}".format(line.total_amount) if line.total_amount else "0.00"
                line.uom = line.uom or "N/A"
                
        context.update({
            'total_amount': "{:.2f}".format(total_amount),
            'total_payable': "{:.2f}".format(total_payable),
            'total_paid': "{:.2f}".format(total_paid),
            'total_due': "{:.2f}".format(total_due),
            'total_quotations': len(quotations),
            'avg_quotation_value': "{:.2f}".format(total_amount / len(quotations)) if quotations else "0.00",
        })
        
        # Build filter summary
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('start_date') and filters.get('end_date'):
                filter_summary.append(f"Period: {filters['start_date']} to {filters['end_date']}")
            elif filters.get('start_date'):
                filter_summary.append(f"From: {filters['start_date']}")
            elif filters.get('end_date'):
                filter_summary.append(f"Until: {filters['end_date']}")
            if filters.get('valid_from') and filters.get('valid_until'):
                filter_summary.append(f"Valid Period: {filters['valid_from']} to {filters['valid_until']}")
            elif filters.get('valid_from'):
                filter_summary.append(f"Valid From: {filters['valid_from']}")
            elif filters.get('valid_until'):
                filter_summary.append(f"Valid Until: {filters['valid_until']}")
            if filters.get('customer'):
                filter_summary.append(f"Customer: {filters['customer'].name}")
            if filters.get('sales_employee'):
                filter_summary.append(f"Sales Employee: {filters['sales_employee'].name}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Sales Quotation Details context: {len(quotations)} quotations, Total Amount: {context['total_amount']}")
        return context

class SalesReportView(GenericFilterView):
    model = SalesOrder
    template_name = 'sales/reports/sales_report.html'
    context_object_name = 'sales_orders'
    filter_form_class = SalesReportFilterForm
    permission_required = 'Sales.view_salesorder'
    paginate_by = 10  # Default to 10 items

    def get_paginate_by(self, queryset):
        """Show 10 records by default, all records when filters are applied"""
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'start_date', 'end_date', 'customer', 'sales_employee']):
                logger.debug("Filters applied, showing all records")
                return None  # Show all records
        logger.debug("No filters applied, using default pagination of 10")
        return self.paginate_by

    def get_queryset(self):
        queryset = SalesOrder.objects.select_related('customer', 'sales_employee').prefetch_related('lines')
        logger.debug(f"Initial Sales Order queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Sales Order count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        else:
            self.filter_form = None
            logger.info("No filter form class provided")
            
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('start_date'):
            try:
                queryset = queryset.filter(document_date__gte=filters['start_date'])
                applied_filters.append(f"start_date={filters['start_date']}")
            except Exception as e:
                logger.error(f"Error applying start_date filter: {e}")
                
        if filters.get('end_date'):
            try:
                queryset = queryset.filter(document_date__lte=filters['end_date'])
                applied_filters.append(f"end_date={filters['end_date']}")
            except Exception as e:
                logger.error(f"Error applying end_date filter: {e}")
                
        if filters.get('customer'):
            queryset = queryset.filter(customer=filters['customer'])
            applied_filters.append(f"customer={filters['customer'].id}")
            
        if filters.get('sales_employee'):
            queryset = queryset.filter(sales_employee=filters['sales_employee'])
            applied_filters.append(f"sales_employee={filters['sales_employee'].id}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
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
        
        orders = context['sales_orders']
        total_amount = sum(order.total_amount or 0 for order in orders)
        total_payable = sum(order.payable_amount or 0 for order in orders)
        total_paid = sum(getattr(order, 'paid_amount', 0) or 0 for order in orders)
        total_due = sum(getattr(order, 'due_amount', 0) or 0 for order in orders)
        
        context.update({
            'total_amount': "{:.2f}".format(total_amount),
            'total_payable': "{:.2f}".format(total_payable),
            'total_paid': "{:.2f}".format(total_paid),
            'total_due': "{:.2f}".format(total_due),
            'total_orders': len(orders),
            'avg_order_value': "{:.2f}".format(total_amount / len(orders)) if orders else "0.00",
        })
        
        # Build filter summary
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
        logger.debug(f"Sales Report context: {len(orders)} orders, Total Amount: {context['total_amount']}")
        return context

class SalesReportDetailsView(GenericFilterView):
    model = SalesOrder
    template_name = 'sales/reports/sales_report_details.html'
    context_object_name = 'sales_orders'
    filter_form_class = SalesReportFilterForm
    permission_required = 'Sales.view_salesorder'
    paginate_by = 10  # Default to 10 items

    def get_paginate_by(self, queryset):
        """Show 10 records by default, all records when filters are applied"""
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'item_filter', 'start_date', 'end_date', 'customer', 'sales_employee']):
                logger.debug("Filters applied, showing all records")
                return None  # Show all records
        logger.debug("No filters applied, using default pagination of 10")
        return self.paginate_by

    def get_queryset(self):
        queryset = SalesOrder.objects.select_related('customer', 'sales_employee')
        logger.debug(f"Initial Sales Order Details queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Sales Order Details count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        else:
            self.filter_form = None
            logger.info("No filter form class provided")
            
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('item_filter'):
            item_filter = filters['item_filter']
            queryset = queryset.filter(lines__item_code__icontains=item_filter).distinct()
            applied_filters.append(f"item_filter={item_filter}")
            
        if filters.get('start_date'):
            try:
                queryset = queryset.filter(document_date__gte=filters['start_date'])
                applied_filters.append(f"start_date={filters['start_date']}")
            except Exception as e:
                logger.error(f"Error applying start_date filter: {e}")
                
        if filters.get('end_date'):
            try:
                queryset = queryset.filter(document_date__lte=filters['end_date'])
                applied_filters.append(f"end_date={filters['end_date']}")
            except Exception as e:
                logger.error(f"Error applying end_date filter: {e}")
                
        if filters.get('customer'):
            queryset = queryset.filter(customer=filters['customer'])
            applied_filters.append(f"customer={filters['customer'].id}")
            
        if filters.get('sales_employee'):
            queryset = queryset.filter(sales_employee=filters['sales_employee'])
            applied_filters.append(f"sales_employee={filters['sales_employee'].id}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'start_date': self.filter_form.cleaned_data.get('start_date', ''),
                'end_date': self.filter_form.cleaned_data.get('end_date', ''),
                'selected_customer': self.filter_form.cleaned_data.get('customer'),
                'selected_employee': self.filter_form.cleaned_data.get('sales_employee'),
                'search_term': self.filter_form.cleaned_data.get('search'),
                'item_filter': self.filter_form.cleaned_data.get('item_filter', ''),
            })
            
        context['page_title'] = 'Sales Report Details'
        context['all_customers'] = BusinessPartner.objects.filter(bp_type='C')
        context['all_sales_employees'] = SalesEmployee.objects.all()
        
        orders = context['sales_orders']

        # Fetch all item codes and their purchase prices from Item model
        item_codes = set(line.item_code for order in orders for line in order.lines.all())
        items = Item.objects.filter(code__in=item_codes).values('code', 'purchase_price')
        item_price_map = {item['code']: Decimal(item['purchase_price'] or 0) for item in items}

        # Enhance sales order lines with purchase price, purchase amount, and profit percentage
        for order in orders:
            for line in order.lines.all():
                line.purchase_price = item_price_map.get(line.item_code, Decimal('0.00'))
                line.purchase_amount = Decimal(line.quantity) * line.purchase_price
                line.total_amount = Decimal(line.quantity) * Decimal(line.unit_price)
                line.profit_percentage = (
                    ((Decimal(line.unit_price) - line.purchase_price) / line.purchase_price * 100)
                    if line.purchase_price > 0 else Decimal('0.00')
                )
                # Format fields for display
                line.quantity = "{:.2f}".format(line.quantity) if line.quantity else "0.00"
                line.unit_price = "{:.2f}".format(line.unit_price) if line.unit_price else "0.00"
                line.purchase_price = "{:.2f}".format(line.purchase_price)
                line.purchase_amount = "{:.2f}".format(line.purchase_amount)
                line.total_amount = "{:.2f}".format(line.total_amount)
                line.profit_percentage = "{:.2f}".format(line.profit_percentage)
                line.uom = line.uom or ""

        total_amount = sum(
            Decimal(line.quantity) * Decimal(line.unit_price)
            for order in orders for line in order.lines.all()
        )
        total_payable = sum(order.payable_amount or 0 for order in orders)
        total_paid = sum(getattr(order, 'paid_amount', 0) or 0 for order in orders)
        total_due = sum(getattr(order, 'due_amount', 0) or 0 for order in orders)

        context.update({
            'total_amount': "{:.2f}".format(total_amount),
            'total_payable': "{:.2f}".format(total_payable),
            'total_paid': "{:.2f}".format(total_paid),
            'total_due': "{:.2f}".format(total_due),
            'total_orders': len(orders),
            'avg_order_value': "{:.2f}".format(total_amount / len(orders)) if orders else "0.00",
        })

        # Build filter summary
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
            if filters.get('item_filter'):
                filter_summary.append(f"Item: '{filters['item_filter']}'")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Sales Report Details context: {len(orders)} orders, Total Amount: {context['total_amount']}")
        return context

class DeliveryReportView(GenericFilterView):
    model = Delivery
    template_name = 'sales/reports/delivery_report.html'
    context_object_name = 'deliveries'
    filter_form_class = SalesReportFilterForm
    permission_required = 'Sales.view_delivery'
    paginate_by = 10  # Default to 10 items

    def get_paginate_by(self, queryset):
        """Show 10 records by default, all records when filters are applied"""
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'start_date', 'end_date', 'customer', 'sales_employee']):
                logger.debug("Filters applied, showing all records")
                return None  # Show all records
        logger.debug("No filters applied, using default pagination of 10")
        return self.paginate_by

    def get_queryset(self):
        queryset = Delivery.objects.select_related('customer', 'sales_employee')
        logger.debug(f"Initial Delivery queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Delivery count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        else:
            self.filter_form = None
            logger.info("No filter form class provided")
            
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('start_date'):
            try:
                queryset = queryset.filter(document_date__gte=filters['start_date'])
                applied_filters.append(f"start_date={filters['start_date']}")
            except Exception as e:
                logger.error(f"Error applying start_date filter: {e}")
                
        if filters.get('end_date'):
            try:
                queryset = queryset.filter(document_date__lte=filters['end_date'])
                applied_filters.append(f"end_date={filters['end_date']}")
            except Exception as e:
                logger.error(f"Error applying end_date filter: {e}")
                
        if filters.get('customer'):
            queryset = queryset.filter(customer=filters['customer'])
            applied_filters.append(f"customer={filters['customer'].id}")
            
        if filters.get('sales_employee'):
            queryset = queryset.filter(sales_employee=filters['sales_employee'])
            applied_filters.append(f"sales_employee={filters['sales_employee'].id}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        context['search_term'] = self.request.GET.get('search', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['all_customers'] = BusinessPartner.objects.filter(bp_type='C')
        context['all_sales_employees'] = SalesEmployee.objects.all()
        context['selected_customer'] = None
        context['selected_employee'] = None

        if self.filter_form and self.filter_form.is_valid():
            context['selected_customer'] = self.filter_form.cleaned_data.get('customer', None)
            context['selected_employee'] = self.filter_form.cleaned_data.get('sales_employee', None)

        total = self.object_list.aggregate(
            total_amount=Sum('total_amount'),
            total_payable=Sum('payable_amount'),
            total_paid=Sum('paid_amount'),
            total_due=Sum('due_amount')
        )
        context['total_amount'] = "{:.2f}".format(total['total_amount'] or 0)
        context['total_payable'] = "{:.2f}".format(total['total_payable'] or 0)
        context['total_paid'] = "{:.2f}".format(total['total_paid'] or 0)
        context['total_due'] = "{:.2f}".format(total['total_due'] or 0)
        context['delivery_count'] = self.object_list.count()
        logger.debug(f"Delivery context: {context['delivery_count']} deliveries, Total Amount: {context['total_amount']}")
        return context
    
class DeliveryReportDetailsView(GenericFilterView):
    model = Delivery
    template_name = 'sales/reports/delivery_report_details.html'
    context_object_name = 'deliveries'
    filter_form_class = SalesReportFilterForm
    permission_required = 'Sales.view_delivery'
    paginate_by = 10  # Default to 10 items

    def get_paginate_by(self, queryset):
        """Show 10 records by default, all records when filters are applied"""
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'start_date', 'end_date', 'customer', 'sales_employee']):
                logger.debug("Filters applied, showing all records")
                return None  # Show all records
        logger.debug("No filters applied, using default pagination of 10")
        return self.paginate_by

    def get_queryset(self):
        queryset = Delivery.objects.select_related('customer', 'sales_employee', 'sales_order').prefetch_related('lines')
        logger.debug(f"Initial Delivery Details queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Delivery Details count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        else:
            self.filter_form = None
            logger.info("No filter form class provided")
            
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term) | Q(sales_order__id__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('start_date'):
            try:
                queryset = queryset.filter(document_date__gte=filters['start_date'])
                applied_filters.append(f"start_date={filters['start_date']}")
            except Exception as e:
                logger.error(f"Error applying start_date filter: {e}")
                
        if filters.get('end_date'):
            try:
                queryset = queryset.filter(document_date__lte=filters['end_date'])
                applied_filters.append(f"end_date={filters['end_date']}")
            except Exception as e:
                logger.error(f"Error applying end_date filter: {e}")
                
        if filters.get('customer'):
            queryset = queryset.filter(customer=filters['customer'])
            applied_filters.append(f"customer={filters['customer'].id}")
            
        if filters.get('sales_employee'):
            queryset = queryset.filter(sales_employee=filters['sales_employee'])
            applied_filters.append(f"sales_employee={filters['sales_employee'].id}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'start_date': self.filter_form.cleaned_data.get('start_date', ''),
                'end_date': self.filter_form.cleaned_data.get('end_date', ''),
                'selected_customer': self.filter_form.cleaned_data.get('customer'),
                'selected_employee': self.filter_form.cleaned_data.get('sales_employee'),
                'search_term': self.filter_form.cleaned_data.get('search'),
            })
            
        context['page_title'] = 'Delivery Report Details'
        context['all_customers'] = BusinessPartner.objects.filter(bp_type='C')
        context['all_sales_employees'] = SalesEmployee.objects.all()
        
        deliveries = context['deliveries']
        total_amount = sum(delivery.total_amount or 0 for delivery in deliveries)
        total_payable = sum(delivery.payable_amount or 0 for delivery in deliveries)
        total_paid = sum(delivery.paid_amount or 0 for delivery in deliveries)
        total_due = sum(delivery.due_amount or 0 for delivery in deliveries)
        
        # Format line items
        for delivery in deliveries:
            for line in delivery.lines.all():
                line.quantity = "{:.2f}".format(line.quantity) if line.quantity else "0.00"
                line.unit_price = "{:.2f}".format(line.unit_price) if line.unit_price else "0.00"
                line.total_amount = "{:.2f}".format(line.total_amount) if line.total_amount else "0.00"
                line.uom = line.uom or "N/A"
                
        context.update({
            'total_amount': "{:.2f}".format(total_amount),
            'total_payable': "{:.2f}".format(total_payable),
            'total_paid': "{:.2f}".format(total_paid),
            'total_due': "{:.2f}".format(total_due),
            'total_orders': len(deliveries),
            'avg_order_value': "{:.2f}".format(total_amount / len(deliveries)) if deliveries else "0.00",
        })
        
        # Build filter summary
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
        logger.debug(f"Delivery Details context: {len(deliveries)} deliveries, Total Amount: {context['total_amount']}")
        return context

class ReturnReportView(GenericFilterView):
    model = Return
    template_name = 'sales/reports/return_report.html'
    context_object_name = 'returns'
    filter_form_class = SalesReportFilterForm
    permission_required = 'Sales.view_return'
    paginate_by = 10  # Default to 10 items

    def get_paginate_by(self, queryset):
        """Show 10 records by default, all records when filters are applied"""
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'start_date', 'end_date', 'customer', 'sales_employee']):
                logger.debug("Filters applied, showing all records")
                return None  # Show all records
        logger.debug("No filters applied, using default pagination of 10")
        return self.paginate_by

    def get_queryset(self):
        queryset = Return.objects.select_related('customer', 'sales_employee')
        logger.debug(f"Initial Return queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Return count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        else:
            self.filter_form = None
            logger.info("No filter form class provided")
            
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('start_date'):
            try:
                queryset = queryset.filter(document_date__gte=filters['start_date'])
                applied_filters.append(f"start_date={filters['start_date']}")
            except Exception as e:
                logger.error(f"Error applying start_date filter: {e}")
                
        if filters.get('end_date'):
            try:
                queryset = queryset.filter(document_date__lte=filters['end_date'])
                applied_filters.append(f"end_date={filters['end_date']}")
            except Exception as e:
                logger.error(f"Error applying end_date filter: {e}")
                
        if filters.get('customer'):
            queryset = queryset.filter(customer=filters['customer'])
            applied_filters.append(f"customer={filters['customer'].id}")
            
        if filters.get('sales_employee'):
            queryset = queryset.filter(sales_employee=filters['sales_employee'])
            applied_filters.append(f"sales_employee={filters['sales_employee'].id}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'start_date': self.filter_form.cleaned_data.get('start_date', ''),
                'end_date': self.filter_form.cleaned_data.get('end_date', ''),
                'selected_customer': self.filter_form.cleaned_data.get('customer'),
                'selected_employee': self.filter_form.cleaned_data.get('sales_employee'),
                'search_term': self.filter_form.cleaned_data.get('search'),
            })
            
        context['page_title'] = 'Return Report'
        context['all_customers'] = BusinessPartner.objects.filter(bp_type='C')
        context['all_sales_employees'] = SalesEmployee.objects.all()
        
        returns = context['returns']
        total_amount = sum(return_obj.total_amount or 0 for return_obj in returns)
        total_payable = sum(return_obj.payable_amount or 0 for return_obj in returns)
        total_paid = sum(return_obj.paid_amount or 0 for return_obj in returns)
        total_due = sum(return_obj.due_amount or 0 for return_obj in returns)
        
        context.update({
            'total_amount': "{:.2f}".format(total_amount),
            'total_payable': "{:.2f}".format(total_payable),
            'total_paid': "{:.2f}".format(total_paid),
            'total_due': "{:.2f}".format(total_due),
            'total_orders': len(returns),
            'avg_order_value': "{:.2f}".format(total_amount / len(returns)) if returns else "0.00",
        })
        
        # Build filter summary
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

class ReturnReportDetailsView(GenericFilterView):
    model = Return
    template_name = 'sales/reports/return_report_details.html'
    context_object_name = 'returns'
    filter_form_class = SalesReportFilterForm
    permission_required = 'Sales.view_return'
    paginate_by = 10  # Default to 10 items

    def get_paginate_by(self, queryset):
        """Show 10 records by default, all records when filters are applied"""
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'start_date', 'end_date', 'customer', 'sales_employee']):
                logger.debug("Filters applied, showing all records")
                return None  # Show all records
        logger.debug("No filters applied, using default pagination of 10")
        return self.paginate_by

    def get_queryset(self):
        queryset = Return.objects.select_related('customer', 'sales_employee').prefetch_related('lines')
        logger.debug(f"Initial Return Details queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Return Details count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        else:
            self.filter_form = None
            logger.info("No filter form class provided")
            
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('start_date'):
            try:
                queryset = queryset.filter(document_date__gte=filters['start_date'])
                applied_filters.append(f"start_date={filters['start_date']}")
            except Exception as e:
                logger.error(f"Error applying start_date filter: {e}")
                
        if filters.get('end_date'):
            try:
                queryset = queryset.filter(document_date__lte=filters['end_date'])
                applied_filters.append(f"end_date={filters['end_date']}")
            except Exception as e:
                logger.error(f"Error applying end_date filter: {e}")
                
        if filters.get('customer'):
            queryset = queryset.filter(customer=filters['customer'])
            applied_filters.append(f"customer={filters['customer'].id}")
            
        if filters.get('sales_employee'):
            queryset = queryset.filter(sales_employee=filters['sales_employee'])
            applied_filters.append(f"sales_employee={filters['sales_employee'].id}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'start_date': self.filter_form.cleaned_data.get('start_date', ''),
                'end_date': self.filter_form.cleaned_data.get('end_date', ''),
                'selected_customer': self.filter_form.cleaned_data.get('customer'),
                'selected_employee': self.filter_form.cleaned_data.get('sales_employee'),
                'search_term': self.filter_form.cleaned_data.get('search'),
            })
            
        context['page_title'] = 'Return Report Details'
        context['all_customers'] = BusinessPartner.objects.filter(bp_type='C')
        context['all_sales_employees'] = SalesEmployee.objects.all()
        
        returns = context['returns']
        total_amount = sum(return_obj.total_amount or 0 for return_obj in returns)
        total_payable = sum(return_obj.payable_amount or 0 for return_obj in returns)
        total_paid = sum(return_obj.paid_amount or 0 for return_obj in returns)
        total_due = sum(return_obj.due_amount or 0 for return_obj in returns)
        
        # Format line items
        for return_obj in returns:
            for line in return_obj.lines.all():
                line.quantity = "{:.2f}".format(line.quantity) if line.quantity else "0.00"
                line.unit_price = "{:.2f}".format(line.unit_price) if line.unit_price else "0.00"
                line.total_amount = "{:.2f}".format(line.total_amount) if line.total_amount else "0.00"
                line.uom = line.uom or ""
                
        context.update({
            'total_amount': "{:.2f}".format(total_amount),
            'total_payable': "{:.2f}".format(total_payable),
            'total_paid': "{:.2f}".format(total_paid),
            'total_due': "{:.2f}".format(total_due),
            'total_orders': len(returns),
            'avg_order_value': "{:.2f}".format(total_amount / len(returns)) if returns else "0.00",
        })
        
        # Build filter summary
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

class ARInvoiceReportView(GenericFilterView):
    model = ARInvoice
    template_name = 'sales/reports/ar_invoice_report.html'
    context_object_name = 'ar_invoices'
    filter_form_class = SalesReportFilterForm
    permission_required = 'Sales.view_arinvoice'
    paginate_by = 10  # Default to 10 items

    def get_paginate_by(self, queryset):
        """Show 10 records by default, all records when filters are applied"""
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'start_date', 'end_date', 'due_start_date', 'due_end_date', 'customer', 'sales_employee']):
                logger.debug("Filters applied, showing all records")
                return None  # Show all records
        logger.debug("No filters applied, using default pagination of 10")
        return self.paginate_by

    def get_queryset(self):
        queryset = ARInvoice.objects.select_related('customer', 'sales_employee', 'sales_order')
        logger.debug(f"Initial AR Invoice queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered AR Invoice count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        else:
            self.filter_form = None
            logger.info("No filter form class provided")
            
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term) | Q(sales_order__id__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('start_date'):
            try:
                queryset = queryset.filter(document_date__gte=filters['start_date'])
                applied_filters.append(f"start_date={filters['start_date']}")
            except Exception as e:
                logger.error(f"Error applying start_date filter: {e}")
                
        if filters.get('end_date'):
            try:
                queryset = queryset.filter(document_date__lte=filters['end_date'])
                applied_filters.append(f"end_date={filters['end_date']}")
            except Exception as e:
                logger.error(f"Error applying end_date filter: {e}")
                
        if filters.get('due_start_date'):
            try:
                queryset = queryset.filter(due_date__gte=filters['due_start_date'])
                applied_filters.append(f"due_start_date={filters['due_start_date']}")
            except Exception as e:
                logger.error(f"Error applying due_start_date filter: {e}")
                
        if filters.get('due_end_date'):
            try:
                queryset = queryset.filter(due_date__lte=filters['due_end_date'])
                applied_filters.append(f"due_end_date={filters['due_end_date']}")
            except Exception as e:
                logger.error(f"Error applying due_end_date filter: {e}")
                
        if filters.get('customer'):
            queryset = queryset.filter(customer=filters['customer'])
            applied_filters.append(f"customer={filters['customer'].id}")
            
        if filters.get('sales_employee'):
            queryset = queryset.filter(sales_employee=filters['sales_employee'])
            applied_filters.append(f"sales_employee={filters['sales_employee'].id}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'start_date': self.filter_form.cleaned_data.get('start_date', ''),
                'end_date': self.filter_form.cleaned_data.get('end_date', ''),
                'due_start_date': self.filter_form.cleaned_data.get('due_start_date', ''),
                'due_end_date': self.filter_form.cleaned_data.get('due_end_date', ''),
                'selected_customer': self.filter_form.cleaned_data.get('customer'),
                'selected_employee': self.filter_form.cleaned_data.get('sales_employee'),
                'search_term': self.filter_form.cleaned_data.get('search'),
            })
            
        context['page_title'] = 'AR Invoice Report'
        context['all_customers'] = BusinessPartner.objects.filter(bp_type='C')
        context['all_sales_employees'] = SalesEmployee.objects.all()
        
        invoices = context['ar_invoices']
        total_amount = sum(invoice.total_amount or 0 for invoice in invoices)
        total_payable = sum(invoice.payable_amount or 0 for invoice in invoices)
        total_paid = sum(invoice.paid_amount or 0 for invoice in invoices)
        total_due = sum(invoice.due_amount or 0 for invoice in invoices)
        
        context.update({
            'total_amount': "{:.2f}".format(total_amount),
            'total_payable': "{:.2f}".format(total_payable),
            'total_paid': "{:.2f}".format(total_paid),
            'total_due': "{:.2f}".format(total_due),
            'total_invoices': len(invoices),
            'avg_invoice_value': "{:.2f}".format(total_amount / len(invoices)) if invoices else "0.00",
        })
        
        # Build filter summary
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('start_date') and filters.get('end_date'):
                filter_summary.append(f"Period: {filters['start_date']} to {filters['end_date']}")
            elif filters.get('start_date'):
                filter_summary.append(f"From: {filters['start_date']}")
            elif filters.get('end_date'):
                filter_summary.append(f"Until: {filters['end_date']}")
            if filters.get('due_start_date') and filters.get('due_end_date'):
                filter_summary.append(f"Due Period: {filters['due_start_date']} to {filters['due_end_date']}")
            elif filters.get('due_start_date'):
                filter_summary.append(f"Due From: {filters['due_start_date']}")
            elif filters.get('due_end_date'):
                filter_summary.append(f"Due Until: {filters['due_end_date']}")
            if filters.get('customer'):
                filter_summary.append(f"Customer: {filters['customer'].name}")
            if filters.get('sales_employee'):
                filter_summary.append(f"Sales Employee: {filters['sales_employee'].name}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"AR Invoice context: {len(invoices)} invoices, Total Amount: {context['total_amount']}")
        return context

class ARInvoiceReportDetailsView(GenericFilterView):
    model = ARInvoice
    template_name = 'sales/reports/ar_invoice_report_details.html'
    context_object_name = 'ar_invoices'
    filter_form_class = SalesReportFilterForm
    permission_required = 'Sales.view_arinvoice'
    paginate_by = 10  # Default to 10 items

    def get_paginate_by(self, queryset):
        """Show 10 records by default, all records when filters are applied"""
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'start_date', 'end_date', 'due_start_date', 'due_end_date', 'customer', 'sales_employee']):
                logger.debug("Filters applied, showing all records")
                return None  # Show all records
        logger.debug("No filters applied, using default pagination of 10")
        return self.paginate_by

    def get_queryset(self):
        queryset = ARInvoice.objects.select_related('customer', 'sales_employee', 'sales_order').prefetch_related('lines')
        logger.debug(f"Initial AR Invoice Details queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered AR Invoice Details count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        else:
            self.filter_form = None
            logger.info("No filter form class provided")
            
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term) | Q(sales_order__id__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('start_date'):
            try:
                queryset = queryset.filter(document_date__gte=filters['start_date'])
                applied_filters.append(f"start_date={filters['start_date']}")
            except Exception as e:
                logger.error(f"Error applying start_date filter: {e}")
                
        if filters.get('end_date'):
            try:
                queryset = queryset.filter(document_date__lte=filters['end_date'])
                applied_filters.append(f"end_date={filters['end_date']}")
            except Exception as e:
                logger.error(f"Error applying end_date filter: {e}")
                
        if filters.get('due_start_date'):
            try:
                queryset = queryset.filter(due_date__gte=filters['due_start_date'])
                applied_filters.append(f"due_start_date={filters['due_start_date']}")
            except Exception as e:
                logger.error(f"Error applying due_start_date filter: {e}")
                
        if filters.get('due_end_date'):
            try:
                queryset = queryset.filter(due_date__lte=filters['due_end_date'])
                applied_filters.append(f"due_end_date={filters['due_end_date']}")
            except Exception as e:
                logger.error(f"Error applying due_end_date filter: {e}")
                
        if filters.get('customer'):
            queryset = queryset.filter(customer=filters['customer'])
            applied_filters.append(f"customer={filters['customer'].id}")
            
        if filters.get('sales_employee'):
            queryset = queryset.filter(sales_employee=filters['sales_employee'])
            applied_filters.append(f"sales_employee={filters['sales_employee'].id}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'start_date': self.filter_form.cleaned_data.get('start_date', ''),
                'end_date': self.filter_form.cleaned_data.get('end_date', ''),
                'due_start_date': self.filter_form.cleaned_data.get('due_start_date', ''),
                'due_end_date': self.filter_form.cleaned_data.get('due_end_date', ''),
                'selected_customer': self.filter_form.cleaned_data.get('customer'),
                'selected_employee': self.filter_form.cleaned_data.get('sales_employee'),
                'search_term': self.filter_form.cleaned_data.get('search'),
            })
            
        context['page_title'] = 'AR Invoice Report Details'
        context['all_customers'] = BusinessPartner.objects.filter(bp_type='C')
        context['all_sales_employees'] = SalesEmployee.objects.all()
        
        invoices = context['ar_invoices']
        total_amount = sum(invoice.total_amount or 0 for invoice in invoices)
        total_payable = sum(invoice.payable_amount or 0 for invoice in invoices)
        total_paid = sum(invoice.paid_amount or 0 for invoice in invoices)
        total_due = sum(invoice.due_amount or 0 for invoice in invoices)
        
        # Format line items
        for invoice in invoices:
            for line in invoice.lines.all():
                line.quantity = "{:.2f}".format(line.quantity) if line.quantity else "0.00"
                line.unit_price = "{:.2f}".format(line.unit_price) if line.unit_price else "0.00"
                line.total_amount = "{:.2f}".format(line.total_amount) if line.total_amount else "0.00"
                line.uom = line.uom or "N/A"
                
        context.update({
            'total_amount': "{:.2f}".format(total_amount),
            'total_payable': "{:.2f}".format(total_payable),
            'total_paid': "{:.2f}".format(total_paid),
            'total_due': "{:.2f}".format(total_due),
            'total_invoices': len(invoices),
            'avg_invoice_value': "{:.2f}".format(total_amount / len(invoices)) if invoices else "0.00",
        })
        
        # Build filter summary
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('start_date') and filters.get('end_date'):
                filter_summary.append(f"Period: {filters['start_date']} to {filters['end_date']}")
            elif filters.get('start_date'):
                filter_summary.append(f"From: {filters['start_date']}")
            elif filters.get('end_date'):
                filter_summary.append(f"Until: {filters['end_date']}")
            if filters.get('due_start_date') and filters.get('due_end_date'):
                filter_summary.append(f"Due Period: {filters['due_start_date']} to {filters['due_end_date']}")
            elif filters.get('due_start_date'):
                filter_summary.append(f"Due From: {filters['due_start_date']}")
            elif filters.get('due_end_date'):
                filter_summary.append(f"Due Until: {filters['due_end_date']}")
            if filters.get('customer'):
                filter_summary.append(f"Customer: {filters['customer'].name}")
            if filters.get('sales_employee'):
                filter_summary.append(f"Sales Employee: {filters['sales_employee'].name}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"AR Invoice Details context: {len(invoices)} invoices, Total Amount: {context['total_amount']}")
        return context

# Additional view for Sales Employee Summary (if needed)
class SalesEmployeeSummaryView(GenericFilterView):
    model = SalesEmployee
    template_name = 'sales/reports/sales_employee_summary.html'
    context_object_name = 'sales_employees'
    filter_form_class = SalesReportFilterForm
    permission_required = 'Sales.view_salesemployee'
    paginate_by = 10  # Default to 10 items

    def get_paginate_by(self, queryset):
        """Show 10 records by default, all records when filters are applied"""
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'start_date', 'end_date']):
                logger.debug("Filters applied, showing all records")
                return None  # Show all records
        logger.debug("No filters applied, using default pagination of 10")
        return self.paginate_by

    def get_queryset(self):
        queryset = SalesEmployee.objects.all()
        logger.debug(f"Initial Sales Employee queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Sales Employee count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        else:
            self.filter_form = None
            logger.info("No filter form class provided")
            
        return queryset.order_by('name')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(name__icontains=search_term) | Q(employee_code__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'start_date': self.filter_form.cleaned_data.get('start_date', ''),
                'end_date': self.filter_form.cleaned_data.get('end_date', ''),
                'search_term': self.filter_form.cleaned_data.get('search'),
            })
            
        context['page_title'] = 'Sales Employee Summary'
        
        # Build filter summary
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('start_date') and filters.get('end_date'):
                filter_summary.append(f"Period: {filters['start_date']} to {filters['end_date']}")
            elif filters.get('start_date'):
                filter_summary.append(f"From: {filters['start_date']}")
            elif filters.get('end_date'):
                filter_summary.append(f"Until: {filters['end_date']}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
                
        context['filter_summary'] = filter_summary
        return context


class MenuPageView(TemplateView):
    template_name = 'sales/menu_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Reports Menu'
        logger.debug("Rendering menu page with context")
        return context        