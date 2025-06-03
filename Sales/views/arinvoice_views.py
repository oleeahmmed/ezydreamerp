from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect

from ..models import ARInvoice, ARInvoiceLine, SalesOrder, Delivery
from ..forms.arinvoice_forms import ARInvoiceForm, ARInvoiceExtraInfoForm, ARInvoiceLineFormSet, ARInvoiceFilterForm,ARInvoiceLineForm
from django.forms import inlineformset_factory

from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class ARInvoiceListView(GenericFilterView):
    model = ARInvoice
    template_name = 'sales/arinvoice_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Sales.view_arinvoice'

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-document_date', '-id')
    
        # Restrict non-superusers to their own invoices
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
        context['title'] = 'AR Invoices'
        context['subtitle'] = 'Manage accounts receivable invoices'
        context['create_url'] = reverse_lazy('Sales:arinvoice_create')
        
        context['can_create'] = self.request.user.has_perm('Sales.add_arinvoice')
        context['can_view'] = self.request.user.has_perm('Sales.view_arinvoice')
        context['can_update'] = self.request.user.has_perm('Sales.change_arinvoice')
        context['can_delete'] = self.request.user.has_perm('Sales.delete_arinvoice')
        context['can_print'] = self.request.user.has_perm('Sales.view_arinvoice')
        context['can_export'] = self.request.user.has_perm('Sales.view_arinvoice')
        context['can_bulk_delete'] = self.request.user.has_perm('Sales.delete_arinvoice')
        
        return context

