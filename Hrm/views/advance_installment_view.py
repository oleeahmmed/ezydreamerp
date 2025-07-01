from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import AdvanceInstallment
from ..forms import AdvanceInstallmentForm, PayrollFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class AdvanceInstallmentListView(GenericFilterView):
    model = AdvanceInstallment
    template_name = 'payroll/advance_installment_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PayrollFilterForm
    permission_required = 'Hrm.view_advanceinstallment'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                employee_advance__employee__employee_id__icontains=filters['search']
            ) | queryset.filter(
                employee_advance__employee__first_name__icontains=filters['search']
            ) | queryset.filter(
                employee_advance__employee__last_name__icontains=filters['search']
            )
            
        if filters.get('department'):
            queryset = queryset.filter(employee_advance__employee__department=filters['department'])
            
        if filters.get('from_date'):
            queryset = queryset.filter(installment_date__gte=filters['from_date'])
            
        if filters.get('to_date'):
            queryset = queryset.filter(installment_date__lte=filters['to_date'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:advance_installment_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_advanceinstallment')
        context['can_view'] = self.request.user.has_perm('Hrm.view_advanceinstallment')
        context['can_update'] = self.request.user.has_perm('Hrm.change_advanceinstallment')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_advanceinstallment')
        context['can_export'] = self.request.user.has_perm('Hrm.view_advanceinstallment')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_advanceinstallment')
        
        return context

class AdvanceInstallmentCreateView(CreateView):
    model = AdvanceInstallment
    form_class = AdvanceInstallmentForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Advance Installment'
        context['subtitle'] = 'Add a new advance installment to the system'
        context['cancel_url'] = reverse_lazy('hrm:advance_installment_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Advance Installment for {self.object.employee_advance.employee.get_full_name()} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:advance_installment_detail', kwargs={'pk': self.object.pk})

class AdvanceInstallmentUpdateView(UpdateView):
    model = AdvanceInstallment
    form_class = AdvanceInstallmentForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Advance Installment'
        context['subtitle'] = f'Edit advance installment for {self.object.employee_advance.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:advance_installment_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Advance Installment for {self.object.employee_advance.employee.get_full_name()} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:advance_installment_detail', kwargs={'pk': self.object.pk})

class AdvanceInstallmentDetailView(DetailView):
    model = AdvanceInstallment
    template_name = 'common/premium-form.html'
    context_object_name = 'advance_installment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Advance Installment Details'
        context['subtitle'] = f'Advance Installment for: {self.object.employee_advance.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:advance_installment_list')
        context['update_url'] = reverse_lazy('hrm:advance_installment_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:advance_installment_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = AdvanceInstallmentForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class AdvanceInstallmentDeleteView(GenericDeleteView):
    model = AdvanceInstallment
    success_url = reverse_lazy('hrm:advance_installment_list')
    permission_required = 'Hrm.delete_advanceinstallment'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Advance Installment detail view."""
        return reverse_lazy('hrm:advance_installment_detail', kwargs={'pk': self.object.pk})

class AdvanceInstallmentExportView(BaseExportView):
    """Export view for Advance Installment."""
    model = AdvanceInstallment
    filename = "advance_installments.csv"
    permission_required = "Hrm.view_advanceinstallment"
    field_names = ["Employee", "Advance", "Installment Date", "Amount", "Status", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class AdvanceInstallmentBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Advance Installments."""
    model = AdvanceInstallment
    permission_required = "Hrm.delete_advanceinstallment"
    display_fields = ["employee_advance__employee__employee_id", "employee_advance__employee__first_name", "installment_date", "amount", "status"]
    cancel_url = reverse_lazy("hrm:advance_installment_list")
    success_url = reverse_lazy("hrm:advance_installment_list")