import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils import timezone
from datetime import datetime, timedelta
from django import forms
from django.db import transaction
from django.db.models import Q

from Hrm.models import ZKDevice, ZKAttendanceLog, Employee

try:
    from zk import ZK
    ZK_AVAILABLE = True
except ImportError:
    ZK_AVAILABLE = False
    logging.warning("ZK library not available. Please install it with 'pip install pyzk'")

logger = logging.getLogger(__name__)

def _connect_to_zk_device(device: ZKDevice):
    """Establishes a connection to a ZK device."""
    if not ZK_AVAILABLE:
        logger.error("ZK library not available. Cannot connect to device.")
        return None
    try:
        conn_params = device.get_connection_params()
        password = conn_params.get('password')
        if password in [None, '']:
            conn_params['password'] = 0
        elif isinstance(password, str) and password.isdigit():
            conn_params['password'] = int(password)
        else:
            conn_params['password'] = 0
            logger.warning(f"Device {device.name} has non-numeric password. Using 0.")
        zk = ZK(**conn_params)
        conn = zk.connect()
        return conn
    except Exception as e:
        logger.error(f"Error connecting to ZK device {device.name} ({device.ip_address}): {str(e)}")
        return None

def _check_duplicate_record(device, user_id, timestamp, tolerance_minutes=1):
    """Check if a record already exists in database with tolerance for timestamp differences."""
    start_time = timestamp - timedelta(minutes=tolerance_minutes)
    end_time = timestamp + timedelta(minutes=tolerance_minutes)
    
    return ZKAttendanceLog.objects.filter(
        device=device,
        user_id=str(user_id),
        timestamp__range=[start_time, end_time]
    ).exists()

def _get_existing_records_bulk(device_records):
    """Bulk check for existing records to improve performance."""
    if not device_records:
        return set()
    
    # Group by device for efficient querying
    device_groups = {}
    for record in device_records:
        device_id = record['device_id']
        if device_id not in device_groups:
            device_groups[device_id] = []
        device_groups[device_id].append(record)
    
    existing_records = set()
    
    for device_id, records in device_groups.items():
        try:
            device = ZKDevice.objects.get(id=device_id)
            
            # Create Q objects for batch checking
            q_objects = Q()
            for record in records:
                timestamp = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                start_time = timestamp - timedelta(minutes=1)
                end_time = timestamp + timedelta(minutes=1)
                
                q_objects |= Q(
                    device=device,
                    user_id=str(record['user_id']),
                    timestamp__range=[start_time, end_time]
                )
            
            if q_objects:
                existing = ZKAttendanceLog.objects.filter(q_objects).values_list(
                    'device_id', 'user_id', 'timestamp'
                )
                
                for device_id, user_id, timestamp in existing:
                    # Create a unique key for comparison
                    key = f"{device_id}_{user_id}_{timestamp.isoformat()}"
                    existing_records.add(key)
                    
        except Exception as e:
            logger.error(f"Error checking existing records for device {device_id}: {str(e)}")
            continue
    
    return existing_records

class ZKAttendanceFilterForm(forms.Form):
    """Form for filtering ZK attendance records by device, date range and user."""
    device = forms.ModelMultipleChoiceField(
        queryset=ZKDevice.objects.all(),
        required=False,
        label=_("Select Devices"),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
            'id': 'device-select',
            'data-placeholder': _('Select one or more devices...'),
        })
    )
    start_date = forms.DateField(
        required=False,
        label=_("Start Date"),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
        })
    )
    end_date = forms.DateField(
        required=False,
        label=_("End Date"),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
        })
    )
    search = forms.CharField(
        required=False,
        label=_("Search User"),
        widget=forms.TextInput(attrs={
            'class': 'form-control w-full rounded-md border border-gray-300 bg-white py-2 px-3 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500',
            'placeholder': _('Search by User ID...'),
            'id': 'user-search',
        })
    )
    show_database_records = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Show Database Records"),
        help_text=_("Show records already imported to database"),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
    hide_imported = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Hide Already Imported"),
        help_text=_("Hide records that are already in database"),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        devices = cleaned_data.get('device')
        search = cleaned_data.get('search', '').strip()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if not devices and not search and not start_date and not end_date:
            raise forms.ValidationError(_("Please select at least one device or enter search criteria."))
        
        return cleaned_data

class ZKAttendanceDeviceListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """View for listing attendance records from ZK Devices with import functionality."""
    template_name = 'zk_device/device_attendance_list.html'
    permission_required = 'Hrm.view_zkdevice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_devices = ZKDevice.objects.all()
        attendance_from_devices = []
        filter_form = ZKAttendanceFilterForm(self.request.POST if self.request.method == 'POST' else None)

        devices_to_query = []
        search_query = ''
        start_date = None
        end_date = None
        show_database_records = False
        hide_imported = False

        if filter_form.is_valid():
            selected_devices = filter_form.cleaned_data.get('device')
            search_query = filter_form.cleaned_data.get('search', '').strip()
            start_date = filter_form.cleaned_data.get('start_date')
            end_date = filter_form.cleaned_data.get('end_date')
            show_database_records = filter_form.cleaned_data.get('show_database_records', False)
            hide_imported = filter_form.cleaned_data.get('hide_imported', False)

            if selected_devices:
                devices_to_query = selected_devices
            else:
                devices_to_query = all_devices.filter(is_active=True)

        # Fetch attendance records only on POST (when "Fetch Records" is clicked)
        if self.request.method == 'POST' and filter_form.is_valid():
            if show_database_records:
                # Show database records
                db_records = ZKAttendanceLog.objects.filter(device__in=devices_to_query)
                
                # Apply filters
                if start_date:
                    db_records = db_records.filter(timestamp__date__gte=start_date)
                if end_date:
                    db_records = db_records.filter(timestamp__date__lte=end_date)
                if search_query:
                    db_records = db_records.filter(user_id__icontains=search_query)
                
                # Group records by user and date to determine Check-In/Check-Out
                records_by_user_date = {}
                for record in db_records.order_by('timestamp'):
                    user_id = record.user_id
                    date_key = record.timestamp.date()
                    key = f"{user_id}_{date_key}"
                    if key not in records_by_user_date:
                        records_by_user_date[key] = []
                    records_by_user_date[key].append(record)
                
                for key, records in records_by_user_date.items():
                    if len(records) > 1:
                        # Set first record as Check-In, last as Check-Out
                        records[0].punch_type = 'Check-In'
                        records[-1].punch_type = 'Check-Out'
                        for record in records[1:-1]:
                            record.punch_type = record.punch_type or ''
                    elif len(records) == 1:
                        records[0].punch_type = records[0].punch_type or 'Check-In'
                    
                    for record in records:
                        attendance_from_devices.append({
                            'device_id': record.device.id,
                            'device_name': record.device.name,
                            'user_id': record.user_id,
                            'timestamp': record.timestamp,
                            'punch_type': record.punch_type,
                            'status': record.status or '',
                            'verify_type': record.verify_type or '',
                            'device': record.device,
                            'record_id': record.id,
                            'source': 'database',
                            'is_imported': True,
                            'work_code': record.work_code or '',
                            'card_no': record.card_no or '',
                            'unique_key': f"{record.device.id}_{record.user_id}_{record.timestamp.isoformat()}",
                        })
            else:
                # Fetch from devices
                if not ZK_AVAILABLE:
                    messages.error(self.request, _("ZK library not available. Cannot fetch attendance records."))
                else:
                    device_records = []
                    
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        future_to_device = {executor.submit(self._fetch_attendance_from_single_device, device, start_date, end_date, search_query): device for device in devices_to_query}
                        for future in as_completed(future_to_device):
                            device = future_to_device[future]
                            try:
                                device_attendance_raw = future.result()
                                if device_attendance_raw:
                                    for record in device_attendance_raw:
                                        # Filter by search query if provided
                                        if search_query and search_query.lower() not in str(record.user_id).lower():
                                            continue
                                        
                                        # Ensure timestamp is timezone-aware
                                        timestamp = record.timestamp
                                        if timezone.is_naive(timestamp):
                                            timestamp = timezone.make_aware(timestamp, timezone=timezone.get_current_timezone())
                                        
                                        device_records.append({
                                            'device_id': device.id,
                                            'device_name': device.name,
                                            'user_id': record.user_id,
                                            'timestamp': timestamp.isoformat(),
                                            'punch_type': getattr(record, 'punch', ''),
                                            'status': getattr(record, 'status', ''),
                                            'verify_type': getattr(record, 'verify_type', ''),
                                            'device': device,
                                            'record_id': getattr(record, 'uid', ''),
                                            'source': 'device',
                                            'work_code': getattr(record, 'work_code', ''),
                                            'card_no': getattr(record, 'card_no', ''),
                                        })
                            except Exception as e:
                                logger.error(f"Error fetching attendance from {device.name}: {str(e)}")
                                messages.error(self.request, _(f"Error fetching attendance from {device.name}: {str(e)}"))

                    # Group device records by user and date
                    records_by_user_date = {}
                    for record in device_records:
                        timestamp_obj = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                        if timezone.is_naive(timestamp_obj):
                            timestamp_obj = timezone.make_aware(timestamp_obj, timezone=timezone.get_current_timezone())
                        user_id = record['user_id']
                        date_key = timestamp_obj.date()
                        key = f"{user_id}_{date_key}"
                        if key not in records_by_user_date:
                            records_by_user_date[key] = []
                        record['timestamp_obj'] = timestamp_obj
                        records_by_user_date[key].append(record)
                    
                    # Assign Check-In/Check-Out
                    for key, records in records_by_user_date.items():
                        if len(records) > 1:
                            records.sort(key=lambda x: x['timestamp_obj'])
                            records[0]['punch_type'] = 'Check-In'
                            records[-1]['punch_type'] = 'Check-Out'
                            for record in records[1:-1]:
                                record['punch_type'] = record['punch_type'] or ''
                        elif len(records) == 1:
                            records[0]['punch_type'] = records[0]['punch_type'] or 'Check-In'
                    
                    # Bulk check for existing records
                    existing_records = _get_existing_records_bulk(device_records)
                    
                    # Process records and mark duplicates
                    for record in device_records:
                        timestamp_obj = record['timestamp_obj']
                        
                        # Check if record exists (with tolerance)
                        is_imported = False
                        for existing_key in existing_records:
                            try:
                                existing_timestamp = datetime.fromisoformat(existing_key.split('_', 2)[2])
                                if timezone.is_naive(existing_timestamp):
                                    existing_timestamp = timezone.make_aware(existing_timestamp, timezone=timezone.get_current_timezone())
                                if (existing_key.startswith(f"{record['device_id']}_{record['user_id']}_") and
                                    abs((existing_timestamp - timestamp_obj).total_seconds()) < 60):
                                    is_imported = True
                                    break
                            except ValueError:
                                continue
                        
                        # Skip if hiding imported records
                        if hide_imported and is_imported:
                            continue
                        
                        record['timestamp'] = timestamp_obj
                        record['is_imported'] = is_imported
                        record['unique_key'] = f"{record['device_id']}_{record['user_id']}_{timestamp_obj.isoformat()}"
                        attendance_from_devices.append(record)

        # Sort records by timestamp (newest first)
        attendance_from_devices.sort(key=lambda x: x['timestamp'], reverse=True)

        # Count statistics
        total_records = len(attendance_from_devices)
        imported_count = sum(1 for record in attendance_from_devices if record.get('is_imported', False))
        new_records_count = total_records - imported_count

        context.update({
            'objects': attendance_from_devices,
            'devices': all_devices,
            'search_query': search_query,
            'start_date': start_date,
            'end_date': end_date,
            'show_database_records': show_database_records,
            'hide_imported': hide_imported,
            'filter_form': filter_form,
            'title': _('ZK Device Attendance Records'),
            'subtitle': _('View and import attendance records from ZKTeco devices'),
            'import_url': reverse_lazy('hrm:zk_attendance_import'),
            'can_view': self.request.user.has_perm('Hrm.view_zkdevice'),
            'can_import': self.request.user.has_perm('Hrm.add_zkattendancelog'),
            'zk_available': ZK_AVAILABLE,
            'model_name': _('ZK Attendance Record'),
            'list_url': reverse_lazy('hrm:zk_attendance_list_device'),
            'total_records': total_records,
            'imported_count': imported_count,
            'new_records_count': new_records_count,
        })
        return context

    def post(self, request, *args, **kwargs):
        """Handle POST request for fetching attendance records."""
        return self.get(request, *args, **kwargs)

    def _fetch_attendance_from_single_device(self, device, start_date=None, end_date=None, search_query=''):
        """Helper to fetch attendance records from a single device."""
        conn = None
        try:
            conn = _connect_to_zk_device(device)
            if conn:
                attendances = conn.get_attendance()

                # Filter by date range if provided
                if start_date or end_date:
                    filtered_attendances = []
                    for att in attendances:
                        att_date = att.timestamp.date()
                        if start_date and att_date < start_date:
                            continue
                        if end_date and att_date > end_date:
                            continue
                        filtered_attendances.append(att)
                    attendances = filtered_attendances

                return attendances
            else:
                messages.warning(self.request, _(f"Could not connect to {device.name}."))
                return []
        except Exception as e:
            logger.error(f"Error fetching attendance from {device.name}: {str(e)}")
            return []
        finally:
            if conn:
                conn.disconnect()
class ZKAttendanceImportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """View for importing attendance records from ZK devices to database."""
    permission_required = 'Hrm.add_zkattendancelog'

    def post(self, request, *args, **kwargs):
        """Handle import request via AJAX."""
        try:
            import json
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'import_selected':
                selected_records = data.get('records', [])
                return self._import_selected_records(selected_records)
            elif action == 'import_all':
                filter_params = data.get('filter_params', {})
                return self._import_all_records(filter_params)
            elif action == 'check_duplicates':
                records = data.get('records', [])
                return self._check_duplicates(records)
            else:
                return JsonResponse({'success': False, 'message': 'Invalid action'})
                
        except Exception as e:
            logger.error(f"Error in import view: {str(e)}")
            return JsonResponse({'success': False, 'message': str(e)})

    def _check_duplicates(self, records):
        """Check which records are duplicates without importing."""
        duplicates = []
        
        for record_data in records:
            try:
                device = ZKDevice.objects.get(id=record_data['device_id'])
                timestamp = datetime.fromisoformat(record_data['timestamp'].replace('Z', '+00:00'))
                
                if _check_duplicate_record(device, record_data['user_id'], timestamp):
                    duplicates.append(record_data['unique_key'])
                    
            except Exception as e:
                logger.error(f"Error checking duplicate: {str(e)}")
                continue
        
        return JsonResponse({
            'success': True,
            'duplicates': duplicates
        })

    def _import_selected_records(self, selected_records):
        """Import specific selected records with enhanced duplicate checking."""
        imported_count = 0
        skipped_count = 0
        error_count = 0
        duplicate_details = []
        
        try:
            with transaction.atomic():
                for record_data in selected_records:
                    try:
                        device = ZKDevice.objects.get(id=record_data['device_id'])
                        timestamp = datetime.fromisoformat(record_data['timestamp'].replace('Z', '+00:00'))
                        
                        # Enhanced duplicate check
                        if _check_duplicate_record(device, record_data['user_id'], timestamp):
                            skipped_count += 1
                            duplicate_details.append({
                                'user_id': record_data['user_id'],
                                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                'device': device.name
                            })
                            continue
                        
                        # Create new record
                        ZKAttendanceLog.objects.create(
                            device=device,
                            user_id=str(record_data['user_id']),
                            timestamp=timestamp,
                            punch_type=str(record_data.get('punch_type', '')),
                            status=str(record_data.get('status', '')),
                            verify_type=str(record_data.get('verify_type', '')),
                            work_code=str(record_data.get('work_code', '')),
                            card_no=str(record_data.get('card_no', '')),
                            record_id=str(record_data.get('record_id', '')),
                        )
                        imported_count += 1
                        
                    except ZKDevice.DoesNotExist:
                        error_count += 1
                        logger.error(f"Device not found: {record_data.get('device_id')}")
                        continue
                    except Exception as e:
                        logger.error(f"Error importing record: {str(e)}")
                        error_count += 1
                        continue
                        
        except Exception as e:
            logger.error(f"Transaction error: {str(e)}")
            return JsonResponse({
                'success': False, 
                'message': f'Transaction failed: {str(e)}'
            })
        
        message = f'Import completed. Imported: {imported_count}, Skipped (duplicates): {skipped_count}, Errors: {error_count}'
        if duplicate_details:
            message += f'\n\nDuplicate records skipped:\n'
            for dup in duplicate_details[:5]:  # Show first 5 duplicates
                message += f"- User {dup['user_id']} at {dup['timestamp']} on {dup['device']}\n"
            if len(duplicate_details) > 5:
                message += f"... and {len(duplicate_details) - 5} more duplicates"
        
        return JsonResponse({
            'success': True,
            'message': message,
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': error_count,
            'duplicates': duplicate_details
        })

    def _import_all_records(self, filter_params):
        """Import all records based on filter parameters with enhanced duplicate checking."""
        imported_count = 0
        skipped_count = 0
        error_count = 0
        duplicate_details = []
        
        try:
            # Get devices based on filter
            device_ids = filter_params.get('device_ids', [])
            if device_ids:
                devices = ZKDevice.objects.filter(id__in=device_ids)
            else:
                devices = ZKDevice.objects.filter(is_active=True)
            
            start_date = None
            end_date = None
            search_query = filter_params.get('search_query', '')
            
            if filter_params.get('start_date'):
                start_date = datetime.strptime(filter_params['start_date'], '%Y-%m-%d').date()
            if filter_params.get('end_date'):
                end_date = datetime.strptime(filter_params['end_date'], '%Y-%m-%d').date()
            
            with transaction.atomic():
                for device in devices:
                    try:
                        conn = _connect_to_zk_device(device)
                        if not conn:
                            continue
                            
                        attendances = conn.get_attendance()
                        conn.disconnect()
                        
                        for record in attendances:
                            try:
                                # Apply filters
                                if start_date and record.timestamp.date() < start_date:
                                    continue
                                if end_date and record.timestamp.date() > end_date:
                                    continue
                                if search_query and search_query.lower() not in str(record.user_id).lower():
                                    continue
                                
                                # Enhanced duplicate check
                                if _check_duplicate_record(device, record.user_id, record.timestamp):
                                    skipped_count += 1
                                    if len(duplicate_details) < 10:  # Limit details for performance
                                        duplicate_details.append({
                                            'user_id': record.user_id,
                                            'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                                            'device': device.name
                                        })
                                    continue
                                
                                # Create new record
                                ZKAttendanceLog.objects.create(
                                    device=device,
                                    user_id=str(record.user_id),
                                    timestamp=record.timestamp,
                                    punch_type=str(getattr(record, 'punch', '')),
                                    status=str(getattr(record, 'status', '')),
                                    verify_type=str(getattr(record, 'verify_type', '')),
                                    work_code=str(getattr(record, 'work_code', '')),
                                    card_no=str(getattr(record, 'card_no', '')),
                                    record_id=str(getattr(record, 'uid', '')),
                                )
                                imported_count += 1
                                
                            except Exception as e:
                                logger.error(f"Error importing record from {device.name}: {str(e)}")
                                error_count += 1
                                continue
                                
                    except Exception as e:
                        logger.error(f"Error processing device {device.name}: {str(e)}")
                        error_count += 1
                        continue
                        
        except Exception as e:
            logger.error(f"Import all transaction error: {str(e)}")
            return JsonResponse({
                'success': False, 
                'message': f'Import failed: {str(e)}'
            })
        
        message = f'Import completed. Imported: {imported_count}, Skipped (duplicates): {skipped_count}, Errors: {error_count}'
        if duplicate_details:
            message += f'\n\nSample duplicate records skipped:\n'
            for dup in duplicate_details:
                message += f"- User {dup['user_id']} at {dup['timestamp']} on {dup['device']}\n"
            if skipped_count > len(duplicate_details):
                message += f"... and {skipped_count - len(duplicate_details)} more duplicates"
        
        return JsonResponse({
            'success': True,
            'message': message,
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': error_count,
            'duplicates': duplicate_details
        })

