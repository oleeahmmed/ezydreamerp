from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db import transaction

from ..models import EmployeeSalaryStructure, SalaryStructureComponent
from ..forms import (
    EmployeeSalaryStructureForm, 
    SalaryStructureComponentFormSet,
    EmployeeSalaryStructureFilterForm
)
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class EmployeeSalaryStructureListView(GenericFilterView):
    model = EmployeeSalaryStructure
    template_name = 'payroll/employee_salary_structure_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = EmployeeSalaryStructureFilterForm
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
            
        if filters.get('effective_date_from'):
            queryset = queryset.filter(effective_date__gte=filters['effective_date_from'])
            
        if filters.get('effective_date_to'):
            queryset = queryset.filter(effective_date__lte=filters['effective_date_to'])
            
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
    template_name = 'payroll/salary_structure_form.html'
    permission_required = 'Hrm.add_employeesalarystructure'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Employee Salary Structure'
        context['subtitle'] = 'Add a new salary structure with components for an employee'
        context['cancel_url'] = reverse_lazy('hrm:employee_salary_structure_list')
        
        if self.request.POST:
            context['formset'] = SalaryStructureComponentFormSet(self.request.POST)
        else:
            context['formset'] = SalaryStructureComponentFormSet()
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            with transaction.atomic():
                # Save the main form
                self.object = form.save()
                
                # Save the formset
                formset.instance = self.object
                formset.save()
            
            messages.success(
                self.request, 
                f'Salary Structure for {self.object.employee.get_full_name()} created successfully.'
            )
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(
            self.request, 
            'Please correct the errors below and try again.'
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_salary_structure_detail', kwargs={'pk': self.object.pk})

class EmployeeSalaryStructureUpdateView(UpdateView):
    model = EmployeeSalaryStructure
    form_class = EmployeeSalaryStructureForm
    template_name = 'payroll/salary_structure_form.html'
    permission_required = 'Hrm.change_employeesalarystructure'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Employee Salary Structure'
        context['subtitle'] = f'Edit salary structure for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_salary_structure_detail', kwargs={'pk': self.object.pk})
        
        if self.request.POST:
            context['formset'] = SalaryStructureComponentFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = SalaryStructureComponentFormSet(instance=self.object)
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            with transaction.atomic():
                # Save the main form
                self.object = form.save()
                
                # Save the formset
                formset.instance = self.object
                formset.save()
            
            messages.success(
                self.request, 
                f'Salary Structure for {self.object.employee.get_full_name()} updated successfully.'
            )
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Handle form validation errors"""
        messages.error(
            self.request, 
            'Please correct the errors below and try again.'
        )
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_salary_structure_detail', kwargs={'pk': self.object.pk})

class EmployeeSalaryStructureDetailView(DetailView):
    model = EmployeeSalaryStructure
    template_name = 'payroll/salary_structure_form.html'
    context_object_name = 'employee_salary_structure'
    permission_required = 'Hrm.view_employeesalarystructure'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Employee Salary Structure Details'
        context['subtitle'] = f'Salary Structure for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_salary_structure_list')
        context['update_url'] = reverse_lazy('hrm:employee_salary_structure_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:employee_salary_structure_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form and formset in read-only mode for the detail view
        context['form'] = EmployeeSalaryStructureForm(instance=self.object)
        context['formset'] = SalaryStructureComponentFormSet(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
            
        # Make formset fields read-only
        for form in context['formset'].forms:
            for field in form.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['disabled'] = 'disabled'
        
        # Add summary information
        context['total_components'] = self.object.components.count()
        context['total_earnings'] = sum(
            component.amount for component in self.object.components.filter(
                component__component_type='EARN'
            )
        )
        context['total_deductions'] = sum(
            component.amount for component in self.object.components.filter(
                component__component_type='DED'
            )
        )
        
        return context

class EmployeeSalaryStructureDeleteView(GenericDeleteView):
    model = EmployeeSalaryStructure
    success_url = reverse_lazy('hrm:employee_salary_structure_list')
    permission_required = 'Hrm.delete_employeesalarystructure'

    def get_cancel_url(self):
        """Override cancel URL to redirect to EmployeeSalaryStructure detail view."""
        return reverse_lazy('hrm:employee_salary_structure_detail', kwargs={'pk': self.object.pk})
    
    def delete(self, request, *args, **kwargs):
        """Override delete to add success message"""
        self.object = self.get_object()
        employee_name = self.object.employee.get_full_name()
        
        with transaction.atomic():
            # Delete related components first (cascade should handle this, but being explicit)
            self.object.components.all().delete()
            # Delete the main object
            response = super().delete(request, *args, **kwargs)
        
        messages.success(
            request, 
            f'Salary Structure for {employee_name} deleted successfully.'
        )
        return response

class EmployeeSalaryStructureExportView(BaseExportView):
    """Export view for EmployeeSalaryStructure."""
    model = EmployeeSalaryStructure
    filename = "employee_salary_structures.csv"
    permission_required = "Hrm.view_employeesalarystructure"
    field_names = ["Employee", "Effective Date", "Gross Salary", "Total Components", "Created At"]

    def get_queryset(self):
        """Get queryset with related data for export"""
        return super().get_queryset().select_related('employee').prefetch_related('components')

    def get_export_data(self, queryset):
        """Customize export data to include component count"""
        data = []
        for obj in queryset:
            data.append({
                'Employee': obj.employee.get_full_name(),
                'Effective Date': obj.effective_date.strftime('%Y-%m-%d'),
                'Gross Salary': str(obj.gross_salary),
                'Total Components': obj.components.count(),
                'Created At': obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })
        return data

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
    
    def get_queryset(self):
        """Get queryset with related data for bulk operations"""
        return super().get_queryset().select_related('employee')
    
    def delete_objects(self, queryset):
        """Override to handle cascade deletion properly"""
        count = 0
        with transaction.atomic():
            for obj in queryset:
                # Delete related components first
                obj.components.all().delete()
                obj.delete()
                count += 1
        
        messages.success(
            self.request,
            f'Successfully deleted {count} salary structure(s).'
        )
        return count

# Additional utility view for copying salary structures
class EmployeeSalaryStructureCopyView(CreateView):
    """View to copy an existing salary structure to create a new one"""
    model = EmployeeSalaryStructure
    form_class = EmployeeSalaryStructureForm
    template_name = 'payroll/salary_structure_form.html'
    permission_required = 'Hrm.add_employeesalarystructure'
    
    def get_source_object(self):
        """Get the source salary structure to copy from"""
        source_pk = self.kwargs.get('source_pk')
        return EmployeeSalaryStructure.objects.get(pk=source_pk)
    
    def get_initial(self):
        """Pre-populate form with source object data"""
        source = self.get_source_object()
        return {
            'employee': None,  # Let user select new employee
            'effective_date': None,  # Let user set new effective date
            'gross_salary': source.gross_salary,
        }
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        source = self.get_source_object()
        
        context['title'] = 'Copy Salary Structure'
        context['subtitle'] = f'Create new salary structure based on {source.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_salary_structure_list')
        
        if self.request.POST:
            context['formset'] = SalaryStructureComponentFormSet(self.request.POST)
        else:
            # Create formset with source components
            initial_data = []
            for component in source.components.all():
                initial_data.append({
                    'component': component.component,
                    'amount': component.amount,
                    'percentage': component.percentage,
                })
            
            context['formset'] = SalaryStructureComponentFormSet(initial=initial_data)
            
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            with transaction.atomic():
                # Save the main form
                self.object = form.save()
                
                # Save the formset
                formset.instance = self.object
                formset.save()
            
            messages.success(
                self.request, 
                f'Salary Structure copied successfully for {self.object.employee.get_full_name()}.'
            )
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_salary_structure_detail', kwargs={'pk': self.object.pk})
