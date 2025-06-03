from django.urls import reverse, NoReverseMatch

def permission_menu_context(request):
    """
    Context processor for Permission app to provide menu visibility flag.
    """
    context = {
        'show_dashboard_menu': False,
        'show_permission_menu': False,
    }

    if not request.user.is_authenticated:
        return context

    # Check if dashboard URL exists
    try:
        reverse('permission:dashboard')
        context['show_dashboard_menu'] = True
    except NoReverseMatch:
        pass

    # Set menu visibility if user has any permission
    context['show_permission_menu'] = any([
        request.user.has_perm('auth.view_user'),
        request.user.has_perm('auth.view_group'),
        request.user.has_perm('auth.view_permission'),
    ])

    return context