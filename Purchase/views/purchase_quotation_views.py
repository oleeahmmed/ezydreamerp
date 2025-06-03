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

from ..models import PurchaseQuotation, PurchaseQuotationLine
from ..forms.purchase_quotation_forms import (
    PurchaseQuotationForm, PurchaseQuotationExtraInfoForm, 
    PurchaseQuotationLineFormSet, PurchaseQuotationFilterForm
)
from config.views import (
    GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView
)

class PurchaseQuotationListView(GenericFilterView):
    model = PurchaseQuotation
    template_name = 'purchase/purchase_quotation_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PurchaseQuotationFilterForm
    permission_required = 'Purchase.view_purchasequotation'
    
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
        context['title'] = 'Purchase Quotations'
        context['subtitle'] = 'Manage purchase quotations'
        context['create_url'] = reverse_lazy('Purchase:purchase_quotation_create')
        context['bulk_delete_url'] = reverse_lazy('Purchase:purchase_quotation_bulk_delete')
        
        context['can_create'] = self.request.user.has_perm('Purchase.add_purchasequotation')
        context['can_view'] = self.request.user.has_perm('Purchase.view_purchasequotation')
        context['can_update'] = self.request.user.has_perm('Purchase.change_purchasequotation')
        context['can_delete'] = self.request.user.has_perm('Purchase.delete_purchasequotation')
        context['can_print'] = self.request.user.has_perm('Purchase.view_purchasequotation')
        context['can_export'] = self.request.user.has_perm('Purchase.view_purchasequotation')
        context['can_bulk_delete'] = self.request.user.has_perm('Purchase.delete_purchasequotation')
        
        return context

class PurchaseQuotationCreateView(CreateView):
    model = PurchaseQuotation
    form_class = PurchaseQuotationForm
    template_name = 'common/formset-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Purchase Quotation'
        context['subtitle'] = 'Create a new purchase quotation'
        context['cancel_url'] = reverse_lazy('Purchase:purchase_quotation_list')
        context['submit_text'] = 'Create Quotation'
        
        if self.request.POST:
            context['extra_form'] = PurchaseQuotationExtraInfoForm(self.request.POST)
            context['formset'] = PurchaseQuotationLineFormSet(self.request.POST)
        else:
            context['extra_form'] = PurchaseQuotationExtraInfoForm()
            context['formset'] = PurchaseQuotationLineFormSet()
        
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
                
                # Calculate due amount (payable - paid)
                self.object.due_amount = self.object.payable_amount - (self.object.paid_amount or 0)
                
                self.object.save()
            
            messages.success(self.request, f'Purchase Quotation {self.object.pk} created successfully.')
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
        return reverse_lazy('Purchase:purchase_quotation_detail', kwargs={'pk': self.object.pk})

class PurchaseQuotationUpdateView(UpdateView):
    model = PurchaseQuotation
    form_class = PurchaseQuotationForm
    template_name = 'common/formset-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Purchase Quotation'
        context['subtitle'] = f'Edit quotation {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Purchase:purchase_quotation_detail', kwargs={'pk': self.object.pk})
        context['submit_text'] = 'Update Quotation'
        
        if self.request.POST:
            context['extra_form'] = PurchaseQuotationExtraInfoForm(self.request.POST, instance=self.object)
            context['formset'] = PurchaseQuotationLineFormSet(self.request.POST, instance=self.object)
        else:
            context['extra_form'] = PurchaseQuotationExtraInfoForm(instance=self.object)
            context['formset'] = PurchaseQuotationLineFormSet(instance=self.object)
        
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
                
                # Calculate due amount (payable - paid)
                self.object.due_amount = self.object.payable_amount - (self.object.paid_amount or 0)
                
                self.object.save()
            
            messages.success(self.request, f'Purchase Quotation {self.object.pk} updated successfully.')
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
        return reverse_lazy('Purchase:purchase_quotation_detail', kwargs={'pk': self.object.pk})

class PurchaseQuotationDetailView(DetailView):
    model = PurchaseQuotation
    template_name = 'common/formset-form.html'
    context_object_name = 'purchase_quotation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Purchase Quotation Details'
        context['subtitle'] = f'Quotation {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Purchase:purchase_quotation_list')
        context['update_url'] = reverse_lazy('Purchase:purchase_quotation_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Purchase:purchase_quotation_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add conversion button if quotation is not expired, cancelled, or already converted
        if self.object.status not in ['Expired', 'Cancelled', 'Converted']:
            context['action_buttons'] = [
                {
                    'url': reverse_lazy('Purchase:convert_quotation_to_order', kwargs={'pk': self.object.pk}),
                    'text': 'Convert to Order',
                    'icon': 'file-text',
                    'class': 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                }
            ]
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = PurchaseQuotationForm(instance=self.object)
        context['extra_form'] = PurchaseQuotationExtraInfoForm(instance=self.object)
        context['formset'] = PurchaseQuotationLineFormSet(instance=self.object)
        
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

class PurchaseQuotationDeleteView(GenericDeleteView):
    model = PurchaseQuotation
    success_url = reverse_lazy('Purchase:purchase_quotation_list')
    permission_required = 'Purchase.delete_purchasequotation'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to Purchase Quotation detail view.
        """
        return reverse_lazy('Purchase:purchase_quotation_detail', kwargs={'pk': self.object.pk})

class PurchaseQuotationExportView(BaseExportView):
    """
    Export view for Purchase Quotation.
    """
    model = PurchaseQuotation
    filename = "purchase_quotations.csv"
    permission_required = "Purchase.view_purchasequotation"
    field_names = ["ID", "Document Date", "Vendor", "Status", "Total Amount", "Discount Amount", "Payable Amount", "Paid Amount", "Due Amount", "Created At"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        return queryset

class PurchaseQuotationBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for Purchase Quotations.
    """
    model = PurchaseQuotation
    permission_required = "Purchase.delete_purchasequotation"
    display_fields = ["id", "document_date", "vendor", "status"]
    cancel_url = reverse_lazy("Purchase:purchase_quotation_list")
    success_url = reverse_lazy("Purchase:purchase_quotation_list")

class PurchaseQuotationPrintView(DetailView):
    model = PurchaseQuotation
    template_name = 'purchase/purchase_quotation_print.html'
    context_object_name = 'purchase_quotation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Print Purchase Quotation'
        context['subtitle'] = f'Quotation {self.object.pk}'
        return context