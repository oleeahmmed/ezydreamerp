from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import EmployeeSalary
from ..forms import EmployeeSalaryForm, PayrollFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class EmployeeSalaryListView(GenericFilterView):
    model = EmployeeSalary
    template_name = 'payroll/employee_salary_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PayrollFilterForm
    permission_required = 'Hrm.view_employeesalary'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                employee__employee_id__icontains=filters['search']
            ) | queryset.filter(
                employee__first_name__icontains=filters['search']
            ) | queryset.filter(
                employee__last_name__icontains=filters['search']
            )
            
        if filters.get('department'):
            queryset = queryset.filter(employee__department=filters['department'])
            
        if filters.get('from_date'):
            queryset = queryset.filter(salary_month__start_date__gte=filters['from_date'])
            
        if filters.get('to_date'):
            queryset = queryset.filter(salary_month__end_date__lte=filters['to_date'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:employee_salary_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_employeesalary')
        context['can_view'] = self.request.user.has_perm('Hrm.view_employeesalary')
        context['can_update'] = self.request.user.has_perm('Hrm.change_employeesalary')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_employeesalary')
        context['can_export'] = self.request.user.has_perm('Hrm.view_employeesalary')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_employeesalary')
        
        return context

class EmployeeSalaryCreateView(CreateView):
    model = EmployeeSalary
    form_class = EmployeeSalaryForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Employee Salary'
        context['subtitle'] = 'Add a new employee salary to the system'
        context['cancel_url'] = reverse_lazy('hrm:employee_salary_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Employee Salary for {self.object.employee.get_full_name()} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_salary_detail', kwargs={'pk': self.object.pk})

class EmployeeSalaryUpdateView(UpdateView):
    model = EmployeeSalary
    form_class = EmployeeSalaryForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Employee Salary'
        context['subtitle'] = f'Edit employee salary for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_salary_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Employee Salary for {self.object.employee.get_full_name()} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_salary_detail', kwargs={'pk': self.object.pk})

class EmployeeSalaryDetailView(DetailView):
    model = EmployeeSalary
    template_name = 'common/premium-form.html'
    context_object_name = 'employee_salary'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Employee Salary Details'
        context['subtitle'] = f'Employee Salary for: {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_salary_list')
        context['update_url'] = reverse_lazy('hrm:employee_salary_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:employee_salary_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = EmployeeSalaryForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class EmployeeSalaryDeleteView(GenericDeleteView):
    model = EmployeeSalary
    success_url = reverse_lazy('hrm:employee_salary_list')
    permission_required = 'Hrm.delete_employeesalary'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Employee Salary detail view."""
        return reverse_lazy('hrm:employee_salary_detail', kwargs={'pk': self.object.pk})

class EmployeeSalaryExportView(BaseExportView):
    """Export view for Employee Salary."""
    model = EmployeeSalary
    filename = "employee_salaries.csv"
    permission_required = "Hrm.view_employeesalary"
    field_names = ["Employee", "Salary Month", "Basic Salary", "Gross Salary", "Net Salary", "Status", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class EmployeeSalaryBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Employee Salaries."""
    model = EmployeeSalary
    permission_required = "Hrm.delete_employeesalary"
    display_fields = ["employee__employee_id", "employee__first_name", "salary_month__name", "gross_salary", "net_salary"]
    cancel_url = reverse_lazy("hrm:employee_salary_list")
    success_url = reverse_lazy("hrm:employee_salary_list")