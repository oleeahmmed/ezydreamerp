from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from Hrm.models import EmployeeSeparation
from Hrm.forms import EmployeeSeparationForm, EmployeeSeparationFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class EmployeeSeparationListView(GenericFilterView):
    model = EmployeeSeparation
    template_name = 'employee/employee_separation_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = EmployeeSeparationFilterForm
    permission_required = 'Hrm.view_employeeseparation'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                reason__icontains=filters['search']
            ) | queryset.filter(
                remarks__icontains=filters['search']
            )
            
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
            
        if filters.get('separation_type'):
            queryset = queryset.filter(separation_type=filters['separation_type'])
            
        if filters.get('clearance_completed') == 'true':
            queryset = queryset.filter(clearance_completed=True)
        elif filters.get('clearance_completed') == 'false':
            queryset = queryset.filter(clearance_completed=False)
            
        if filters.get('final_settlement_completed') == 'true':
            queryset = queryset.filter(final_settlement_completed=True)
        elif filters.get('final_settlement_completed') == 'false':
            queryset = queryset.filter(final_settlement_completed=False)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:employee_separation_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_employeeseparation')
        context['can_view'] = self.request.user.has_perm('Hrm.view_employeeseparation')
        context['can_update'] = self.request.user.has_perm('Hrm.change_employeeseparation')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_employeeseparation')
        context['can_export'] = self.request.user.has_perm('Hrm.view_employeeseparation')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_employeeseparation')
        
        return context

class EmployeeSeparationCreateView(CreateView):
    model = EmployeeSeparation
    form_class = EmployeeSeparationForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Employee Separation'
        context['subtitle'] = 'Record employee separation'
        context['cancel_url'] = reverse_lazy('hrm:employee_separation_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Separation for {self.object.employee.get_full_name()} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_separation_detail', kwargs={'pk': self.object.pk})

class EmployeeSeparationUpdateView(UpdateView):
    model = EmployeeSeparation
    form_class = EmployeeSeparationForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Employee Separation'
        context['subtitle'] = f'Edit separation for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_separation_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Separation for {self.object.employee.get_full_name()} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_separation_detail', kwargs={'pk': self.object.pk})

class EmployeeSeparationDetailView(DetailView):
    model = EmployeeSeparation
    template_name = 'common/premium-form.html'
    context_object_name = 'employee_separation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Employee Separation Details'
        context['subtitle'] = f'Separation for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_separation_list')
        context['update_url'] = reverse_lazy('hrm:employee_separation_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:employee_separation_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = EmployeeSeparationForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class EmployeeSeparationDeleteView(GenericDeleteView):
    model = EmployeeSeparation
    success_url = reverse_lazy('hrm:employee_separation_list')
    permission_required = 'Hrm.delete_employeeseparation'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Employee Separation detail view."""
        return reverse_lazy('hrm:employee_separation_detail', kwargs={'pk': self.object.pk})

class EmployeeSeparationExportView(BaseExportView):
    """Export view for Employee Separation."""
    model = EmployeeSeparation
    filename = "employee_separations.csv"
    permission_required = "Hrm.view_employeeseparation"
    field_names = ["Employee", "Separation Type", "Separation Date", "Clearance Completed", "Final Settlement Completed"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class EmployeeSeparationBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Employee Separations."""
    model = EmployeeSeparation
    permission_required = "Hrm.delete_employeeseparation"
    display_fields = ["employee", "separation_type", "separation_date", "clearance_completed", "final_settlement_completed"]
    cancel_url = reverse_lazy("hrm:employee_separation_list")
    success_url = reverse_lazy("hrm:employee_separation_list")

