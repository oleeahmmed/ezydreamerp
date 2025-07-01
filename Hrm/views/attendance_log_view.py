from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import AttendanceLog
from ..forms import AttendanceLogForm, AttendanceFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class AttendanceLogListView(GenericFilterView):
    model = AttendanceLog
    template_name = 'attendance/attendance_log_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = AttendanceFilterForm
    permission_required = 'hrm.view_attendancelog'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                notes__icontains=filters['search']
            ) | queryset.filter(
                location__icontains=filters['search']
            ) | queryset.filter(
                device__icontains=filters['search']
            )
            
        if filters.get('employee'):
            queryset = queryset.filter(employee=filters['employee'])
            
        if filters.get('date_from'):
            queryset = queryset.filter(timestamp__date__gte=filters['date_from'])
            
        if filters.get('date_to'):
            queryset = queryset.filter(timestamp__date__lte=filters['date_to'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:attendance_log_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('hrm.add_attendancelog')
        context['can_view'] = self.request.user.has_perm('hrm.view_attendancelog')
        context['can_update'] = self.request.user.has_perm('hrm.change_attendancelog')
        context['can_delete'] = self.request.user.has_perm('hrm.delete_attendancelog')
        context['can_export'] = self.request.user.has_perm('hrm.view_attendancelog')
        context['can_bulk_delete'] = self.request.user.has_perm('hrm.delete_attendancelog')
        
        return context

class AttendanceLogCreateView(CreateView):
    model = AttendanceLog
    form_class = AttendanceLogForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Attendance Log'
        context['subtitle'] = 'Add a new attendance log to the system'
        context['cancel_url'] = reverse_lazy('hrm:attendance_log_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        log_type = "Check-in" if self.object.is_in else "Check-out"
        messages.success(self.request, f'{log_type} for {self.object.employee.get_full_name()} at {self.object.timestamp} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:attendance_log_detail', kwargs={'pk': self.object.pk})

class AttendanceLogUpdateView(UpdateView):
    model = AttendanceLog
    form_class = AttendanceLogForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        log_type = "Check-in" if self.object.is_in else "Check-out"
        context['title'] = 'Update Attendance Log'
        context['subtitle'] = f'Edit {log_type} for {self.object.employee.get_full_name()} at {self.object.timestamp}'
        context['cancel_url'] = reverse_lazy('hrm:attendance_log_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        log_type = "Check-in" if self.object.is_in else "Check-out"
        messages.success(self.request, f'{log_type} for {self.object.employee.get_full_name()} at {self.object.timestamp} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:attendance_log_detail', kwargs={'pk': self.object.pk})

class AttendanceLogDetailView(DetailView):
    model = AttendanceLog
    template_name = 'common/premium-form.html'
    context_object_name = 'attendance_log'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        log_type = "Check-in" if self.object.is_in else "Check-out"
        context['title'] = 'Attendance Log Details'
        context['subtitle'] = f'{log_type} for {self.object.employee.get_full_name()} at {self.object.timestamp}'
        context['cancel_url'] = reverse_lazy('hrm:attendance_log_list')
        context['update_url'] = reverse_lazy('hrm:attendance_log_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:attendance_log_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = AttendanceLogForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class AttendanceLogDeleteView(GenericDeleteView):
    model = AttendanceLog
    success_url = reverse_lazy('hrm:attendance_log_list')
    permission_required = 'hrm.delete_attendancelog'

    def get_cancel_url(self):
        """Override cancel URL to redirect to AttendanceLog detail view."""
        return reverse_lazy('hrm:attendance_log_detail', kwargs={'pk': self.object.pk})

class AttendanceLogExportView(BaseExportView):
    """Export view for AttendanceLog."""
    model = AttendanceLog
    filename = "attendance_logs.csv"
    permission_required = "hrm.view_attendancelog"
    field_names = ["Employee", "Timestamp", "Type", "Location", "Device", "Notes", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class AttendanceLogBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for AttendanceLog."""
    model = AttendanceLog
    permission_required = "hrm.delete_attendancelog"
    display_fields = ["employee", "timestamp", "is_in", "location", "device"]
    cancel_url = reverse_lazy("hrm:attendance_log_list")
    success_url = reverse_lazy("hrm:attendance_log_list")

