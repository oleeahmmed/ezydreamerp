from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect

from ..models import ProductionReceipt, ProductionReceiptLine, ProductionOrder
from ..forms.production_receipt_forms import (
    ProductionReceiptForm, ProductionReceiptExtraInfoForm,
    get_production_receipt_line_formset, ProductionReceiptFilterForm
)
from config.views import (
    GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView
)

class ProductionReceiptListView(GenericFilterView):
    model = ProductionReceipt
    template_name = 'production/production_receipt_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = ProductionReceiptFilterForm
    permission_required = 'Production.view_productionreceipt'
    
    def get_queryset(self):
        queryset = super().get_queryset().order_by('-document_date')

        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                receipt_number__icontains=search_query
            ) | queryset.filter(
                production_order__order_number__icontains=search_query
            ) | queryset.filter(
                production_order__product__name__icontains=search_query
            )

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Receipts'
        context['subtitle'] = 'Manage production receipts'
        context['create_url'] = reverse_lazy('Production:production_receipt_create')
        context['list_url'] = reverse_lazy('Production:production_receipt_list')
        context['print_url'] = reverse_lazy('Production:production_receipt_export')
        context['model_name'] = 'Production Receipt'
        
        context['can_create'] = self.request.user.has_perm('Production.add_productionreceipt')
        context['can_view'] = self.request.user.has_perm('Production.view_productionreceipt')
        context['can_update'] = self.request.user.has_perm('Production.change_productionreceipt')
        context['can_delete'] = self.request.user.has_perm('Production.delete_productionreceipt')
        context['can_print'] = self.request.user.has_perm('Production.view_productionreceipt')
        context['can_export'] = self.request.user.has_perm('Production.view_productionreceipt')
        
        return context

class ProductionReceiptCreateView(CreateView):
    model = ProductionReceipt
    form_class = ProductionReceiptForm
    template_name = 'production/production_receipt_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Production Receipt'
        context['subtitle'] = 'Create a new production receipt'
        context['cancel_url'] = reverse_lazy('Production:production_receipt_list')
        context['submit_text'] = 'Create Receipt'
        
        # Check if we're creating from a production order
        production_order_id = self.request.GET.get('production_order')
        if production_order_id and not self.request.POST:
            try:
                production_order = ProductionOrder.objects.get(pk=production_order_id)
                # Pre-populate the form with production order data
                form = context['form']
                form.initial['production_order'] = production_order
                form.initial['warehouse'] = production_order.warehouse
            except ProductionOrder.DoesNotExist:
                pass
        
        if self.request.POST:
            context['extra_form'] = ProductionReceiptExtraInfoForm(self.request.POST)
            context['formset'] = get_production_receipt_line_formset(request=self.request, data=self.request.POST)
        else:
            context['extra_form'] = ProductionReceiptExtraInfoForm()
            context['formset'] = get_production_receipt_line_formset(request=self.request)
            
            # If we have a production order, pre-populate the receipt line with the product
            if production_order_id and not self.request.POST:
                try:
                    production_order = ProductionOrder.objects.get(pk=production_order_id)
                    # Get the first form in the formset
                    if context['formset'].forms:
                        first_form = context['formset'].forms[0]
                        first_form.initial['item_code'] = production_order.product.code
                        first_form.initial['item_name'] = production_order.product.name
                        # Calculate remaining quantity to produce
                        remaining_qty = production_order.planned_quantity - production_order.produced_quantity
                        first_form.initial['quantity'] = remaining_qty if remaining_qty > 0 else 0
                        if production_order.product.sales_uom:
                            first_form.initial['uom'] = production_order.product.sales_uom.name
                except (ProductionOrder.DoesNotExist, AttributeError):
                    pass
        
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
            
            messages.success(self.request, f'Production Receipt {self.object.receipt_number} created successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Production:production_receipt_detail', kwargs={'pk': self.object.pk})

class ProductionReceiptUpdateView(UpdateView):
    model = ProductionReceipt
    form_class = ProductionReceiptForm
    template_name = 'production/production_receipt_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Production Receipt'
        context['subtitle'] = f'Edit receipt {self.object.receipt_number}'
        context['cancel_url'] = reverse_lazy('Production:production_receipt_detail', kwargs={'pk': self.object.pk})
        context['submit_text'] = 'Update Receipt'
        
        if self.request.POST:
            context['extra_form'] = ProductionReceiptExtraInfoForm(self.request.POST, instance=self.object)
            context['formset'] = get_production_receipt_line_formset(
                request=self.request, 
                data=self.request.POST, 
                instance=self.object
            )
        else:
            context['extra_form'] = ProductionReceiptExtraInfoForm(instance=self.object)
            context['formset'] = get_production_receipt_line_formset(
                request=self.request, 
                instance=self.object
            )
        
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
            
            messages.success(self.request, f'Production Receipt {self.object.receipt_number} updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Production:production_receipt_detail', kwargs={'pk': self.object.pk})

class ProductionReceiptDetailView(DetailView):
    model = ProductionReceipt
    template_name = 'production/production_receipt_form.html'
    context_object_name = 'production_receipt'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Production Receipt Details'
        context['subtitle'] = f'Receipt {self.object.receipt_number}'
        context['cancel_url'] = reverse_lazy('Production:production_receipt_list')
        context['update_url'] = reverse_lazy('Production:production_receipt_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Production:production_receipt_delete', kwargs={'pk': self.object.pk})
        context['print_url'] = reverse_lazy('Production:production_receipt_print', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = ProductionReceiptForm(instance=self.object)
        context['extra_form'] = ProductionReceiptExtraInfoForm(instance=self.object)
        context['formset'] = get_production_receipt_line_formset(instance=self.object)
        
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

class ProductionReceiptDeleteView(GenericDeleteView):
    model = ProductionReceipt
    success_url = reverse_lazy('Production:production_receipt_list')
    permission_required = 'Production.delete_productionreceipt'
    template_name = 'common/delete_confirm.html'

    def get_cancel_url(self):
        return reverse_lazy('Production:production_receipt_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = 'Production Receipt'
        return context

class ProductionReceiptExportView(BaseExportView):
    model = ProductionReceipt
    filename = "production_receipts.csv"
    permission_required = "Production.view_productionreceipt"
    field_names = ["Receipt Number", "Document Date", "Production Order", "Warehouse", "Status"]

class ProductionReceiptBulkDeleteView(BaseBulkDeleteConfirmView):
    model = ProductionReceipt
    permission_required = "Production.delete_productionreceipt"
    display_fields = ["receipt_number", "document_date", "production_order", "status"]
    cancel_url = reverse_lazy("Production:production_receipt_list")
    success_url = reverse_lazy("Production:production_receipt_list")

class ProductionReceiptPrintView(DetailView):
    model = ProductionReceipt
    template_name = 'production/production_receipt_print.html'
    context_object_name = 'production_receipt'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Print Production Receipt'
        context['subtitle'] = f'Receipt {self.object.receipt_number}'
        return context
