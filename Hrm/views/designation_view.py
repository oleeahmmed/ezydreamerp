from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import Designation
from ..forms import DesignationForm, DesignationFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class DesignationListView(GenericFilterView):
    model = Designation
    template_name = 'employee/designation_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = DesignationFilterForm
    permission_required = 'hrm.view_designation'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                name__icontains=filters['search']
            ) | queryset.filter(
                description__icontains=filters['search']
            )
            
        if filters.get('department'):
            queryset = queryset.filter(department=filters['department'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:designation_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('hrm.add_designation')
        context['can_view'] = self.request.user.has_perm('hrm.view_designation')
        context['can_update'] = self.request.user.has_perm('hrm.change_designation')
        context['can_delete'] = self.request.user.has_perm('hrm.delete_designation')
        context['can_export'] = self.request.user.has_perm('hrm.view_designation')
        context['can_bulk_delete'] = self.request.user.has_perm('hrm.delete_designation')
        
        return context

class DesignationCreateView(CreateView):
    model = Designation
    form_class = DesignationForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Designation'
        context['subtitle'] = 'Add a new designation to the system'
        context['cancel_url'] = reverse_lazy('hrm:designation_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Designation {self.object.name} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:designation_detail', kwargs={'pk': self.object.pk})

class DesignationUpdateView(UpdateView):
    model = Designation
    form_class = DesignationForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Designation'
        context['subtitle'] = f'Edit designation {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:designation_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Designation {self.object.name} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:designation_detail', kwargs={'pk': self.object.pk})

class DesignationDetailView(DetailView):
    model = Designation
    template_name = 'common/premium-form.html'
    context_object_name = 'designation'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Designation Details'
        context['subtitle'] = f'Designation: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:designation_list')
        context['update_url'] = reverse_lazy('hrm:designation_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:designation_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = DesignationForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class DesignationDeleteView(GenericDeleteView):
    model = Designation
    success_url = reverse_lazy('hrm:designation_list')
    permission_required = 'hrm.delete_designation'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Designation detail view."""
        return reverse_lazy('hrm:designation_detail', kwargs={'pk': self.object.pk})

class DesignationExportView(BaseExportView):
    """Export view for Designation."""
    model = Designation
    filename = "designations.csv"
    permission_required = "hrm.view_designation"
    field_names = ["Name", "Department", "Description", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class DesignationBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Designations."""
    model = Designation
    permission_required = "hrm.delete_designation"
    display_fields = ["name", "department", "created_at"]
    cancel_url = reverse_lazy("hrm:designation_list")
    success_url = reverse_lazy("hrm:designation_list")

