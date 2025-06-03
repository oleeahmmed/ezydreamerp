from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import EmployeeBonus
from ..forms import EmployeeBonusForm, PayrollFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class EmployeeBonusListView(GenericFilterView):
    model = EmployeeBonus
    template_name = 'payroll/employee_bonus_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PayrollFilterForm
    permission_required = 'Hrm.view_employeebonus'
    
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
                bonus_month__bonus_setup__name__icontains=filters['search']
            )
            
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
            
        if filters.get('year'):
            queryset = queryset.filter(bonus_month__year=filters['year'])
            
        if filters.get('month'):
            queryset = queryset.filter(bonus_month__month=filters['month'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:employee_bonus_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_employeebonus')
        context['can_view'] = self.request.user.has_perm('Hrm.view_employeebonus')
        context['can_update'] = self.request.user.has_perm('Hrm.change_employeebonus')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_employeebonus')
        context['can_export'] = self.request.user.has_perm('Hrm.view_employeebonus')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_employeebonus')
        
        return context

class EmployeeBonusCreateView(CreateView):
    model = EmployeeBonus
    form_class = EmployeeBonusForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Employee Bonus'
        context['subtitle'] = 'Add a new employee bonus to the system'
        context['cancel_url'] = reverse_lazy('hrm:employee_bonus_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Bonus for {self.object.employee.get_full_name()} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_bonus_detail', kwargs={'pk': self.object.pk})

class EmployeeBonusUpdateView(UpdateView):
    model = EmployeeBonus
    form_class = EmployeeBonusForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Employee Bonus'
        context['subtitle'] = f'Edit bonus for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_bonus_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Bonus for {self.object.employee.get_full_name()} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:employee_bonus_detail', kwargs={'pk': self.object.pk})

class EmployeeBonusDetailView(DetailView):
    model = EmployeeBonus
    template_name = 'common/premium-form.html'
    context_object_name = 'employee_bonus'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Employee Bonus Details'
        context['subtitle'] = f'Bonus for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:employee_bonus_list')
        context['update_url'] = reverse_lazy('hrm:employee_bonus_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:employee_bonus_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = EmployeeBonusForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class EmployeeBonusDeleteView(GenericDeleteView):
    model = EmployeeBonus
    success_url = reverse_lazy('hrm:employee_bonus_list')
    permission_required = 'Hrm.delete_employeebonus'

    def get_cancel_url(self):
        """Override cancel URL to redirect to EmployeeBonus detail view."""
        return reverse_lazy('hrm:employee_bonus_detail', kwargs={'pk': self.object.pk})

class EmployeeBonusExportView(BaseExportView):
    """Export view for EmployeeBonus."""
    model = EmployeeBonus
    filename = "employee_bonuses.csv"
    permission_required = "Hrm.view_employeebonus"
    field_names = ["Employee", "Bonus Month", "Amount", "Remarks", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class EmployeeBonusBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for EmployeeBonus."""
    model = EmployeeBonus
    permission_required = "Hrm.delete_employeebonus"
    display_fields = ["employee", "bonus_month", "amount", "created_at"]
    cancel_url = reverse_lazy("hrm:employee_bonus_list")
    success_url = reverse_lazy("hrm:employee_bonus_list")