class ARInvoiceCreateView(CreateView):
    model = ARInvoice
    form_class = ARInvoiceForm
    template_name = 'common/formset-form.html'
    permission_required = 'Sales.add_arinvoice'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        prefill_data = self.request.session.pop('prefill_invoice_data', None)
        if prefill_data:
            self.prefill_lines = prefill_data.get('lines', [])
            self.prefill_delivery = prefill_data.get('delivery')
            self.prefill_order = prefill_data.get('sales_order')
            for key, value in prefill_data.items():
                if key not in ['lines', 'delivery', 'sales_order']:
                    initial[key] = value
            initial['delivery_number'] = self.prefill_delivery
            initial['sales_order_number'] = self.prefill_order
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create AR Invoice'
        context['subtitle'] = 'Create a new accounts receivable invoice'
        context['cancel_url'] = reverse_lazy('Sales:arinvoice_list')
        context['submit_text'] = 'Create Invoice'

        if self.request.POST:
            context['formset'] = ARInvoiceLineFormSet(self.request.POST)
            context['extra_form'] = ARInvoiceExtraInfoForm(self.request.POST)
        else:
            initial_lines = getattr(self, 'prefill_lines', [])
            extra_count = len(initial_lines) if initial_lines else 1
            dynamic_formset = inlineformset_factory(
                ARInvoice,
                ARInvoiceLine,
                form=ARInvoiceLineForm,
                extra=extra_count,
                can_delete=True
            )
            context['formset'] = dynamic_formset(initial=initial_lines)
            context['extra_form'] = ARInvoiceExtraInfoForm(initial=self.get_initial())

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        extra_form = context['extra_form']

        if formset.is_valid() and extra_form.is_valid():
            with transaction.atomic():
                # Validate invoice quantities
                if hasattr(self, 'prefill_delivery'):
                    self._validate_invoice_quantities_from_delivery(form, formset)
                elif hasattr(self, 'prefill_order'):
                    self._validate_invoice_quantities_from_order(form, formset)

                # Save the invoice
                self.object = form.save()

                # Set delivery and sales_order if converting
                if hasattr(self, 'prefill_delivery'):
                    self.object.delivery_id = self.prefill_delivery
                if hasattr(self, 'prefill_order'):
                    self.object.sales_order_id = self.prefill_order

                # Update with extra form data
                for field in extra_form.cleaned_data:
                    if hasattr(self.object, field):
                        setattr(self.object, field, extra_form.cleaned_data[field])
                self.object.save()

                # Save the formset
                formset.instance = self.object
                formset.save()

                # Calculate financial totals
                self._calculate_financial_totals(self.object)

            messages.success(self.request, f"AR Invoice {self.object.pk} created successfully.")
            return HttpResponseRedirect(self.get_success_url())

        return self.form_invalid(form)

    def _validate_invoice_quantities_from_delivery(self, form, formset):
        """
        Validate that invoice quantities don't exceed remaining delivery quantities
        """
        delivery = Delivery.objects.get(pk=self.prefill_delivery)
        
        # Get delivery lines as dictionary for easy lookup
        delivery_lines = {}
        for line in delivery.lines.all():
            key = (line.item_code, line.uom)
            delivery_lines[key] = line.quantity
        
        # Calculate already invoiced quantities
        invoiced = ARInvoiceLine.objects.filter(
            invoice__delivery=delivery
        ).values('item_code', 'uom').annotate(total=Sum('quantity'))
        
        already_invoiced = {}
        for entry in invoiced:
            key = (entry['item_code'], entry['uom'])
            already_invoiced[key] = entry['total']
        
        # Validate each form line
        errors = []
        for f in formset:
            if not f.cleaned_data or f.cleaned_data.get('DELETE', False):
                continue
                
            item_code = f.cleaned_data['item_code']
            uom = f.cleaned_data['uom']
            quantity = f.cleaned_data['quantity']
            key = (item_code, uom)
            
            delivered_qty = delivery_lines.get(key, 0)
            invoiced_qty = already_invoiced.get(key, 0) or 0
            
            if quantity + invoiced_qty > delivered_qty:
                errors.append(
                    f"{item_code} - {uom}: Invoice exceeds delivery "
                    f"({invoiced_qty} already invoiced, trying to add {quantity}, "
                    f"but only {delivered_qty} delivered)."
                )
        
        if errors:
            for err in errors:
                messages.error(self.request, err)
            raise ValueError("Invoice quantities exceed delivery quantities")

    def _validate_invoice_quantities_from_order(self, form, formset):
        """
        Validate that invoice quantities don't exceed remaining order quantities
        """
        order = SalesOrder.objects.get(pk=self.prefill_order)
        
        # Get order lines as dictionary for easy lookup
        order_lines = {}
        for line in order.lines.all():
            key = (line.item_code, line.uom)
            order_lines[key] = line.quantity
        
        # Calculate already invoiced quantities
        invoiced = ARInvoiceLine.objects.filter(
            invoice__sales_order=order
        ).values('item_code', 'uom').annotate(total=Sum('quantity'))
        
        already_invoiced = {}
        for entry in invoiced:
            key = (entry['item_code'], entry['uom'])
            already_invoiced[key] = entry['total']
        
        # Validate each form line
        errors = []
        for f in formset:
            if not f.cleaned_data or f.cleaned_data.get('DELETE', False):
                continue
                
            item_code = f.cleaned_data['item_code']
            uom = f.cleaned_data['uom']
            quantity = f.cleaned_data['quantity']
            key = (item_code, uom)
            
            ordered_qty = order_lines.get(key, 0)
            invoiced_qty = already_invoiced.get(key, 0) or 0
            
            if quantity + invoiced_qty > ordered_qty:
                errors.append(
                    f"{item_code} - {uom}: Invoice exceeds order "
                    f"({invoiced_qty} already invoiced, trying to add {quantity}, "
                    f"but only {ordered_qty} ordered)."
                )
        
        if errors:
            for err in errors:
                messages.error(self.request, err)
            raise ValueError("Invoice quantities exceed order quantities")

    def _calculate_financial_totals(self, invoice):
        """
        Calculate financial totals for the invoice
        """
        if not invoice:
            return
        
        # Calculate total amount from lines
        total_amount = sum(
            line.quantity * line.unit_price 
            for line in invoice.lines.filter(is_active=True)
        )
        
        # Set total amount
        invoice.total_amount = total_amount
        
        # Calculate payable amount (total - discount)
        discount_amount = invoice.discount_amount or 0
        invoice.payable_amount = invoice.total_amount - discount_amount
        
        # Calculate due amount (payable - paid)
        paid_amount = invoice.paid_amount or 0
        invoice.due_amount = invoice.payable_amount - paid_amount
        
        # Save the invoice
        invoice.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])

    def get_success_url(self):
        return reverse_lazy('Sales:arinvoice_detail', kwargs={'pk': self.object.pk})

