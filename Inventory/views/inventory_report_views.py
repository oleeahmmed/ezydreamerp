from django.views.generic import TemplateView
from django.db.models import Sum, Q, Count, F, Value, DecimalField, Case, When
from decimal import Decimal
from django.utils import timezone
from Inventory.models import ItemWarehouseInfo, GoodsReceipt, GoodsReceiptLine, GoodsIssue, GoodsIssueLine, InventoryTransfer, InventoryTransferLine, InventoryTransaction, Item, Warehouse
from config.views import GenericFilterView
from django import forms
from config.forms import BaseFilterForm
import logging

logger = logging.getLogger(__name__)

# Filter Form
class InventoryReportFilterForm(BaseFilterForm):
    item = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Item Code or Name', 'class': 'form-control'}),
        label="Item"
    )
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Warehouse"
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status'), ('Draft', 'Draft'), ('Posted', 'Posted'), ('Cancelled', 'Cancelled')],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_from'].label = "Start Date"
        self.fields['date_to'].label = "End Date"

# Report List View
class InventoryReportListView(TemplateView):
    template_name = 'inventory/reports/inventory_report_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Inventory Reports'
        logger.debug("Rendering inventory reports list page")
        return context

# Stock Reports
class CurrentStockReportView(GenericFilterView):
    model = ItemWarehouseInfo
    template_name = 'inventory/reports/current_stock_report.html'
    context_object_name = 'stock_records'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_itemwarehouseinfo'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'item', 'warehouse']):
                logger.debug("Filters applied, showing all records")
                return None
        logger.debug("No filters applied, using default pagination of 10")
        return self.paginate_by

    def get_queryset(self):
        queryset = ItemWarehouseInfo.objects.select_related('item', 'warehouse').filter(item__is_active=True, warehouse__is_active=True)
        logger.debug(f"Initial Current Stock queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Current Stock count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('item__code', 'warehouse__code')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(item__code__icontains=search_term) | Q(item__name__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('item'):
            item_term = filters['item'].strip()
            queryset = queryset.filter(Q(item__code__icontains=item_term) | Q(item__name__icontains=item_term))
            applied_filters.append(f"item={item_term}")
            
        if filters.get('warehouse'):
            queryset = queryset.filter(warehouse=filters['warehouse'])
            applied_filters.append(f"warehouse={filters['warehouse'].code}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'item_term': self.filter_form.cleaned_data.get('item', ''),
                'selected_warehouse': self.filter_form.cleaned_data.get('warehouse'),
            })
            
        context['page_title'] = 'Current Stock Report'
        context['all_warehouses'] = Warehouse.objects.filter(is_active=True)
        
        records = context['stock_records']
        totals = records.aggregate(
            total_in_stock=Sum('in_stock'),
            total_committed=Sum('committed'),
            total_ordered=Sum('ordered'),
            total_available=Sum('available')
        )
        
        context.update({
            'total_in_stock': "{:.2f}".format(totals['total_in_stock'] or 0),
            'total_committed': "{:.2f}".format(totals['total_committed'] or 0),
            'total_ordered': "{:.2f}".format(totals['total_ordered'] or 0),
            'total_available': "{:.2f}".format(totals['total_available'] or 0),
            'total_records': len(records),
        })
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('item'):
                filter_summary.append(f"Item: '{filters['item']}'")
            if filters.get('warehouse'):
                filter_summary.append(f"Warehouse: {filters['warehouse'].name}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Current Stock context: {len(records)} records, Total Available: {context['total_available']}")
        return context

class StockByWarehouseReportView(GenericFilterView):
    model = ItemWarehouseInfo
    template_name = 'inventory/reports/stock_by_warehouse_report.html'
    context_object_name = 'warehouse_stocks'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_itemwarehouseinfo'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'warehouse']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = ItemWarehouseInfo.objects.select_related('warehouse').filter(warehouse__is_active=True).values(
            'warehouse__code', 
            'warehouse__name',
            'warehouse__id',  # Added to fix KeyError
        ).annotate(
            total_in_stock=Sum('in_stock'),
            total_available=Sum('available')
        ).order_by('warehouse__code')
        logger.debug(f"Initial Stock by Warehouse queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Stock by Warehouse count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(warehouse__code__icontains=search_term) | Q(warehouse__name__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('warehouse'):
            queryset = queryset.filter(warehouse__id=filters['warehouse'].id)
            applied_filters.append(f"warehouse={filters['warehouse'].code}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'selected_warehouse': self.filter_form.cleaned_data.get('warehouse'),
            })
            
        context['page_title'] = 'Stock by Warehouse Report'
        context['all_warehouses'] = Warehouse.objects.filter(is_active=True)
        
        records = context['warehouse_stocks']
        totals = ItemWarehouseInfo.objects.filter(
            warehouse__is_active=True,
            warehouse__in=[r['warehouse__id'] for r in records] if records else Warehouse.objects.filter(is_active=True)
        ).aggregate(
            total_in_stock=Sum('in_stock'),
            total_available=Sum('available')
        )
        
        context.update({
            'total_in_stock': "{:.2f}".format(totals['total_in_stock'] or 0),
            'total_available': "{:.2f}".format(totals['total_available'] or 0),
            'total_warehouses': len(records),
        })
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('warehouse'):
                filter_summary.append(f"Warehouse: {filters['warehouse'].name}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Stock by Warehouse context: {len(records)} warehouses, Total Available: {context['total_available']}")
        return context
