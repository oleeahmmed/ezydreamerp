from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from Hrm.models import Shift
from Hrm.forms import ShiftForm, ShiftFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class ShiftListView(GenericFilterView):
    model = Shift
    template_name = 'roster/shift_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = ShiftFilterForm
    permission_required = 'Hrm.view_shift'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                name__icontains=filters['search']
            )
            
        if filters.get('start_time_from'):
            queryset = queryset.filter(start_time__gte=filters['start_time_from'])
            
        if filters.get('start_time_to'):
            queryset = queryset.filter(start_time__lte=filters['start_time_to'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:shift_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_shift')
        context['can_view'] = self.request.user.has_perm('Hrm.view_shift')
        context['can_update'] = self.request.user.has_perm('Hrm.change_shift')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_shift')
        context['can_export'] = self.request.user.has_perm('Hrm.view_shift')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_shift')
        
        return context

class ShiftCreateView(CreateView):
    model = Shift
    form_class = ShiftForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Shift'
        context['subtitle'] = 'Add a new shift to the system'
        context['cancel_url'] = reverse_lazy('hrm:shift_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Shift {self.object.name} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:shift_detail', kwargs={'pk': self.object.pk})

class ShiftUpdateView(UpdateView):
    model = Shift
    form_class = ShiftForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Shift'
        context['subtitle'] = f'Edit shift {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:shift_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Shift {self.object.name} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:shift_detail', kwargs={'pk': self.object.pk})

class ShiftDetailView(DetailView):
    model = Shift
    template_name = 'common/premium-form.html'
    context_object_name = 'shift'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Shift Details'
        context['subtitle'] = f'Shift: {self.object.name}'
        context['cancel_url'] = reverse_lazy('hrm:shift_list')
        context['update_url'] = reverse_lazy('hrm:shift_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:shift_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = ShiftForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class ShiftDeleteView(GenericDeleteView):
    model = Shift
    success_url = reverse_lazy('hrm:shift_list')
    permission_required = 'Hrm.delete_shift'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Shift detail view."""
        return reverse_lazy('hrm:shift_detail', kwargs={'pk': self.object.pk})

class ShiftExportView(BaseExportView):
    """Export view for Shift."""
    model = Shift
    filename = "shifts.csv"
    permission_required = "Hrm.view_shift"
    field_names = ["Name", "Start Time", "End Time", "Break Time", "Grace Time", "Duration"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class ShiftBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Shifts."""
    model = Shift
    permission_required = "Hrm.delete_shift"
    display_fields = ["name", "start_time", "end_time", "duration"]
    cancel_url = reverse_lazy("hrm:shift_list")
    success_url = reverse_lazy("hrm:shift_list")

