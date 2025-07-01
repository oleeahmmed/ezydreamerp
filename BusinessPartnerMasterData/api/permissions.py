# BusinessPartnerMasterData/api/permissions.py
from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)

class BusinessPartnerHasDynamicModelPermission(permissions.BasePermission):
    """
    Custom permission to only allow users with the appropriate permissions based on the model.
    """

    def has_permission(self, request, view):
        # Determine the model name dynamically from the viewset.
        model_name = view.queryset.model._meta.model_name
        
        # Map HTTP methods to permission types.
        if request.method in permissions.SAFE_METHODS:
            perm_action = 'view'
        elif request.method == 'POST':
            perm_action = 'add'
        elif request.method in ['PUT', 'PATCH']:
            perm_action = 'change'
        elif request.method == 'DELETE':
            perm_action = 'delete'
        else:
            return False

        # Check if the user has the required permission.
        required_permission = f'BusinessPartnerMasterData.{perm_action}_{model_name}'
        
        # Debug log
        logger.debug(f"Checking permission: {required_permission} for user {request.user.username}")
        logger.debug(f"User permissions: {[p for p in request.user.get_all_permissions()]}")
        
        has_perm = request.user.has_perm(required_permission)
        logger.debug(f"Permission check result: {has_perm}")
        
        return has_perm

    def has_object_permission(self, request, view, obj):
        # Similar to has_permission, but checks permissions on an object level.
        model_name = obj._meta.model_name
        
        if request.method in permissions.SAFE_METHODS:
            perm_action = 'view'
        elif request.method in ['PUT', 'PATCH']:
            perm_action = 'change'
        elif request.method == 'DELETE':
            perm_action = 'delete'
        else:
            return False

        required_permission = f'BusinessPartnerMasterData.{perm_action}_{model_name}'
        
        # Debug log
        logger.debug(f"Checking object permission: {required_permission} for user {request.user.username}")
        
        # For object-level permissions, we should check both model-level and object-level permissions
        # First check if user has model-level permission
        if request.user.has_perm(required_permission):
            return True
            
        # If not, check object-level permission (if applicable)
        # Note: Django's default permission system doesn't have object-level permissions
        # If you're using a custom permission system, you might need to adjust this
        return request.user.has_perm(required_permission, obj)