class ReorderReportView(GenericFilterView):
    model = ItemWarehouseInfo
    template_name = 'inventory/reports/reorder_report.html'
    context_object_name = 'reorder_items'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_itemwarehouseinfo'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'item', 'warehouse']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = ItemWarehouseInfo.objects.select_related('item', 'warehouse').filter(
            item__is_active=True,
            warehouse__is_active=True,
            reorder_point__gt=0,  # Ensure reorder_point is set
            available__lt=F('reorder_point')
        ).annotate(
            shortage=F('reorder_point') - F('available'),
            suggested_qty=Case(
                When(max_stock__isnull=False, then=F('max_stock') - F('available')),
                default=F('reorder_point') * Value(2, output_field=DecimalField()),
                output_field=DecimalField()
            )
        )
        logger.debug(f"Initial Reorder queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Reorder count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('item__code', 'warehouse__code')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(item__code__icontains=search_term) | Q(item__name__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('item'):
            item_term = filters['item'].strip()
            queryset = queryset.filter(Q(item__code__icontains=item_term) | Q(item__name__icontains=item_term))
            applied_filters.append(f"item={item_term}")
            
        if filters.get('warehouse'):
            queryset = queryset.filter(warehouse=filters['warehouse'])
            applied_filters.append(f"warehouse={filters['warehouse'].code}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'item_term': self.filter_form.cleaned_data.get('item', ''),
                'selected_warehouse': self.filter_form.cleaned_data.get('warehouse'),
            })
            
        context['page_title'] = 'Reorder Report'
        context['all_warehouses'] = Warehouse.objects.filter(is_active=True)
        
        records = context['reorder_items']
        totals = records.aggregate(
            total_shortage=Sum('shortage'),
            total_suggested_qty=Sum('suggested_qty')
        )
        
        context.update({
            'total_items': len(records),
            'total_shortage': "{:.2f}".format(totals['total_shortage'] or 0),
            'total_suggested_qty': "{:.2f}".format(totals['total_suggested_qty'] or 0),
        })
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('item'):
                filter_summary.append(f"Item: '{filters['item']}'")
            if filters.get('warehouse'):
                filter_summary.append(f"Warehouse: {filters['warehouse'].name}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Reorder context: {len(records)} items, Total Shortage: {context['total_shortage']}")
        return context
class OverstockReportView(GenericFilterView):
    model = ItemWarehouseInfo
    template_name = 'inventory/reports/overstock_report.html'
    context_object_name = 'overstock_items'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_itemwarehouseinfo'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'item', 'warehouse']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = ItemWarehouseInfo.objects.select_related('item', 'warehouse').filter(
            item__is_active=True,
            warehouse__is_active=True,
            max_stock__gt=0,  # Ensure max_stock is set to avoid invalid comparisons
            available__gt=F('max_stock')
        ).annotate(
            excess_qty=F('available') - F('max_stock'),  # Excess quantity = available - max_stock
            excess_value=(F('available') - F('max_stock')) * F('item__item_cost')  # Excess value = excess_qty * item_cost
        )
        logger.debug(f"Initial Overstock queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Overstock count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('item__code', 'warehouse__code')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(item__code__icontains=search_term) | Q(item__name__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('item'):
            item_term = filters['item'].strip()
            queryset = queryset.filter(Q(item__code__icontains=item_term) | Q(item__name__icontains=item_term))
            applied_filters.append(f"item={item_term}")
            
        if filters.get('warehouse'):
            queryset = queryset.filter(warehouse=filters['warehouse'])
            applied_filters.append(f"warehouse={filters['warehouse'].code}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'item_term': self.filter_form.cleaned_data.get('item', ''),
                'selected_warehouse': self.filter_form.cleaned_data.get('warehouse'),
            })
            
        context['page_title'] = 'Overstock Report'
        context['all_warehouses'] = Warehouse.objects.filter(is_active=True)
        
        records = context['overstock_items']
        context['total_items'] = len(records)
        
        totals = records.aggregate(
            total_excess_qty=Sum('excess_qty'),
            total_excess_value=Sum('excess_value')
        )
        context['total_excess_qty'] = totals['total_excess_qty'] or 0
        context['total_excess_value'] = totals['total_excess_value'] or 0
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('item'):
                filter_summary.append(f"Item: '{filters['item']}'")
            if filters.get('warehouse'):
                filter_summary.append(f"Warehouse: {filters['warehouse'].name}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Overstock context: {len(records)} items")
        return context
