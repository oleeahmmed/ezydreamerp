from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect

from ..models import APInvoice, APInvoiceLine, PurchaseOrder, GoodsReceiptPo
from ..forms import APInvoiceForm, APInvoiceExtraInfoForm, APInvoiceLineFormSet, APInvoiceFilterForm
from ..forms.ap_invoice_forms import copy_from_purchase_order, copy_from_goods_receipt

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class APInvoiceListView(GenericFilterView):
    model = APInvoice
    template_name = 'purchase/apinvoice_list.html'
    context_object_name = 'objects'
    paginate_by = 10

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
        context['title'] = 'AP Invoices'
        context['subtitle'] = 'Manage accounts payable invoices'
        context['create_url'] = reverse_lazy('Purchase:apinvoice_create')
        
        context['can_create'] = self.request.user.has_perm('Purchase.add_apinvoice')
        context['can_view'] = self.request.user.has_perm('Purchase.view_apinvoice')
        context['can_update'] = self.request.user.has_perm('Purchase.change_apinvoice')
        context['can_delete'] = self.request.user.has_perm('Purchase.delete_apinvoice')
        context['can_print'] = self.request.user.has_perm('Purchase.view_apinvoice')
        context['can_export'] = self.request.user.has_perm('Purchase.view_apinvoice')
        context['can_bulk_delete'] = self.request.user.has_perm('Purchase.delete_apinvoice')
        
        return context

class APInvoiceCreateView(CreateView):
    model = APInvoice
    form_class = APInvoiceForm
    template_name = 'common/formset-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create AP Invoice'
        context['subtitle'] = 'Create a new accounts payable invoice'
        context['cancel_url'] = reverse_lazy('Purchase:apinvoice_list')
        context['submit_text'] = 'Create Invoice'
        
        if self.request.POST:
            context['formset'] = APInvoiceLineFormSet(self.request.POST)
            context['extra_form'] = APInvoiceExtraInfoForm(self.request.POST)
        else:
            context['formset'] = APInvoiceLineFormSet()
            context['extra_form'] = APInvoiceExtraInfoForm()
            
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
                
                # Update purchase order status if needed
                if self.object.purchase_order:
                    self._update_purchase_order_status(self.object.purchase_order)
            
            messages.success(self.request, f'AP Invoice {self.object.pk} created successfully.')
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
    
    def _update_purchase_order_status(self, purchase_order):
        """Update the purchase order status based on invoice status"""
        # Check if all order lines have been fully invoiced
        order_lines = purchase_order.lines.all()
        all_invoiced = True
        
        for line in order_lines:
            invoiced_qty = sum(il.quantity for il in line.invoice_lines.all())
            if invoiced_qty < line.quantity:
                all_invoiced = False
                break
        
        if all_invoiced:
            purchase_order.status = 'Invoiced'
        else:
            # Check if any lines have been invoiced
            any_invoiced = False
            for line in order_lines:
                if line.invoice_lines.exists():
                    any_invoiced = True
                    break
            
            if any_invoiced:
                purchase_order.status = 'Partially Invoiced'
        
        purchase_order.save(update_fields=['status'])
    
    def get_success_url(self):
        # Return to create URL after successful creation
        return reverse_lazy('Purchase:apinvoice_create')

class APInvoiceUpdateView(UpdateView):
    model = APInvoice
    form_class = APInvoiceForm
    template_name = 'common/formset-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update AP Invoice'
        context['subtitle'] = f'Edit invoice {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Purchase:apinvoice_list')
        context['submit_text'] = 'Update Invoice'
        
        if self.request.POST:
            context['formset'] = APInvoiceLineFormSet(self.request.POST, instance=self.object)
            context['extra_form'] = APInvoiceExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = APInvoiceLineFormSet(instance=self.object)
            context['extra_form'] = APInvoiceExtraInfoForm(instance=self.object)
            
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
                
                # Update purchase order status if needed
                if self.object.purchase_order:
                    self._update_purchase_order_status(self.object.purchase_order)
            
            messages.success(self.request, f'AP Invoice {self.object.pk} updated successfully.')
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
    
    def _update_purchase_order_status(self, purchase_order):
        """Update the purchase order status based on invoice status"""
        # Check if all order lines have been fully invoiced
        order_lines = purchase_order.lines.all()
        all_invoiced = True
        
        for line in order_lines:
            invoiced_qty = sum(il.quantity for il in line.invoice_lines.all())
            if invoiced_qty < line.quantity:
                all_invoiced = False
                break
        
        if all_invoiced:
            purchase_order.status = 'Invoiced'
        else:
            # Check if any lines have been invoiced
            any_invoiced = False
            for line in order_lines:
                if line.invoice_lines.exists():
                    any_invoiced = True
                    break
            
            if any_invoiced:
                purchase_order.status = 'Partially Invoiced'
        
        purchase_order.save(update_fields=['status'])
    
    def get_success_url(self):
        # Return to update URL after successful update
        return reverse_lazy('Purchase:apinvoice_update', kwargs={'pk': self.object.pk})

class APInvoiceDetailView(DetailView):
    model = APInvoice
    template_name = 'common/formset-form.html'  
    context_object_name = 'apinvoice'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'AP Invoice Details'
        context['subtitle'] = f'Invoice {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Purchase:apinvoice_list')
        context['update_url'] = reverse_lazy('Purchase:apinvoice_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Purchase:apinvoice_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = APInvoiceForm(instance=self.object)
        context['extra_form'] = APInvoiceExtraInfoForm(instance=self.object)
        context['formset'] = APInvoiceLineFormSet(instance=self.object)
        
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

class APInvoiceDeleteView(GenericDeleteView):
    model = APInvoice
    success_url = reverse_lazy('Purchase:apinvoice_list')
    permission_required = 'Purchase.delete_apinvoice'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to AP Invoice detail view.
        """
        return reverse_lazy('Purchase:apinvoice_detail', kwargs={'pk': self.object.pk})        

class APInvoiceExportView(BaseExportView):
    """
    Export view for AP Invoice.
    """
    model = APInvoice
    filename = "ap_invoices.csv"
    permission_required = "Purchase.view_apinvoice"
    field_names = ["ID", "Document Date", "Due Date", "Vendor", "Status", "Total Amount", "Created At"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        return queryset

class APInvoiceBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for AP Invoices.
    """
    model = APInvoice
    permission_required = "Purchase.delete_apinvoice"
    display_fields = ["id", "document_date", "vendor", "status"]
    cancel_url = reverse_lazy("Purchase:apinvoice_list")
    success_url = reverse_lazy("Purchase:apinvoice_list")

class APInvoicePrintView(DetailView):
    model = APInvoice
    template_name = 'purchase/apinvoice_print.html'
    context_object_name = 'apinvoice'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'AP Invoice'
        context['subtitle'] = f'Invoice {self.object.pk}'
        return context

