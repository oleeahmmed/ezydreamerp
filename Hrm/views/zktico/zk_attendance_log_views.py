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

# === Missing Attendance View ===
class MissingAttendanceView(LoginRequiredMixin, FormView):
    """
    Enhanced view to identify employees with incomplete attendance records.
    Checks both record count and minimum working hours requirements.
    """
    template_name = 'zk_device/missing_attendance_list.html'
    form_class = MissingAttendanceForm

    def get_context_data(self, **kwargs):
        """Add title and employees to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _("Enhanced Missing Attendance Report"),
            'subtitle': _("Find days with incomplete punch records or insufficient working hours"),
            'employees': Employee.objects.filter(is_active=True).order_by('employee_id'),
        })
        return context

    def form_valid(self, form):
        """Process form and generate enhanced missing attendance report."""
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']
        employee_id = form.cleaned_data.get('employee_id')
        minimum_records = int(form.cleaned_data['minimum_records'])
        minimum_working_hours = form.cleaned_data['minimum_working_hours']
        grace_period_minutes = form.cleaned_data['grace_period_minutes']
        device = form.cleaned_data.get('device')
        validation_type = form.cleaned_data['validation_type']

        # Build base queryset
        queryset = ZKAttendanceLog.objects.select_related('device')
        
        # Apply filters
        if start_date:
            queryset = queryset.filter(timestamp__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__date__lte=end_date)
        if employee_id:
            queryset = queryset.filter(user_id=employee_id)
        if device:
            queryset = queryset.filter(device=device)

        # Get attendance data grouped by user and date
        attendance_data = defaultdict(lambda: defaultdict(list))
        
        for log in queryset.order_by('timestamp'):
            date_key = log.timestamp.date()
            attendance_data[log.user_id][date_key].append({
                'timestamp': log.timestamp,
                'punch_type': log.punch_type,
                'device_name': log.device.name if log.device else 'Unknown',
                'device': log.device
            })

        # Analyze incomplete days with enhanced validation
        missing_data = []
        total_days = 0
        total_missing_days = 0
        employees_with_missing = set()

        for user_id, user_dates in attendance_data.items():
            employee_name = self._get_employee_name(user_id)
            department = self._get_employee_department(user_id)
            
            user_missing_days = []
            user_total_days = len(user_dates)
            user_incomplete_days = 0

            for date, records in user_dates.items():
                record_count = len(records)
                
                # Skip days with no records
                if record_count == 0:
                    continue
                
                # Calculate working hours between first and last punch
                if len(records) >= 2:
                    first_punch = min([r['timestamp'] for r in records])
                    last_punch = max([r['timestamp'] for r in records])
                    working_duration = last_punch - first_punch
                    working_hours = working_duration.total_seconds() / 3600
                    
                    # Apply grace period
                    minimum_hours_with_grace = float(minimum_working_hours) - (grace_period_minutes / 60)
                else:
                    working_hours = 0
                    first_punch = records[0]['timestamp'] if records else None
                    last_punch = first_punch
                    minimum_hours_with_grace = float(minimum_working_hours)

                # Determine if day is incomplete based on validation type
                is_incomplete = False
                missing_reasons = []
                
                if validation_type in ['records_only', 'both']:
                    if record_count < minimum_records:
                        is_incomplete = True
                        missing_reasons.append(f"Records: {record_count}/{minimum_records}")
                
                if validation_type in ['hours_only', 'both']:
                    if working_hours < minimum_hours_with_grace:
                        is_incomplete = True
                        missing_reasons.append(f"Hours: {working_hours:.1f}h/{minimum_working_hours}h")
                
                if is_incomplete:
                    user_incomplete_days += 1
                    employees_with_missing.add(user_id)
                    
                    # Analyze what's missing
                    devices_used = list(set([r['device_name'] for r in records]))
                    existing_punch_types = [r['punch_type'] for r in records if r['punch_type']]
                    missing_punch_info = self._analyze_missing_punches(existing_punch_types, minimum_records)
                    
                    # Determine missing type
                    if record_count < minimum_records and working_hours < minimum_hours_with_grace:
                        missing_type = "Both Records & Hours"
                        missing_severity = "high"
                    elif record_count < minimum_records:
                        missing_type = "Insufficient Records"
                        missing_severity = "medium"
                    elif working_hours < minimum_hours_with_grace:
                        missing_type = "Insufficient Hours"
                        missing_severity = "medium"
                    else:
                        missing_type = "Other"
                        missing_severity = "low"
                    
                    user_missing_days.append({
                        'date': date,
                        'day_name': date.strftime('%A'),
                        'record_count': record_count,
                        'missing_records': max(0, minimum_records - record_count),
                        'working_hours': working_hours,
                        'minimum_working_hours': float(minimum_working_hours),
                        'hours_deficit': max(0, float(minimum_working_hours) - working_hours),
                        'first_punch': first_punch,
                        'last_punch': last_punch,
                        'devices_used': ', '.join(devices_used),
                        'records': records,
                        'missing_punch_info': missing_punch_info,
                        'missing_reasons': ', '.join(missing_reasons),
                        'missing_type': missing_type,
                        'missing_severity': missing_severity,
                    })

            if user_missing_days:
                # Calculate percentages
                attendance_percentage = round((user_total_days / max(1, (end_date - start_date).days + 1)) * 100, 1) if start_date and end_date else 0
                completeness_percentage = round(((user_total_days - user_incomplete_days) / max(1, user_total_days)) * 100, 1)
                
                missing_data.append({
                    'user_id': user_id,
                    'employee_name': employee_name,
                    'department': department,
                    'total_days_with_records': user_total_days,
                    'days_with_incomplete_records': user_incomplete_days,
                    'attendance_percentage': attendance_percentage,
                    'completeness_percentage': completeness_percentage,
                    'missing_days': user_missing_days,
                })
                
                total_missing_days += user_incomplete_days
            
            total_days += user_total_days

        # Sort by most incomplete days first
        missing_data.sort(key=lambda x: x['days_with_incomplete_records'], reverse=True)

        # Flatten missing records for table display
        missing_records = []
        for employee_data in missing_data:
            for missing_day in employee_data['missing_days']:
                missing_records.append({
                    'user_id': employee_data['user_id'],
                    'employee_name': employee_data['employee_name'],
                    'department': employee_data['department'],
                    'date': missing_day['date'],
                    'day_name': missing_day['day_name'],
                    'record_count': missing_day['record_count'],
                    'missing_count': missing_day['missing_records'],
                    'working_hours': missing_day['working_hours'],
                    'minimum_working_hours': missing_day['minimum_working_hours'],
                    'hours_deficit': missing_day['hours_deficit'],
                    'first_punch': missing_day['first_punch'],
                    'last_punch': missing_day['last_punch'],
                    'devices_used': missing_day['devices_used'],
                    'missing_reasons': missing_day['missing_reasons'],
                    'missing_type': missing_day['missing_type'],
                    'missing_severity': missing_day['missing_severity'],
                })

        # Calculate date range
        date_range_days = (end_date - start_date).days + 1 if start_date and end_date else 0

        context = self.get_context_data(form=form)
        context.update({
            'report_generated': True,
            'missing_data': missing_data,
            'missing_records': missing_records,
            'start_date': start_date,
            'end_date': end_date,
            'minimum_records': minimum_records,
            'minimum_working_hours': minimum_working_hours,
            'grace_period_minutes': grace_period_minutes,
            'validation_type': validation_type,
            'total_days': total_days,
            'total_missing_days': total_missing_days,
            'total_employees_with_missing': len(employees_with_missing),
            'date_range_days': date_range_days,
        })
        
        return render(self.request, self.template_name, context)

    def _get_employee_name(self, user_id):
        """Get employee name from Employee model or return user_id."""
        try:
            employee = Employee.objects.get(employee_id=user_id)
            return f"{employee.first_name} {employee.last_name}".strip() or employee.name or f"User {user_id}"
        except Employee.DoesNotExist:
            return f"User {user_id}"

    def _get_employee_department(self, user_id):
        """Get employee department from Employee model."""
        try:
            employee = Employee.objects.get(employee_id=user_id)
            return employee.department.name if employee.department else "Unknown"
        except Employee.DoesNotExist:
            return "Unknown"

    def _analyze_missing_punches(self, existing_punch_types, minimum_records):
        """Analyze what punch types might be missing."""
        if not existing_punch_types:
            return "No punch types recorded"
        
        # Common punch type patterns
        common_patterns = {
            2: ["Check In", "Check Out"],
            4: ["Check In", "Break Out", "Break In", "Check Out"],
        }
        
        expected_pattern = common_patterns.get(minimum_records, [])
        if not expected_pattern:
            return f"Expected {minimum_records} records, found {len(existing_punch_types)}"
        
        missing_types = []
        for expected_type in expected_pattern:
            if expected_type not in existing_punch_types:
                missing_types.append(expected_type)
        
        if missing_types:
            return f"Likely missing: {', '.join(missing_types)}"
        else:
            return f"Has {len(existing_punch_types)} records but expected {minimum_records}"

class MissingAttendanceExportView(LoginRequiredMixin, View):
    """Export missing attendance report to CSV."""
    
    def get(self, request, *args, **kwargs):
        """Export missing attendance data to CSV."""
        # Get parameters from request
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        minimum_records = int(request.GET.get('minimum_records', 2))
        
        if not start_date_str or not end_date_str:
            messages.error(request, _("Start date and end date are required for export."))
            return redirect('hrm:missing_attendance')
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, _("Invalid date format."))
            return redirect('hrm:missing_attendance')
        
        # Recreate the missing attendance logic (simplified for export)
        queryset = ZKAttendanceLog.objects.filter(
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        ).select_related('device').order_by('timestamp')
        
        # Group by user and date
        attendance_data = defaultdict(lambda: defaultdict(list))
        for log in queryset:
            date_key = log.timestamp.date()
            attendance_data[log.user_id][date_key].append({
                'timestamp': log.timestamp,
                'punch_type': log.punch_type,
                'device_name': log.device.name if log.device else 'Unknown',
            })
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="incomplete_attendance_{start_date}_{end_date}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Employee ID', 'Employee Name', 'Department', 'Date', 'Day', 
            'Records Found', 'Records Expected', 'Missing Count', 'First Punch', 
            'Last Punch', 'Devices Used', 'Existing Punch Types'
        ])
        
        # Process data for export
        for user_id, user_dates in attendance_data.items():
            employee_name = self._get_employee_name(user_id)
            department = self._get_employee_department(user_id)
            
            for date, records in user_dates.items():
                record_count = len(records)
                
                # Only export incomplete days
                if 1 <= record_count < minimum_records:
                    first_punch = min([r['timestamp'] for r in records])
                    last_punch = max([r['timestamp'] for r in records])
                    devices_used = ', '.join(set([r['device_name'] for r in records]))
                    punch_types = ', '.join([r['punch_type'] for r in records if r['punch_type']])
                    
                    writer.writerow([
                        user_id,
                        employee_name,
                        department,
                        date.strftime('%Y-%m-%d'),
                        date.strftime('%A'),
                        record_count,
                        minimum_records,
                        minimum_records - record_count,
                        first_punch.strftime('%H:%M:%S'),
                        last_punch.strftime('%H:%M:%S'),
                        devices_used,
                        punch_types,
                    ])
        
        return response
    
    def _get_employee_name(self, user_id):
        """Get employee name from Employee model or return user_id."""
        try:
            employee = Employee.objects.get(employee_id=user_id)
            return f"{employee.first_name} {employee.last_name}".strip() or employee.name or f"User {user_id}"
        except Employee.DoesNotExist:
            return f"User {user_id}"

    def _get_employee_department(self, user_id):
        """Get employee department from Employee model."""
        try:
            employee = Employee.objects.get(employee_id=user_id)
            return employee.department.name if employee.department else "Unknown"
        except Employee.DoesNotExist:
            return "Unknown"