# Inbound Reports
class GoodsReceiptSummaryView(GenericFilterView):
    model = GoodsReceipt
    template_name = 'inventory/reports/goods_receipt_summary.html'
    context_object_name = 'goods_receipts'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_goodsreceipt'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'date_from', 'date_to']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = GoodsReceipt.objects.filter(
            is_active=True
        ).annotate(
            calculated_due_amount=F('payable_amount') - F('paid_amount')
        )
        logger.debug(f"Initial Goods Receipt queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Goods Receipt count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(
                Q(id__icontains=search_term) | 
                Q(supplier__icontains=search_term)
            )
            applied_filters.append(f"search={search_term}")
            
        if filters.get('date_from'):
            queryset = queryset.filter(document_date__gte=filters['date_from'])
            applied_filters.append(f"date_from={filters['date_from']}")
            
        if filters.get('date_to'):
            queryset = queryset.filter(document_date__lte=filters['date_to'])
            applied_filters.append(f"date_to={filters['date_to']}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'date_from': self.filter_form.cleaned_data.get('date_from'),
                'date_to': self.filter_form.cleaned_data.get('date_to'),
            })
            
        context['page_title'] = 'Goods Receipt Summary'
        
        records = context['goods_receipts']
        context['total_items'] = len(records)
        
        totals = records.aggregate(
            total_amount=Sum('total_amount'),
            total_payable=Sum('payable_amount'),
            total_paid=Sum('paid_amount'),
            total_due=Sum('calculated_due_amount')
        )
        context['total_amount'] = totals['total_amount'] or 0
        context['total_payable'] = totals['total_payable'] or 0
        context['total_paid'] = totals['total_paid'] or 0
        context['total_due'] = totals['total_due'] or 0
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('date_from') or filters.get('date_to'):
                date_range = []
                if filters.get('date_from'):
                    date_range.append(f"From: {filters['date_from']}")
                if filters.get('date_to'):
                    date_range.append(f"To: {filters['date_to']}")
                filter_summary.append(f"Date Range: {', '.join(date_range)}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Goods Receipt context: {len(records)} items, Total Amount: {context['total_amount']}")
        return context
class PendingGoodsReceiptView(GenericFilterView):
    model = GoodsReceipt
    template_name = 'inventory/reports/pending_goods_receipt.html'
    context_object_name = 'pending_receipts'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_goodsreceipt'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'date_from', 'date_to']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        # Placeholder: Assuming 'Draft' status indicates pending receipts
        queryset = GoodsReceipt.objects.select_related().filter(is_active=True, status='Draft')
        logger.debug(f"Initial Pending Goods Receipt queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Pending Goods Receipt count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term) | Q(supplier__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('date_from'):
            queryset = queryset.filter(document_date__gte=filters['date_from'])
            applied_filters.append(f"date_from={filters['date_from']}")
            
        if filters.get('date_to'):
            queryset = queryset.filter(document_date__lte=filters['date_to'])
            applied_filters.append(f"date_to={filters['date_to']}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'start_date': self.filter_form.cleaned_data.get('date_from', ''),
                'end_date': self.filter_form.cleaned_data.get('date_to', ''),
            })
            
        context['page_title'] = 'Pending Goods Receipt Report'
        
        receipts = context['pending_receipts']
        context['total_receipts'] = len(receipts)
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('date_from') and filters.get('date_to'):
                filter_summary.append(f"Period: {filters['date_from']} to {filters['date_to']}")
            elif filters.get('date_from'):
                filter_summary.append(f"From: {filters['date_from']}")
            elif filters.get('date_to'):
                filter_summary.append(f"Until: {filters['date_to']}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Pending Goods Receipt context: {len(receipts)} receipts")
        return context

