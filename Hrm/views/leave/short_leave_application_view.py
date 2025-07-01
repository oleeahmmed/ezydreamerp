from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from Hrm.models import ShortLeaveApplication
from Hrm.forms import ShortLeaveApplicationForm, ShortLeaveApplicationFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class ShortLeaveApplicationListView(GenericFilterView):
    model = ShortLeaveApplication
    template_name = 'leave/short_leave_application_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = ShortLeaveApplicationFilterForm
    permission_required = 'Hrm.view_shortleaveapplication'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                reason__icontains=filters['search']
            ) | queryset.filter(
                remarks__icontains=filters['search']
            )
            
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
            
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
            
        if filters.get('date_from'):
            queryset = queryset.filter(date__gte=filters['date_from'])
            
        if filters.get('date_to'):
            queryset = queryset.filter(date__lte=filters['date_to'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:short_leave_application_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_shortleaveapplication')
        context['can_view'] = self.request.user.has_perm('Hrm.view_shortleaveapplication')
        context['can_update'] = self.request.user.has_perm('Hrm.change_shortleaveapplication')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_shortleaveapplication')
        context['can_export'] = self.request.user.has_perm('Hrm.view_shortleaveapplication')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_shortleaveapplication')
        
        return context

class ShortLeaveApplicationCreateView(CreateView):
    model = ShortLeaveApplication
    form_class = ShortLeaveApplicationForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Short Leave Application'
        context['subtitle'] = 'Apply for short leave'
        context['cancel_url'] = reverse_lazy('hrm:short_leave_application_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Short leave application for {self.object.employee.get_full_name()} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:short_leave_application_detail', kwargs={'pk': self.object.pk})

class ShortLeaveApplicationUpdateView(UpdateView):
    model = ShortLeaveApplication
    form_class = ShortLeaveApplicationForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Short Leave Application'
        context['subtitle'] = f'Edit short leave application for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:short_leave_application_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Short leave application for {self.object.employee.get_full_name()} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:short_leave_application_detail', kwargs={'pk': self.object.pk})

class ShortLeaveApplicationDetailView(DetailView):
    model = ShortLeaveApplication
    template_name = 'common/premium-form.html'
    context_object_name = 'short_leave_application'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Short Leave Application Details'
        context['subtitle'] = f'Short leave application for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:short_leave_application_list')
        context['update_url'] = reverse_lazy('hrm:short_leave_application_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:short_leave_application_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = ShortLeaveApplicationForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class ShortLeaveApplicationDeleteView(GenericDeleteView):
    model = ShortLeaveApplication
    success_url = reverse_lazy('hrm:short_leave_application_list')
    permission_required = 'Hrm.delete_shortleaveapplication'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Short Leave Application detail view."""
        return reverse_lazy('hrm:short_leave_application_detail', kwargs={'pk': self.object.pk})

class ShortLeaveApplicationExportView(BaseExportView):
    """Export view for Short Leave Application."""
    model = ShortLeaveApplication
    filename = "short_leave_applications.csv"
    permission_required = "Hrm.view_shortleaveapplication"
    field_names = ["Employee", "Date", "Start Time", "End Time", "Duration Hours", "Status", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class ShortLeaveApplicationBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Short Leave Applications."""
    model = ShortLeaveApplication
    permission_required = "Hrm.delete_shortleaveapplication"
    display_fields = ["employee", "date", "start_time", "end_time", "status"]
    cancel_url = reverse_lazy("hrm:short_leave_application_list")
    success_url = reverse_lazy("hrm:short_leave_application_list")

