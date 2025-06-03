from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
import csv
from datetime import datetime, timedelta

from ..models import InventoryTransaction, Warehouse, Item
from ..forms import InventoryTransactionForm, InventoryTransactionFilterForm

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class InventoryTransactionAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class InventoryTransactionListView(InventoryTransactionAccessMixin, GenericFilterView):
    model = InventoryTransaction
    template_name = 'inventory/inventory_transaction_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Inventory.view_inventorytransaction'
    filter_form_class = InventoryTransactionFilterForm

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Get filter parameters from request
        search = self.request.GET.get('search', '')
        document_type = self.request.GET.get('document_type', '')
        warehouse_id = self.request.GET.get('warehouse', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        is_active = self.request.GET.get('is_active', '')
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(item_code__icontains=search) |
                Q(item_name__icontains=search) |
                Q(remarks__icontains=search)
            )
        
        # Apply document type filter
        if document_type:
            queryset = queryset.filter(document_type__icontains=document_type)
            
        # Apply warehouse filter
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
            
        # Apply date range filter
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(transaction_date__date__gte=date_from_obj)
            except ValueError:
                pass
                
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                # Add one day to include the end date
                date_to_obj = date_to_obj + timedelta(days=1)
                queryset = queryset.filter(transaction_date__date__lt=date_to_obj)
            except ValueError:
                pass
        
        # Apply active status filter
        if is_active:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset.order_by('-transaction_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'filter_form': InventoryTransactionFilterForm(self.request.GET) if hasattr(self, 'request') else None,
            'title': "Inventory Transactions",
            'subtitle': "Manage inventory transactions",
            'create_url': reverse_lazy('Inventory:inventory_transaction_create'),
            'print_url': reverse_lazy('Inventory:inventory_transaction_print_list'),
            'export_url': reverse_lazy('Inventory:inventory_transaction_export'),
            'model_name': "transaction",
            'can_create': self.request.user.has_perm('Inventory.add_inventorytransaction'),
            'can_delete': self.request.user.has_perm('Inventory.delete_inventorytransaction'),
        })
        return context

class InventoryTransactionCreateView(InventoryTransactionAccessMixin, SuccessMessageMixin, CreateView):
    model = InventoryTransaction
    form_class = InventoryTransactionForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Inventory:inventory_transaction_list')
    success_message = "Inventory transaction was created successfully"
    permission_required = 'Inventory.add_inventorytransaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create Inventory Transaction",
            'subtitle': "Add a new inventory transaction",
            'cancel_url': reverse_lazy('Inventory:inventory_transaction_list'),
        })
        return context
    
    def form_valid(self, form):
        # Calculate total_amount before saving
        form.instance.total_amount = form.instance.quantity * form.instance.unit_price
        return super().form_valid(form)

class InventoryTransactionUpdateView(InventoryTransactionAccessMixin, SuccessMessageMixin, UpdateView):
    model = InventoryTransaction
    form_class = InventoryTransactionForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Inventory:inventory_transaction_list')
    success_message = "Inventory transaction was updated successfully"
    permission_required = 'Inventory.change_inventorytransaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update Inventory Transaction",
            'subtitle': f"Edit details for transaction {self.object.pk}",
            'cancel_url': reverse_lazy('Inventory:inventory_transaction_detail', kwargs={'pk': self.object.pk}),
        })
        return context
    
    def form_valid(self, form):
        # Calculate total_amount before saving
        form.instance.total_amount = form.instance.quantity * form.instance.unit_price
        return super().form_valid(form)

class InventoryTransactionDeleteView(InventoryTransactionAccessMixin, GenericDeleteView):
    model = InventoryTransaction
    success_url = reverse_lazy('Inventory:inventory_transaction_list')
    permission_required = 'Inventory.delete_inventorytransaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Delete Inventory Transaction",
            'subtitle': f"Delete transaction {self.object.pk}",
            'cancel_url': reverse_lazy('Inventory:inventory_transaction_detail', kwargs={'pk': self.object.pk}),
        })
        return context

    def get_cancel_url(self):
        return reverse_lazy('Inventory:inventory_transaction_detail', kwargs={'pk': self.object.pk})

