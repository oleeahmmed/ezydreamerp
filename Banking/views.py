from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import Payment, PaymentMethod
from .forms import (
    PaymentForm, PaymentExtraInfoForm, PaymentLineFormSet, PaymentFilterForm,
    PaymentMethodForm, PaymentMethodFilterForm
)
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView
from Finance.models import ChartOfAccounts 

# Payment Method Views
class PaymentMethodListView(GenericFilterView):
    model = PaymentMethod
    template_name = 'banking/payment_method_list.html'
    context_object_name = 'objects'
    filter_form_class = PaymentMethodFilterForm
    permission_required = 'Banking.view_paymentmethod'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by search query if provided
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Payment Methods'
        context['subtitle'] = 'Manage payment methods'
        context['create_url'] = reverse_lazy('Banking:payment_method_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Banking.add_paymentmethod')
        context['can_view'] = self.request.user.has_perm('Banking.view_paymentmethod')
        context['can_update'] = self.request.user.has_perm('Banking.change_paymentmethod')
        context['can_delete'] = self.request.user.has_perm('Banking.delete_paymentmethod')
        context['can_export'] = self.request.user.has_perm('Banking.view_paymentmethod')
        context['can_bulk_delete'] = self.request.user.has_perm('Banking.delete_paymentmethod')
        
        return context

class PaymentMethodCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = 'common/premium-form.html'
    permission_required = 'Banking.add_paymentmethod'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Payment Method'
        context['subtitle'] = 'Add a new payment method'
        context['cancel_url'] = reverse_lazy('Banking:payment_method_list')
        context['submit_text'] = 'Create Payment Method'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment method created successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('Banking:payment_method_list')

class PaymentMethodUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = PaymentMethod
    form_class = PaymentMethodForm
    template_name = 'common/premium-form.html'
    permission_required = 'Banking.change_paymentmethod'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Payment Method'
        context['subtitle'] = f'Edit {self.object.name}'
        context['cancel_url'] = reverse_lazy('Banking:payment_method_list')
        context['submit_text'] = 'Update Payment Method'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment method updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('Banking:payment_method_list')

class PaymentMethodDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = PaymentMethod
    template_name = 'banking/common/premium-form.html'
    context_object_name = 'payment_method'
    permission_required = 'Banking.view_paymentmethod'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Payment Method Details'
        context['subtitle'] = f'{self.object.name}'
        context['cancel_url'] = reverse_lazy('Banking:payment_method_list')
        context['update_url'] = reverse_lazy('Banking:payment_method_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Banking:payment_method_delete', kwargs={'pk': self.object.pk})
        return context

class PaymentMethodDeleteView(GenericDeleteView):
    model = PaymentMethod
    success_url = reverse_lazy('Banking:payment_method_list')
    permission_required = 'Banking.delete_paymentmethod'
    
    def get_cancel_url(self):
        return reverse_lazy('Banking:payment_method_detail', kwargs={'pk': self.object.pk})

class PaymentMethodExportView(BaseExportView):
    model = PaymentMethod
    filename = "payment_methods.csv"
    permission_required = "Banking.view_paymentmethod"
    field_names = ["Name", "Description", "Created At"]

class PaymentMethodBulkDeleteView(BaseBulkDeleteConfirmView):
    model = PaymentMethod
    permission_required = "Banking.delete_paymentmethod"
    display_fields = ["name", "description", "created_at"]
    cancel_url = reverse_lazy("Banking:payment_method_list")
    success_url = reverse_lazy("Banking:payment_method_list")

# Payment Views
class PaymentListView(GenericFilterView):
    model = Payment
    template_name = 'banking/payment_list.html'
    context_object_name = 'objects'
    filter_form_class = PaymentFilterForm
    permission_required = 'Banking.view_payment'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by search query if provided
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                doc_num__icontains=search_query
            ) | queryset.filter(
                reference__icontains=search_query
            )
        
        # Filter by payment type
        payment_type = self.request.GET.get('payment_type', '')
        if payment_type:
            queryset = queryset.filter(payment_type=payment_type)
        
        # Filter by reconciliation status
        is_reconciled = self.request.GET.get('is_reconciled', '')
        if is_reconciled == 'true':
            queryset = queryset.filter(is_reconciled=True)
        elif is_reconciled == 'false':
            queryset = queryset.filter(is_reconciled=False)
        
        # Filter by date range
        date_from = self.request.GET.get('date_from', '')
        if date_from:
            queryset = queryset.filter(payment_date__gte=date_from)
        
        date_to = self.request.GET.get('date_to', '')
        if date_to:
            queryset = queryset.filter(payment_date__lte=date_to)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Payments'
        context['subtitle'] = 'Manage incoming and outgoing payments'
        context['create_url'] = reverse_lazy('Banking:payment_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Banking.add_payment')
        context['can_view'] = self.request.user.has_perm('Banking.view_payment')
        context['can_update'] = self.request.user.has_perm('Banking.change_payment')
        context['can_delete'] = self.request.user.has_perm('Banking.delete_payment')
        context['can_export'] = self.request.user.has_perm('Banking.view_payment')
        context['can_bulk_delete'] = self.request.user.has_perm('Banking.delete_payment')
        
        return context

class PaymentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'banking/banking-formset.html'
    permission_required = 'Banking.add_payment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Payment'
        context['subtitle'] = 'Record a new payment'
        context['cancel_url'] = reverse_lazy('Banking:payment_list')
        context['submit_text'] = 'Create Payment'
        
        if self.request.POST:
            context['formset'] = PaymentLineFormSet(self.request.POST)
            context['extra_form'] = PaymentExtraInfoForm(self.request.POST)
        else:
            context['formset'] = PaymentLineFormSet()
            context['extra_form'] = PaymentExtraInfoForm()
        context['accounts'] = ChartOfAccounts.objects.filter(is_active=True)
            
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
            
            messages.success(self.request, f'Payment {self.object.doc_num} created successfully.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('Banking:payment_detail', kwargs={'pk': self.object.pk})


# class PaymentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
#     model = Payment
#     form_class = PaymentForm
#     template_name = 'common/premium-form.html'
#     permission_required = 'Banking.add_payment'
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = 'Create Payment'
#         context['subtitle'] = 'Record a new payment'
#         context['cancel_url'] = reverse_lazy('Banking:payment_list')
#         context['submit_text'] = 'Create Payment'
#         return context
    
#     def form_valid(self, form):
#         messages.success(self.request, 'Payment  created successfully.')
#         return super().form_valid(form)
    
#     def get_success_url(self):
#         return reverse_lazy('Banking:payment_detail', kwargs={'pk': self.object.pk})

class PaymentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'common/premium-form.html'
    permission_required = 'Banking.change_payment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Payment'
        context['subtitle'] = f'Edit payment {self.object.doc_num}'
        context['cancel_url'] = reverse_lazy('Banking:payment_detail', kwargs={'pk': self.object.pk})
        context['submit_text'] = 'Update Payment'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment updated successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('Banking:payment_detail', kwargs={'pk': self.object.pk})


# class PaymentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
#     model = Payment
#     form_class = PaymentForm
#     template_name = 'banking/banking-formset.html'
#     permission_required = 'Banking.change_payment'
    
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['title'] = 'Update Payment'
#         context['subtitle'] = f'Edit payment {self.object.doc_num}'
#         context['cancel_url'] = reverse_lazy('Banking:payment_detail', kwargs={'pk': self.object.pk})
#         context['submit_text'] = 'Update Payment'
        
#         if self.request.POST:
#             context['formset'] = PaymentLineFormSet(self.request.POST, instance=self.object)
#             context['extra_form'] = PaymentExtraInfoForm(self.request.POST, instance=self.object)
#         else:
#             context['formset'] = PaymentLineFormSet(instance=self.object)
#             context['extra_form'] = PaymentExtraInfoForm(instance=self.object)
            
#         return context
    
#     def form_valid(self, form):
#         context = self.get_context_data()
#         formset = context['formset']
#         extra_form = context['extra_form']
        
#         if formset.is_valid() and extra_form.is_valid():
#             with transaction.atomic():
#                 # Save the main form
#                 self.object = form.save()
                
#                 # Update with extra form data
#                 for field in extra_form.cleaned_data:
#                     if hasattr(self.object, field):
#                         setattr(self.object, field, extra_form.cleaned_data[field])
#                 self.object.save()
                
#                 # Save the formset
#                 formset.instance = self.object
#                 formset.save()
            
#             messages.success(self.request, f'Payment {self.object.doc_num} updated successfully.')
#             return HttpResponseRedirect(self.get_success_url())
#         else:
#             return self.form_invalid(form)
    
#     def get_success_url(self):
#         return reverse_lazy('Banking:payment_detail', kwargs={'pk': self.object.pk})

class PaymentDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Payment
    template_name = 'banking/banking-formset.html'
    context_object_name = 'payment'
    permission_required = 'Banking.view_payment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Payment Details'
        context['subtitle'] = f'Payment {self.object.doc_num}'
        context['cancel_url'] = reverse_lazy('Banking:payment_list')
        context['update_url'] = reverse_lazy('Banking:payment_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('Banking:payment_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = PaymentForm(instance=self.object)
        context['extra_form'] = PaymentExtraInfoForm(instance=self.object)
        context['formset'] = PaymentLineFormSet(instance=self.object)
        
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

class PaymentDeleteView(GenericDeleteView):
    model = Payment
    success_url = reverse_lazy('Banking:payment_list')
    permission_required = 'Banking.delete_payment'
    
    def get_cancel_url(self):
        return reverse_lazy('Banking:payment_detail', kwargs={'pk': self.object.pk})

class PaymentExportView(BaseExportView):
    model = Payment
    filename = "payments.csv"
    permission_required = "Banking.view_payment"
    field_names = ["Document Number", "Business Partner", "Payment Type", "Amount", "Payment Date", "Is Reconciled", "Created At"]

class PaymentBulkDeleteView(BaseBulkDeleteConfirmView):
    model = Payment
    permission_required = "Banking.delete_payment"
    display_fields = ["doc_num", "business_partner", "payment_type", "amount", "payment_date"]
    cancel_url = reverse_lazy("Banking:payment_list")
    success_url = reverse_lazy("Banking:payment_list")

class PaymentPrintView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Payment
    template_name = 'banking/payment_print.html'
    context_object_name = 'payment'
    permission_required = 'Banking.view_payment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Payment Receipt'
        context['subtitle'] = f'Payment {self.object.doc_num}'
        return context

