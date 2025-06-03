from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied

from ..models import InventoryTransfer
from ..forms import InventoryTransferForm, InventoryTransferExtraInfoForm, InventoryTransferLineFormSet

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class InventoryTransferAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class InventoryTransferListView(InventoryTransferAccessMixin, GenericFilterView):
    model = InventoryTransfer
    template_name = 'inventory/inventory_transfer_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Inventory.view_inventorytransfer'
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-posting_date')
        
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                id__icontains=search_query
            ) | queryset.filter(
                remarks__icontains=search_query
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Inventory Transfers'
        context['subtitle'] = 'Manage inventory transfers'
        context['create_url'] = reverse_lazy('Inventory:inventory_transfer_create')
        
        context['can_create'] = self.request.user.has_perm('Inventory.add_inventorytransfer')
        context['can_view'] = self.request.user.has_perm('Inventory.view_inventorytransfer')
        context['can_update'] = self.request.user.has_perm('Inventory.change_inventorytransfer')
        context['can_delete'] = self.request.user.has_perm('Inventory.delete_inventorytransfer')
        context['can_print'] = self.request.user.has_perm('Inventory.view_inventorytransfer')
        context['can_export'] = self.request.user.has_perm('Inventory.view_inventorytransfer')
        context['can_bulk_delete'] = self.request.user.has_perm('Inventory.delete_inventorytransfer')
        
        return context

class InventoryTransferCreateView(InventoryTransferAccessMixin, CreateView):
    model = InventoryTransfer
    form_class = InventoryTransferForm
    template_name = 'common/formset-form.html'
    permission_required = 'Inventory.add_inventorytransfer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Inventory Transfer'
        context['subtitle'] = 'Record new inventory transfer'
        context['cancel_url'] = reverse_lazy('Inventory:inventory_transfer_list')
        context['submit_text'] = 'Create Transfer'
        
        if self.request.POST:
            context['formset'] = InventoryTransferLineFormSet(self.request.POST)
            context['extra_form'] = InventoryTransferExtraInfoForm(self.request.POST)
        else:
            context['formset'] = InventoryTransferLineFormSet()
            context['extra_form'] = InventoryTransferExtraInfoForm()
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        extra_form = context['extra_form']
        
        if formset.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                self.object = form.save()
                
                for field in extra_form.cleaned_data:
                    if hasattr(self.object, field):
                        setattr(self.object, field, extra_form.cleaned_data[field])
                self.object.save()
                
                # Save formset but set the warehouses first
                formset.instance = self.object
                for form in formset:
                    if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                        # Set the warehouses from the parent object before saving
                        form.instance.from_warehouse = self.object.from_warehouse
                        form.instance.to_warehouse = self.object.to_warehouse
            
                formset.save()
            
            messages.success(self.request, f'Inventory Transfer {self.object.pk} created successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Inventory:inventory_transfer_detail', kwargs={'pk': self.object.pk})

class InventoryTransferUpdateView(InventoryTransferAccessMixin, UpdateView):
    model = InventoryTransfer
    form_class = InventoryTransferForm
    template_name = 'common/formset-form.html'
    permission_required = 'Inventory.change_inventorytransfer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Inventory Transfer'
        context['subtitle'] = f'Edit transfer {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Inventory:inventory_transfer_list')
        context['submit_text'] = 'Update Transfer'
        
        if self.request.POST:
            context['formset'] = InventoryTransferLineFormSet(self.request.POST, instance=self.object)
            context['extra_form'] = InventoryTransferExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = InventoryTransferLineFormSet(instance=self.object)
            context['extra_form'] = InventoryTransferExtraInfoForm(instance=self.object)
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        extra_form = context['extra_form']
        
        if formset.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                self.object = form.save()
                
                for field in extra_form.cleaned_data:
                    if hasattr(self.object, field):
                        setattr(self.object, field, extra_form.cleaned_data[field])
                self.object.save()
                
                # Save formset but set the warehouses first
                formset.instance = self.object
                for form in formset:
                    if form.is_valid() and not form.cleaned_data.get('DELETE', False):
                        # Set the ware  and not form.cleaned_data.get('DELETE', False):
                        # Set the warehouses from the parent object before saving
                        form.instance.from_warehouse = self.object.from_warehouse
                        form.instance.to_warehouse = self.object.to_warehouse
            
                formset.save()
            
            messages.success(self.request, f'Inventory Transfer {self.object.pk} updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Inventory:inventory_transfer_detail', kwargs={'pk': self.object.pk})

class InventoryTransferDetailView(InventoryTransferAccessMixin, DetailView):
    model = InventoryTransfer
    template_name = 'common/formset-form.html'  
    context_object_name = 'inventory_transfer'
    permission_required = 'Inventory.view_inventorytransfer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Inventory Transfer Details'
        context['subtitle'] = f'Transfer {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Inventory:inventory_transfer_list')
        context['update_url'] = reverse_lazy('Inventory:inventory_transfer_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Inventory:inventory_transfer_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        context['form'] = InventoryTransferForm(instance=self.object)
        context['extra_form'] = InventoryTransferExtraInfoForm(instance=self.object)
        context['formset'] = InventoryTransferLineFormSet(instance=self.object)
        
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        for form_field in context['extra_form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        for form in context['formset'].forms:
            for field in form.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['disabled'] = 'disabled'
        
        return context

class InventoryTransferDeleteView(InventoryTransferAccessMixin, GenericDeleteView):
    model = InventoryTransfer
    success_url = reverse_lazy('Inventory:inventory_transfer_list')
    permission_required = 'Inventory.delete_inventorytransfer'

    def get_cancel_url(self):
        return reverse_lazy('Inventory:inventory_transfer_detail', kwargs={'pk': self.object.pk})        

class InventoryTransferExportView(InventoryTransferAccessMixin, BaseExportView):
    model = InventoryTransfer
    filename = "inventory_transfers.csv"
    permission_required = "Inventory.view_inventorytransfer"
    field_names = ["Document Number", "Posting Date", "From Warehouse", "To Warehouse", "Status", "Total Amount", "Created At"]

    def queryset_filter(self, request, queryset):
        return queryset

class InventoryTransferPrintView(InventoryTransferAccessMixin, DetailView):
    model = InventoryTransfer
    template_name = 'inventory/inventory_transfer_print.html'
    context_object_name = 'inventory_transfer'
    permission_required = 'Inventory.view_inventorytransfer'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Inventory Transfer'
        context['subtitle'] = f'Transfer {self.object.pk}'
        return context

class InventoryTransferBulkDeleteView(InventoryTransferAccessMixin, BaseBulkDeleteConfirmView):
    model = InventoryTransfer
    permission_required = "Inventory.delete_inventorytransfer"
    display_fields = ["id", "posting_date", "from_warehouse", "to_warehouse", "status"]
    cancel_url = reverse_lazy("Inventory:inventory_transfer_list")
    success_url = reverse_lazy("Inventory:inventory_transfer_list")