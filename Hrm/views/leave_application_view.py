from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import LeaveApplication
from ..forms import LeaveApplicationForm, LeaveApplicationFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class LeaveApplicationListView(GenericFilterView):
    model = LeaveApplication
    template_name = 'leave/leave_application_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = LeaveApplicationFilterForm
    permission_required = 'Hrm.view_leaveapplication'
    
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
            
        if filters.get('leave_type'):
            queryset = queryset.filter(leave_type=filters['leave_type'])
            
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
            
        if filters.get('date_from'):
            queryset = queryset.filter(start_date__gte=filters['date_from'])
            
        if filters.get('date_to'):
            queryset = queryset.filter(end_date__lte=filters['date_to'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:leave_application_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('hrm.add_leaveapplication')
        context['can_view'] = self.request.user.has_perm('hrm.view_leaveapplication')
        context['can_update'] = self.request.user.has_perm('hrm.change_leaveapplication')
        context['can_delete'] = self.request.user.has_perm('hrm.delete_leaveapplication')
        context['can_export'] = self.request.user.has_perm('hrm.view_leaveapplication')
        context['can_bulk_delete'] = self.request.user.has_perm('hrm.delete_leaveapplication')
        
        return context

class LeaveApplicationCreateView(CreateView):
    model = LeaveApplication
    form_class = LeaveApplicationForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Leave Application'
        context['subtitle'] = 'Apply for leave'
        context['cancel_url'] = reverse_lazy('hrm:leave_application_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Leave application for {self.object.employee.get_full_name()} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:leave_application_detail', kwargs={'pk': self.object.pk})

class LeaveApplicationUpdateView(UpdateView):
    model = LeaveApplication
    form_class = LeaveApplicationForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Leave Application'
        context['subtitle'] = f'Edit leave application for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:leave_application_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Leave application for {self.object.employee.get_full_name()} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:leave_application_detail', kwargs={'pk': self.object.pk})

class LeaveApplicationDetailView(DetailView):
    model = LeaveApplication
    template_name = 'common/premium-form.html'
    context_object_name = 'leave_application'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Leave Application Details'
        context['subtitle'] = f'Leave application for {self.object.employee.get_full_name()}'
        context['cancel_url'] = reverse_lazy('hrm:leave_application_list')
        context['update_url'] = reverse_lazy('hrm:leave_application_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:leave_application_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = LeaveApplicationForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class LeaveApplicationDeleteView(GenericDeleteView):
    model = LeaveApplication
    success_url = reverse_lazy('hrm:leave_application_list')
    permission_required = 'hrm.delete_leaveapplication'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Leave Application detail view."""
        return reverse_lazy('hrm:leave_application_detail', kwargs={'pk': self.object.pk})

class LeaveApplicationExportView(BaseExportView):
    """Export view for Leave Application."""
    model = LeaveApplication
    filename = "leave_applications.csv"
    permission_required = "hrm.view_leaveapplication"
    field_names = ["Employee", "Leave Type", "Start Date", "End Date", "Status", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class LeaveApplicationBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Leave Applications."""
    model = LeaveApplication
    permission_required = "hrm.delete_leaveapplication"
    display_fields = ["employee", "leave_type", "start_date", "end_date", "status"]
    cancel_url = reverse_lazy("hrm:leave_application_list")
    success_url = reverse_lazy("hrm:leave_application_list")