class InventoryTransactionDetailView(InventoryTransactionAccessMixin, DetailView):
    model = InventoryTransaction
    template_name = 'common/premium-form.html'
    permission_required = 'Inventory.view_inventorytransaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Transaction Details",
            'subtitle': f"View details for transaction {self.object.pk}",
            'form': InventoryTransactionForm(instance=self.object),
            'readonly': True,
            'print_url': reverse_lazy('Inventory:inventory_transaction_print_detail', kwargs={'pk': self.object.pk}),
            'update_url': reverse_lazy('Inventory:inventory_transaction_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('Inventory:inventory_transaction_delete', kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('Inventory:inventory_transaction_list'),
            'can_update': self.request.user.has_perm('Inventory.change_inventorytransaction'),
            'can_delete': self.request.user.has_perm('Inventory.delete_inventorytransaction'),
        })
        return context

class InventoryTransactionPrintDetailView(InventoryTransactionAccessMixin, View):
    permission_required = 'Inventory.view_inventorytransaction'
    template_name = 'inventory/inventory_transaction_print_detail.html'

    def get(self, request, *args, **kwargs):
        transaction = get_object_or_404(InventoryTransaction, pk=kwargs['pk'])
        context = {
            'transaction': transaction,
            'title': f'Transaction: {transaction.pk}',
            'user': request.user,
            'timestamp': timezone.now(),
            'company_info': getattr(settings, 'COMPANY_INFO', {}),
        }
        return render(request, self.template_name, context)

class InventoryTransactionPrintView(InventoryTransactionAccessMixin, View):
    permission_required = 'Inventory.view_inventorytransaction'
    template_name = 'inventory/inventory_transaction_print_list.html'

    def get_context_data(self, **kwargs):
        context = {
            'user': self.request.user,
            'timestamp': timezone.now(),
            'company_info': getattr(settings, 'COMPANY_INFO', {}),
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        
        # Get filtered transactions
        search = request.GET.get('search', '')
        document_type = request.GET.get('document_type', '')
        warehouse_id = request.GET.get('warehouse', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        transactions = InventoryTransaction.objects.filter(is_active=True)
        
        if search:
            transactions = transactions.filter(
                Q(item_code__icontains=search) |
                Q(item_name__icontains=search) |
                Q(remarks__icontains=search)
            )
        
        if document_type:
            transactions = transactions.filter(document_type__icontains=document_type)
            
        if warehouse_id:
            transactions = transactions.filter(warehouse_id=warehouse_id)
            
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                transactions = transactions.filter(transaction_date__date__gte=date_from_obj)
            except ValueError:
                pass
                
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                # Add one day to include the end date
                date_to_obj = date_to_obj + timedelta(days=1)
                transactions = transactions.filter(transaction_date__date__lt=date_to_obj)
            except ValueError:
                pass
        
        transactions = transactions.order_by('-transaction_date')
        
        context.update({
            'transactions': transactions,
            'title': 'Inventory Transactions List',
        })
        
        return render(request, self.template_name, context)

class InventoryTransactionExportView(InventoryTransactionAccessMixin, BaseExportView):
    model = InventoryTransaction
    filename = "inventory_transactions.csv"
    permission_required = "Inventory.view_inventorytransaction"
    field_names = ["Document Type", "Document Number", "Transaction Date", 
                  "Item Code", "Item Name", "Warehouse", "Quantity",
                  "Unit Price", "Total Amount", "Remarks",
                  "Created At", "Updated At", "Is Active"]

    def queryset_filter(self, request, queryset):
        # Get filtered transactions
        search = request.GET.get('search', '')
        document_type = request.GET.get('document_type', '')
        warehouse_id = request.GET.get('warehouse', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        is_active = request.GET.get('is_active', '')
        
        if search:
            queryset = queryset.filter(
                Q(item_code__icontains=search) |
                Q(item_name__icontains=search) |
                Q(remarks__icontains=search)
            )
        
        if document_type:
            queryset = queryset.filter(document_type__icontains=document_type)
            
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
            
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(transaction_date__date__gte=date_from_obj)
            except ValueError:
                pass
                
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                # Add one day to include the end date
                date_to_obj = date_to_obj + timedelta(days=1)
                queryset = queryset.filter(transaction_date__date__lt=date_to_obj)
            except ValueError:
                pass
        
        if is_active:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset.select_related('warehouse').order_by('-transaction_date')

class InventoryTransactionBulkDeleteView(InventoryTransactionAccessMixin, BaseBulkDeleteConfirmView):
    model = InventoryTransaction
    permission_required = "Inventory.delete_inventorytransaction"
    display_fields = ["id", "transaction_date", "item_code", "item_name", "quantity"]
    cancel_url = reverse_lazy("Inventory:inventory_transaction_list")
    success_url = reverse_lazy("Inventory:inventory_transaction_list")
    template_name = 'bulk_delete_confirm.html'