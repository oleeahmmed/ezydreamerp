from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.forms import inlineformset_factory

from ..models import SalesOrder, SalesOrderLine, Delivery, DeliveryLine
from ..forms.sales_order_forms import SalesOrderForm, SalesOrderExtraInfoForm, SalesOrderLineFormSet, SalesOrderFilterForm,SalesOrderLineForm

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class SalesOrderListView(GenericFilterView):
    model = SalesOrder
    template_name = 'sales/sales_order_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Sales.view_salesorder'

    # def get_queryset(self):
    #     queryset = super().get_queryset().order_by('-document_date')

    #     search_query = self.request.GET.get('search', '')
    #     if search_query:
    #         queryset = queryset.filter(
    #             id__icontains=search_query
    #         ) | queryset.filter(
    #             customer__name__icontains=search_query
    #         ) | queryset.filter(
    #             remarks__icontains=search_query
    #         ) | queryset.filter(
    #             sales_employee__name__icontains=search_query
    #         ) | queryset.filter(
    #             status__icontains=search_query
    #         )

    #     return queryset

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-document_date', '-id')

    
        # Restrict non-superusers to their own sales orders
        user = self.request.user
        if not user.is_superuser:
            if hasattr(user, 'sales_employee'):
                queryset = queryset.filter(sales_employee=user.sales_employee)
            else:
                # If the user is not a sales employee, return no results
                queryset = queryset.none()
    
        # Apply search filter if any
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                id__icontains=search_query
            ) | queryset.filter(
                customer__name__icontains=search_query
            ) | queryset.filter(
                remarks__icontains=search_query
            ) | queryset.filter(
                sales_employee__name__icontains=search_query
            ) | queryset.filter(
                status__icontains=search_query
            )
    
        return queryset

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sales Orders'
        context['subtitle'] = 'Manage sales orders'
        context['create_url'] = reverse_lazy('Sales:sales_order_create')
        
        context['can_create'] = self.request.user.has_perm('Sales.add_salesorder')
        context['can_view'] = self.request.user.has_perm('Sales.view_salesorder')
        context['can_update'] = self.request.user.has_perm('Sales.change_salesorder')
        context['can_delete'] = self.request.user.has_perm('Sales.delete_salesorder')
        context['can_print'] = self.request.user.has_perm('Sales.view_salesorder')
        context['can_export'] = self.request.user.has_perm('Sales.view_salesorder')
        context['can_bulk_delete'] = self.request.user.has_perm('Sales.delete_salesorder')
        
        return context

class SalesOrderCreateView(CreateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'common/formset-form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        prefill_data = self.request.session.pop('prefill_order_data', None)
        if prefill_data:
            self.prefill_lines = prefill_data.get('lines', [])
            self.prefill_quotation = prefill_data.get('quotation_id')
            for key, value in prefill_data.items():
                if key not in ['lines', 'quotation_id']:
                    initial[key] = value
            initial['quotation'] = self.prefill_quotation  
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Sales Order'
        context['subtitle'] = 'Create a new sales order'
        context['cancel_url'] = reverse_lazy('Sales:sales_order_list')
        context['submit_text'] = 'Create Order'

        if self.request.POST:
            context['formset'] = SalesOrderLineFormSet(self.request.POST)
            context['extra_form'] = SalesOrderExtraInfoForm(self.request.POST)
        else:
            initial_lines = getattr(self, 'prefill_lines', [])
            extra_count = len(initial_lines) if initial_lines else 1 
            dynamic_formset = inlineformset_factory(
                SalesOrder,
                SalesOrderLine,
                form=SalesOrderLineForm,
                extra=extra_count,
                can_delete=True
            )
            context['formset'] = dynamic_formset(initial=initial_lines)
            context['extra_form'] = SalesOrderExtraInfoForm(initial=self.get_initial())

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        extra_form = context['extra_form']

        if formset.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                self.object = form.save(commit=False)

                if hasattr(self, 'prefill_quotation'):
                    self.object.quotation_id = self.prefill_quotation

                for field, value in extra_form.cleaned_data.items():
                    if hasattr(self.object, field):
                        setattr(self.object, field, value)

                self.object.save()

                formset.instance = self.object
                formset.save()

                if hasattr(self, 'prefill_quotation'):
                    quotation = SalesQuotation.objects.get(pk=self.prefill_quotation)
                    quotation.status = 'Converted'
                    quotation.save(update_fields=['status'])

            messages.success(self.request, f"Sales Order {self.object.pk} created successfully.")
            return HttpResponseRedirect(self.get_success_url())

        return self.form_invalid(form)


    def get_success_url(self):
        return reverse_lazy('Sales:sales_order_create')



class SalesOrderUpdateView(UpdateView):
    model = SalesOrder
    form_class = SalesOrderForm
    template_name = 'common/formset-form.html'
    permission_required = 'Sales.change_salesorder'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.change_salesorder'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # Pass request to form
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Sales Order'
        context['subtitle'] = f'Edit order {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Sales:sales_order_list')
        context['submit_text'] = 'Update Order'
        
        if self.request.POST:
            context['formset'] = SalesOrderLineFormSet(self.request.POST, instance=self.object)
            context['extra_form'] = SalesOrderExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = SalesOrderLineFormSet(instance=self.object)
            context['extra_form'] = SalesOrderExtraInfoForm(instance=self.object)
            
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
            
            messages.success(self.request, f'Sales Order {self.object.pk} updated successfully.')
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
        return reverse_lazy('Sales:sales_order_update', kwargs={'pk': self.object.pk})

