import json
import logging
from datetime import datetime, timedelta
from django.contrib import messages
from collections import defaultdict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Min, Max, Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, FormView
from django import forms

from Hrm.models import ZKAttendanceLog, ZKDevice, Employee
from Hrm.forms.zk_device_forms import ZKAttendanceLogForm
from config.views import BaseBulkDeleteConfirmView, BaseExportView, GenericDeleteView

logger = logging.getLogger(__name__)

# === ZK Attendance Log List View ===
class ZKAttendanceLogListView(LoginRequiredMixin, ListView):
    """List view for ZK Attendance Logs."""
    model = ZKAttendanceLog
    template_name = 'zk_device/attendance_log_list.html'
    context_object_name = 'logs'
    paginate_by = 50
    permission_required = 'Hrm.view_zkattendancelog'

    def get_queryset(self):
        """Filter and order attendance logs based on query parameters."""
        queryset = super().get_queryset()
        if device_id := self.request.GET.get('device'):
            queryset = queryset.filter(device_id=device_id)
        if user_id := self.request.GET.get('user_id'):
            queryset = queryset.filter(user_id=user_id)
        if start_date := self.request.GET.get('start_date'):
            queryset = queryset.filter(timestamp__date__gte=start_date)
        if end_date := self.request.GET.get('end_date'):
            queryset = queryset.filter(timestamp__date__lte=end_date)
        if search := self.request.GET.get('search'):
            queryset = queryset.filter(user_id__icontains=search) | queryset.filter(device__name__icontains=search)
        return queryset.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        """Add devices and permissions to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'devices': ZKDevice.objects.all(),
            'can_create': self.request.user.has_perm('Hrm.add_zkattendancelog'),
            'can_view': self.request.user.has_perm('Hrm.view_zkattendancelog'),
            'can_update': self.request.user.has_perm('Hrm.change_zkattendancelog'),
            'can_delete': self.request.user.has_perm('Hrm.delete_zkattendancelog'),
            'can_export': self.request.user.has_perm('Hrm.view_zkattendancelog'),
            'can_bulk_delete': self.request.user.has_perm('Hrm.delete_zkattendancelog'),
        })
        return context

# === ZK Attendance Log Create View ===
class ZKAttendanceLogCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new ZK Attendance Log."""
    model = ZKAttendanceLog
    form_class = ZKAttendanceLogForm
    template_name = 'common/premium-form.html'
    permission_required = 'Hrm.add_zkattendancelog'

    def get_context_data(self, **kwargs):
        """Add title and cancel URL to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('Create Attendance Log'),
            'subtitle': _('Add a new attendance record'),
            'cancel_url': reverse_lazy('hrm:zk_attendance_log_list'),
        })
        return context

    def form_valid(self, form):
        """Handle valid form submission."""
        self.object = form.save()
        messages.success(self.request, _('Attendance log for user "{}" created successfully.').format(self.object.user_id))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to attendance log detail page after creation."""
        return reverse_lazy('hrm:zk_attendance_log_detail', kwargs={'pk': self.object.pk})

# === ZK Attendance Log Update View ===
class ZKAttendanceLogUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating an existing ZK Attendance Log."""
    model = ZKAttendanceLog
    form_class = ZKAttendanceLogForm
    template_name = 'common/premium-form.html'
    permission_required = 'Hrm.change_zkattendancelog'

    def get_context_data(self, **kwargs):
        """Add title and cancel URL to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _('Update Attendance Log'),
            'subtitle': _('Edit attendance record for user: {}').format(self.object.user_id),
            'cancel_url': reverse_lazy('hrm:zk_attendance_log_detail', kwargs={'pk': self.object.pk}),
        })
        return context

    def form_valid(self, form):
        """Handle valid form submission."""
        self.object = form.save()
        messages.success(self.request, _('Attendance log for user "{}" updated successfully.').format(self.object.user_id))
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to attendance log detail page after update."""
        return reverse_lazy('hrm:zk_attendance_log_detail', kwargs={'pk': self.object.pk})

# === ZK Attendance Log Detail View ===
class ZKAttendanceLogDetailView(LoginRequiredMixin, DetailView):
    """View for displaying ZK Attendance Log details."""
    model = ZKAttendanceLog
    template_name = 'common/premium-form.html'
    context_object_name = 'attendance_log'
    permission_required = 'Hrm.view_zkattendancelog'

    def get_context_data(self, **kwargs):
        """Add form and URLs to context."""
        context = super().get_context_data(**kwargs)
        form = ZKAttendanceLogForm(instance=self.object)
        
        # Make form fields readonly for detail view
        for field in form.fields.values():
            field.widget.attrs.update({'readonly': True, 'disabled': 'disabled'})
        
        context.update({
            'title': _('Attendance Log Details'),
            'subtitle': _('User: {} - {}').format(self.object.user_id, self.object.timestamp.strftime('%Y-%m-%d %H:%M:%S')),
            'cancel_url': reverse_lazy('hrm:zk_attendance_log_list'),
            'update_url': reverse_lazy('hrm:zk_attendance_log_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('hrm:zk_attendance_log_delete', kwargs={'pk': self.object.pk}),
            'is_detail_view': True,
            'form': form,
            'object': self.object,
        })
        return context

# === ZK Attendance Log Export View ===
class ZKAttendanceLogExportView(BaseExportView):
    """View for exporting ZK Attendance Log data to CSV."""
    model = ZKAttendanceLog
    filename = "zk_attendance_logs.csv"
    permission_required = "Hrm.view_zkattendancelog"
    field_names = ["user_id", "device__name", "timestamp", "punch_type", "status", "verify_type", "work_code", "created_at"]

    def queryset_filter(self, request, queryset):
        """Apply any filters to the queryset."""
        if device_id := request.GET.get('device'):
            queryset = queryset.filter(device_id=device_id)
        if user_id := request.GET.get('user_id'):
            queryset = queryset.filter(user_id=user_id)
        if start_date := request.GET.get('start_date'):
            queryset = queryset.filter(timestamp__date__gte=start_date)
        if end_date := request.GET.get('end_date'):
            queryset = queryset.filter(timestamp__date__lte=end_date)
        if search := request.GET.get('search'):
            queryset = queryset.filter(user_id__icontains=search) | queryset.filter(device__name__icontains=search)
        return queryset.order_by('-timestamp')

# === ZK Attendance Log Bulk Delete View ===
class ZKAttendanceLogBulkDeleteView(BaseBulkDeleteConfirmView):
    """View for bulk deleting ZK Attendance Logs."""
    model = ZKAttendanceLog
    permission_required = "Hrm.zk_attendance_log_bulk_delete"
    display_fields = ["user_id", "device__name", "timestamp", "punch_type"]
    cancel_url = reverse_lazy("hrm:zk_attendance_log_list")
    success_url = reverse_lazy("hrm:zk_attendance_log_list")
    template_name = "common/bulk_delete_confirm.html"

# === ZK Attendance Log Delete View ===
class ZKAttendanceLogDeleteView(GenericDeleteView):
    """View for deleting a single ZK Attendance Log."""
    model = ZKAttendanceLog
    template_name = 'common/delete_confirm.html'
    success_url = reverse_lazy('hrm:zk_attendance_log_list')
    permission_required = 'Hrm.delete_zkattendancelog'

    def get_context_data(self, **kwargs):
        """Add title and cancel URL to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _("Delete Attendance Log"),
            'subtitle': _("Are you sure you want to delete this attendance log?"),
            'object': self.object,
            'model_name': self.model._meta.verbose_name.title(),
            'cancel_url': reverse_lazy('hrm:zk_attendance_log_list'),
        })
        return context

