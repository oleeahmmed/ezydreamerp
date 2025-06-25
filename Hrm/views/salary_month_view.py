from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import SalaryMonth
from ..forms import SalaryMonthForm, PayrollFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class SalaryMonthListView(GenericFilterView):
    model = SalaryMonth
    template_name = 'payroll/salary_month_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PayrollFilterForm
    permission_required = 'Hrm.view_salarymonth'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                name__icontains=filters['search']
            )
            
        if filters.get('from_date'):
            queryset = queryset.filter(start_date__gte=filters['from_date'])
            
        if filters.get('to_date'):
            queryset = queryset.filter(end_date__lte=filters['to_date'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:salary_month_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_salarymonth')
        context['can_view'] = self.request.user.has_perm('Hrm.view_salarymonth')
        context['can_update'] = self.request.user.has_perm('Hrm.change_salarymonth')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_salarymonth')
        context['can_export'] = self.request.user.has_perm('Hrm.view_salarymonth')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_salarymonth')
        
        return context

class SalaryMonthCreateView(CreateView):
    model = SalaryMonth
    form_class = SalaryMonthForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Salary Month'
        context['subtitle'] = 'Add a new salary month to the system'
        context['cancel_url'] = reverse_lazy('hrm:salary_month_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Salary Month {self.object.id} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:salary_month_detail', kwargs={'pk': self.object.pk})

class SalaryMonthUpdateView(UpdateView):
    model = SalaryMonth
    form_class = SalaryMonthForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Salary Month'
        context['subtitle'] = f'Edit salary month {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:salary_month_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Salary Month {self.object.name} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:salary_month_detail', kwargs={'pk': self.object.pk})

class SalaryMonthDetailView(DetailView):
    model = SalaryMonth
    template_name = 'common/premium-form.html'
    context_object_name = 'salary_month'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Salary Month Details'
        context['subtitle'] = f'Salary Month: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:salary_month_list')
        context['update_url'] = reverse_lazy('hrm:salary_month_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:salary_month_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = SalaryMonthForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class SalaryMonthDeleteView(GenericDeleteView):
    model = SalaryMonth
    success_url = reverse_lazy('hrm:salary_month_list')
    permission_required = 'Hrm.delete_salarymonth'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Salary Month detail view."""
        return reverse_lazy('hrm:salary_month_detail', kwargs={'pk': self.object.pk})

class SalaryMonthExportView(BaseExportView):
    """Export view for Salary Month."""
    model = SalaryMonth
    filename = "salary_months.csv"
    permission_required = "Hrm.view_salarymonth"
    field_names = ["Name", "Start Date", "End Date", "Status", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class SalaryMonthBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Salary Months."""
    model = SalaryMonth
    permission_required = "Hrm.delete_salarymonth"
    display_fields = ["name", "start_date", "end_date", "status", "created_at"]
    cancel_url = reverse_lazy("hrm:salary_month_list")
    success_url = reverse_lazy("hrm:salary_month_list")