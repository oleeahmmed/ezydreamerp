from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import SalaryComponent
from ..forms import SalaryComponentForm, PayrollFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class SalaryComponentListView(GenericFilterView):
    model = SalaryComponent
    template_name = 'payroll/salary_component_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = PayrollFilterForm
    permission_required = 'Hrm.view_salarycomponent'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                name__icontains=filters['search']
            ) | queryset.filter(
                code__icontains=filters['search']
            ) | queryset.filter(
                description__icontains=filters['search']
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:salary_component_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_salarycomponent')
        context['can_view'] = self.request.user.has_perm('Hrm.view_salarycomponent')
        context['can_update'] = self.request.user.has_perm('Hrm.change_salarycomponent')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_salarycomponent')
        context['can_export'] = self.request.user.has_perm('Hrm.view_salarycomponent')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_salarycomponent')
        
        return context

class SalaryComponentCreateView(CreateView):
    model = SalaryComponent
    form_class = SalaryComponentForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Salary Component'
        context['subtitle'] = 'Add a new salary component to the system'
        context['cancel_url'] = reverse_lazy('hrm:salary_component_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Salary Component {self.object.name} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:salary_component_detail', kwargs={'pk': self.object.pk})

class SalaryComponentUpdateView(UpdateView):
    model = SalaryComponent
    form_class = SalaryComponentForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Salary Component'
        context['subtitle'] = f'Edit salary component {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:salary_component_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Salary Component {self.object.name} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:salary_component_detail', kwargs={'pk': self.object.pk})

class SalaryComponentDetailView(DetailView):
    model = SalaryComponent
    template_name = 'common/premium-form.html'
    context_object_name = 'salary_component'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Salary Component Details'
        context['subtitle'] = f'Salary Component: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:salary_component_list')
        context['update_url'] = reverse_lazy('hrm:salary_component_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:salary_component_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = SalaryComponentForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class SalaryComponentDeleteView(GenericDeleteView):
    model = SalaryComponent
    success_url = reverse_lazy('hrm:salary_component_list')
    permission_required = 'Hrm.delete_salarycomponent'

    def get_cancel_url(self):
        """Override cancel URL to redirect to SalaryComponent detail view."""
        return reverse_lazy('hrm:salary_component_detail', kwargs={'pk': self.object.pk})

class SalaryComponentExportView(BaseExportView):
    """Export view for SalaryComponent."""
    model = SalaryComponent
    filename = "salary_components.csv"
    permission_required = "Hrm.view_salarycomponent"
    field_names = ["Name", "Code", "Component Type", "Is Taxable", "Is Fixed", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class SalaryComponentBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for SalaryComponent."""
    model = SalaryComponent
    permission_required = "Hrm.delete_salarycomponent"
    display_fields = ["name", "code", "component_type", "is_taxable", "is_fixed"]
    cancel_url = reverse_lazy("hrm:salary_component_list")
    success_url = reverse_lazy("hrm:salary_component_list")

