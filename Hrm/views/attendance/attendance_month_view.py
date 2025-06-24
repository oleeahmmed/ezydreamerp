from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from Hrm.models import AttendanceMonth
from Hrm.forms import AttendanceMonthForm, AttendanceFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class AttendanceMonthListView(GenericFilterView):
    model = AttendanceMonth
    template_name = 'attendance/attendance_month_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = AttendanceFilterForm
    permission_required = 'Hrm.view_attendancemonth'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(
                year__icontains=filters['search']
            ) | queryset.filter(
                month__icontains=filters['search']
            )
            
        if filters.get('year'):
            queryset = queryset.filter(year=filters['year'])
            
        if filters.get('month'):
            queryset = queryset.filter(month=filters['month'])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:attendance_month_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_attendancemonth')
        context['can_view'] = self.request.user.has_perm('Hrm.view_attendancemonth')
        context['can_update'] = self.request.user.has_perm('Hrm.change_attendancemonth')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_attendancemonth')
        context['can_export'] = self.request.user.has_perm('Hrm.view_attendancemonth')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_attendancemonth')
        
        return context

class AttendanceMonthCreateView(CreateView):
    model = AttendanceMonth
    form_class = AttendanceMonthForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Attendance Month'
        context['subtitle'] = 'Add a new attendance month to the system'
        context['cancel_url'] = reverse_lazy('hrm:attendance_month_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Attendance Month {self.object.year}-{self.object.month:02d} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:attendance_month_detail', kwargs={'pk': self.object.pk})

class AttendanceMonthUpdateView(UpdateView):
    model = AttendanceMonth
    form_class = AttendanceMonthForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Attendance Month'
        context['subtitle'] = f'Edit attendance month {self.object.year}-{self.object.month:02d}'
        context['cancel_url'] = reverse_lazy('hrm:attendance_month_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Attendance Month {self.object.year}-{self.object.month:02d} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:attendance_month_detail', kwargs={'pk': self.object.pk})

class AttendanceMonthDetailView(DetailView):
    model = AttendanceMonth
    template_name = 'common/premium-form.html'
    context_object_name = 'attendance_month'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Attendance Month Details'
        context['subtitle'] = f'Attendance Month: {self.object.year}-{self.object.month:02d}'
        context['cancel_url'] = reverse_lazy('hrm:attendance_month_list')
        context['update_url'] = reverse_lazy('hrm:attendance_month_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:attendance_month_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = AttendanceMonthForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class AttendanceMonthDeleteView(GenericDeleteView):
    model = AttendanceMonth
    success_url = reverse_lazy('hrm:attendance_month_list')
    permission_required = 'Hrm.delete_attendancemonth'

    def get_cancel_url(self):
        """Override cancel URL to redirect to AttendanceMonth detail view."""
        return reverse_lazy('hrm:attendance_month_detail', kwargs={'pk': self.object.pk})

class AttendanceMonthExportView(BaseExportView):
    """Export view for AttendanceMonth."""
    model = AttendanceMonth
    filename = "attendance_months.csv"
    permission_required = "Hrm.view_attendancemonth"
    field_names = ["Year", "Month", "Is Processed", "Processed Date", "Processed By", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class AttendanceMonthBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for AttendanceMonth."""
    model = AttendanceMonth
    permission_required = "Hrm.delete_attendancemonth"
    display_fields = ["year", "month", "is_processed", "created_at"]
    cancel_url = reverse_lazy("hrm:attendance_month_list")
    success_url = reverse_lazy("hrm:attendance_month_list")

