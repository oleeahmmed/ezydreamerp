from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
import csv
from django.http import HttpResponse

from ..models import Item, ItemGroup, Warehouse, ItemWarehouseInfo
from ..forms import ItemForm, ItemFilterForm

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class ItemListView(GenericFilterView):
    model = Item
    template_name = 'inventory/item_list.html'
    context_object_name = 'objects'  # Changed to 'objects' to match the template
    paginate_by = 10
    permission_required = 'Inventory.view_item'
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-created_at')
        
        # Filter by search query if provided
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(code__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(barcode__icontains=search_query) |
                Q(item_group__name__icontains=search_query)
            )
        
        # Apply item type filter
        item_type = self.request.GET.get('type', '')
        if item_type:
            if item_type == 'inventory':
                queryset = queryset.filter(is_inventory_item=True)
            elif item_type == 'sales':
                queryset = queryset.filter(is_sales_item=True)
            elif item_type == 'purchase':
                queryset = queryset.filter(is_purchase_item=True)
            elif item_type == 'service':
                queryset = queryset.filter(is_service=True)
        
        # Apply group filter
        group_id = self.request.GET.get('group', '')
        if group_id:
            queryset = queryset.filter(item_group_id=group_id)
        
        # Apply warehouse filter
        warehouse_id = self.request.GET.get('warehouse', '')
        if warehouse_id:
            queryset = queryset.filter(warehouse_info__warehouse_id=warehouse_id)
        
        # Apply active status filter
        is_active = self.request.GET.get('is_active', '')
        if is_active:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
            
        # Optimize query with select_related and prefetch_related
        return queryset.select_related(
            'item_group', 
            'inventory_uom',
            'default_warehouse'
        ).prefetch_related('warehouse_info__warehouse').distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Items'
        context['subtitle'] = 'Manage inventory items'
        context['create_url'] = reverse_lazy('Inventory:item_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Inventory.add_item')
        context['can_view'] = self.request.user.has_perm('Inventory.view_item')
        context['can_update'] = self.request.user.has_perm('Inventory.change_item')
        context['can_delete'] = self.request.user.has_perm('Inventory.delete_item')
        context['can_print'] = self.request.user.has_perm('Inventory.view_item')
        context['can_export'] = self.request.user.has_perm('Inventory.view_item')
        context['can_bulk_delete'] = self.request.user.has_perm('Inventory.delete_item')
        
        # Add filter form and other context data
        context['filter_form'] = ItemFilterForm(self.request.GET)
        context['item_groups'] = ItemGroup.objects.filter(is_active=True)
        context['warehouses'] = Warehouse.objects.filter(is_active=True)
        
        return context

class ItemAllListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Item
    template_name = 'inventory/item_all_list.html'
    context_object_name = 'objects'
    permission_required = 'Inventory.view_item'

    def get_queryset(self):
        return Item.objects.all().select_related(
            'item_group',
            'inventory_uom',
            'purchase_uom',
            'sales_uom',
            'default_warehouse'
        ).prefetch_related('warehouse_info__warehouse')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        items = context['objects']
        item_data = []

        total_sales_value = 0
        total_purchase_value = 0

        for item in items:
            stock = item.in_stock or 0
            sales_price = item.unit_price or 0  # Treated as sales price
            purchase_price = item.purchase_price or 0

            sales_total = sales_price * stock
            purchase_total = purchase_price * stock

            total_sales_value += sales_total
            total_purchase_value += purchase_total

            item_data.append({
                'object': item,
                'code': item.code,
                'name': item.name,
                'in_stock': stock,
                'unit_price': sales_price,
                'purchase_price': purchase_price,
                'sales_total': sales_total,
                'purchase_total': purchase_total,
            })

        context['item_data'] = item_data
        context['total_sales_value'] = total_sales_value
        context['total_purchase_value'] = total_purchase_value
        return context


class ItemCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = 'common/tabs-form.html'
    permission_required = 'Inventory.add_item'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Item'
        context['subtitle'] = 'Add a new item to your inventory'
        context['cancel_url'] = reverse_lazy('Inventory:item_list')
        context['submit_text'] = 'Create Item'
        
        return context
    
    def form_valid(self, form):
        with transaction.atomic():
            # Save the main form
            self.object = form.save()
            
            # Create default warehouse info if it doesn't exist
            if self.object.is_inventory_item and self.object.default_warehouse:
                ItemWarehouseInfo.objects.get_or_create(
                    item=self.object,
                    warehouse=self.object.default_warehouse,
                    defaults={
                        'in_stock': 0,
                        'committed': 0,
                        'ordered': 0,
                        'available': 0,
                        'min_stock': self.object.minimum_stock,
                        'max_stock': self.object.maximum_stock
                    }
                )
        
        messages.success(self.request, f'Item {self.object.code} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        # Return to list URL after successful creation
        return reverse_lazy('Inventory:item_list')

class ItemUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = 'common/tabs-form.html'
    permission_required = 'Inventory.change_item'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Item'
        context['subtitle'] = f'Edit item {self.object.code}'
        context['cancel_url'] = reverse_lazy('Inventory:item_detail', kwargs={'pk': self.object.pk})
        context['submit_text'] = 'Update Item'
        
        # Add stock display
        form = context.get('form')
        if form:
            context['stock_display'] = form.get_stock_display()
            
        return context
    
    def form_valid(self, form):
        with transaction.atomic():
            # Save the main form
            self.object = form.save()
            
            # Update or create warehouse info
            if self.object.is_inventory_item and self.object.default_warehouse:
                warehouse_info, created = ItemWarehouseInfo.objects.get_or_create(
                    item=self.object,
                    warehouse=self.object.default_warehouse,
                    defaults={
                        'in_stock': 0,
                        'committed': 0,
                        'ordered': 0,
                        'available': 0,
                        'min_stock': self.object.minimum_stock,
                        'max_stock': self.object.maximum_stock
                    }
                )
                
                if not created:
                    # Update existing warehouse info
                    warehouse_info.min_stock = self.object.minimum_stock
                    warehouse_info.max_stock = self.object.maximum_stock
                    warehouse_info.save()
        
        messages.success(self.request, f'Item {self.object.code} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        # Return to detail URL after successful update
        return reverse_lazy('Inventory:item_detail', kwargs={'pk': self.object.pk})

class ItemDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Item
    template_name = 'common/tabs-form.html'
    context_object_name = 'item'
    permission_required = 'Inventory.view_item'
    
    def get_queryset(self):
        # Optimize query with select_related and prefetch_related
        return Item.objects.select_related(
            'item_group',
            'inventory_uom',
            'purchase_uom',
            'sales_uom',
            'default_warehouse'
        ).prefetch_related('warehouse_info__warehouse')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Item Details'
        context['subtitle'] = f'Item {self.object.code}'
        context['cancel_url'] = reverse_lazy('Inventory:item_list')
        context['update_url'] = reverse_lazy('Inventory:item_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Inventory:item_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        form = ItemForm(instance=self.object)
        context['form'] = form
        context['stock_display'] = form.get_stock_display()
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class ItemDeleteView(GenericDeleteView):
    model = Item
    success_url = reverse_lazy('Inventory:item_list')
    permission_required = 'Inventory.delete_item'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to Item detail view.
        """
        return reverse_lazy('Inventory:item_detail', kwargs={'pk': self.object.pk})

class ItemExportView(BaseExportView):
    """
    Export view for Item.
    """
    model = Item
    filename = "items.csv"
    permission_required = "Inventory.view_item"
    field_names = ["Code", "Name", "Group", "UOM", "Is Active", "Is Inventory", "Is Sales", "Is Purchase", "Is Service", "Minimum Stock", "Maximum Stock", "Reorder Point"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        return queryset.select_related('item_group', 'inventory_uom')

class ItemPrintDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Item
    template_name = 'inventory/item_print_detail.html'
    context_object_name = 'item'
    permission_required = 'Inventory.view_item'
    
    def get_queryset(self):
        # Optimize query with select_related and prefetch_related
        return Item.objects.select_related(
            'item_group',
            'inventory_uom',
            'purchase_uom',
            'sales_uom',
            'default_warehouse'
        ).prefetch_related('warehouse_info__warehouse')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Item'
        context['subtitle'] = f'Item {self.object.code}'
        context['user'] = self.request.user
        context['timestamp'] = timezone.now()
        context['company_info'] = getattr(settings, 'COMPANY_INFO', {})
        return context

class ItemPrintView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Item
    template_name = 'inventory/item_print_list.html'
    permission_required = 'Inventory.view_item'
    
    def get_queryset(self):
        # Optimize query with select_related and prefetch_related
        return Item.objects.select_related(
            'item_group',
            'inventory_uom',
            'default_warehouse'
        ).prefetch_related('warehouse_info__warehouse')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Items List'
        context['user'] = self.request.user
        context['timestamp'] = timezone.now()
        context['company_info'] = getattr(settings, 'COMPANY_INFO', {})
        return context

class ItemBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for Items.
    """
    model = Item
    permission_required = "Inventory.delete_item"
    display_fields = ["code", "name", "item_group", "is_active"]
    cancel_url = reverse_lazy("Inventory:item_list")  # Manually setting the cancel URL
    success_url = reverse_lazy("Inventory:item_list")  # Redirect after successful delete

class ItemSearchAPIView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Item
    permission_required = "Inventory.view_item"
    
    def get(self, request, *args, **kwargs):
        query = request.GET.get('query', '')
        
        if query:
            # Search for items matching the query
            items = Item.objects.filter(
                Q(code__icontains=query) | 
                Q(name__icontains=query)
            ).filter(is_active=True).select_related(
                'inventory_uom', 
                'default_warehouse'
            ).prefetch_related('warehouse_info__warehouse')[:100]
        else:
            # Return all active items when no query is provided
            items = Item.objects.filter(is_active=True).select_related(
                'inventory_uom', 
                'default_warehouse'
            ).prefetch_related('warehouse_info__warehouse')[:500]
        
        # Format the response
        items_data = []
        for item in items:
            # Get warehouse info for stock data
            warehouse_info = item.warehouse_info.filter(warehouse=item.default_warehouse).first()
            
            items_data.append({
                'id': item.id,
                'code': item.code,
                'name': item.name,
                'uom': item.inventory_uom.code if item.inventory_uom else '',
                'stock': str(item.in_stock),
                'in_stock': str(item.in_stock),
                'committed': str(item.committed),
                'ordered': str(item.ordered),
                'available': str(item.available),
                'unit_price': str(item.unit_price) if item.unit_price is not None else '0.00',
                'default_warehouse_id': item.default_warehouse.id if item.default_warehouse else None,
                'default_warehouse_name': item.default_warehouse.name if item.default_warehouse else '',
            })
        
        return JsonResponse({'items': items_data})