class ARInvoiceUpdateView(UpdateView):
    model = ARInvoice
    form_class = ARInvoiceForm
    template_name = 'common/formset-form.html'
    permission_required = 'Sales.change_arinvoice'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.change_arinvoice'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # Pass request to form
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update AR Invoice'
        context['subtitle'] = f'Edit invoice {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Sales:arinvoice_list')
        context['submit_text'] = 'Update Invoice'
        
        if self.request.POST:
            context['formset'] = ARInvoiceLineFormSet(self.request.POST, instance=self.object)
            context['extra_form'] = ARInvoiceExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = ARInvoiceLineFormSet(instance=self.object)
            context['extra_form'] = ARInvoiceExtraInfoForm(instance=self.object)
            
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
                
                # Update sales order status if needed
                if self.object.sales_order:
                    self._update_sales_order_status(self.object.sales_order)
            
            messages.success(self.request, f'AR Invoice {self.object.pk} updated successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def _update_sales_order_status(self, sales_order):
        """Update the sales order status based on invoice status"""
        # Check if all order lines have been fully invoiced
        order_lines = sales_order.lines.all()
        all_invoiced = True
        
        for line in order_lines:
            invoiced_qty = sum(il.quantity for il in line.invoice_lines.all())
            if invoiced_qty < line.quantity:
                all_invoiced = False
                break
        
        if all_invoiced:
            sales_order.status = 'Invoiced'
        else:
            # Check if any lines have been invoiced
            any_invoiced = False
            for line in order_lines:
                if line.invoice_lines.exists():
                    any_invoiced = True
                    break
            
            if any_invoiced:
                sales_order.status = 'Partially Invoiced'
        
        sales_order.save(update_fields=['status'])
    
    def get_success_url(self):
        return reverse_lazy('Sales:arinvoice_detail', kwargs={'pk': self.object.pk})

class ARInvoiceDetailView(DetailView):
    model = ARInvoice
    template_name = 'common/formset-form.html'  
    context_object_name = 'arinvoice'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.view_arinvoice'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'AR Invoice Details'
        context['subtitle'] = f'Invoice {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Sales:arinvoice_list')
        context['update_url'] = reverse_lazy('Sales:arinvoice_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Sales:arinvoice_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = ARInvoiceForm(instance=self.object, request=self.request)
        context['extra_form'] = ARInvoiceExtraInfoForm(instance=self.object)
        context['formset'] = ARInvoiceLineFormSet(instance=self.object)
        
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

class ARInvoiceDeleteView(GenericDeleteView):
    model = ARInvoice
    success_url = reverse_lazy('Sales:arinvoice_list')
    permission_required = 'Sales.delete_arinvoice'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to AR Invoice detail view.
        """
        return reverse_lazy('Sales:arinvoice_detail', kwargs={'pk': self.object.pk})        

class ARInvoiceExportView(BaseExportView):
    """
    Export view for AR Invoice.
    """
    model = ARInvoice
    filename = "ar_invoices.csv"
    permission_required = "Sales.view_arinvoice"
    field_names = ["ID", "Document Date", "Due Date", "Customer", "Status", "Total Amount", "Created At"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        # Restrict non-superusers to their own invoices
        user = request.user
        if not user.is_superuser:
            if hasattr(user, 'sales_employee'):
                queryset = queryset.filter(sales_employee=user.sales_employee)
            else:
                # If the user is not a sales employee, return no results
                queryset = queryset.none()
        return queryset

class ARInvoiceBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for AR Invoices.
    """
    model = ARInvoice
    permission_required = "Sales.delete_arinvoice"
    display_fields = ["id", "document_date", "customer", "status"]
    cancel_url = reverse_lazy("Sales:arinvoice_list")
    success_url = reverse_lazy("Sales:arinvoice_list")

class ARInvoicePrintView(DetailView):
    model = ARInvoice
    template_name = 'sales/arinvoice/arinvoice_print_creative.html'
    context_object_name = 'arinvoice'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.view_arinvoice'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'AR Invoice'
        context['subtitle'] = f'Invoice {self.object.pk}'
        return context
