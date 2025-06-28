from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import Department
from ..forms import DepartmentForm, DepartmentFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class DepartmentListView(GenericFilterView):
    model = Department
    template_name = 'employee/department_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = DepartmentFilterForm
    permission_required = 'hrm.view_department'
    
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
            
        if filters.get('code'):
            queryset = queryset.filter(code__icontains=filters['code'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:department_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('hrm.add_department')
        context['can_view'] = self.request.user.has_perm('hrm.view_department')
        context['can_update'] = self.request.user.has_perm('hrm.change_department')
        context['can_delete'] = self.request.user.has_perm('hrm.delete_department')
        context['can_export'] = self.request.user.has_perm('hrm.view_department')
        context['can_bulk_delete'] = self.request.user.has_perm('hrm.delete_department')
        
        return context

class DepartmentCreateView(CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Department'
        context['subtitle'] = 'Add a new department to the system'
        context['cancel_url'] = reverse_lazy('hrm:department_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Department {self.object.name} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:department_detail', kwargs={'pk': self.object.pk})

class DepartmentUpdateView(UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Department'
        context['subtitle'] = f'Edit department {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:department_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Department {self.object.name} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:department_detail', kwargs={'pk': self.object.pk})

class DepartmentDetailView(DetailView):
    model = Department
    template_name = 'common/premium-form.html'
    context_object_name = 'department'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Department Details'
        context['subtitle'] = f'Department: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:department_list')
        context['update_url'] = reverse_lazy('hrm:department_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:department_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = DepartmentForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class DepartmentDeleteView(GenericDeleteView):
    model = Department
    success_url = reverse_lazy('hrm:department_list')
    permission_required = 'hrm.delete_department'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Department detail view."""
        return reverse_lazy('hrm:department_detail', kwargs={'pk': self.object.pk})

class DepartmentExportView(BaseExportView):
    """Export view for Department."""
    model = Department
    filename = "departments.csv"
    permission_required = "hrm.view_department"
    field_names = ["Name", "Code", "Description", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class DepartmentBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Departments."""
    model = Department
    permission_required = "hrm.delete_department"
    display_fields = ["name", "code", "created_at"]
    cancel_url = reverse_lazy("hrm:department_list")
    success_url = reverse_lazy("hrm:department_list")

