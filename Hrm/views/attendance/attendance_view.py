from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from Hrm.models import Attendance
from Hrm.forms import AttendanceForm, AttendanceFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class AttendanceListView(GenericFilterView):
    model = Attendance
    template_name = 'attendance/attendance_list.html'
    context_object_name = 'objects'
    paginate_by = 30
    filter_form_class = AttendanceFilterForm
    permission_required = 'Hrm.view_attendance'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
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
        context['create_url'] = reverse_lazy('hrm:attendance_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_attendance')
        context['can_view'] = self.request.user.has_perm('Hrm.view_attendance')
        context['can_update'] = self.request.user.has_perm('Hrm.change_attendance')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_attendance')
        context['can_export'] = self.request.user.has_perm('Hrm.view_attendance')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_attendance')
        
        return context

class AttendanceCreateView(CreateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Attendance'
        context['subtitle'] = 'Record employee attendance'
        context['cancel_url'] = reverse_lazy('hrm:attendance_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Attendance for {self.object.employee.get_full_name()} on {self.object.date} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:attendance_detail', kwargs={'pk': self.object.pk})

class AttendanceUpdateView(UpdateView):
    model = Attendance
    form_class = AttendanceForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Attendance'
        context['subtitle'] = f'Edit attendance for {self.object.employee.get_full_name()} on {self.object.date}'
        context['cancel_url'] = reverse_lazy('hrm:attendance_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Attendance for {self.object.employee.get_full_name()} on {self.object.date} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:attendance_detail', kwargs={'pk': self.object.pk})

class AttendanceDetailView(DetailView):
    model = Attendance
    template_name = 'common/premium-form.html'
    context_object_name = 'attendance'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Attendance Details'
        context['subtitle'] = f'Attendance for {self.object.employee.get_full_name()} on {self.object.date}'
        context['cancel_url'] = reverse_lazy('hrm:attendance_list')
        context['update_url'] = reverse_lazy('hrm:attendance_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:attendance_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = AttendanceForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class AttendanceDeleteView(GenericDeleteView):
    model = Attendance
    success_url = reverse_lazy('hrm:attendance_list')
    permission_required = 'Hrm.delete_attendance'

    def get_cancel_url(self):
        """Override cancel URL to redirect to Attendance detail view."""
        return reverse_lazy('hrm:attendance_detail', kwargs={'pk': self.object.pk})

class AttendanceExportView(BaseExportView):
    """Export view for Attendance."""
    model = Attendance
    filename = "attendance.csv"
    permission_required = "Hrm.view_attendance"
    field_names = ["Employee", "Date", "Status", "Check In", "Check Out", "Working Hours", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class AttendanceBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for Attendance."""
    model = Attendance
    permission_required = "Hrm.delete_attendance"
    display_fields = ["employee", "date", "status", "check_in", "check_out"]
    cancel_url = reverse_lazy("hrm:attendance_list")
    success_url = reverse_lazy("hrm:attendance_list")

