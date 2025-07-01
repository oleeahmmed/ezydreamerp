from django.views.generic import CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect

from ..models import OvertimeRecord
from ..forms import OvertimeRecordForm, AttendanceFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView

class OvertimeRecordListView(GenericFilterView):
    model = OvertimeRecord
    template_name = 'attendance/overtime_record_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = AttendanceFilterForm
    permission_required = 'hrm.view_overtimerecord'
    
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
        context['create_url'] = reverse_lazy('hrm:overtime_record_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('hrm.add_overtimerecord')
        context['can_view'] = self.request.user.has_perm('hrm.view_overtimerecord')
        context['can_update'] = self.request.user.has_perm('hrm.change_overtimerecord')
        context['can_delete'] = self.request.user.has_perm('hrm.delete_overtimerecord')
        context['can_export'] = self.request.user.has_perm('hrm.view_overtimerecord')
        context['can_bulk_delete'] = self.request.user.has_perm('hrm.delete_overtimerecord')
        
        return context

class OvertimeRecordCreateView(CreateView):
    model = OvertimeRecord
    form_class = OvertimeRecordForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Overtime Record'
        context['subtitle'] = 'Add a new overtime record to the system'
        context['cancel_url'] = reverse_lazy('hrm:overtime_record_list')
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Overtime record for {self.object.employee.get_full_name()} on {self.object.date} created successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:overtime_record_detail', kwargs={'pk': self.object.pk})

class OvertimeRecordUpdateView(UpdateView):
    model = OvertimeRecord
    form_class = OvertimeRecordForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Overtime Record'
        context['subtitle'] = f'Edit overtime record for {self.object.employee.get_full_name()} on {self.object.date}'
        context['cancel_url'] = reverse_lazy('hrm:overtime_record_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Overtime record for {self.object.employee.get_full_name()} on {self.object.date} updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:overtime_record_detail', kwargs={'pk': self.object.pk})

class OvertimeRecordDetailView(DetailView):
    model = OvertimeRecord
    template_name = 'common/premium-form.html'
    context_object_name = 'overtime_record'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Overtime Record Details'
        context['subtitle'] = f'Overtime record for {self.object.employee.get_full_name()} on {self.object.date}'
        context['cancel_url'] = reverse_lazy('hrm:overtime_record_list')
        context['update_url'] = reverse_lazy('hrm:overtime_record_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:overtime_record_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = OvertimeRecordForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class OvertimeRecordDeleteView(GenericDeleteView):
    model = OvertimeRecord
    success_url = reverse_lazy('hrm:overtime_record_list')
    permission_required = 'hrm.delete_overtimerecord'

    def get_cancel_url(self):
        """Override cancel URL to redirect to OvertimeRecord detail view."""
        return reverse_lazy('hrm:overtime_record_detail', kwargs={'pk': self.object.pk})

class OvertimeRecordExportView(BaseExportView):
    """Export view for OvertimeRecord."""
    model = OvertimeRecord
    filename = "overtime_records.csv"
    permission_required = "hrm.view_overtimerecord"
    field_names = ["Employee", "Date", "Start Time", "End Time", "Hours", "Status", "Created At"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class OvertimeRecordBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for OvertimeRecord."""
    model = OvertimeRecord
    permission_required = "hrm.delete_overtimerecord"
    display_fields = ["employee", "date", "start_time", "end_time", "hours", "status"]
    cancel_url = reverse_lazy("hrm:overtime_record_list")
    success_url = reverse_lazy("hrm:overtime_record_list")

