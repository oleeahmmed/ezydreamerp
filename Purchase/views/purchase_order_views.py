from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseRedirect
import csv
from io import StringIO
from decimal import Decimal

from ..models import PurchaseOrder, PurchaseOrderLine
from ..forms.purchase_order_forms import (
    PurchaseOrderForm, PurchaseOrderExtraInfoForm, 
    PurchaseOrderLineFormSet, PurchaseOrderFilterForm
)
from config.views import (
    GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView
)

class PurchaseOrderListView(GenericFilterView):
    model = PurchaseOrder
    template_name = 'purchase/purchase_order_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PurchaseOrderFilterForm
    permission_required = 'Purchase.view_purchaseorder'
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-document_date')

        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                id__icontains=search_query
            ) | queryset.filter(
                vendor__name__icontains=search_query
            ) | queryset.filter(
                remarks__icontains=search_query
            )

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Purchase Orders'
        context['subtitle'] = 'Manage purchase orders'
        context['create_url'] = reverse_lazy('Purchase:purchase_order_create')
        context['bulk_delete_url'] = reverse_lazy('Purchase:purchase_order_bulk_delete')
        
        context['can_create'] = self.request.user.has_perm('Purchase.add_purchaseorder')
        context['can_view'] = self.request.user.has_perm('Purchase.view_purchaseorder')
        context['can_update'] = self.request.user.has_perm('Purchase.change_purchaseorder')
        context['can_delete'] = self.request.user.has_perm('Purchase.delete_purchaseorder')
        context['can_print'] = self.request.user.has_perm('Purchase.view_purchaseorder')
        context['can_export'] = self.request.user.has_perm('Purchase.view_purchaseorder')
        context['can_bulk_delete'] = self.request.user.has_perm('Purchase.delete_purchaseorder')
        
        return context

