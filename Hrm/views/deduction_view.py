
from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import Deduction
from ..forms import DeductionForm, PayrollFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class DeductionListView(GenericFilterView):
    model = Deduction
    template_name = 'payroll/deduction_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PayrollFilterForm
    permission_required = 'Hrm.view_deduction'
    
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
            ) | queryset.filter(
                description__icontains=filters['search']
            )
            
        if filters.get('department'):
            queryset = queryset.filter(employee__department=filters['department'])
            
        if filters.get('from_date'):
            queryset = queryset.filter(deduction_date__gte=filters['from_date'])
            
        if filters.get('to_date'):
            queryset = queryset.filter(deduction_date__lte=filters['to_date'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:deduction_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_deduction')
        context['can_view'] = self.request.user.has_perm('Hrm.view_deduction')
        context['can_update'] = self.request.user.has_perm('Hrm.change_deduction')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_deduction')
        context['can_export'] = self.request.user.has_perm('Hrm.view_deduction')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_deduction')
        
        return context

class DeductionCreateView(CreateView):
    model = Deduction
    form_class = DeductionForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Deduction'
        context['subtitle'] = 'Add a new deduction to the system'
        context['cancel_url'] = reverse_lazy('hrm:deduction_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Deduction for {self.object.employee.get_full_name()} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:deduction_detail', kwargs={'pk': self.object.pk})

class DeductionUpdateView(UpdateView):
    model = Deduction
    form_class = DeductionForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Deduction'
        context['subtitle'] = f'Edit deduction for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:deduction_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Deduction for {self.object.employee.get_full_name()} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:deduction_detail', kwargs={'pk': self.object.pk})

class DeductionDetailView(DetailView):
    model = Deduction
    template_name = 'common/premium-form.html'
    context_object_name = 'deduction'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Deduction Details'
        context['subtitle'] = f'Deduction for: {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:deduction_list')
        context['update_url'] = reverse_lazy('hrm:deduction_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:deduction_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = DeductionForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class DeductionDeleteView(GenericDeleteView):
    model = Deduction
    success_url = reverse_lazy('hrm:deduction_list')
    permission_required = 'Hrm.delete_deduction'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Deduction detail view."""
        return reverse_lazy('hrm:deduction_detail', kwargs={'pk': self.object.pk})

class DeductionExportView(BaseExportView):
    """Export view for Deduction."""
    model = Deduction
    filename = "deductions.csv"
    permission_required = "Hrm.view_deduction"
    field_names = ["Employee", "Deduction Date", "Amount", "Description", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class DeductionBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Deductions."""
    model = Deduction
    permission_required = "Hrm.delete_deduction"
    display_fields = ["employee__employee_id", "employee__first_name", "deduction_date", "amount", "description"]
    cancel_url = reverse_lazy("hrm:deduction_list")
    success_url = reverse_lazy("hrm:deduction_list")