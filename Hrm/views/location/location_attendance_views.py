from django.views.generic import CreateView, UpdateView, DetailView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from math import radians, cos, sin, asin, sqrt
from decimal import Decimal
import logging

from Hrm.models import LocationAttendance, Location, UserLocation
from Hrm.forms.location_forms import LocationAttendanceForm, LocationAttendanceFilterForm
from config.views import GenericFilterView, GenericDeleteView, BaseExportView, BaseBulkDeleteConfirmView
# Set up logging
logger = logging.getLogger(__name__)
class LocationAttendanceListView(GenericFilterView):
    model = LocationAttendance
    template_name = 'location/location_attendance_list.html'
    context_object_name = 'objects'
    paginate_by = 10
    filter_form_class = LocationAttendanceFilterForm
    permission_required = 'Hrm.view_locationattendance'
    
    def apply_filters(self, queryset):
        """Apply filters from the filter form"""
        filters = self.filter_form.cleaned_data
        if filters.get('user'):
            queryset = queryset.filter(user=filters['user'])
            
        if filters.get('location'):
            queryset = queryset.filter(location=filters['location'])
            
        if filters.get('attendance_type'):
            queryset = queryset.filter(attendance_type=filters['attendance_type'])
            
        if filters.get('date_from'):
            queryset = queryset.filter(timestamp__date__gte=filters['date_from'])
            
        if filters.get('date_to'):
            queryset = queryset.filter(timestamp__date__lte=filters['date_to'])
            

            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['create_url'] = reverse_lazy('hrm:location_attendance_create')
        
        # Add permission context variables
        context['can_create'] = self.request.user.has_perm('Hrm.add_locationattendance')
        context['can_view'] = self.request.user.has_perm('Hrm.view_locationattendance')
        context['can_update'] = self.request.user.has_perm('Hrm.change_locationattendance')
        context['can_delete'] = self.request.user.has_perm('Hrm.delete_locationattendance')
        context['can_export'] = self.request.user.has_perm('Hrm.view_locationattendance')
        context['can_bulk_delete'] = self.request.user.has_perm('Hrm.delete_locationattendance')
        
        return context

class LocationAttendanceCreateView(CreateView):
    model = LocationAttendance
    form_class = LocationAttendanceForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Record Location Attendance'
        context['subtitle'] = 'Manually record attendance at a location'
        context['cancel_url'] = reverse_lazy('hrm:location_attendance_list')
        return context
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        self.object = form.save()
        messages.success(self.request, f'Attendance recorded successfully at {self.object.location.name}.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:location_attendance_detail', kwargs={'pk': self.object.pk})

class LocationAttendanceUpdateView(UpdateView):
    model = LocationAttendance
    form_class = LocationAttendanceForm
    template_name = 'common/premium-form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update Location Attendance'
        context['subtitle'] = f'Edit attendance record for {self.object.user.username} at {self.object.location.name}'
        context['cancel_url'] = reverse_lazy('hrm:location_attendance_detail', kwargs={'pk': self.object.pk})
        return context
    
    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, f'Attendance record updated successfully.')
        return HttpResponseRedirect(self.get_success_url())
    
    def get_success_url(self):
        return reverse_lazy('hrm:location_attendance_detail', kwargs={'pk': self.object.pk})

class LocationAttendanceDetailView(DetailView):
    model = LocationAttendance
    template_name = 'common/premium-form.html'
    context_object_name = 'location_attendance'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Location Attendance Details'
        context['subtitle'] = f'Attendance: {self.object.user.username} - {self.object.location.name} - {self.object.timestamp}'
        context['cancel_url'] = reverse_lazy('hrm:location_attendance_list')
        context['update_url'] = reverse_lazy('hrm:location_attendance_update', kwargs={'pk': self.object.pk})
        context['delete_url'] = reverse_lazy('hrm:location_attendance_delete', kwargs={'pk': self.object.pk})
        context['is_detail_view'] = True
        
        # Add form in read-only mode for the detail view
        context['form'] = LocationAttendanceForm(instance=self.object)
        
        # Make all form fields read-only
        for form_field in context['form'].fields.values():
            form_field.widget.attrs['readonly'] = True
            form_field.widget.attrs['disabled'] = 'disabled'
        
        return context

class LocationAttendanceDeleteView(GenericDeleteView):
    model = LocationAttendance
    success_url = reverse_lazy('hrm:location_attendance_list')
    permission_required = 'Hrm.delete_locationattendance'

    def get_cancel_url(self):
        """Override cancel URL to redirect to LocationAttendance detail view."""
        return reverse_lazy('hrm:location_attendance_detail', kwargs={'pk': self.object.pk})

