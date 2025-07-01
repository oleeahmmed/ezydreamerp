from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied

from ..models import GoodsReceipt
from ..forms import GoodsReceiptForm, GoodsReceiptExtraInfoForm, GoodsReceiptLineFormSet

from config.views import GenericFilterView

class GoodsReceiptAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class GoodsReceiptListView(GoodsReceiptAccessMixin, GenericFilterView):
    model = GoodsReceipt
    template_name = 'inventory/goods_receipt_list.html'
    context_object_name = 'objects'  # Changed to 'objects' to match the template
    paginate_by = 10
    permission_required = 'Inventory.view_goodsreceipt'
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-id')
        
        # Filter by search query if provided
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
        context['title'] = 'Goods Receipts'
        context['subtitle'] = 'Manage inventory receipts'
        context['create_url'] = reverse_lazy('Inventory:goods_receipt_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Inventory.add_goodsreceipt')
        context['can_view'] = self.request.user.has_perm('Inventory.view_goodsreceipt')
        context['can_update'] = self.request.user.has_perm('Inventory.change_goodsreceipt')
        context['can_delete'] = self.request.user.has_perm('Inventory.delete_goodsreceipt')
        context['can_print'] = self.request.user.has_perm('Inventory.view_goodsreceipt')
        context['can_export'] = self.request.user.has_perm('Inventory.view_goodsreceipt')
        context['can_bulk_delete'] = self.request.user.has_perm('Inventory.delete_goodsreceipt')
        
        return context

class GoodsReceiptCreateView(GoodsReceiptAccessMixin, CreateView):
    model = GoodsReceipt
    form_class = GoodsReceiptForm
    template_name = 'common/formset-form.html'
    permission_required = 'Inventory.add_goodsreceipt'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Goods Receipt'
        context['subtitle'] = 'Record new inventory receipt'
        context['cancel_url'] = reverse_lazy('Inventory:goods_receipt_list')
        context['submit_text'] = 'Create Receipt'
        
        if self.request.POST:
            context['formset'] = GoodsReceiptLineFormSet(self.request.POST)
            context['extra_form'] = GoodsReceiptExtraInfoForm(self.request.POST)
        else:
            context['formset'] = GoodsReceiptLineFormSet()
            context['extra_form'] = GoodsReceiptExtraInfoForm()
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        extra_form = context['extra_form']
        
        if formset.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                # Save the main form
                self.object = form.save()
                
                # Update with extra form data
                for field in extra_form.cleaned_data:
                    if hasattr(self.object, field):
                        setattr(self.object, field, extra_form.cleaned_data[field])
                self.object.save()
                
                # Save the formset
                formset.instance = self.object
                formset.save()
            
            messages.success(self.request, f'Goods Receipt {self.object.pk} created successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        # Return to create URL after successful creation
        return reverse_lazy('Inventory:goods_receipt_create')

class GoodsReceiptUpdateView(GoodsReceiptAccessMixin, UpdateView):
    model = GoodsReceipt
    form_class = GoodsReceiptForm
    template_name = 'common/formset-form.html'
    permission_required = 'Inventory.change_goodsreceipt'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Goods Receipt'
        context['subtitle'] = f'Edit receipt {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Inventory:goods_receipt_list')
        context['submit_text'] = 'Update Receipt'
        
        if self.request.POST:
            context['formset'] = GoodsReceiptLineFormSet(self.request.POST, instance=self.object)
            context['extra_form'] = GoodsReceiptExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = GoodsReceiptLineFormSet(instance=self.object)
            context['extra_form'] = GoodsReceiptExtraInfoForm(instance=self.object)
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        extra_form = context['extra_form']
        
        if formset.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                # Save the main form
                self.object = form.save()
                
                # Update with extra form data
                for field in extra_form.cleaned_data:
                    if hasattr(self.object, field):
                        setattr(self.object, field, extra_form.cleaned_data[field])
                self.object.save()
                
                # Save the formset
                formset.instance = self.object
                formset.save()
            
            messages.success(self.request, f'Goods Receipt {self.object.pk} updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        # Return to update URL after successful update
        return reverse_lazy('Inventory:goods_receipt_update', kwargs={'pk': self.object.pk})

class GoodsReceiptDetailView(GoodsReceiptAccessMixin, DetailView):
    model = GoodsReceipt
    template_name = 'common/formset-form.html'  
    context_object_name = 'goods_receipt'
    permission_required = 'Inventory.view_goodsreceipt'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Goods Receipt Details'
        context['subtitle'] = f'Receipt {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Inventory:goods_receipt_list')
        context['update_url'] = reverse_lazy('Inventory:goods_receipt_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Inventory:goods_receipt_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = GoodsReceiptForm(instance=self.object)
        context['extra_form'] = GoodsReceiptExtraInfoForm(instance=self.object)
        context['formset'] = GoodsReceiptLineFormSet(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        for form_field in context['extra_form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        # Make formset fields read-only
        for form in context['formset'].forms:
            for field in form.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['disabled'] = 'disabled'
        
        return context

from config.views import GenericDeleteView
class GoodsReceiptDeleteView(GoodsReceiptAccessMixin, GenericDeleteView):
    model = GoodsReceipt
    success_url = reverse_lazy('Inventory:goods_receipt_list')
    permission_required = 'Inventory.delete_goodsreceipt'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to Goods Receipt detail view.
        """
        return reverse_lazy('Inventory:goods_receipt_detail', kwargs={'pk': self.object.pk})        

from config.views import BaseExportView
class GoodsReceiptExportView(GoodsReceiptAccessMixin, BaseExportView):
    """
    Export view for Goods Receipt.
    """
    model = GoodsReceipt
    filename = "goods_receipts.csv"
    permission_required = "Inventory.view_goodsreceipt"
    field_names = ["Document Number", "Posting Date", "Supplier", "Status", "Total Amount", "Created At"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        return queryset

class GoodsReceiptPrintView(GoodsReceiptAccessMixin, DetailView):
    model = GoodsReceipt
    template_name = 'inventory/goods_receipt_print.html'
    context_object_name = 'goods_receipt'
    permission_required = 'Inventory.view_goodsreceipt'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Goods Receipt'
        context['subtitle'] = f'Receipt {self.object.pk}'
        return context

from config.views import BaseBulkDeleteConfirmView
class GoodsReceiptBulkDeleteView(GoodsReceiptAccessMixin, BaseBulkDeleteConfirmView):
    """
    Bulk delete view for Goods Receipts.
    """
    model = GoodsReceipt
    permission_required = "Inventory.delete_goodsreceipt"
    display_fields = ["id", "posting_date", "supplier", "status"]
    cancel_url = reverse_lazy("Inventory:goods_receipt_list")  # Manually setting the cancel URL
    success_url = reverse_lazy("Inventory:goods_receipt_list")  # Redirect after successful delete