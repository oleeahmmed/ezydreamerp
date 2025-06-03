from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from ..models import UserLocation, Location

@login_required
def debug_user_locations(request):
    """Debug view to check user's location assignments"""
    try:
        # Get all user locations
        user_locations = UserLocation.objects.filter(
            user=request.user
        ).select_related('location')
        
        # Get all active locations
        active_locations = Location.objects.filter(is_active=True)
        
        # Format the data
        user_location_data = [{
            'id': ul.id,
            'user_id': ul.user.id,
            'user_username': ul.user.username,
            'location_id': ul.location.id,
            'location_name': ul.location.name,
            'location_is_active': ul.location.is_active,
            'is_primary': ul.is_primary,
            'created_at': ul.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for ul in user_locations]
        
        active_location_data = [{
            'id': loc.id,
            'name': loc.name,
            'address': loc.address,
            'latitude': float(loc.latitude),
            'longitude': float(loc.longitude),
            'radius': float(loc.radius),
            'is_active': loc.is_active
        } for loc in active_locations]
        
        return JsonResponse({
            'status': 'success',
            'user_id': request.user.id,
            'username': request.user.username,
            'user_locations_count': len(user_locations),
            'active_locations_count': active_locations.count(),
            'user_locations': user_location_data,
            'active_locations': active_location_data
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })