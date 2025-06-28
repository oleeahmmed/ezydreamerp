from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import Location
from ..forms.location_forms import LocationForm, LocationFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class LocationListView(GenericFilterView):
    model = Location
    template_name = 'location/location_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = LocationFilterForm
    permission_required = 'Hrm.view_location'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('name'):
            queryset = queryset.filter(name__icontains=filters['name'])
            
        if filters.get('is_active') is not None:
            queryset = queryset.filter(is_active=filters['is_active'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:location_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('hrm.add_location')
        context['can_view'] = self.request.user.has_perm('hrm.view_location')
        context['can_update'] = self.request.user.has_perm('hrm.change_location')
        context['can_delete'] = self.request.user.has_perm('hrm.delete_location')
        context['can_export'] = self.request.user.has_perm('hrm.view_location')
        context['can_bulk_delete'] = self.request.user.has_perm('hrm.delete_location')
        
        return context

class LocationCreateView(CreateView):
    model = Location
    form_class = LocationForm
    template_name = 'location/location_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Location'
        context['subtitle'] = 'Add a new location for attendance tracking'
        context['cancel_url'] = reverse_lazy('hrm:location_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Location "{self.object.name}" created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:location_detail', kwargs={'pk': self.object.pk})

class LocationUpdateView(UpdateView):
    model = Location
    form_class = LocationForm
    template_name = 'location/location_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Location'
        context['subtitle'] = f'Edit location "{self.object.name}"'
        context['cancel_url'] = reverse_lazy('hrm:location_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Location "{self.object.name}" updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:location_detail', kwargs={'pk': self.object.pk})

class LocationDetailView(DetailView):
    model = Location
    template_name = 'location/location_form.html'
    context_object_name = 'location'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Location Details'
        context['subtitle'] = f'Location: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:location_list')
        context['update_url'] = reverse_lazy('hrm:location_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:location_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = LocationForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class LocationDeleteView(GenericDeleteView):
    model = Location
    success_url = reverse_lazy('hrm:location_list')
    permission_required = 'hrm.delete_location'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Location detail view."""
        return reverse_lazy('hrm:location_detail', kwargs={'pk': self.object.pk})

class LocationExportView(BaseExportView):
    """Export view for Location."""
    model = Location
    filename = "locations.csv"
    permission_required = "hrm.view_location"
    field_names = ["Name", "Address", "Latitude", "Longitude", "Radius", "Is Active", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class LocationBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Location."""
    model = Location
    permission_required = "hrm.delete_location"
    display_fields = ["name", "address", "latitude", "longitude", "radius", "is_active"]
    cancel_url = reverse_lazy("hrm:location_list")
    success_url = reverse_lazy("hrm:location_list")