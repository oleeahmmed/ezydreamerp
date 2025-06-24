from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from Hrm.models import WorkPlace
from Hrm.forms import WorkPlaceForm, WorkPlaceFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class WorkPlaceListView(GenericFilterView):
    model = WorkPlace
    template_name = 'roster/workplace_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = WorkPlaceFilterForm
    permission_required = 'Hrm.view_workplace'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                name__icontains=filters['search']
            ) | queryset.filter(
                address__icontains=filters['search']
            ) | queryset.filter(
                description__icontains=filters['search']
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:workplace_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_workplace')
        context['can_view'] = self.request.user.has_perm('Hrm.view_workplace')
        context['can_update'] = self.request.user.has_perm('Hrm.change_workplace')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_workplace')
        context['can_export'] = self.request.user.has_perm('Hrm.view_workplace')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_workplace')
        
        return context

class WorkPlaceCreateView(CreateView):
    model = WorkPlace
    form_class = WorkPlaceForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Workplace'
        context['subtitle'] = 'Add a new workplace to the system'
        context['cancel_url'] = reverse_lazy('hrm:workplace_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Workplace {self.object.name} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:workplace_detail', kwargs={'pk': self.object.pk})

class WorkPlaceUpdateView(UpdateView):
    model = WorkPlace
    form_class = WorkPlaceForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Workplace'
        context['subtitle'] = f'Edit workplace {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:workplace_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Workplace {self.object.name} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:workplace_detail', kwargs={'pk': self.object.pk})

class WorkPlaceDetailView(DetailView):
    model = WorkPlace
    template_name = 'common/premium-form.html'
    context_object_name = 'workplace'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Workplace Details'
        context['subtitle'] = f'Workplace: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:workplace_list')
        context['update_url'] = reverse_lazy('hrm:workplace_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:workplace_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = WorkPlaceForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class WorkPlaceDeleteView(GenericDeleteView):
    model = WorkPlace
    success_url = reverse_lazy('hrm:workplace_list')
    permission_required = 'Hrm.delete_workplace'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Workplace detail view."""
        return reverse_lazy('hrm:workplace_detail', kwargs={'pk': self.object.pk})

class WorkPlaceExportView(BaseExportView):
    """Export view for Workplace."""
    model = WorkPlace
    filename = "workplaces.csv"
    permission_required = "Hrm.view_workplace"
    field_names = ["Name", "Address", "Description", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class WorkPlaceBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Workplaces."""
    model = WorkPlace
    permission_required = "Hrm.delete_workplace"
    display_fields = ["name", "address", "created_at"]
    cancel_url = reverse_lazy("hrm:workplace_list")
    success_url = reverse_lazy("hrm:workplace_list")