# === Missing Attendance Form ===
class MissingAttendanceForm(forms.Form):
    """Form for generating missing attendance reports with working hours validation."""
    
    start_date = forms.DateField(
        label=_("Start Date"),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-700 transition-all duration-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200'
        }),
        help_text=_("Select the start date for the report")
    )
    
    end_date = forms.DateField(
        label=_("End Date"),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-700 transition-all duration-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200'
        }),
        help_text=_("Select the end date for the report")
    )
    
    employee_id = forms.CharField(
        label=_("Employee ID"),
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Optional - leave blank for all employees'),
            'class': 'w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-700 transition-all duration-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200'
        }),
        help_text=_("Filter by specific employee ID (optional)")
    )
    
    MINIMUM_RECORDS_CHOICES = [
        (2, _("2 Records (In/Out) - 8 hours")),
        (3, _("3 Records - 8 hours")),
        (4, _("4 Records (In/Break/Break/Out) - 8 hours")),
    ]
    
    minimum_records = forms.ChoiceField(
        label=_("Minimum Records Required"),
        choices=MINIMUM_RECORDS_CHOICES,
        initial=2,
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-700 cursor-pointer'
        }),
        help_text=_("Minimum number of punch records expected per day")
    )
    
    # New field for minimum working hours
    minimum_working_hours = forms.DecimalField(
        label=_("Minimum Working Hours"),
        initial=8.0,
        min_value=1.0,
        max_value=24.0,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'step': '0.5',
            'class': 'w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-700 transition-all duration-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200'
        }),
        help_text=_("Minimum working hours required between first and last punch")
    )
    
    # New field for grace period
    grace_period_minutes = forms.IntegerField(
        label=_("Grace Period (Minutes)"),
        initial=30,
        min_value=0,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-700 transition-all duration-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200'
        }),
        help_text=_("Grace period in minutes for minimum working hours")
    )
    
    device = forms.ModelChoiceField(
        label=_("Filter by Device"),
        queryset=ZKDevice.objects.filter(is_active=True),
        required=False,
        empty_label=_("All Devices"),
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-700 cursor-pointer'
        }),
        help_text=_("Filter records by specific device (optional)")
    )
    
    # New field for validation type
    VALIDATION_TYPE_CHOICES = [
        ('records_only', _("Records Count Only")),
        ('hours_only', _("Working Hours Only")),
        ('both', _("Both Records Count and Working Hours")),
    ]
    
    validation_type = forms.ChoiceField(
        label=_("Validation Type"),
        choices=VALIDATION_TYPE_CHOICES,
        initial='both',
        widget=forms.Select(attrs={
            'class': 'w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-700 cursor-pointer'
        }),
        help_text=_("Choose what to validate: records count, working hours, or both")
    )

    def clean(self):
        """Validate form data."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError(_("Start date cannot be after end date."))
            
            # Check if date range is too large (more than 3 months)
            date_diff = (end_date - start_date).days
            if date_diff > 90:
                raise forms.ValidationError(_("Date range cannot exceed 90 days."))
        
        return cleaned_data

