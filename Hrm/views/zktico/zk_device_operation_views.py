import json
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Min, Max, OuterRef, Subquery
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, UpdateView
from Hrm.models import Department, Designation, Employee, ZKAttendanceLog, ZKDevice
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from Hrm.forms.zk_device_forms import ZKDeviceConnectionTestForm, ZKDeviceSyncForm,EmployeeAttendanceReportForm,ZKAttendanceLogForm,ZKAttendanceLogFilterForm
from Hrm.models import ZKDevice, Employee, Department, Designation,Shift,Attendance,ZKAttendanceLog,OvertimeRecord
from config.views import BaseBulkDeleteConfirmView, BaseBulkDeleteView, BaseExportView, GenericDeleteView, GenericFilterView

try:
    from zk import ZK
    ZK_AVAILABLE = True
except ImportError:
    ZK_AVAILABLE = False
    logging.warning("ZK library not available. Please install it with 'pip install pyzk'")


logger = logging.getLogger(__name__)

# === ZK Device Connection Test View ===
class ZKDeviceConnectionTestView(LoginRequiredMixin, FormView):
    """View for testing connection to multiple ZK Devices."""
    template_name = 'zk_device/device_test_connection.html'
    form_class = ZKDeviceConnectionTestForm

    def get_context_data(self, **kwargs):
        """Add title and ZK availability to context."""
        context = super().get_context_data(**kwargs)
        context.update({
            'title': _("Test Device Connection"),
            'subtitle': _("Verify connection to multiple ZKTeco devices"),
            'zk_available': ZK_AVAILABLE,
            'cancel_url': reverse_lazy('hrm:zk_device_list'),
        })
        return context

    def form_valid(self, form):
        """Handle valid form submission by testing device connections."""
        if not ZK_AVAILABLE:
            messages.error(self.request, _("ZK library not available. Please install it with 'pip install pyzk'"))
            return self.form_invalid(form)

        devices = form.cleaned_data['devices']
        test_results = self._test_multiple_devices(devices)
        context = self.get_context_data(form=form)
        context.update({
            'test_results': test_results,
            'connection_tested': True,
        })
        return render(self.request, self.template_name, context)

    def _test_multiple_devices(self, devices):
        """Test connection to multiple devices concurrently."""
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_device = {executor.submit(self._test_device_connection, device): device for device in devices}
            for future in as_completed(future_to_device):
                device = future_to_device[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error testing device {device.name}: {str(e)}")
                    results.append({
                        'device': device,
                        'success': False,
                        'error': str(e),
                        'device_info': {},
                        'attendance_preview': [],
                    })
        return results

    def _test_device_connection(self, device):
        """Test connection to a single device."""
        result = {
            'device': device,
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
                raise ValueError("Password must be numeric or empty.")
            
            zk = ZK(**conn_params)
            conn = zk.connect()
            if conn:
                result['device_info'] = {
                    'firmware_version': conn.get_firmware_version() or 'N/A',
                    'serial_number': conn.get_serialnumber() or 'N/A',
                    'platform': conn.get_platform() or 'N/A',
                    'device_name': conn.get_device_name() or 'N/A',
                    'user_count': len(conn.get_users()),
                    'attendance_count': len(conn.get_attendance()),
                }
                attendance = conn.get_attendance()
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
                messages.success(self.request, _("Successfully connected to device {}").format(device.name))
            else:
                result['error'] = _("Failed to connect to device")
                messages.error(self.request, _("Failed to connect to {}").format(device.name))
        except Exception as e:
            logger.error(f"Error connecting to device {device.name}: {str(e)}")
            result['error'] = str(e)
            messages.error(self.request, _("Error connecting to device {}: {}").format(device.name, str(e)))
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
                        verify_type = getattr(record, 'verify_type', None)
                        logger.debug(f"Device: {device.name}, User ID: {record.user_id}, Punch: {record.punch}, Punch Type: {punch_type}, Verify Type: {verify_type}")
                        attendance_data = {
                            'device_id': device.id,
                            'device_name': device.name,
                            'user_id': int(record.user_id),
                            'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            'punch_type': punch_type,
                            'status': getattr(record, 'status', None),
                            'verify_type': verify_type,
                            'work_code': getattr(record, 'work_code', None),
                            'selected': True  # Default select all
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
            punch_type = punch_types.get(record.punch, f'Unknown ({record.punch})')
            logger.debug(f"Record punch: {record.punch}, Mapped punch_type: {punch_type}")
            return punch_type
        logger.debug("No punch attribute in record or punch is None")
        return None

# === ZK Device Save Data View ===
@method_decorator(csrf_exempt, name='dispatch')
class ZKDeviceSaveDataView(View):
    """View for saving synced attendance data to the database, ensuring no duplicates."""
    def post(self, request, *args, **kwargs):
        """Handle POST request to save selected attendance data."""
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
            saved_records = []

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

                    # Log record details for debugging
                    logger.debug(f"Saving record: Device ID: {record['device_id']}, User ID: {record['user_id']}, Timestamp: {record['timestamp']}, Punch Type: {record.get('punch_type')}, Verify Type: {record.get('verify_type')}")

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
                    log = ZKAttendanceLog.objects.create(
                        device=device,
                        user_id=str(record['user_id']),
                        timestamp=timestamp,
                        punch_type=record.get('punch_type') or None,
                        status=record.get('status') or None,
                        verify_type=record.get('verify_type') or None,
                        work_code=record.get('work_code') or None
                    )
                    saved_count += 1
                    saved_records.append({
                        'device_name': device.name,
                        'user_id': record['user_id'],
                        'timestamp': record['timestamp'],
                        'punch_type': record.get('punch_type', '-'),
                        'verify_type': record.get('verify_type', '-')
                    })
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
                'saved_records': saved_records,
                'message': _("%d records saved successfully, %d duplicates skipped, %d errors occurred") % (saved_count, skipped_count, len(errors))
            }
            logger.info(f"Save operation completed: {response['message']}")
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
                                'card_no': str(user.card) if user.card else '',
                                'privilege': getattr(user, 'privilege', 0),
                                'password': getattr(user, 'password', ''),
                                'group_id': getattr(user, 'group_id', ''),
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

# === ZK User Save View ===
@method_decorator(csrf_exempt, name='dispatch')
class ZKUserSaveView(View):
    """View for saving ZK Users to the Employee table."""

    def post(self, request, *args, **kwargs):
        """Handle POST request to save users."""
        try:
            data = json.loads(request.body)
            users = data.get('users', [])
            if not users:
                return JsonResponse({
                    'success': False,
                    'error': 'No users selected'
                }, status=400)

            saved_count = 0
            skipped_count = 0
            errors = []
            saved_users = []

            # Default fallback department and designation
            default_department, _ = Department.objects.get_or_create(
                code='ZK_DEFAULT',
                defaults={'name': 'ZK Users', 'description': 'Users from ZK devices'}
            )
            default_designation, _ = Designation.objects.get_or_create(
                name='ZK Employee',
                department=default_department,
                defaults={'description': 'Employee from ZK device'}
            )

            # Create or get default shift
            default_shift, _ = Shift.objects.get_or_create(
                name='Default Shift',
                defaults={
                    'start_time': timezone.datetime.strptime('09:00:00', '%H:%M:%S').time(),
                    'end_time': timezone.datetime.strptime('17:00:00', '%H:%M:%S').time(),
                    'break_time': 60,
                    'grace_time': 15
                }
            )

            for user in users:
                user_id = user.get('user_id')
                name = user.get('name', f'User {user_id}')
                card_no = user.get('card_no', '')
                device_id = user.get('device_id')

                if not user_id:
                    errors.append('Missing user_id')
                    continue

                if Employee.objects.filter(employee_id=user_id).exists():
                    skipped_count += 1
                    continue

                # Start with fallback
                used_department = default_department
                used_designation = default_designation

                # Check device and override department if available
                if device_id:
                    try:
                        device = ZKDevice.objects.get(id=device_id)
                        department_name = device.location if device.location else device.name
                        department_code = f'DEVICE_{device_id}'

                        used_department, _ = Department.objects.get_or_create(
                            code=department_code,
                            defaults={'name': department_name, 'description': f'Imported from device {department_name}'}
                        )

                        used_designation, _ = Designation.objects.get_or_create(
                            name='ZK Employee',
                            department=used_department,
                            defaults={'description': 'Employee from ZK device'}
                        )

                    except ZKDevice.DoesNotExist:
                        logger.warning(f"Device with ID {device_id} not found. Falling back to default department.")

                # Split name safely
                first_name = name
                last_name = ''
                if ' ' in name:
                    name_parts = name.split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''

                try:
                    employee = Employee.objects.create(
                        employee_id=user_id,
                        first_name=first_name,
                        last_name=last_name,
                        name=name,
                        card_no=card_no if card_no else None,
                        gender='M',
                        date_of_birth=timezone.now().date() - timezone.timedelta(days=365 * 25),
                        marital_status='S',
                        email=f'user{user_id}@company.com',
                        phone=f'000-{user_id}',
                        present_address='To be updated',
                        permanent_address='To be updated',
                        department=used_department,
                        designation=used_designation,
                        joining_date=timezone.now().date(),
                        basic_salary=0.00,
                        is_active=True,
                        default_shift=default_shift  # Assign the default shift
                    )
                    saved_count += 1
                    saved_users.append({
                        'employee_id': employee.employee_id,
                        'full_name': employee.get_full_name(),
                        'department': employee.department.name,
                        'designation': employee.designation.name,
                        'shift_name': default_shift.name
                    })
                except Exception as e:
                    error_msg = f"Error saving user {user_id}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            return JsonResponse({
                'success': True,
                'saved_count': saved_count,
                'skipped_count': skipped_count,
                'errors': errors,
                'saved_users': saved_users,
                'message': f'Saved {saved_count} users, {skipped_count} already existed, {len(errors)} errors'
            })

        except json.JSONDecodeError:
            logger.error("Invalid JSON data received")
            return JsonResponse({
                'success': False,
                'error': "Invalid JSON data"
            }, status=400)
        except Exception as e:
            logger.error(f"Error saving users: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
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

    """View for saving ZK Users to the Employee table."""
    permission_required = 'Hrm.add_employee'

    def post(self, request, *args, **kwargs):
        """Handle POST request to save users."""
        try:
            data = json.loads(request.body)
            users = data.get('users', [])
            if not users:
                return JsonResponse({
                    'success': False,
                    'error': 'No users selected'
                }, status=400)

            saved_count = 0
            skipped_count = 0
            errors = []
            
            department, _ = Department.objects.get_or_create(
                code='ZK_DEFAULT',
                defaults={'name': 'ZK Users', 'description': 'Users from ZK devices'}
            )
            designation, _ = Designation.objects.get_or_create(
                name='ZK Employee',
                department=department,
                defaults={'description': 'Employee from ZK device'}
            )

            for user in users:
                user_id = user.get('user_id')
                name = user.get('name', f'User {user_id}')
                card_no = user.get('card_no', '')
                
                if not user_id:
                    errors.append('Missing user_id')
                    continue
                if Employee.objects.filter(employee_id=user_id).exists():
                    skipped_count += 1
                    continue
                
                try:
                    Employee.objects.create(
                        employee_id=user_id,
                        name=name,
                        card_no=card_no if card_no else None,
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
                except Exception as e:
                    error_msg = f"Error saving user {user_id}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            return JsonResponse({
                'success': True,
                'saved_count': saved_count,
                'skipped_count': skipped_count,
                'errors': errors,
                'message': f'Saved {saved_count} users, {skipped_count} already existed, {len(errors)} errors'
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


