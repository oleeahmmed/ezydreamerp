from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import Increment
from ..forms import IncrementForm, PayrollFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class IncrementListView(GenericFilterView):
    model = Increment
    template_name = 'payroll/increment_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PayrollFilterForm
    permission_required = 'Hrm.view_increment'
    
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
            queryset = queryset.filter(effective_date__gte=filters['from_date'])
            
        if filters.get('to_date'):
            queryset = queryset.filter(effective_date__lte=filters['to_date'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:increment_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_increment')
        context['can_view'] = self.request.user.has_perm('Hrm.view_increment')
        context['can_update'] = self.request.user.has_perm('Hrm.change_increment')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_increment')
        context['can_export'] = self.request.user.has_perm('Hrm.view_increment')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_increment')
        
        return context

class IncrementCreateView(CreateView):
    model = Increment
    form_class = IncrementForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Increment'
        context['subtitle'] = 'Add a new increment to the system'
        context['cancel_url'] = reverse_lazy('hrm:increment_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Increment for {self.object.employee.get_full_name()} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:increment_detail', kwargs={'pk': self.object.pk})

class IncrementUpdateView(UpdateView):
    model = Increment
    form_class = IncrementForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Increment'
        context['subtitle'] = f'Edit increment for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:increment_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Increment for {self.object.employee.get_full_name()} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:increment_detail', kwargs={'pk': self.object.pk})

class IncrementDetailView(DetailView):
    model = Increment
    template_name = 'common/premium-form.html'
    context_object_name = 'increment'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Increment Details'
        context['subtitle'] = f'Increment for: {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:increment_list')
        context['update_url'] = reverse_lazy('hrm:increment_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:increment_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = IncrementForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class IncrementDeleteView(GenericDeleteView):
    model = Increment
    success_url = reverse_lazy('hrm:increment_list')
    permission_required = 'Hrm.delete_increment'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Increment detail view."""
        return reverse_lazy('hrm:increment_detail', kwargs={'pk': self.object.pk})

class IncrementExportView(BaseExportView):
    """Export view for Increment."""
    model = Increment
    filename = "increments.csv"
    permission_required = "Hrm.view_increment"
    field_names = ["Employee", "Previous Salary", "Increment Amount", "New Salary", "Effective Date", "Remarks", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class IncrementBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Increments."""
    model = Increment
    permission_required = "Hrm.delete_increment"
    display_fields = ["employee__employee_id", "employee__first_name", "previous_salary", "increment_amount", "new_salary", "effective_date"]
    cancel_url = reverse_lazy("hrm:increment_list")
    success_url = reverse_lazy("hrm:increment_list")