# Outbound Reports
class GoodsIssueSummaryView(GenericFilterView):
    model = GoodsIssue
    template_name = 'inventory/reports/goods_issue_summary.html'
    context_object_name = 'goods_issues'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_goodsissue'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'date_from', 'date_to', 'status']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = GoodsIssue.objects.select_related().filter(is_active=True)
        logger.debug(f"Initial Goods Issue queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Goods Issue count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term) | Q(recipient__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('date_from'):
            queryset = queryset.filter(document_date__gte=filters['date_from'])
            applied_filters.append(f"date_from={filters['date_from']}")
            
        if filters.get('date_to'):
            queryset = queryset.filter(document_date__lte=filters['date_to'])
            applied_filters.append(f"date_to={filters['date_to']}")
            
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
            applied_filters.append(f"status={filters['status']}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'start_date': self.filter_form.cleaned_data.get('date_from', ''),
                'end_date': self.filter_form.cleaned_data.get('date_to', ''),
                'selected_status': self.filter_form.cleaned_data.get('status', ''),
            })
            
        context['page_title'] = 'Goods Issue Summary'
        
        issues = context['goods_issues']
        totals = issues.aggregate(
            total_amount=Sum('total_amount'),
            total_payable=Sum('payable_amount'),
            total_paid=Sum('paid_amount'),
            total_due=Sum('due_amount')
        )
        
        context.update({
            'total_amount': "{:.2f}".format(totals['total_amount'] or 0),
            'total_payable': "{:.2f}".format(totals['total_payable'] or 0),
            'total_paid': "{:.2f}".format(totals['total_paid'] or 0),
            'total_due': "{:.2f}".format(totals['total_due'] or 0),
            'total_issues': len(issues),
            'avg_issue_value': "{:.2f}".format(totals['total_amount'] / len(issues)) if issues else "0.00",
        })
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('date_from') and filters.get('date_to'):
                filter_summary.append(f"Period: {filters['date_from']} to {filters['date_to']}")
            elif filters.get('date_from'):
                filter_summary.append(f"From: {filters['date_from']}")
            elif filters.get('date_to'):
                filter_summary.append(f"Until: {filters['date_to']}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('status'):
                filter_summary.append(f"Status: {filters['status']}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Goods Issue context: {len(issues)} issues, Total Amount: {context['total_amount']}")
        return context

class InventoryConsumptionReportView(GenericFilterView):
    model = GoodsIssueLine
    template_name = 'inventory/reports/inventory_consumption_report.html'
    context_object_name = 'consumption_records'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_goodsissue'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'item', 'date_from', 'date_to']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = GoodsIssueLine.objects.select_related('goods_issue').filter(
            goods_issue__is_active=True, goods_issue__status='Posted'
        ).values('item_code', 'item_name').annotate(
            total_quantity=Sum('quantity')
        ).order_by('item_code')
        logger.debug(f"Initial Inventory Consumption queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Inventory Consumption count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(item_code__icontains=search_term) | Q(item_name__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('item'):
            item_term = filters['item'].strip()
            queryset = queryset.filter(Q(item_code__icontains=item_term) | Q(item_name__icontains=item_term))
            applied_filters.append(f"item={item_term}")
            
        if filters.get('date_from'):
            queryset = queryset.filter(goods_issue__document_date__gte=filters['date_from'])
            applied_filters.append(f"date_from={filters['date_from']}")
            
        if filters.get('date_to'):
            queryset = queryset.filter(goods_issue__document_date__lte=filters['date_to'])
            applied_filters.append(f"date_to={filters['date_to']}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'item_term': self.filter_form.cleaned_data.get('item', ''),
                'start_date': self.filter_form.cleaned_data.get('date_from', ''),
                'end_date': self.filter_form.cleaned_data.get('date_to', ''),
            })
            
        context['page_title'] = 'Inventory Consumption Report'
        
        records = context['consumption_records']
        total_quantity = sum(r['total_quantity'] for r in records)
        
        context.update({
            'total_quantity': "{:.2f}".format(total_quantity or 0),
            'total_items': len(records),
        })
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('date_from') and filters.get('date_to'):
                filter_summary.append(f"Period: {filters['date_from']} to {filters['date_to']}")
            elif filters.get('date_from'):
                filter_summary.append(f"From: {filters['date_from']}")
            elif filters.get('date_to'):
                filter_summary.append(f"Until: {filters['date_to']}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('item'):
                filter_summary.append(f"Item: '{filters['item']}'")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Inventory Consumption context: {len(records)} items, Total Quantity: {context['total_quantity']}")
        return context

# Inventory Movement Reports
class InventoryTransactionsLedgerView(GenericFilterView):
    model = InventoryTransaction
    template_name = 'inventory/reports/inventory_transactions_ledger.html'
    context_object_name = 'transactions'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_inventorytransaction'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'item', 'warehouse', 'date_from', 'date_to']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = InventoryTransaction.objects.select_related('warehouse').filter(is_active=True)
        logger.debug(f"Initial Inventory Transactions queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Inventory Transactions count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('-transaction_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(item_code__icontains=search_term) | Q(item_name__icontains=search_term) | Q(reference__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('item'):
            item_term = filters['item'].strip()
            queryset = queryset.filter(Q(item_code__icontains=item_term) | Q(item_name__icontains=item_term))
            applied_filters.append(f"item={item_term}")
            
        if filters.get('warehouse'):
            queryset = queryset.filter(warehouse=filters['warehouse'])
            applied_filters.append(f"warehouse={filters['warehouse'].code}")
            
        if filters.get('date_from'):
            queryset = queryset.filter(transaction_date__gte=filters['date_from'])
            applied_filters.append(f"date_from={filters['date_from']}")
            
        if filters.get('date_to'):
            queryset = queryset.filter(transaction_date__lte=filters['date_to'])
            applied_filters.append(f"date_to={filters['date_to']}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'item_term': self.filter_form.cleaned_data.get('item', ''),
                'selected_warehouse': self.filter_form.cleaned_data.get('warehouse'),
                'start_date': self.filter_form.cleaned_data.get('date_from', ''),
                'end_date': self.filter_form.cleaned_data.get('date_to', ''),
            })
            
        context['page_title'] = 'Inventory Transactions Ledger'
        context['all_warehouses'] = Warehouse.objects.filter(is_active=True)
        
        transactions = context['transactions']
        totals = transactions.aggregate(
            total_quantity=Sum('quantity'),
            total_amount=Sum('total_amount')
        )
        
        context.update({
            'total_quantity': "{:.2f}".format(totals['total_quantity'] or 0),
            'total_amount': "{:.2f}".format(totals['total_amount'] or 0),
            'total_transactions': len(transactions),
        })
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('date_from') and filters.get('date_to'):
                filter_summary.append(f"Period: {filters['date_from']} to {filters['date_to']}")
            elif filters.get('date_from'):
                filter_summary.append(f"From: {filters['date_from']}")
            elif filters.get('date_to'):
                filter_summary.append(f"Until: {filters['date_to']}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('item'):
                filter_summary.append(f"Item: '{filters['item']}'")
            if filters.get('warehouse'):
                filter_summary.append(f"Warehouse: {filters['warehouse'].name}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Inventory Transactions context: {len(transactions)} transactions, Total Amount: {context['total_amount']}")
        return context

class InventoryValuationReportView(GenericFilterView):
    model = ItemWarehouseInfo
    template_name = 'inventory/reports/inventory_valuation_report.html'
    context_object_name = 'valuation_records'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_itemwarehouseinfo'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'item', 'warehouse']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = ItemWarehouseInfo.objects.select_related('item', 'warehouse').filter(
            item__is_active=True, warehouse__is_active=True
        ).annotate(
            total_value=F('available') * F('item__item_cost')
        )
        logger.debug(f"Initial Inventory Valuation queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Inventory Valuation count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('item__code', 'warehouse__code')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(item__code__icontains=search_term) | Q(item__name__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('item'):
            item_term = filters['item'].strip()
            queryset = queryset.filter(Q(item__code__icontains=item_term) | Q(item__name__icontains=item_term))
            applied_filters.append(f"item={item_term}")
            
        if filters.get('warehouse'):
            queryset = queryset.filter(warehouse=filters['warehouse'])
            applied_filters.append(f"warehouse={filters['warehouse'].code}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'item_term': self.filter_form.cleaned_data.get('item', ''),
                'selected_warehouse': self.filter_form.cleaned_data.get('warehouse'),
            })
            
        context['page_title'] = 'Inventory Valuation Report'
        context['all_warehouses'] = Warehouse.objects.filter(is_active=True)
        
        records = context['valuation_records']
        total_value = sum(r.total_value or 0 for r in records)
        
        context.update({
            'total_value': "{:.2f}".format(total_value),
            'total_items': len(records),
        })
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('item'):
                filter_summary.append(f"Item: '{filters['item']}'")
            if filters.get('warehouse'):
                filter_summary.append(f"Warehouse: {filters['warehouse'].name}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Inventory Valuation context: {len(records)} items, Total Value: {context['total_value']}")
        return context

class ItemMovementReportView(GenericFilterView):
    model = InventoryTransaction
    template_name = 'inventory/reports/item_movement_report.html'
    context_object_name = 'movements'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_inventorytransaction'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'item', 'warehouse', 'date_from', 'date_to']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = InventoryTransaction.objects.select_related('warehouse').filter(
            is_active=True
        ).values('item_code', 'item_name').annotate(
            total_in=Sum('quantity', filter=Q(transaction_type__in=['PURCHASE', 'RECEIPT', 'RETURN'])),
            total_out=Sum('quantity', filter=Q(transaction_type__in=['SALE', 'ISSUE', 'DELIVERY']))
        ).order_by('item_code')
        logger.debug(f"Initial Item Movement queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Item Movement count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(item_code__icontains=search_term) | Q(item_name__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('item'):
            item_term = filters['item'].strip()
            queryset = queryset.filter(Q(item_code__icontains=item_term) | Q(item_name__icontains=item_term))
            applied_filters.append(f"item={item_term}")
            
        if filters.get('warehouse'):
            queryset = queryset.filter(warehouse=filters['warehouse'])
            applied_filters.append(f"warehouse={filters['warehouse'].code}")
            
        if filters.get('date_from'):
            queryset = queryset.filter(transaction_date__gte=filters['date_from'])
            applied_filters.append(f"date_from={filters['date_from']}")
            
        if filters.get('date_to'):
            queryset = queryset.filter(transaction_date__lte=filters['date_to'])
            applied_filters.append(f"date_to={filters['date_to']}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'item_term': self.filter_form.cleaned_data.get('item', ''),
                'selected_warehouse': self.filter_form.cleaned_data.get('warehouse'),
                'start_date': self.filter_form.cleaned_data.get('date_from', ''),
                'end_date': self.filter_form.cleaned_data.get('date_to', ''),
            })
            
        context['page_title'] = 'Item Movement Report'
        context['all_warehouses'] = Warehouse.objects.filter(is_active=True)
        
        records = context['movements']
        total_in = sum(r['total_in'] or 0 for r in records)
        total_out = sum(r['total_out'] or 0 for r in records)
        
        context.update({
            'total_in': "{:.2f}".format(total_in),
            'total_out': "{:.2f}".format(total_out),
            'total_items': len(records),
        })
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('date_from') and filters.get('date_to'):
                filter_summary.append(f"Period: {filters['date_from']} to {filters['date_to']}")
            elif filters.get('date_from'):
                filter_summary.append(f"From: {filters['date_from']}")
            elif filters.get('date_to'):
                filter_summary.append(f"Until: {filters['date_to']}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('item'):
                filter_summary.append(f"Item: '{filters['item']}'")
            if filters.get('warehouse'):
                filter_summary.append(f"Warehouse: {filters['warehouse'].name}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Item Movement context: {len(records)} items, Total In: {context['total_in']}")
        return context

# Transfer Reports
class TransferSummaryView(GenericFilterView):
    model = InventoryTransfer
    template_name = 'inventory/reports/transfer_summary.html'
    context_object_name = 'transfers'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_inventorytransfer'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'date_from', 'date_to', 'warehouse', 'status']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = InventoryTransfer.objects.select_related('from_warehouse', 'to_warehouse').filter(is_active=True)
        logger.debug(f"Initial Inventory Transfer queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Inventory Transfer count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term) | Q(reference_document__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('date_from'):
            queryset = queryset.filter(document_date__gte=filters['date_from'])
            applied_filters.append(f"date_from={filters['date_from']}")
            
        if filters.get('date_to'):
            queryset = queryset.filter(document_date__lte=filters['date_to'])
            applied_filters.append(f"date_to={filters['date_to']}")
            
        if filters.get('warehouse'):
            queryset = queryset.filter(Q(from_warehouse=filters['warehouse']) | Q(to_warehouse=filters['warehouse']))
            applied_filters.append(f"warehouse={filters['warehouse'].code}")
            
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
            applied_filters.append(f"status={filters['status']}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'start_date': self.filter_form.cleaned_data.get('date_from', ''),
                'end_date': self.filter_form.cleaned_data.get('date_to', ''),
                'selected_warehouse': self.filter_form.cleaned_data.get('warehouse'),
                'selected_status': self.filter_form.cleaned_data.get('status', ''),
            })
            
        context['page_title'] = 'Transfer Summary'
        context['all_warehouses'] = Warehouse.objects.filter(is_active=True)
        
        transfers = context['transfers']
        totals = transfers.aggregate(
            total_amount=Sum('total_amount'),
            total_quantity=Sum('lines__quantity')
        )
        
        context.update({
            'total_amount': "{:.2f}".format(totals['total_amount'] or 0),
            'total_quantity': "{:.2f}".format(totals['total_quantity'] or 0),
            'total_transfers': len(transfers),
        })
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('date_from') and filters.get('date_to'):
                filter_summary.append(f"Period: {filters['date_from']} to {filters['date_to']}")
            elif filters.get('date_from'):
                filter_summary.append(f"From: {filters['date_from']}")
            elif filters.get('date_to'):
                filter_summary.append(f"Until: {filters['date_to']}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('warehouse'):
                filter_summary.append(f"Warehouse: {filters['warehouse'].name}")
            if filters.get('status'):
                filter_summary.append(f"Status: {filters['status']}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Transfer Summary context: {len(transfers)} transfers, Total Amount: {context['total_amount']}")
        return context

class PendingTransfersView(GenericFilterView):
    model = InventoryTransfer
    template_name = 'inventory/reports/pending_transfers.html'
    context_object_name = 'pending_transfers'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_inventorytransfer'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'date_from', 'date_to', 'warehouse']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        # Placeholder: Assuming 'Draft' status indicates pending transfers
        queryset = InventoryTransfer.objects.select_related('from_warehouse', 'to_warehouse').filter(
            is_active=True, status='Draft'
        )
        logger.debug(f"Initial Pending Transfers queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Pending Transfers count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('-document_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(id__icontains=search_term) | Q(reference_document__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('date_from'):
            queryset = queryset.filter(document_date__gte=filters['date_from'])
            applied_filters.append(f"date_from={filters['date_from']}")
            
        if filters.get('date_to'):
            queryset = queryset.filter(document_date__lte=filters['date_to'])
            applied_filters.append(f"date_to={filters['date_to']}")
            
        if filters.get('warehouse'):
            queryset = queryset.filter(Q(from_warehouse=filters['warehouse']) | Q(to_warehouse=filters['warehouse']))
            applied_filters.append(f"warehouse={filters['warehouse'].code}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'start_date': self.filter_form.cleaned_data.get('date_from', ''),
                'end_date': self.filter_form.cleaned_data.get('date_to', ''),
                'selected_warehouse': self.filter_form.cleaned_data.get('warehouse'),
            })
            
        context['page_title'] = 'Pending Transfers Report'
        context['all_warehouses'] = Warehouse.objects.filter(is_active=True)
        
        transfers = context['pending_transfers']
        context['total_transfers'] = len(transfers)
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('date_from') and filters.get('date_to'):
                filter_summary.append(f"Period: {filters['date_from']} to {filters['date_to']}")
            elif filters.get('date_from'):
                filter_summary.append(f"From: {filters['date_from']}")
            elif filters.get('date_to'):
                filter_summary.append(f"Until: {filters['date_to']}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('warehouse'):
                filter_summary.append(f"Warehouse: {filters['warehouse'].name}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Pending Transfers context: {len(transfers)} transfers")
        return context

# Adjustment Reports
class StockAdjustmentHistoryView(GenericFilterView):
    model = InventoryTransaction
    template_name = 'inventory/reports/stock_adjustment_history.html'
    context_object_name = 'adjustments'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_inventorytransaction'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'item', 'warehouse', 'date_from', 'date_to']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = InventoryTransaction.objects.select_related('warehouse').filter(
            is_active=True, transaction_type='ADJUSTMENT'
        )
        logger.debug(f"Initial Stock Adjustment queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Stock Adjustment count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('-transaction_date')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(item_code__icontains=search_term) | Q(item_name__icontains=search_term) | Q(reference__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('item'):
            item_term = filters['item'].strip()
            queryset = queryset.filter(Q(item_code__icontains=item_term) | Q(item_name__icontains=item_term))
            applied_filters.append(f"item={item_term}")
            
        if filters.get('warehouse'):
            queryset = queryset.filter(warehouse=filters['warehouse'])
            applied_filters.append(f"warehouse={filters['warehouse'].code}")
            
        if filters.get('date_from'):
            queryset = queryset.filter(transaction_date__gte=filters['date_from'])
            applied_filters.append(f"date_from={filters['date_from']}")
            
        if filters.get('date_to'):
            queryset = queryset.filter(transaction_date__lte=filters['date_to'])
            applied_filters.append(f"date_to={filters['date_to']}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'item_term': self.filter_form.cleaned_data.get('item', ''),
                'selected_warehouse': self.filter_form.cleaned_data.get('warehouse'),
                'start_date': self.filter_form.cleaned_data.get('date_from', ''),
                'end_date': self.filter_form.cleaned_data.get('date_to', ''),
            })
            
        context['page_title'] = 'Stock Adjustment History'
        context['all_warehouses'] = Warehouse.objects.filter(is_active=True)
        
        adjustments = context['adjustments']
        totals = adjustments.aggregate(
            total_quantity=Sum('quantity'),
            total_amount=Sum('total_amount')
        )
        
        context.update({
            'total_quantity': "{:.2f}".format(totals['total_quantity'] or 0),
            'total_amount': "{:.2f}".format(totals['total_amount'] or 0),
            'total_adjustments': len(adjustments),
        })
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('date_from') and filters.get('date_to'):
                filter_summary.append(f"Period: {filters['date_from']} to {filters['date_to']}")
            elif filters.get('date_from'):
                filter_summary.append(f"From: {filters['date_from']}")
            elif filters.get('date_to'):
                filter_summary.append(f"Until: {filters['date_to']}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('item'):
                filter_summary.append(f"Item: '{filters['item']}'")
            if filters.get('warehouse'):
                filter_summary.append(f"Warehouse: {filters['warehouse'].name}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Stock Adjustment context: {len(adjustments)} adjustments, Total Quantity: {context['total_quantity']}")
        return context

# Exception Reports
class StockBelowMinimumView(GenericFilterView):
    model = ItemWarehouseInfo
    template_name = 'inventory/reports/stock_below_minimum.html'
    context_object_name = 'low_stock_items'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_itemwarehouseinfo'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'item', 'warehouse']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = ItemWarehouseInfo.objects.select_related('item', 'warehouse').filter(
            item__is_active=True,
            warehouse__is_active=True,
            available__lt=F('min_stock')
        )
        logger.debug(f"Initial Stock Below Minimum queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Stock Below Minimum count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('item__code', 'warehouse__code')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(item__code__icontains=search_term) | Q(item__name__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('item'):
            item_term = filters['item'].strip()
            queryset = queryset.filter(Q(item__code__icontains=item_term) | Q(item__name__icontains=item_term))
            applied_filters.append(f"item={item_term}")
            
        if filters.get('warehouse'):
            queryset = queryset.filter(warehouse=filters['warehouse'])
            applied_filters.append(f"warehouse={filters['warehouse'].code}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'item_term': self.filter_form.cleaned_data.get('item', ''),
                'selected_warehouse': self.filter_form.cleaned_data.get('warehouse'),
            })
            
        context['page_title'] = 'Stock Below Minimum Report'
        context['all_warehouses'] = Warehouse.objects.filter(is_active=True)
        
        records = context['low_stock_items']
        context['total_items'] = len(records)
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('item'):
                filter_summary.append(f"Item: '{filters['item']}'")
            if filters.get('warehouse'):
                filter_summary.append(f"Warehouse: {filters['warehouse'].name}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Stock Below Minimum context: {len(records)} items")
        return context

class NegativeStockReportView(GenericFilterView):
    model = ItemWarehouseInfo
    template_name = 'inventory/reports/negative_stock_report.html'
    context_object_name = 'negative_stock_items'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_itemwarehouseinfo'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'item', 'warehouse']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = ItemWarehouseInfo.objects.select_related('item', 'warehouse').filter(
            item__is_active=True,
            warehouse__is_active=True,
            available__lt=0
        )
        logger.debug(f"Initial Negative Stock queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Negative Stock count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('item__code', 'warehouse__code')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(item__code__icontains=search_term) | Q(item__name__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('item'):
            item_term = filters['item'].strip()
            queryset = queryset.filter(Q(item__code__icontains=item_term) | Q(item__name__icontains=item_term))
            applied_filters.append(f"item={item_term}")
            
        if filters.get('warehouse'):
            queryset = queryset.filter(warehouse=filters['warehouse'])
            applied_filters.append(f"warehouse={filters['warehouse'].code}")
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'item_term': self.filter_form.cleaned_data.get('item', ''),
                'selected_warehouse': self.filter_form.cleaned_data.get('warehouse'),
            })
            
        context['page_title'] = 'Negative Stock Report'
        context['all_warehouses'] = Warehouse.objects.filter(is_active=True)
        
        records = context['negative_stock_items']
        context['total_items'] = len(records)
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('item'):
                filter_summary.append(f"Item: '{filters['item']}'")
            if filters.get('warehouse'):
                filter_summary.append(f"Warehouse: {filters['warehouse'].name}")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Negative Stock context: {len(records)} items")
        return context

