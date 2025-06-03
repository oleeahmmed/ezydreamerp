from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q, F
from django.utils import timezone
from django.conf import settings
import csv
from django.core.exceptions import PermissionDenied

from ..models import ItemWarehouseInfo, Item, Warehouse, ItemGroup
from ..forms.item_warehouse_info_form import ItemWarehouseInfoForm, ItemWarehouseInfoFilterForm

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class ItemWarehouseInfoAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Base mixin for ItemWarehouseInfo views with common settings"""
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class ItemWarehouseInfoListView(ItemWarehouseInfoAccessMixin, ListView):
    model = ItemWarehouseInfo
    template_name = 'inventory/item_warehouse_info_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'inventory.view_itemwarehouseinfo'
    filter_form_class = ItemWarehouseInfoFilterForm

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Get filter parameters from request
        search = self.request.GET.get('search', '')
        warehouse_id = self.request.GET.get('warehouse', '')
        item_group_id = self.request.GET.get('item_group', '')
        stock_status = self.request.GET.get('stock_status', '')
        is_active = self.request.GET.get('is_active', '')
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(item__code__icontains=search) |
                Q(item__name__icontains=search) |
                Q(warehouse__name__icontains=search) |
                Q(warehouse__code__icontains=search)
            )
        
        # Apply warehouse filter
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        # Apply item group filter
        if item_group_id:
            queryset = queryset.filter(item__item_group_id=item_group_id)
        
        # Apply stock status filter
        if stock_status:
            if stock_status == 'low':
                # Low stock: in_stock <= min_stock and in_stock > 0
                queryset = queryset.filter(
                    in_stock__lte=F('min_stock'),
                    in_stock__gt=0
                )
            elif stock_status == 'normal':
                # Normal stock: in_stock > min_stock and in_stock < max_stock
                queryset = queryset.filter(
                    in_stock__gt=F('min_stock'),
                    in_stock__lt=F('max_stock')
                )
            elif stock_status == 'high':
                # High stock: in_stock >= max_stock
                queryset = queryset.filter(in_stock__gte=F('max_stock'))
            elif stock_status == 'out':
                # Out of stock: in_stock = 0
                queryset = queryset.filter(in_stock=0)
        
        # Apply active status filter
        if is_active:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        return queryset.select_related(
            'item', 
            'item__item_group',
            'warehouse'
        ).order_by('warehouse__name', 'item__code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter form and other context data
        context.update({
            'filter_form': ItemWarehouseInfoFilterForm(self.request.GET),
            'title': "Inventory by Warehouse",
            'subtitle': "Manage your inventory levels across warehouses",
            'create_url': reverse_lazy('Inventory:item_warehouse_info_create'),
            'print_url': reverse_lazy('Inventory:item_warehouse_info_print_list'),
            'export_url': reverse_lazy('Inventory:item_warehouse_info_export'),
            'model_name': "inventory",
            'can_create': self.request.user.has_perm('inventory.add_itemwarehouseinfo'),
            'can_delete': self.request.user.has_perm('inventory.delete_itemwarehouseinfo'),
            'warehouses': Warehouse.objects.filter(is_active=True),
            'item_groups': ItemGroup.objects.filter(is_active=True),
        })
        return context

class ItemWarehouseInfoCreateView(ItemWarehouseInfoAccessMixin, SuccessMessageMixin, CreateView):
    model = ItemWarehouseInfo
    form_class = ItemWarehouseInfoForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Inventory:item_warehouse_info_list')
    success_message = "Inventory record was created successfully"
    permission_required = 'inventory.add_itemwarehouseinfo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create Inventory Record",
            'subtitle': "Add a new inventory record for an item in a warehouse",
            'cancel_url': reverse_lazy('Inventory:item_warehouse_info_list'),
        })
        return context

    def get_initial(self):
        initial = super().get_initial()
        
        # Pre-populate item and warehouse if provided in URL
        item_id = self.request.GET.get('item')
        warehouse_id = self.request.GET.get('warehouse')
        
        if item_id:
            try:
                initial['item'] = Item.objects.get(pk=item_id)
            except Item.DoesNotExist:
                pass
                
        if warehouse_id:
            try:
                initial['warehouse'] = Warehouse.objects.get(pk=warehouse_id)
            except Warehouse.DoesNotExist:
                pass
                
        return initial

class ItemWarehouseInfoUpdateView(ItemWarehouseInfoAccessMixin, SuccessMessageMixin, UpdateView):
    model = ItemWarehouseInfo
    form_class = ItemWarehouseInfoForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Inventory:item_warehouse_info_list')
    success_message = "Inventory record was updated successfully"
    permission_required = 'inventory.change_itemwarehouseinfo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update Inventory Record",
            'subtitle': f"Edit inventory for {self.object.item.code} in {self.object.warehouse.name}",
            'cancel_url': reverse_lazy('Inventory:item_warehouse_info_detail', kwargs={'pk': self.object.pk}),
        })
        return context

class ItemWarehouseInfoDetailView(ItemWarehouseInfoAccessMixin, DetailView):
    model = ItemWarehouseInfo
    template_name = 'common/premium-form.html'
    permission_required = 'inventory.view_itemwarehouseinfo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = ItemWarehouseInfoForm(instance=self.object)
        context.update({
            'title': "Inventory Record Details",
            'subtitle': f"View inventory for {self.object.item.code} in {self.object.warehouse.name}",
            'form': form,
            'readonly': True,
            'print_url': reverse_lazy('Inventory:item_warehouse_info_print_detail', kwargs={'pk': self.object.pk}),
            'update_url': reverse_lazy('Inventory:item_warehouse_info_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('Inventory:item_warehouse_info_delete', kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('Inventory:item_warehouse_info_list'),
            'can_update': self.request.user.has_perm('inventory.change_itemwarehouseinfo'),
            'can_delete': self.request.user.has_perm('inventory.delete_itemwarehouseinfo'),
        })
        return context

class ItemWarehouseInfoDeleteView(ItemWarehouseInfoAccessMixin, GenericDeleteView):
    model = ItemWarehouseInfo
    success_url = reverse_lazy('Inventory:item_warehouse_info_list')
    permission_required = 'inventory.delete_itemwarehouseinfo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Delete Inventory Record",
            'subtitle': f"Delete inventory record for {self.object.item.code} in {self.object.warehouse.name}",
        })
        return context
        
    def get_cancel_url(self):
        return reverse_lazy('Inventory:item_warehouse_info_detail', kwargs={'pk': self.object.pk})

class ItemWarehouseInfoExportView(ItemWarehouseInfoAccessMixin, BaseExportView):
    model = ItemWarehouseInfo
    filename = "inventory_by_warehouse.csv"
    permission_required = "inventory.view_itemwarehouseinfo"
    field_names = ["Item Code", "Item Name", "Warehouse", "In Stock", 
                  "Committed", "Ordered", "Available", "Min Stock", "Max Stock", "Status"]

    def queryset_filter(self, request, queryset):
        # Get filter parameters from request
        search = request.GET.get('search', '')
        warehouse_id = request.GET.get('warehouse', '')
        item_group_id = request.GET.get('item_group', '')
        stock_status = request.GET.get('stock_status', '')
        is_active = request.GET.get('is_active', '')
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(item__code__icontains=search) |
                Q(item__name__icontains=search) |
                Q(warehouse__name__icontains=search) |
                Q(warehouse__code__icontains=search)
            )
        
        # Apply warehouse filter
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        # Apply item group filter
        if item_group_id:
            queryset = queryset.filter(item__item_group_id=item_group_id)
        
        # Apply stock status filter
        if stock_status:
            if stock_status == 'low':
                queryset = queryset.filter(
                    in_stock__lte=F('min_stock'),
                    in_stock__gt=0
                )
            elif stock_status == 'normal':
                queryset = queryset.filter(
                    in_stock__gt=F('min_stock'),
                    in_stock__lt=F('max_stock')
                )
            elif stock_status == 'high':
                queryset = queryset.filter(in_stock__gte=F('max_stock'))
            elif stock_status == 'out':
                queryset = queryset.filter(in_stock=0)
        
        # Apply active status filter
        if is_active:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
            
        return queryset.select_related('item', 'warehouse')

class ItemWarehouseInfoBulkDeleteView(ItemWarehouseInfoAccessMixin, BaseBulkDeleteConfirmView):
    model = ItemWarehouseInfo
    permission_required = "inventory.delete_itemwarehouseinfo"
    display_fields = ["item__code", "item__name", "warehouse__name", "in_stock", "available"]
    cancel_url = reverse_lazy("Inventory:item_warehouse_info_list")
    success_url = reverse_lazy("Inventory:item_warehouse_info_list")
    template_name = 'inventory/item_warehouse_info_bulk_delete.html'

class ItemWarehouseInfoPrintDetailView(ItemWarehouseInfoAccessMixin, View):
    permission_required = 'inventory.view_itemwarehouseinfo'
    template_name = 'inventory/item_warehouse_info_print_detail.html'

    def get(self, request, *args, **kwargs):
        record = get_object_or_404(
            ItemWarehouseInfo.objects.select_related(
                'item',
                'item__item_group',
                'item__inventory_uom',
                'warehouse'
            ),
            pk=kwargs['pk']
        )
        
        context = {
            'record': record,
            'title': f'Inventory: {record.item.code} in {record.warehouse.name}',
            'user': request.user,
            'timestamp': timezone.now(),
            'company_info': getattr(settings, 'COMPANY_INFO', {}),
        }
        
        return render(request, self.template_name, context)

class ItemWarehouseInfoPrintView(ItemWarehouseInfoAccessMixin, View):
    permission_required = 'inventory.view_itemwarehouseinfo'

    def get_context_data(self, **kwargs):
        context = {
            'user': self.request.user,
            'timestamp': timezone.now(),
            'company_info': getattr(settings, 'COMPANY_INFO', {}),
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        
        if 'pk' in kwargs:
            # Single record print view
            record = get_object_or_404(
                ItemWarehouseInfo.objects.select_related(
                    'item',
                    'item__item_group',
                    'item__inventory_uom',
                    'warehouse'
                ),
                pk=kwargs['pk']
            )
            
            context.update({
                'record': record,
                'title': f'Inventory: {record.item.code} in {record.warehouse.name}',
            })
            template_name = 'inventory/item_warehouse_info_print_detail.html'
        else:
            # List print view
            records = ItemWarehouseInfo.objects.select_related(
                'item',
                'item__item_group',
                'warehouse'
            ).order_by('warehouse__name', 'item__code')
            
            context.update({
                'records': records,
                'title': 'Inventory by Warehouse',
            })
            template_name = 'inventory/item_warehouse_info_print_list.html'
        
        return render(request, template_name, context)