class PurchaseOrderCreateView(CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'common/formset-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Purchase Order'
        context['subtitle'] = 'Create a new purchase order'
        context['cancel_url'] = reverse_lazy('Purchase:purchase_order_list')
        context['submit_text'] = 'Create Order'
        
        if self.request.POST:
            context['extra_form'] = PurchaseOrderExtraInfoForm(self.request.POST)
            context['formset'] = PurchaseOrderLineFormSet(self.request.POST)
        else:
            context['extra_form'] = PurchaseOrderExtraInfoForm()
            context['formset'] = PurchaseOrderLineFormSet()
        
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
                
                # Calculate total amount from line items
                total_amount = sum(
                    line.quantity * line.unit_price 
                    for line in self.object.lines.filter(is_active=True)
                )
                
                # Update the total amount
                self.object.total_amount = total_amount
                
                # Calculate payable amount (total - discount)
                self.object.payable_amount = total_amount - (self.object.discount_amount or 0)
                
                self.object.save()
            
            messages.success(self.request, f'Purchase Order {self.object.pk} created successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            # Print detailed error information
            print("Form errors:", form.errors)
            print("Extra form errors:", extra_form.errors)
            print("Formset errors:", formset.errors)
            if hasattr(formset, 'non_form_errors'):
                print("Formset non-form errors:", formset.non_form_errors())
            
            # Check each form in the formset
            for i, form_instance in enumerate(formset.forms):
                if form_instance.errors:
                    print(f"Formset form {i} errors:", form_instance.errors)
            
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Purchase:purchase_order_detail', kwargs={'pk': self.object.pk})

class PurchaseOrderUpdateView(UpdateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'common/formset-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Purchase Order'
        context['subtitle'] = f'Edit order {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Purchase:purchase_order_detail', kwargs={'pk': self.object.pk})
        context['submit_text'] = 'Update Order'
        
        if self.request.POST:
            context['extra_form'] = PurchaseOrderExtraInfoForm(self.request.POST, instance=self.object)
            context['formset'] = PurchaseOrderLineFormSet(self.request.POST, instance=self.object)
        else:
            context['extra_form'] = PurchaseOrderExtraInfoForm(instance=self.object)
            context['formset'] = PurchaseOrderLineFormSet(instance=self.object)
        
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
                
                # Calculate total amount from line items
                total_amount = sum(
                    line.quantity * line.unit_price 
                    for line in self.object.lines.filter(is_active=True)
                )
                
                # Update the total amount
                self.object.total_amount = total_amount
                
                # Calculate payable amount (total - discount)
                self.object.payable_amount = total_amount - (self.object.discount_amount or 0)
                
                self.object.save()
            
            messages.success(self.request, f'Purchase Order {self.object.pk} updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            # Print detailed error information
            print("Form errors:", form.errors)
            print("Extra form errors:", extra_form.errors)
            print("Formset errors:", formset.errors)
            if hasattr(formset, 'non_form_errors'):
                print("Formset non-form errors:", formset.non_form_errors())
            
            # Check each form in the formset
            for i, form_instance in enumerate(formset.forms):
                if form_instance.errors:
                    print(f"Formset form {i} errors:", form_instance.errors)
            
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Purchase:purchase_order_detail', kwargs={'pk': self.object.pk})

class PurchaseOrderDetailView(DetailView):
    model = PurchaseOrder
    template_name = 'common/formset-form.html'
    context_object_name = 'purchase_order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Purchase Order Details'
        context['subtitle'] = f'Order {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Purchase:purchase_order_list')
        context['update_url'] = reverse_lazy('Purchase:purchase_order_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Purchase:purchase_order_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add conversion buttons if order is not cancelled or closed
        if self.object.status not in ['Cancelled', 'Closed']:
            context['action_buttons'] = [
                {
                    'url': reverse_lazy('Purchase:convert_order_to_goods_receipt', kwargs={'pk': self.object.pk}),
                    'text': 'Convert to Goods Receipt',
                    'icon': 'truck',
                    'class': 'bg-green-100 text-green-700 hover:bg-green-200'
                },
                {
                    'url': reverse_lazy('Purchase:convert_order_to_invoice', kwargs={'pk': self.object.pk}),
                    'text': 'Convert to Invoice',
                    'icon': 'file-text',
                    'class': 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                },
                {
                    'url': reverse_lazy('Purchase:convert_order_to_return', kwargs={'pk': self.object.pk}),
                    'text': 'Convert to Return',
                    'icon': 'rotate-ccw',
                    'class': 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                }
            ]
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = PurchaseOrderForm(instance=self.object)
        context['extra_form'] = PurchaseOrderExtraInfoForm(instance=self.object)
        context['formset'] = PurchaseOrderLineFormSet(instance=self.object)
        
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

class PurchaseOrderDeleteView(GenericDeleteView):
    model = PurchaseOrder
    success_url = reverse_lazy('Purchase:purchase_order_list')
    permission_required = 'Purchase.delete_purchaseorder'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to Purchase Order detail view.
        """
        return reverse_lazy('Purchase:purchase_order_detail', kwargs={'pk': self.object.pk})

class PurchaseOrderExportView(BaseExportView):
    """
    Export view for Purchase Order.
    """
    model = PurchaseOrder
    filename = "purchase_orders.csv"
    permission_required = "Purchase.view_purchaseorder"
    field_names = ["ID", "Document Date", "Delivery Date", "Vendor", "Status", "Total Amount", "Discount Amount", "Payable Amount", "Created At"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        return queryset

class PurchaseOrderBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for Purchase Orders.
    """
    model = PurchaseOrder
    permission_required = "Purchase.delete_purchaseorder"
    display_fields = ["id", "document_date", "vendor", "status"]
    cancel_url = reverse_lazy("Purchase:purchase_order_list")
    success_url = reverse_lazy("Purchase:purchase_order_list")

class PurchaseOrderPrintView(DetailView):
    model = PurchaseOrder
    template_name = 'purchase/purchase_order_print.html'
    context_object_name = 'purchase_order'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Print Purchase Order'
        context['subtitle'] = f'Order {self.object.pk}'
        return context