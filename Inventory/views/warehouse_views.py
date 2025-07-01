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

from ..models import Warehouse
from ..forms import WarehouseForm, WarehouseFilterForm

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class WarehouseAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class WarehouseListView(WarehouseAccessMixin, GenericFilterView):
    model = Warehouse
    template_name = 'inventory/warehouse_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Inventory.view_warehouse'
    filter_form_class = WarehouseFilterForm

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Get filter parameters from request
        search = self.request.GET.get('search', '')
        is_active = self.request.GET.get('is_active', '')
        is_default = self.request.GET.get('is_default', '')
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(address__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(contact_phone__icontains=search)
            )
        
        # Apply active status filter
        if is_active:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
            
        # Apply default warehouse filter
        if is_default:
            is_default_bool = is_default.lower() == 'true'
            queryset = queryset.filter(is_default=is_default_bool)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'filter_form': WarehouseFilterForm(self.request.GET) if hasattr(self, 'request') else None,
            'title': "Warehouses",
            'subtitle': "Manage warehouses",
            'create_url': reverse_lazy('Inventory:warehouse_create'),
            'print_url': reverse_lazy('Inventory:warehouse_print_list'),
            'export_url': reverse_lazy('Inventory:warehouse_export'),
            'model_name': "warehouse",
            'can_create': self.request.user.has_perm('Inventory.add_warehouse'),
            'can_delete': self.request.user.has_perm('Inventory.delete_warehouse'),
        })
        return context

class WarehouseCreateView(WarehouseAccessMixin, SuccessMessageMixin, CreateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Inventory:warehouse_list')
    success_message = "Warehouse %(name)s was created successfully"
    permission_required = 'Inventory.add_warehouse'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Create Warehouse",
            'subtitle': "Add a new warehouse",
            'cancel_url': reverse_lazy('Inventory:warehouse_list'),
        })
        return context

class WarehouseUpdateView(WarehouseAccessMixin, SuccessMessageMixin, UpdateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'common/premium-form.html'
    success_url = reverse_lazy('Inventory:warehouse_list')
    success_message = "Warehouse %(name)s was updated successfully"
    permission_required = 'Inventory.change_warehouse'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Update Warehouse",
            'subtitle': f"Edit details for {self.object.name}",
            'cancel_url': reverse_lazy('Inventory:warehouse_detail', kwargs={'pk': self.object.pk}),
        })
        return context

class WarehouseDeleteView(WarehouseAccessMixin, GenericDeleteView):
    model = Warehouse
    success_url = reverse_lazy('Inventory:warehouse_list')
    permission_required = 'Inventory.delete_warehouse'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Delete Warehouse",
            'subtitle': f"Delete warehouse {self.object.name}",
        })
        return context
        
    def get_cancel_url(self):
        return reverse_lazy('Inventory:warehouse_detail', kwargs={'pk': self.object.pk})

class WarehouseDetailView(WarehouseAccessMixin, DetailView):
    model = Warehouse
    template_name = 'common/premium-form.html'
    permission_required = 'Inventory.view_warehouse'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': "Warehouse Details",
            'subtitle': f"View details for {self.object.name}",
            'form': WarehouseForm(instance=self.object),
            'readonly': True,
            'print_url': reverse_lazy('Inventory:warehouse_print_detail', kwargs={'pk': self.object.pk}),
            'update_url': reverse_lazy('Inventory:warehouse_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('Inventory:warehouse_delete', kwargs={'pk': self.object.pk}),
            'cancel_url': reverse_lazy('Inventory:warehouse_list'),
            'can_update': self.request.user.has_perm('Inventory.change_warehouse'),
            'can_delete': self.request.user.has_perm('Inventory.delete_warehouse'),
        })
        return context

class WarehousePrintDetailView(WarehouseAccessMixin, View):
    permission_required = 'Inventory.view_warehouse'
    template_name = 'inventory/warehouse_print_detail.html'

    def get(self, request, *args, **kwargs):
        warehouse = get_object_or_404(Warehouse, pk=kwargs['pk'])
        context = {
            'warehouse': warehouse,
            'title': f'Warehouse: {warehouse.code}',
            'user': request.user,
            'timestamp': timezone.now(),
            'company_info': getattr(settings, 'COMPANY_INFO', {}),
        }
        return render(request, self.template_name, context)

class WarehousePrintView(WarehouseAccessMixin, View):
    permission_required = 'Inventory.view_warehouse'
    template_name = 'inventory/warehouse_print_list.html'

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
            # Single warehouse print view
            warehouse = get_object_or_404(Warehouse, pk=kwargs['pk'])
            
            context.update({
                'warehouse': warehouse,
                'title': f'Warehouse: {warehouse.code}',
            })
            template_name = 'inventory/warehouse_print_detail.html'
        else:
            # List print view
            warehouses = Warehouse.objects.all()
            
            context.update({
                'warehouses': warehouses,
                'title': 'Warehouses List',
            })
            template_name = 'inventory/warehouse_print_list.html'
        
        return render(request, template_name, context)

class WarehouseExportView(WarehouseAccessMixin, BaseExportView):
    model = Warehouse
    filename = "warehouses.csv"
    permission_required = "Inventory.view_warehouse"
    field_names = ["Code", "Name", "Is Default", "Is Active", 
                  "Address", "Contact Person", "Contact Phone", "Notes"]

    def queryset_filter(self, request, queryset):
        # Apply filters from request if needed
        search = request.GET.get('search', '')
        is_active = request.GET.get('is_active', '')
        is_default = request.GET.get('is_default', '')
        
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(address__icontains=search) |
                Q(contact_person__icontains=search) |
                Q(contact_phone__icontains=search)
            )
        
        if is_active:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
            
        if is_default:
            is_default_bool = is_default.lower() == 'true'
            queryset = queryset.filter(is_default=is_default_bool)
            
        return queryset

class WarehouseBulkDeleteView(WarehouseAccessMixin, BaseBulkDeleteConfirmView):
    model = Warehouse
    permission_required = "Inventory.delete_warehouse"
    display_fields = ["code", "name", "is_default", "is_active"]
    cancel_url = reverse_lazy("Inventory:warehouse_list")
    success_url = reverse_lazy("Inventory:warehouse_list")
    template_name = 'inventory/warehouse_bulk_delete.html'