# --- ZK Attendance Detail View (Read-only) ---
class ZKAttendanceDetailView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    """View for displaying ZK Attendance record details (read-only)."""
    template_name = 'zk_device/attendance_detail.html'
    permission_required = 'Hrm.view_zkdevice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        device_id = self.kwargs['device_id']
        user_id = self.kwargs['user_id']
        timestamp_str = self.kwargs['timestamp']
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
        
        device = get_object_or_404(ZKDevice, pk=device_id)
        attendance_data = None
        
        # Try database first
        try:
            db_record = ZKAttendanceLog.objects.filter(
                device=device,
                user_id=user_id,
                timestamp__range=[
                    timestamp - timedelta(minutes=1),
                    timestamp + timedelta(minutes=1)
                ]
            ).first()
            
            if db_record:
                attendance_data = {
                    'user_id': db_record.user_id,
                    'timestamp': db_record.timestamp,
                    'punch_type': db_record.punch_type,
                    'verify_type': db_record.verify_type,
                    'status': db_record.status,
                    'work_code': db_record.work_code,
                    'card_no': db_record.card_no,
                    'source': 'database'
                }
        except Exception as e:
            logger.error(f"Error fetching from database: {str(e)}")
        
        # Fallback to device if not found in database
        if not attendance_data and ZK_AVAILABLE:
            try:
                conn = _connect_to_zk_device(device)
                if conn:
                    attendances = conn.get_attendance()
                    conn.disconnect()
                    for att in attendances:
                        if (str(att.user_id) == str(user_id) and 
                            abs((att.timestamp - timestamp).total_seconds()) < 60):
                            attendance_data = {
                                'user_id': att.user_id,
                                'timestamp': att.timestamp,
                                'punch_type': getattr(att, 'punch', ''),
                                'verify_type': getattr(att, 'verify_type', ''),
                                'status': getattr(att, 'status', ''),
                                'work_code': getattr(att, 'work_code', ''),
                                'card_no': getattr(att, 'card_no', ''),
                                'source': 'device'
                            }
                            break
            except Exception as e:
                logger.error(f"Error fetching from device: {str(e)}")

        if not attendance_data:
            messages.error(self.request, _("Attendance record not found."))

        context.update({
            'title': _("ZK Attendance Record Details"),
            'subtitle': f"User {user_id}" if attendance_data else _("Record Not Found"),
            'cancel_url': reverse_lazy('hrm:zk_attendance_list_device'),
            'attendance_data': attendance_data,
            'device': device,
            'zk_available': ZK_AVAILABLE,
        })
        return context