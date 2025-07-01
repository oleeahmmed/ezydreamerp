from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect

from ..models import Return, ReturnLine, Delivery, DeliveryLine
from ..forms.return_forms import ReturnForm, ReturnExtraInfoForm, ReturnLineFormSet, ReturnFilterForm,ReturnLineForm
from django.forms import inlineformset_factory
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class ReturnListView(GenericFilterView):
    model = Return
    template_name = 'sales/return_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    permission_required = 'Sales.view_return'

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
        context['title'] = 'Returns'
        context['subtitle'] = 'Manage return documents'
        context['create_url'] = reverse_lazy('Sales:return_create')
        
        context['can_create'] = self.request.user.has_perm('Sales.add_return')
        context['can_view'] = self.request.user.has_perm('Sales.view_return')
        context['can_update'] = self.request.user.has_perm('Sales.change_return')
        context['can_delete'] = self.request.user.has_perm('Sales.delete_return')
        context['can_print'] = self.request.user.has_perm('Sales.view_return')
        context['can_export'] = self.request.user.has_perm('Sales.view_return')
        context['can_bulk_delete'] = self.request.user.has_perm('Sales.delete_return')
        
        return context

class ReturnCreateView(CreateView):
    model = Return
    form_class = ReturnForm
    template_name = 'common/formset-form.html'
    permission_required = 'Sales.add_return'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        prefill_data = self.request.session.pop('prefill_return_data', None)
        if prefill_data:
            self.prefill_lines = prefill_data.get('lines', [])
            self.prefill_delivery = prefill_data.get('delivery')
            
            # Store all prefill data in initial
            for key, value in prefill_data.items():
                if key != 'lines':
                    initial[key] = value
                    
            if self.prefill_delivery:
                initial['delivery'] = self.prefill_delivery
                
            self.delivery_line_mapping = {line['item_code']: line['delivery_line'] for line in self.prefill_lines if 'delivery_line' in line}
        
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Return'
        context['subtitle'] = 'Create a new return document'
        context['cancel_url'] = reverse_lazy('Sales:return_list')
        context['submit_text'] = 'Create Return'

        if self.request.POST:
            context['formset'] = ReturnLineFormSet(self.request.POST)
            context['extra_form'] = ReturnExtraInfoForm(self.request.POST)
        else:
            initial_lines = getattr(self, 'prefill_lines', [])
            extra_count = len(initial_lines) if initial_lines else 1
            
            dynamic_formset = inlineformset_factory(
                Return,
                ReturnLine,
                form=ReturnLineForm,
                extra=extra_count,
                can_delete=True
            )
            context['formset'] = dynamic_formset(initial=initial_lines)
            context['extra_form'] = ReturnExtraInfoForm(initial=self.get_initial())

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
                formset.instance = self.object
                return_lines = formset.save()

                if hasattr(self, 'delivery_line_mapping') and return_lines:
                    for return_line in return_lines:
                        item_code = return_line.item_code
                        if item_code in self.delivery_line_mapping:
                            try:
                                delivery_line = DeliveryLine.objects.get(id=self.delivery_line_mapping[item_code])
                                return_line.delivery_line = delivery_line
                                return_line.save(update_fields=['delivery_line'])
                            except DeliveryLine.DoesNotExist:
                                pass

                self._calculate_financial_totals(self.object)

            messages.success(self.request, f"Return {self.object.pk} created successfully.")
            return HttpResponseRedirect(self.get_success_url())

        return self.form_invalid(form)

    def _calculate_financial_totals(self, return_doc):
        if not return_doc:
            return
        
        total_amount = sum(line.quantity * line.unit_price for line in return_doc.lines.filter(is_active=True))
        return_doc.total_amount = total_amount
        discount_amount = return_doc.discount_amount or 0
        return_doc.payable_amount = return_doc.total_amount - discount_amount
        paid_amount = return_doc.paid_amount or 0
        return_doc.due_amount = return_doc.payable_amount - paid_amount
        return_doc.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])

    def get_success_url(self):
        return reverse_lazy('Sales:return_detail', kwargs={'pk': self.object.pk})

class ReturnUpdateView(UpdateView):
    model = Return
    form_class = ReturnForm
    template_name = 'common/formset-form.html'
    permission_required = 'Sales.change_return'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.change_return'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Return'
        context['subtitle'] = f'Edit return {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Sales:return_list')
        context['submit_text'] = 'Update Return'
        
        if self.request.POST:
            context['formset'] = ReturnLineFormSet(self.request.POST, instance=self.object)
            context['extra_form'] = ReturnExtraInfoForm(self.request.POST, instance=self.object)
        else:
            context['formset'] = ReturnLineFormSet(instance=self.object)
            context['extra_form'] = ReturnExtraInfoForm(instance=self.object)
            
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
            
            messages.success(self.request, f'Return {self.object.pk} updated successfully.')
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
        return reverse_lazy('Sales:return_update', kwargs={'pk': self.object.pk})

class ReturnDetailView(DetailView):
    model = Return
    template_name = 'common/formset-form.html'  
    context_object_name = 'return'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('Sales.view_return'):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Return Details'
        context['subtitle'] = f'Return {self.object.pk}'
        context['cancel_url'] = reverse_lazy('Sales:return_list')
        context['update_url'] = reverse_lazy('Sales:return_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Sales:return_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = ReturnForm(instance=self.object, request=self.request)
        context['extra_form'] = ReturnExtraInfoForm(instance=self.object)
        context['formset'] = ReturnLineFormSet(instance=self.object)
        
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

class ReturnDeleteView(GenericDeleteView):
    model = Return
    success_url = reverse_lazy('Sales:return_list')
    permission_required = 'Sales.delete_return'

    def get_cancel_url(self):
        """
        Override cancel URL to redirect to Return detail view.
        """
        return reverse_lazy('Sales:return_detail', kwargs={'pk': self.object.pk})        

class ReturnExportView(BaseExportView):
    """
    Export view for Return.
    """
    model = Return
    filename = "returns.csv"
    permission_required = "Sales.view_return"
    field_names = ["ID", "Document Date", "Posting Date", "Customer", "Status", "Total Amount", "Created At"]

    def queryset_filter(self, request, queryset):
        """
        Apply filtering if needed (e.g., user restrictions).
        """
        return queryset

class ReturnBulkDeleteView(BaseBulkDeleteConfirmView):
    """
    Bulk delete view for Returns.
    """
    model = Return
    permission_required = "Sales.delete_return"
    display_fields = ["id", "document_date", "customer", "status"]
    cancel_url = reverse_lazy("Sales:return_list")
    success_url = reverse_lazy("Sales:return_list")