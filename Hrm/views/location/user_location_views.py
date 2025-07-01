from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from Hrm.models import UserLocation
from Hrm.forms.location_forms import UserLocationForm, UserLocationFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class UserLocationListView(GenericFilterView):
    model = UserLocation
    template_name = 'location/user_location_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = UserLocationFilterForm
    permission_required = 'Hrm.view_userlocation'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('user'):
            queryset = queryset.filter(user=filters['user'])
            
        if filters.get('location'):
            queryset = queryset.filter(location=filters['location'])
            

            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:user_location_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_userlocation')
        context['can_view'] = self.request.user.has_perm('Hrm.view_userlocation')
        context['can_update'] = self.request.user.has_perm('Hrm.change_userlocation')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_userlocation')
        context['can_export'] = self.request.user.has_perm('Hrm.view_userlocation')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_userlocation')
        
        return context

class UserLocationCreateView(CreateView):
    model = UserLocation
    form_class = UserLocationForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Assign Location to User'
        context['subtitle'] = 'Assign a location to a user for attendance tracking'
        context['cancel_url'] = reverse_lazy('hrm:user_location_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        
        # If this is set as primary, update other user locations to not be primary
        if self.object.is_primary:
            UserLocation.objects.filter(
                user=self.object.user
            ).exclude(
                pk=self.object.pk
            ).update(is_primary=False)
            
        messages.success(self.request, f'Location "{self.object.location.name}" assigned to {self.object.user.username} successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:user_location_detail', kwargs={'pk': self.object.pk})

class UserLocationUpdateView(UpdateView):
    model = UserLocation
    form_class = UserLocationForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update User Location'
        context['subtitle'] = f'Edit location assignment for {self.object.user.username}'
        context['cancel_url'] = reverse_lazy('hrm:user_location_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        
        # If this is set as primary, update other user locations to not be primary
        if self.object.is_primary:
            UserLocation.objects.filter(
                user=self.object.user
            ).exclude(
                pk=self.object.pk
            ).update(is_primary=False)
            
        messages.success(self.request, f'Location assignment for {self.object.user.username} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:user_location_detail', kwargs={'pk': self.object.pk})

class UserLocationDetailView(DetailView):
    model = UserLocation
    template_name = 'common/premium-form.html'
    context_object_name = 'user_location'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'User Location Details'
        context['subtitle'] = f'Location assignment: {self.object.user.username} - {self.object.location.name}'
        context['cancel_url'] = reverse_lazy('hrm:user_location_list')
        context['update_url'] = reverse_lazy('hrm:user_location_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:user_location_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = UserLocationForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class UserLocationDeleteView(GenericDeleteView):
    model = UserLocation
    success_url = reverse_lazy('hrm:user_location_list')
    permission_required = 'Hrm.delete_userlocation'

    def get_cancel_url(self):
        """Override cancel URL to redirect to UserLocation detail view."""
        return reverse_lazy('hrm:user_location_detail', kwargs={'pk': self.object.pk})

class UserLocationExportView(BaseExportView):
    """Export view for UserLocation."""
    model = UserLocation
    filename = "user_locations.csv"
    permission_required = "Hrm.view_userlocation"
    field_names = ["User", "Location", "Is Primary", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class UserLocationBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for UserLocation."""
    model = UserLocation
    permission_required = "Hrm.delete_userlocation"
    display_fields = ["user", "location", "is_primary", "created_at"]
    cancel_url = reverse_lazy("hrm:user_location_list")
    success_url = reverse_lazy("hrm:user_location_list")