class LocationAttendanceExportView(BaseExportView):
    """Export view for LocationAttendance."""
    model = LocationAttendance
    filename = "location_attendance.csv"
    permission_required = "Hrm.view_locationattendance"
    field_names = ["User", "Location", "Attendance Type", "Timestamp", "Latitude", "Longitude", "Is Within Radius", "Distance"]

    def queryset_filter(self, request, queryset):
        """Apply filtering if needed."""
        return queryset

class LocationAttendanceBulkDeleteView(BaseBulkDeleteConfirmView):
    """Bulk delete view for LocationAttendance."""
    model = LocationAttendance
    permission_required = "Hrm.delete_locationattendance"
    display_fields = ["user", "location", "attendance_type", "timestamp", "is_within_radius"]
    cancel_url = reverse_lazy("hrm:location_attendance_list")
    success_url = reverse_lazy("hrm:location_attendance_list")

# Helper function to calculate distance between two points
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

@login_required
def attendance_page(request):
    """View for the attendance page where users can mark attendance"""
    # Get all user locations without filtering
    user_locations = UserLocation.objects.filter(user=request.user).select_related('location')
    
    # Log for debugging
    logger.debug(f"User {request.user.username} has {user_locations.count()} assigned locations")
    for ul in user_locations:
        logger.debug(f"Location: {ul.location.name}, Primary: {ul.is_primary}")
    
    context = {
        'title': _('Mark Attendance'),
        'subtitle': _('Check-in or check-out at your assigned locations'),
        'has_locations': user_locations.exists(),
        'debug_info': {
            'username': request.user.username,
            'user_id': request.user.id,
            'location_count': user_locations.count(),
            'locations': [
                {
                    'id': ul.location.id,
                    'name': ul.location.name,
                    'is_primary': ul.is_primary
                } for ul in user_locations
            ]
        }
    }
    
    return render(request, 'location/attendance_page.html', context)

@login_required
def mark_attendance(request):
    """API view to mark attendance at a location"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': _('Invalid request method')})
    
    try:
        location_id = request.POST.get('location_id')
        attendance_type = request.POST.get('attendance_type')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        device_info = request.POST.get('device_info', '')
        
        # Log for debugging
        logger.debug(f"Mark attendance request: user={request.user.username}, location_id={location_id}, type={attendance_type}")
        
        # Validate required fields
        if not all([location_id, attendance_type, latitude, longitude]):
            return JsonResponse({'status': 'error', 'message': _('Missing required fields')})
        
        # Validate attendance type
        if attendance_type not in ['IN', 'OUT']:
            return JsonResponse({'status': 'error', 'message': _('Invalid attendance type')})
        
        # Get location
        try:
            location = Location.objects.get(id=location_id)
        except Location.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': _('Location not found')})
        
        # Check if user is assigned to this location
        user_location = UserLocation.objects.filter(user=request.user, location=location).first()
        if not user_location:
            logger.warning(f"User {request.user.username} attempted to mark attendance at unassigned location {location.name}")
            return JsonResponse({'status': 'error', 'message': _('You are not assigned to this location')})
        
        # Calculate distance
        distance = haversine(
            location.latitude, 
            location.longitude, 
            Decimal(latitude), 
            Decimal(longitude)
        )
        
        # Check if within radius
        is_within_radius = distance <= float(location.radius)
        
        # Create attendance record
        attendance = LocationAttendance.objects.create(
            user=request.user,
            location=location,
            attendance_type=attendance_type,
            latitude=latitude,
            longitude=longitude,
            is_within_radius=is_within_radius,
            distance=distance,
            device_info=device_info,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        logger.info(f"Attendance marked: user={request.user.username}, location={location.name}, type={attendance_type}, within_radius={is_within_radius}")
        
        return JsonResponse({
            'status': 'success',
            'message': _('Attendance marked successfully'),
            'data': {
                'id': attendance.id,
                'timestamp': attendance.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'is_within_radius': is_within_radius,
                'distance': round(distance, 2)
            }
        })
        
    except Exception as e:
        logger.exception(f"Error marking attendance: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
def get_locations(request):
    """API view to get user's assigned locations"""
    try:
        # Get all user locations without filtering
        user_locations = UserLocation.objects.filter(
            user=request.user
        ).select_related('location')
        
        # Log for debugging
        logger.debug(f"get_locations: User {request.user.username} has {user_locations.count()} assigned locations")
        
        locations = [{
            'id': ul.location.id,
            'name': ul.location.name,
            'address': ul.location.address,
            'latitude': float(ul.location.latitude),
            'longitude': float(ul.location.longitude),
            'radius': float(ul.location.radius),
            'is_primary': ul.is_primary
        } for ul in user_locations]
        
        return JsonResponse({
            'status': 'success',
            'data': locations,
            'debug': {
                'user_id': request.user.id,
                'username': request.user.username,
                'location_count': user_locations.count()
            }
        })
    except Exception as e:
        logger.exception(f"Error getting locations: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })