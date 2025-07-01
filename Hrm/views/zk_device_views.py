import json
import logging
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Min, Max
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView

from config.views import BaseBulkDeleteConfirmView, BaseBulkDeleteView, BaseExportView, GenericDeleteView, GenericFilterView
from ..forms.zk_device_forms import ZKDeviceFilterForm, ZKDeviceForm, ZKDeviceConnectionTestForm, ZKDeviceSyncForm
from ..models import Department, Designation, Employee, ZKAttendanceLog, ZKDevice

# Attempt to import ZK library
try:
    from zk import ZK
    ZK_AVAILABLE = True
except ImportError:
    ZK_AVAILABLE = False
    logging.warning("ZK library not available. Please install it with 'pip install pyzk'")

logger = logging.getLogger(__name__)

# === ZK Device List View ===
class ZKDeviceListView(GenericFilterView):
    """List view for ZK Devices with filtering and pagination."""
    model = ZKDevice
    template_name = 'zk_device/device_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = ZKDeviceFilterForm
    permission_required = 'hrm.view_zkdevice'

    def apply_filters(self, queryset):
        """Apply filters based on form data."""
        filters = self.filter_form.cleaned_data
        if filters.get('search'):
            queryset = queryset.filter(name__icontains=filters['search']) | queryset.filter(ip_address__icontains=filters['search'])
        if filters.get('is_active') is not None:
            queryset = queryset.filter(is_active=filters['is_active'])
        return queryset

    def get_context_data(self, **kwargs):
        """Add additional context data for the template."""
        context = super().get_context_data(**kwargs)
        context.update({
            'create_url': reverse_lazy('hrm:zk_device_create'),
            'can_create': self.request.user.has_perm('hrm.add_zkdevice'),
            'can_view': self.request.user.has_perm('hrm.view_zkdevice'),
            'can_update': self.request.user.has_perm('hrm.change_zkdevice'),
            'can_delete': self.request.user.has_perm('hrm.delete_zkdevice'),
            'can_export': self.request.user.has_perm('hrm.view_zkdevice'),
            'can_bulk_delete': self.request.user.has_perm('hrm.delete_zkdevice'),
            'zk_available': ZK_AVAILABLE,
        })
        return context

# === ZK Device Create View ===
class ZKDeviceCreateView(CreateView):
    """View for creating a new ZK Device."""
    model = ZKDevice
    form_class = ZKDeviceForm
    template_name = 'common/premium-form.html'

    def get_context_data(self, **kwargs):
        """Add title and cancel URL to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Create ZK Device',
            'subtitle': 'Register a new ZKTeco device',
            'cancel_url': reverse_lazy('hrm:zk_device_list'),
        })
        return context

    def form_valid(self, form):
        """Handle valid form submission."""
        self.object = form.save()
        messages.success(self.request, f'Device "{self.object.name}" created successfully.')
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to device detail page after creation."""
        return reverse_lazy('hrm:zk_device_detail', kwargs={'pk': self.object.pk})

# === ZK Device Update View ===
class ZKDeviceUpdateView(UpdateView):
    """View for updating an existing ZK Device."""
    model = ZKDevice
    form_class = ZKDeviceForm
    template_name = 'common/premium-form.html'

    def get_context_data(self, **kwargs):
        """Add title and cancel URL to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'Update ZK Device',
            'subtitle': f'Edit device: {self.object.name}',
            'cancel_url': reverse_lazy('hrm:zk_device_detail', kwargs={'pk': self.object.pk}),
        })
        return context

    def form_valid(self, form):
        """Handle valid form submission."""
        self.object = form.save()
        messages.success(self.request, f'Device "{self.object.name}" updated successfully.')
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to device detail page after update."""
        return reverse_lazy('hrm:zk_device_detail', kwargs={'pk': self.object.pk})

# === ZK Device Detail View ===
class ZKDeviceDetailView(DetailView):
    """View for displaying ZK Device details."""
    model = ZKDevice
    template_name = 'common/premium-form.html'
    context_object_name = 'device'

    def get_context_data(self, **kwargs):
        """Add form and URLs to context."""
        context = super().get_context_data(**kwargs)
        form = ZKDeviceForm(instance=self.object)
        for field in form.fields.values():
            field.widget.attrs.update({'readonly': True, 'disabled': 'disabled'})
        context.update({
            'title': 'ZK Device Details',
            'subtitle': self.object.name,
            'cancel_url': reverse_lazy('hrm:zk_device_list'),
            'update_url': reverse_lazy('hrm:zk_device_update', kwargs={'pk': self.object.pk}),
            'delete_url': reverse_lazy('hrm:zk_device_delete', kwargs={'pk': self.object.pk}),
            'is_detail_view': True,
            'form': form,
        })
        return context

# === ZK Device Delete View ===
class ZKDeviceDeleteView(GenericDeleteView):
    """View for deleting a ZK Device."""
    model = ZKDevice
    success_url = reverse_lazy('hrm:zk_device_list')
    permission_required = 'hrm.delete_zkdevice'

    def get_cancel_url(self):
        """Return URL to cancel deletion."""
        return reverse_lazy('hrm:zk_device_detail', kwargs={'pk': self.object.pk})

# === ZK Device Export View ===
class ZKDeviceExportView(BaseExportView):
    """View for exporting ZK Device data to CSV."""
    model = ZKDevice
    filename = "zk_devices.csv"
    permission_required = "hrm.view_zkdevice"
    field_names = ["name", "ip_address", "port", "device_id", "is_active", "timeout", "force_udp", "created_at"]

    def queryset_filter(self, request, queryset):
        """Apply any filters to the queryset."""
        return queryset

# === ZK Device Bulk Delete View ===
class ZKDeviceBulkDeleteView(BaseBulkDeleteConfirmView):
    """View for bulk deleting ZK Devices."""
    model = ZKDevice
    permission_required = "hrm.delete_zkdevice"
    display_fields = ["name", "ip_address", "is_active", "port"]
    cancel_url = reverse_lazy("hrm:zk_device_list")
    success_url = reverse_lazy("hrm:zk_device_list")

# === ZK Device Connection Test View ===
class ZKDeviceConnectionTestView(FormView):
    """View for testing connection to a ZK Device."""
    template_name = 'zk_device/device_test_connection.html'
    form_class = ZKDeviceConnectionTestForm

    def get_context_data(self, **kwargs):
        """Add title and ZK availability to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _("Test Device Connection"),
            'subtitle': _("Verify connection to ZKTeco device"),
            'zk_available': ZK_AVAILABLE,
        })
        return context

    def form_valid(self, form):
        """Handle valid form submission by testing device connection."""
        if not ZK_AVAILABLE:
            messages.error(self.request, _("ZK library not available. Please install it with 'pip install pyzk'"))
            return self.form_invalid(form)

        device = form.cleaned_data['device']
        test_result = self._test_device_connection(device)
        context = self.get_context_data(form=form)
        context.update(test_result)
        return render(self.request, self.template_name, context)

    def _test_device_connection(self, device):
        """Test connection to the specified device and return result."""
        result = {
            'device': device,
            'connection_tested': True,
            'success': False,
            'error': None,
            'device_info': {},
            'attendance_preview': []
        }
        try:
            conn_params = device.get_connection_params()
            password = conn_params.get('password')
            if password in [None, '']:
                conn_params['password'] = 0
            elif isinstance(password, str) and password.isdigit():
                conn_params['password'] = int(password)
            else:
                raise ValueError("Password must be numeric or blank.")
            
            zk = ZK(**conn_params)
            conn = zk.connect()
            if conn:
                result['device_info'] = {
                    'firmware_version': conn.get_firmware_version() or 'N/A',
                    'serial_number': conn.get_serialnumber() or 'N/A',
                    'platform': conn.get_platform() or 'N/A',
                    'device_name': conn.get_device_name() or 'N/A',
                    'user_count': len(conn.get_users()),
                }
                attendance = conn.get_attendance()
                result['device_info']['attendance_count'] = len(attendance)
                sorted_attendance = sorted(attendance, key=lambda x: x.timestamp, reverse=True)
                for record in sorted_attendance[:50]:
                    if not record.user_id or str(record.user_id).strip() == "":
                        continue
                    punch_type = self._get_punch_type(record)
                    result['attendance_preview'].append({
                        'user_id': record.user_id,
                        'timestamp': record.timestamp,
                        'punch_type': punch_type,
                        'status': getattr(record, 'status', None),
                        'verify_type': getattr(record, 'verify_type', None),
                    })
                conn.disconnect()
                result['success'] = True
                messages.success(self.request, _("Successfully connected to device"))
            else:
                result['error'] = _("Failed to connect to device")
                messages.error(self.request, result['error'])
        except Exception as e:
            logger.error(f"Error connecting to device {device.name}: {str(e)}")
            result['error'] = str(e)
            messages.error(self.request, _("Error connecting to device: {}").format(str(e)))
        return result

    def _get_punch_type(self, record):
        """Map punch type code to human-readable string."""
        if hasattr(record, 'punch') and record.punch is not None:
            punch_types = {
                0: 'Check In',
                1: 'Check Out',
                2: 'Break Out',
                3: 'Break In',
                4: 'Overtime In',
                5: 'Overtime Out'
            }
            return punch_types.get(record.punch, f'Unknown ({record.punch})')
        return None

# === ZK Device Sync View ===
class ZKDeviceSyncView(FormView):
    """View for syncing attendance data from ZK Devices."""
    template_name = 'zk_device/device_sync.html'
    form_class = ZKDeviceSyncForm

    def get_context_data(self, **kwargs):
        """Add title and ZK availability to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _("Sync Attendance Data"),
            'subtitle': _("Retrieve and preview attendance data from ZKTeco devices"),
            'zk_available': ZK_AVAILABLE,
        })
        return context

    def form_valid(self, form):
        """Handle valid form submission by syncing devices."""
        if not ZK_AVAILABLE:
            messages.error(self.request, _("ZK library not available"))
            return self.form_invalid(form)

        devices = form.cleaned_data['devices']
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        sync_result = self._sync_devices(devices, start_date, end_date)
        context = self.get_context_data(form=form)
        context.update(sync_result)
        return render(self.request, self.template_name, context)

    def _sync_devices(self, devices, start_date=None, end_date=None):
        """Sync attendance data from specified devices."""
        result = {
            'sync_performed': True,
            'sync_results': [],
            'total_records': 0,
            'all_attendance_data': [],
            'start_date': start_date,
            'end_date': end_date
        }
        for device in devices:
            device_result = {
                'device': device,
                'success': False,
                'records_found': 0,
                'error': None,
                'attendance_data': []
            }
            try:
                conn_params = device.get_connection_params()
                password = conn_params.get('password')
                if password in [None, '']:
                    conn_params['password'] = 0
                elif isinstance(password, str) and password.isdigit():
                    conn_params['password'] = int(password)
                
                zk = ZK(**conn_params)
                conn = zk.connect()
                if conn:
                    attendance = conn.get_attendance()
                    if start_date or end_date:
                        filtered_attendance = [
                            record for record in attendance
                            if (not start_date or record.timestamp.date() >= start_date) and
                               (not end_date or record.timestamp.date() <= end_date)
                        ]
                        attendance = filtered_attendance
                    for record in attendance:
                        if not record.user_id or str(record.user_id).strip() == "":
                            continue
                        punch_type = self._get_punch_type(record)
                        attendance_data = {
                            'device_id': device.id,
                            'device_name': device.name,
                            'user_id': int(record.user_id),
                            'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            'punch_type': punch_type,
                            'status': getattr(record, 'status', None),
                            'verify_type': getattr(record, 'verify_type', None),
                            'work_code': getattr(record, 'work_code', None),
                        }
                        device_result['attendance_data'].append(attendance_data)
                        result['all_attendance_data'].append(attendance_data)
                    device_result['success'] = True
                    device_result['records_found'] = len(device_result['attendance_data'])
                    result['total_records'] += device_result['records_found']
                    conn.disconnect()
                    messages.success(self.request, 
                        _("Retrieved {} records from {}").format(device_result['records_found'], device.name))
                else:
                    device_result['error'] = _("Failed to connect to device")
                    messages.error(self.request, _("Failed to connect to {}").format(device.name))
            except Exception as e:
                logger.error(f"Error syncing device {device.name}: {str(e)}")
                device_result['error'] = str(e)
                messages.error(self.request, _("Error syncing {}: {}").format(device.name, str(e)))
            result['sync_results'].append(device_result)
        result['all_attendance_data'].sort(key=lambda x: x['timestamp'], reverse=True)
        return result

    def _get_punch_type(self, record):
        """Map punch type code to human-readable string."""
        if hasattr(record, 'punch') and record.punch is not None:
            punch_types = {
                0: 'Check In',
                1: 'Check Out',
                2: 'Break Out',
                3: 'Break In',
                4: 'Overtime In',
                5: 'Overtime Out'
            }
            return punch_types.get(record.punch, f'Unknown ({record.punch})')
        return None

# === ZK Device Save Data View ===
@method_decorator(csrf_exempt, name='dispatch')
class ZKDeviceSaveDataView(View):
    """View for saving synced attendance data to the database, ensuring no duplicates."""
    def post(self, request, *args, **kwargs):
        """Handle POST request to save unique attendance data."""
        try:
            data = json.loads(request.body)
            attendance_data = data.get('attendance_data', [])
            if not attendance_data:
                return JsonResponse({
                    'success': False,
                    'error': _('No attendance data provided')
                }, status=400)

            saved_count = 0
            skipped_count = 0
            errors = []
            for record in attendance_data:
                try:
                    # Validate required fields
                    required_fields = ['device_id', 'user_id', 'timestamp']
                    if not all(field in record for field in required_fields):
                        errors.append(f"Missing required fields in record: {record}")
                        continue

                    # Fetch device
                    try:
                        device = ZKDevice.objects.get(id=record['device_id'])
                    except ZKDevice.DoesNotExist:
                        errors.append(f"Device with ID {record['device_id']} not found")
                        continue

                    # Parse timestamp
                    try:
                        timestamp = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        errors.append(f"Invalid timestamp format for user {record['user_id']}: {record['timestamp']}")
                        continue

                    # Check for duplicate record
                    if ZKAttendanceLog.objects.filter(
                        device=device,
                        user_id=str(record['user_id']),
                        timestamp=timestamp,
                        punch_type=record.get('punch_type') or None
                    ).exists():
                        skipped_count += 1
                        logger.info(f"Skipped duplicate record for user {record['user_id']} at {record['timestamp']}")
                        continue

                    # Create attendance log
                    ZKAttendanceLog.objects.create(
                        device=device,
                        user_id=str(record['user_id']),
                        timestamp=timestamp,
                        punch_type=record.get('punch_type') or None,
                        status=record.get('status') or None,
                        verify_type=record.get('verify_type') or None,
                        work_code=record.get('work_code') or None
                    )
                    saved_count += 1
                except Exception as e:
                    error_msg = f"Error saving record for user {record.get('user_id', 'unknown')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

            response = {
                'success': saved_count > 0 or skipped_count > 0,
                'saved_count': saved_count,
                'skipped_count': skipped_count,
                'error_count': len(errors),
                'errors': errors,
                'message': _("%d records saved successfully, %d duplicates skipped, %d errors occurred") % (saved_count, skipped_count, len(errors))
            }
            return JsonResponse(response, status=200 if saved_count > 0 or skipped_count > 0 else 400)

        except json.JSONDecodeError:
            logger.error("Invalid JSON data received")
            return JsonResponse({
                'success': False,
                'error': _("Invalid JSON data")
            }, status=400)
        except Exception as e:
            logger.error(f"Error saving attendance data: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

# === ZK Attendance Log List View ===
class ZKAttendanceLogListView(LoginRequiredMixin, ListView):
    """List view for ZK Attendance Logs."""
    model = ZKAttendanceLog
    template_name = 'zk_device/attendance_log_list.html'
    context_object_name = 'logs'
    paginate_by = 50

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
        """Add devices to context."""
        context = super().get_context_data(**kwargs)
        context['devices'] = ZKDevice.objects.all()
        return context

# === ZK Attendance Log Bulk Delete View ===
class ZKAttendanceLogBulkDeleteView(BaseBulkDeleteConfirmView):
    """View for bulk deleting ZK Attendance Logs."""
    model = ZKAttendanceLog
    permission_required = "hrm.zk_attendance_log_bulk_delete"
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
    permission_required = 'hrm.delete_zkattendancelog'

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

# === ZK User List View ===
class ZKUserListView(ListView):
    """List view for managing ZK Users."""
    template_name = 'zk_device/user_list_modern.html'
    context_object_name = 'users'
    paginate_by = 50

    def get_queryset(self):
        """Generate a list of users with attendance statistics."""
        user_data = ZKAttendanceLog.objects.values('user_id').annotate(
            total_records=Count('id'),
            first_attendance_id=Min('id'),
            last_attendance_id=Max('id'),
            device_count=Count('device', distinct=True)
        ).order_by('user_id')

        if search := self.request.GET.get('search', '').strip():
            user_data = user_data.filter(user_id__icontains=search)
        if status_filter := self.request.GET.get('status', ''):
            user_data = [
                user for user in user_data
                if (status_filter == 'in_employee' and Employee.objects.filter(employee_id=user['user_id']).exists()) or
                   (status_filter == 'not_in_employee' and not Employee.objects.filter(employee_id=user['user_id']).exists())
            ]

        users = []
        for user in user_data:
            user_id = user['user_id']
            existing_employee = Employee.objects.filter(employee_id=user_id).first()
            first_attendance = ZKAttendanceLog.objects.filter(id=user['first_attendance_id']).first()
            last_attendance = ZKAttendanceLog.objects.filter(id=user['last_attendance_id']).first()
            devices = list(ZKAttendanceLog.objects.filter(user_id=user_id).values_list('device__name', flat=True).distinct())
            preview_data = self._prepare_user_preview_data(user_id, existing_employee, first_attendance)
            users.append({
                'user_id': user_id,
                'total_records': user['total_records'],
                'device_count': user['device_count'],
                'first_attendance': first_attendance,
                'last_attendance': last_attendance,
                'devices': devices,
                'is_in_employee_table': bool(existing_employee),
                'existing_employee': existing_employee,
                'preview_data': preview_data,
            })
        return users

    def _prepare_user_preview_data(self, user_id, existing_employee, first_attendance):
        """Prepare preview data for a user."""
        if existing_employee:
            return {
                'employee_id': existing_employee.employee_id,
                'first_name': existing_employee.first_name,
                'last_name': existing_employee.last_name,
                'full_name': existing_employee.get_full_name(),
                'email': existing_employee.email,
                'phone': existing_employee.phone,
                'department': existing_employee.department.name if existing_employee.department else 'N/A',
                'designation': existing_employee.designation.name if existing_employee.designation else 'N/A',
                'joining_date': existing_employee.joining_date,
                'basic_salary': existing_employee.basic_salary,
                'is_active': existing_employee.is_active,
                'status': 'existing'
            }
        joining_date = first_attendance.timestamp.date() if first_attendance else timezone.now().date()
        return {
            'employee_id': user_id,
            'first_name': f'User {user_id}',
            'last_name': '',
            'full_name': f'User {user_id}',
            'email': f'user{user_id}@company.com',
            'phone': '000-000-0000',
            'department': 'Default Department',
            'designation': 'Employee',
            'joining_date': joining_date,
            'basic_salary': '0.00',
            'is_active': True,
            'status': 'new'
        }

    def get_context_data(self, **kwargs):
        """Add statistics and filters to context."""
        context = super().get_context_data(**kwargs)
        all_users = ZKAttendanceLog.objects.values('user_id').distinct()
        total_users = all_users.count()
        users_in_employee = sum(1 for user in all_users if Employee.objects.filter(employee_id=user['user_id']).exists())
        context.update({
            'title': _("ZK Users Management"),
            'subtitle': _("Preview and manage users from ZKTeco device sync data"),
            'search': self.request.GET.get('search', ''),
            'status_filter': self.request.GET.get('status', ''),
            'stats': {
                'total_users': total_users,
                'users_in_employee': users_in_employee,
                'users_not_in_employee': total_users - users_in_employee,
                'total_attendance_records': ZKAttendanceLog.objects.count(),
                'unique_devices': ZKDevice.objects.filter(attendance_logs__isnull=False).distinct().count(),
            }
        })
        return context

# === ZK User Insert View ===
@method_decorator(csrf_exempt, name='dispatch')
class ZKUserInsertView(View):
    """View for inserting ZK Users into the Employee table."""
    def post(self, request, *args, **kwargs):
        """Handle POST request to insert users."""
        try:
            data = json.loads(request.body)
            user_ids = data.get('user_ids', [])
            if not user_ids:
                return JsonResponse({
                    'success': False,
                    'error': _('No user IDs provided')
                }, status=400)

            inserted_count = 0
            skipped_count = 0
            errors = []
            inserted_users = []

            default_department, _ = Department.objects.get_or_create(
                code='ZK_DEFAULT',
                defaults={
                    'name': 'ZK Device Users',
                    'description': 'Default department for users imported from ZK devices'
                }
            )
            default_designation, _ = Designation.objects.get_or_create(
                name='ZK Employee',
                department=default_department,
                defaults={
                    'description': 'Default designation for users imported from ZK devices'
                }
            )

            for user_id in user_ids:
                try:
                    if Employee.objects.filter(employee_id=user_id).exists():
                        skipped_count += 1
                        continue
                    user_attendance_data = ZKAttendanceLog.objects.filter(user_id=user_id)
                    if not user_attendance_data.exists():
                        errors.append(f'No attendance data found for user {user_id}')
                        continue
                    first_attendance = user_attendance_data.order_by('timestamp').first()
                    joining_date = first_attendance.timestamp.date() if first_attendance else timezone.now().date()
                    employee = Employee.objects.create(
                        employee_id=user_id,
                        first_name=f'ZK User {user_id}',
                        last_name='',
                        gender='M',
                        date_of_birth=timezone.now().date() - timezone.timedelta(days=365*30),
                        marital_status='S',
                        email=f'zkuser{user_id}@company.com',
                        phone=f'+880-{user_id}-0000',
                        present_address='Address to be updated from ZK device import',
                        permanent_address='Address to be updated from ZK device import',
                        department=default_department,
                        designation=default_designation,
                        joining_date=joining_date,
                        basic_salary=0.00,
                        is_active=True
                    )
                    total_records = user_attendance_data.count()
                    devices_used = list(user_attendance_data.values_list('device__name', flat=True).distinct())
                    inserted_users.append({
                        'employee_id': employee.employee_id,
                        'full_name': employee.get_full_name(),
                        'department': employee.department.name,
                        'designation': employee.designation.name,
                        'joining_date': employee.joining_date.strftime('%Y-%m-%d'),
                        'total_records': total_records,
                        'devices': devices_used
                    })
                    inserted_count += 1
                except Exception as e:
                    error_msg = f'Error inserting user {user_id}: {str(e)}'
                    errors.append(error_msg)
                    logger.error(error_msg)
                    continue

            message_parts = []
            if inserted_count:
                message_parts.append(f'{inserted_count} users successfully imported to Employee table')
            if skipped_count:
                message_parts.append(f'{skipped_count} users skipped (already exist in Employee table)')
            if errors:
                message_parts.append(f'{len(errors)} errors occurred during import')
            message = '. '.join(message_parts) + '.'

            return JsonResponse({
                'success': True,
                'inserted_count': inserted_count,
                'skipped_count': skipped_count,
                'error_count': len(errors),
                'errors': errors,
                'inserted_users': inserted_users,
                'message': message,
                'summary': {
                    'total_processed': len(user_ids),
                    'successful': inserted_count,
                    'skipped': skipped_count,
                    'failed': len(errors)
                }
            })
        except json.JSONDecodeError:
            logger.error("Invalid JSON data received")
            return JsonResponse({
                'success': False,
                'error': _("Invalid JSON data")
            }, status=400)
        except Exception as e:
            logger.error(f'Error in ZKUserInsertView: {str(e)}')
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

# === ZK User Sync View ===
class ZKUserSyncView(FormView):
    """View for syncing user data from ZK Devices."""
    template_name = 'zk_device/user_sync.html'
    form_class = ZKDeviceSyncForm

    def get_context_data(self, **kwargs):
        """Add title to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _("Sync Users from Devices"),
            'subtitle': _("Select devices and sync user data"),
        })
        return context

    def form_valid(self, form):
        """Handle valid form submission by syncing users."""
        if not ZK_AVAILABLE:
            messages.error(self.request, _("ZK library not available"))
            return self.form_invalid(form)

        devices = form.cleaned_data['devices']
        users_data = []
        for device in devices:
            try:
                conn_params = device.get_connection_params()
                password = conn_params.get('password')
                if password in [None, '']:
                    conn_params['password'] = 0
                elif isinstance(password, str) and password.isdigit():
                    conn_params['password'] = int(password)
                
                zk = ZK(**conn_params)
                conn = zk.connect()
                if conn:
                    for user in conn.get_users():
                        if user.user_id:
                            users_data.append({
                                'device': device,
                                'user_id': user.user_id,
                                'name': user.name or f'User {user.user_id}',
                                'privilege': getattr(user, 'privilege', 0),
                                'password': getattr(user, 'password', ''),
                                'group_id': getattr(user, 'group_id', ''),
                                'card': getattr(user, 'card', 0),
                            })
                    conn.disconnect()
                    messages.success(self.request, f"Synced {len(users_data)} users from {device.name}")
            except Exception as e:
                logger.error(f"Error syncing users from {device.name}: {str(e)}")
                messages.error(self.request, f"Error syncing {device.name}: {str(e)}")
        
        context = self.get_context_data(form=form)
        context.update({
            'users_data': users_data,
            'sync_performed': True
        })
        return render(self.request, self.template_name, context)

# === ZK User Simple List View ===
class ZKUserSimpleListView(ListView):
    """Simple list view for ZK Users."""
    template_name = 'zk_device/user_simple_list.html'
    context_object_name = 'users'
    paginate_by = 50

    def get_queryset(self):
        """Return users with basic statistics."""
        users = ZKAttendanceLog.objects.values('user_id').annotate(
            total_records=Count('id'),
            device_names=Count('device__name', distinct=True)
        ).order_by('user_id')
        if search := self.request.GET.get('search', '').strip():
            users = users.filter(user_id__icontains=search)
        return users

    def get_context_data(self, **kwargs):
        """Add statistics and create URL to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _("ZK Users"),
            'subtitle': _("Manage users from ZK devices"),
            'create_url': reverse_lazy('hrm:zk_user_sync'),
            'total_users': ZKAttendanceLog.objects.values('user_id').distinct().count(),
            'total_records': ZKAttendanceLog.objects.count(),
        })
        return context

# === ZK User Save View ===
@method_decorator(csrf_exempt, name='dispatch')
class ZKUserSaveView(View):
    """View for saving ZK Users to the Employee table."""
    def post(self, request, *args, **kwargs):
        """Handle POST request to save users."""
        try:
            data = json.loads(request.body)
            user_ids = data.get('user_ids', [])
            if not user_ids:
                return JsonResponse({
                    'success': False,
                    'error': 'No users selected'
                }, status=400)

            saved_count = 0
            skipped_count = 0
            department, _ = Department.objects.get_or_create(
                code='ZK_DEFAULT',
                defaults={'name': 'ZK Users', 'description': 'Users from ZK devices'}
            )
            designation, _ = Designation.objects.get_or_create(
                name='ZK Employee',
                department=department,
                defaults={'description': 'Employee from ZK device'}
            )

            for user_id in user_ids:
                if Employee.objects.filter(employee_id=user_id).exists():
                    skipped_count += 1
                    continue
                user_name = f'User {user_id}'
                first_name = user_name
                last_name = ''
                if ' ' in user_name:
                    name_parts = user_name.split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                Employee.objects.create(
                    employee_id=user_id,
                    first_name=first_name,
                    last_name=last_name,
                    gender='M',
                    date_of_birth=timezone.now().date() - timezone.timedelta(days=365*25),
                    marital_status='S',
                    email=f'user{user_id}@company.com',
                    phone=f'000-{user_id}',
                    present_address='To be updated',
                    permanent_address='To be updated',
                    department=department,
                    designation=designation,
                    joining_date=timezone.now().date(),
                    basic_salary=0.00,
                    is_active=True
                )
                saved_count += 1

            return JsonResponse({
                'success': True,
                'saved_count': saved_count,
                'skipped_count': skipped_count,
                'message': f'Saved {saved_count} users, {skipped_count} already existed'
            })
        except json.JSONDecodeError:
            logger.error("Invalid JSON data received")
            return JsonResponse({
                'success': False,
                'error': _("Invalid JSON data")
            }, status=400)
        except Exception as e:
            logger.error(f"Error saving users: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)