from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import EmployeeAdvance
from ..forms import EmployeeAdvanceForm, PayrollFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class EmployeeAdvanceListView(GenericFilterView):
    model = EmployeeAdvance
    template_name = 'payroll/employee_advance_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PayrollFilterForm
    permission_required = 'Hrm.view_employeeadvance'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                employee__first_name__icontains=filters['search']
            ) | queryset.filter(
                employee__last_name__icontains=filters['search']
            ) | queryset.filter(
                employee__employee_id__icontains=filters['search']
            ) | queryset.filter(
                advance_setup__name__icontains=filters['search']
            ) | queryset.filter(
                reason__icontains=filters['search']
            )
            
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
            
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
            
        if filters.get('date_from'):
            queryset = queryset.filter(application_date__gte=filters['date_from'])
            
        if filters.get('date_to'):
            queryset = queryset.filter(application_date__lte=filters['date_to'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:employee_advance_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_employeeadvance')
        context['can_view'] = self.request.user.has_perm('Hrm.view_employeeadvance')
        context['can_update'] = self.request.user.has_perm('Hrm.change_employeeadvance')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_employeeadvance')
        context['can_export'] = self.request.user.has_perm('Hrm.view_employeeadvance')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_employeeadvance')
        
        return context

class EmployeeAdvanceCreateView(CreateView):
    model = EmployeeAdvance
    form_class = EmployeeAdvanceForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Employee Advance'
        context['subtitle'] = 'Add a new employee advance to the system'
        context['cancel_url'] = reverse_lazy('hrm:employee_advance_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Advance for {self.object.employee.get_full_name()} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_advance_detail', kwargs={'pk': self.object.pk})

class EmployeeAdvanceUpdateView(UpdateView):
    model = EmployeeAdvance
    form_class = EmployeeAdvanceForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Employee Advance'
        context['subtitle'] = f'Edit advance for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_advance_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Advance for {self.object.employee.get_full_name()} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_advance_detail', kwargs={'pk': self.object.pk})

class EmployeeAdvanceDetailView(DetailView):
    model = EmployeeAdvance
    template_name = 'common/premium-form.html'
    context_object_name = 'employee_advance'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Employee Advance Details'
        context['subtitle'] = f'Advance for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_advance_list')
        context['update_url'] = reverse_lazy('hrm:employee_advance_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:employee_advance_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = EmployeeAdvanceForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class EmployeeAdvanceDeleteView(GenericDeleteView):
    model = EmployeeAdvance
    success_url = reverse_lazy('hrm:employee_advance_list')
    permission_required = 'Hrm.delete_employeeadvance'

    def get_cancel_url(self):
        """Override cancel URL to redirect to EmployeeAdvance detail view."""
        return reverse_lazy('hrm:employee_advance_detail', kwargs={'pk': self.object.pk})

class EmployeeAdvanceExportView(BaseExportView):
    """Export view for EmployeeAdvance."""
    model = EmployeeAdvance
    filename = "employee_advances.csv"
    permission_required = "Hrm.view_employeeadvance"
    field_names = ["Employee", "Advance Setup", "Amount", "Installments", "Status", "Application Date", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class EmployeeAdvanceBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for EmployeeAdvance."""
    model = EmployeeAdvance
    permission_required = "Hrm.delete_employeeadvance"
    display_fields = ["employee", "advance_setup", "amount", "installments", "status", "application_date"]
    cancel_url = reverse_lazy("hrm:employee_advance_list")
    success_url = reverse_lazy("hrm:employee_advance_list")

