from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

from ..models import SalesQuotation, SalesQuotationLine, SalesOrder, SalesOrderLine
from ..forms.sales_quotation_forms import SalesQuotationForm, SalesQuotationExtraInfoForm, SalesQuotationLineFormSet, SalesQuotationFilterForm


class SalesQuotationListView(GenericFilterView):
    model = SalesQuotation
    template_name = 'sales/sales_quotation_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Sales.view_salesquotation'

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-document_date', '-id')


        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                id__icontains=search_query
            ) | queryset.filter(
                customer__name__icontains=search_query
            ) | queryset.filter(
                remarks__icontains=search_query
            )

        return queryset

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sales Quotations'
        context['subtitle'] = 'Manage sales quotations'
        context['create_url'] = reverse_lazy('Sales:sales_quotation_create')
        
        context['can_create'] = self.request.user.has_perm('Sales.add_salesquotation')
        context['can_view'] = self.request.user.has_perm('Sales.view_salesquotation')
        context['can_update'] = self.request.user.has_perm('Sales.change_salesquotation')
        context['can_delete'] = self.request.user.has_perm('Sales.delete_salesquotation')
        context['can_print'] = self.request.user.has_perm('Sales.view_salesquotation')
        context['can_export'] = self.request.user.has_perm('Sales.view_salesquotation')
        context['can_bulk_delete'] = self.request.user.has_perm('Sales.delete_salesquotation')
        
        return context

class SalesQuotationCreateView(CreateView):
    model = SalesQuotation
    form_class = SalesQuotationForm
    template_name = 'common/formset-form.html'
    permission_required = 'Sales.add_salesquotation'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.add_salesquotation'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # Pass request to form
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Sales Quotation'
        context['subtitle'] = 'Create a new sales quotation'
        context['cancel_url'] = reverse_lazy('Sales:sales_quotation_list')
        context['submit_text'] = 'Create Quotation'
        
        if self.request.POST:
            context['formset'] = SalesQuotationLineFormSet(self.request.POST)
            context['extra_form'] = SalesQuotationExtraInfoForm(self.request.POST)
        else:
            context['formset'] = SalesQuotationLineFormSet()
            context['extra_form'] = SalesQuotationExtraInfoForm()
            
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
            
            messages.success(self.request, f'Sales Quotation {self.object.pk} created successfully.')
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
        # Return to create URL after successful creation
        return reverse_lazy('Sales:sales_quotation_create')

class SalesQuotationUpdateView(UpdateView):
    model = SalesQuotation
    form_class = SalesQuotationForm
    template_name = 'common/formset-form.html'
    permission_required = 'Sales.change_salesquotation'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.change_salesquotation'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # Pass request to form
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Sales Quotation'
        context['subtitle'] = f'Edit quotation {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Sales:sales_quotation_list')
        context['submit_text'] = 'Update Quotation'
        
        if self.request.POST:
            context['formset'] = SalesQuotationLineFormSet(self.request.POST, instance=self.object)
            context['extra_form'] = SalesQuotationExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = SalesQuotationLineFormSet(instance=self.object)
            context['extra_form'] = SalesQuotationExtraInfoForm(instance=self.object)
            
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
            
            messages.success(self.request, f'Sales Quotation {self.object.pk} updated successfully.')
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
        # Return to update URL after successful update
        return reverse_lazy('Sales:sales_quotation_update', kwargs={'pk': self.object.pk})

class SalesQuotationDetailView(DetailView):
    model = SalesQuotation
    template_name = 'common/formset-form.html'  
    context_object_name = 'sales_quotation'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.view_salesquotation'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sales Quotation Details'
        context['subtitle'] = f'Quotation {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Sales:sales_quotation_list')
        context['update_url'] = reverse_lazy('Sales:sales_quotation_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Sales:sales_quotation_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add conversion button if quotation is not expired, cancelled, or already converted
        if self.object.status not in ['Expired', 'Cancelled', 'Converted']:
            context['action_buttons'] = [
                {
                    'url': reverse_lazy('Sales:convert_quotation_to_order', kwargs={'pk': self.object.pk}),
                    'text': 'Convert to Order',
                    'icon': 'file-text',
                    'class': 'bg-green-100 text-green-700 hover:bg-green-200'
                }
            ]
            
        # Add form and formset in read-only mode for the detail view
        context['form'] = SalesQuotationForm(instance=self.object, request=self.request)
        context['extra_form'] = SalesQuotationExtraInfoForm(instance=self.object)
        context['formset'] = SalesQuotationLineFormSet(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        # for form_field in context['extra_form'].fields.values  = 'disabled'
        for form_field in context['extra_form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        # Make formset fields read-only
        for form in context['formset'].forms:
            for field in form.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['disabled'] = 'disabled'
        
        return context

class SalesQuotationDeleteView(GenericDeleteView):
    model = SalesQuotation
    success_url = reverse_lazy('Sales:sales_quotation_list')
    permission_required = 'Sales.delete_salesquotation'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to Sales Quotation detail view.
        """
        return reverse_lazy('Sales:sales_quotation_detail', kwargs={'pk': self.object.pk})        

class SalesQuotationExportView(BaseExportView):
    """
    Export view for Sales Quotation.
    """
    model = SalesQuotation
    filename = "sales_quotations.csv"
    permission_required = "Sales.view_salesquotation"
    field_names = ["ID", "Document Date", "Valid Until", "Customer", "Status", "Total Amount", "Created At"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        return queryset

class SalesQuotationPrintView(DetailView):
    model = SalesQuotation
    template_name = 'sales/sales_quotation_print.html'
    context_object_name = 'sales_quotation'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.view_salesquotation'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sales Quotation'
        context['subtitle'] = f'Quotation {self.object.pk}'
        return context

class SalesQuotationBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for Sales Quotations.
    """
    model = SalesQuotation
    permission_required = "Sales.delete_salesquotation"
    display_fields = ["id", "document_date", "customer", "status"]
    cancel_url = reverse_lazy("Sales:sales_quotation_list")
    success_url = reverse_lazy("Sales:sales_quotation_list")