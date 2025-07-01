import math
from decimal import Decimal, InvalidOperation

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points using the Haversine formula
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
        
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    try:
        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)
    except (ValueError, TypeError, InvalidOperation) as e:
        raise ValueError(f"Invalid coordinate value: {e}")
    
    lat1_rad = lat1 * math.pi / 180
    lon1_rad = lon1 * math.pi / 180
    lat2_rad = lat2 * math.pi / 180
    lon2_rad = lon2 * math.pi / 180
    
    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r

def is_within_radius(user_lat, user_lon, location_lat, location_lon, radius):
    """
    Check if user is within the specified radius of a location
    
    Args:
        user_lat, user_lon: User's latitude and longitude
        location_lat, location_lon: Location's latitude and longitude
        radius: Maximum allowed distance in kilometers
        
    Returns:
        (bool, float): Tuple containing:
            - Boolean indicating if user is within radius
            - Actual distance in kilometers
    """
    # Ensure all inputs are properly converted to float for calculation
    try:
        user_lat = float(user_lat)
        user_lon = float(user_lon)
        location_lat = float(location_lat)
        location_lon = float(location_lon)
        radius = float(radius)
    except (ValueError, TypeError, InvalidOperation) as e:
        raise ValueError(f"Invalid value for distance calculation: {e}")
    
    distance = calculate_distance(user_lat, user_lon, location_lat, location_lon)
    return distance <= radius, distance

def get_user_assigned_locations(user):
    """
    Get locations assigned to a user
    
    Args:
        user: User object
        
    Returns:
        QuerySet of Location objects
    """
    from .models import UserLocation
    
    user_locations = UserLocation.objects.filter(user=user)
    if user_locations.exists():
        # Return locations assigned to the user
        return [ul.location for ul in user_locations]
    else:
        # If no locations are assigned, return an empty list
        return []

def get_user_primary_location(user):
    """
    Get the primary location assigned to a user
    
    Args:
        user: User object
        
    Returns:
        Location object or None
    """
    from .models import UserLocation
    
    try:
        user_location = UserLocation.objects.get(user=user, is_primary=True)
        return user_location.location
    except UserLocation.DoesNotExist:
        # If no primary location is assigned, try to get any location
        user_locations = UserLocation.objects.filter(user=user)
        if user_locations.exists():
            return user_locations.first().location
        return None