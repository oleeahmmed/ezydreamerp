from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import EmployeeSalaryStructure
from ..forms import EmployeeSalaryStructureForm, PayrollFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class EmployeeSalaryStructureListView(GenericFilterView):
    model = EmployeeSalaryStructure
    template_name = 'payroll/employee_salary_structure_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PayrollFilterForm
    permission_required = 'Hrm.view_employeesalarystructure'
    
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
            )
            
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
            
        if filters.get('date_from'):
            queryset = queryset.filter(effective_date__gte=filters['date_from'])
            
        if filters.get('date_to'):
            queryset = queryset.filter(effective_date__lte=filters['date_to'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:employee_salary_structure_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_employeesalarystructure')
        context['can_view'] = self.request.user.has_perm('Hrm.view_employeesalarystructure')
        context['can_update'] = self.request.user.has_perm('Hrm.change_employeesalarystructure')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_employeesalarystructure')
        context['can_export'] = self.request.user.has_perm('Hrm.view_employeesalarystructure')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_employeesalarystructure')
        
        return context

class EmployeeSalaryStructureCreateView(CreateView):
    model = EmployeeSalaryStructure
    form_class = EmployeeSalaryStructureForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Employee Salary Structure'
        context['subtitle'] = 'Add a new salary structure for an employee'
        context['cancel_url'] = reverse_lazy('hrm:employee_salary_structure_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Salary Structure for {self.object.employee.get_full_name()} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_salary_structure_detail', kwargs={'pk': self.object.pk})

class EmployeeSalaryStructureUpdateView(UpdateView):
    model = EmployeeSalaryStructure
    form_class = EmployeeSalaryStructureForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Employee Salary Structure'
        context['subtitle'] = f'Edit salary structure for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_salary_structure_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Salary Structure for {self.object.employee.get_full_name()} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_salary_structure_detail', kwargs={'pk': self.object.pk})

class EmployeeSalaryStructureDetailView(DetailView):
    model = EmployeeSalaryStructure
    template_name = 'common/premium-form.html'
    context_object_name = 'employee_salary_structure'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Employee Salary Structure Details'
        context['subtitle'] = f'Salary Structure for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_salary_structure_list')
        context['update_url'] = reverse_lazy('hrm:employee_salary_structure_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:employee_salary_structure_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = EmployeeSalaryStructureForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class EmployeeSalaryStructureDeleteView(GenericDeleteView):
    model = EmployeeSalaryStructure
    success_url = reverse_lazy('hrm:employee_salary_structure_list')
    permission_required = 'Hrm.delete_employeesalarystructure'

    def get_cancel_url(self):
        """Override cancel URL to redirect to EmployeeSalaryStructure detail view."""
        return reverse_lazy('hrm:employee_salary_structure_detail', kwargs={'pk': self.object.pk})

class EmployeeSalaryStructureExportView(BaseExportView):
    """Export view for EmployeeSalaryStructure."""
    model = EmployeeSalaryStructure
    filename = "employee_salary_structures.csv"
    permission_required = "Hrm.view_employeesalarystructure"
    field_names = ["Employee", "Effective Date", "Gross Salary", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class EmployeeSalaryStructureBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for EmployeeSalaryStructure."""
    model = EmployeeSalaryStructure
    permission_required = "Hrm.delete_employeesalarystructure"
    display_fields = ["employee", "effective_date", "gross_salary", "created_at"]
    cancel_url = reverse_lazy("hrm:employee_salary_structure_list")
    success_url = reverse_lazy("hrm:employee_salary_structure_list")

