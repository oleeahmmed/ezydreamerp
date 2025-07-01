# permission/context_processors.py
from django.urls import reverse, NoReverseMatch

def permission_menu_context(request):
    """
    Context processor for Permission app to provide menu visibility flag and submenu permissions.
    """
    context = {
        'show_dashboard_menu': False,
        'show_permission_menu': False,
        'can_view_user': False,
        'can_view_group': False,
        'can_view_permission': False,
    }

    if not request.user.is_authenticated:
        return context

    # Check if dashboard URL exists
    try:
        reverse('permission:dashboard')
        context['show_dashboard_menu'] = True
    except NoReverseMatch:
        pass

    # Set menu visibility and submenu permissions
    context['can_view_user'] = request.user.has_perm('auth.view_user')
    context['can_view_group'] = request.user.has_perm('auth.view_group')
    context['can_view_permission'] = request.user.has_perm('auth.view_permission')
    context['show_permission_menu'] = any([
        context['can_view_user'],
        context['can_view_group'],
        context['can_view_permission'],
    ])

    return context