class SalesOrderDetailView(DetailView):
    model = SalesOrder
    template_name = 'common/formset-form.html'  
    context_object_name = 'sales_order'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.view_salesorder'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sales Order Details'
        context['subtitle'] = f'Order {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Sales:sales_order_list')
        context['update_url'] = reverse_lazy('Sales:sales_order_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Sales:sales_order_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add conversion buttons if order is not cancelled or closed
        if self.object.status not in ['Cancelled', 'Closed']:
            context['action_buttons'] = [
                {
                    'url': reverse_lazy('Sales:convert_order_to_delivery', kwargs={'pk': self.object.pk}),
                    'text': 'Convert to Delivery',
                    'icon': 'truck',
                    'class': 'bg-green-100 text-green-700 hover:bg-green-200'
                },
                # {
                #     'url': reverse_lazy('Sales:convert_order_to_invoice', kwargs={'pk': self.object.pk}),
                #     'text': 'Convert to Invoice',
                #     'icon': 'file-text',
                #     'class': 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                # }
            ]
        
        # Add form and formset in read-only mode for the detail view
        self.object.refresh_from_db()
        context['form'] = SalesOrderForm(instance=self.object, request=self.request)
        context['extra_form'] = SalesOrderExtraInfoForm(instance=self.object)
        context['formset'] = SalesOrderLineFormSet(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        for form_field in context['extra_form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            # form_field.widget.attrs['disabled'] = 'disabled'
            
        # Make formset fields read-only
        for form in context['formset'].forms:
            for field in form.fields.values():
                field.widget.attrs['readonly'] = True
                # field.widget.attrs['disabled'] = 'disabled'
        
        return context

class SalesOrderDeleteView(GenericDeleteView):
    model = SalesOrder
    success_url = reverse_lazy('Sales:sales_order_list')
    permission_required = 'Sales.delete_salesorder'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to Sales Order detail view.
        """
        return reverse_lazy('Sales:sales_order_detail', kwargs={'pk': self.object.pk})        

class SalesOrderExportView(BaseExportView):
    """
    Export view for Sales Order.
    """
    model = SalesOrder
    filename = "sales_orders.csv"
    permission_required = "Sales.view_salesorder"
    field_names = ["ID", "Document Date", "Delivery Date", "Customer", "Status", "Total Amount", "Created At"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        return queryset

class SalesOrderPrintView(DetailView):
    model = SalesOrder
    template_name = 'sales/sales_order_print.html'
    context_object_name = 'sales_order'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.view_salesorder'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sales Order'
        context['subtitle'] = f'Order {self.object.pk}'
        return context

class SalesOrderBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for Sales Orders.
    """
    model = SalesOrder
    permission_required = "Sales.delete_salesorder"
    display_fields = ["id", "document_date", "customer", "status"]
    cancel_url = reverse_lazy("Sales:sales_order_list")
    success_url = reverse_lazy("Sales:sales_order_list")