class ZeroMovementReportView(GenericFilterView):
    model = Item
    template_name = 'inventory/reports/zero_movement_report.html'
    context_object_name = 'zero_movement_items'
    filter_form_class = InventoryReportFilterForm
    permission_required = 'Inventory.view_item'
    paginate_by = 10

    def get_paginate_by(self, queryset):
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if any(cleaned_data.get(key) for key in ['search', 'item', 'date_from', 'date_to']):
                logger.debug("Filters applied, showing all records")
                return None
        return self.paginate_by

    def get_queryset(self):
        queryset = Item.objects.filter(is_active=True)
        logger.debug(f"Initial Zero Movement queryset: {queryset.count()} records")
        
        if self.filter_form_class:
            self.filter_form = self.filter_form_class(self.request.GET)
            if self.filter_form.is_valid():
                queryset = self.apply_filters(queryset)
                logger.debug(f"Filtered Zero Movement count: {queryset.count()}")
            else:
                logger.warning(f"Filter form is invalid: {self.filter_form.errors}")
        
        return queryset.order_by('code')

    def apply_filters(self, queryset):
        filters = self.filter_form.cleaned_data
        applied_filters = []
        
        if filters.get('search'):
            search_term = filters['search'].strip()
            queryset = queryset.filter(Q(code__icontains=search_term) | Q(name__icontains=search_term))
            applied_filters.append(f"search={search_term}")
            
        if filters.get('item'):
            item_term = filters['item'].strip()
            queryset = queryset.filter(Q(code__icontains=item_term) | Q(name__icontains=item_term))
            applied_filters.append(f"item={item_term}")
            
        if filters.get('date_from') or filters.get('date_to'):
            transaction_filter = Q()
            if filters.get('date_from'):
                transaction_filter &= Q(transaction_date__gte=filters['date_from'])
                applied_filters.append(f"date_from={filters['date_from']}")
            if filters.get('date_to'):
                transaction_filter &= Q(transaction_date__lte=filters['date_to'])
                applied_filters.append(f"date_to={filters['date_to']}")
            # Exclude items with transactions in the period
            items_with_movement = InventoryTransaction.objects.filter(
                transaction_filter
            ).values('item_code').distinct()
            queryset = queryset.exclude(code__in=items_with_movement)
            
        logger.debug(f"Applied filters: {', '.join(applied_filters)}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            context.update({
                'search_term': self.filter_form.cleaned_data.get('search', ''),
                'item_term': self.filter_form.cleaned_data.get('item', ''),
                'start_date': self.filter_form.cleaned_data.get('date_from', ''),
                'end_date': self.filter_form.cleaned_data.get('date_to', ''),
            })
            
        context['page_title'] = 'Zero Movement Report'
        context['all_warehouses'] = Warehouse.objects.filter(is_active=True)
        
        records = context['zero_movement_items']
        context['total_items'] = len(records)
        
        filter_summary = []
        if hasattr(self, 'filter_form') and self.filter_form and self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
            if filters.get('date_from') and filters.get('date_to'):
                filter_summary.append(f"Period: {filters['date_from']} to {filters['date_to']}")
            elif filters.get('date_from'):
                filter_summary.append(f"From: {filters['date_from']}")
            elif filters.get('date_to'):
                filter_summary.append(f"Until: {filters['date_to']}")
            if filters.get('search'):
                filter_summary.append(f"Search: '{filters['search']}'")
            if filters.get('item'):
                filter_summary.append(f"Item: '{filters['item']}'")
                
        context['filter_summary'] = filter_summary
        logger.debug(f"Zero Movement context: {len(records)} items")
        return context


class MenuPageView(TemplateView):
    template_name = 'inventory/inventory_menu_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Reports Menu'
        logger.debug("Rendering menu page with context")
        return context               