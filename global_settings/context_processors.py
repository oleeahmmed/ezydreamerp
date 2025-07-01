from django.apps import apps

def global_settings_context(request):
    """
    Context processor for Global Settings app to provide menu visibility flag and notification count.
    """
    context = {
        'show_global_settings_menu': False,
        'unread_notification_count': 0,
    }

    if not request.user.is_authenticated:
        return context

    # Set menu visibility if user has any permission
    context['show_global_settings_menu'] = any([
        request.user.has_perm('global_settings.view_currency'),
        request.user.has_perm('global_settings.view_paymentterms'),
        request.user.has_perm('global_settings.view_companyinfo'),
        request.user.has_perm('global_settings.view_localization'),
        request.user.has_perm('global_settings.view_accounting'),
        request.user.has_perm('global_settings.view_usersettings'),
        request.user.has_perm('global_settings.view_emailsettings'),
        request.user.has_perm('global_settings.view_taxsettings'),
        request.user.has_perm('global_settings.view_paymentsettings'),
        request.user.has_perm('global_settings.view_backupsettings'),
        request.user.has_perm('global_settings.view_generalsettings'),
    ])

    # Notification count logic
    if apps.is_installed('global_settings'):
        # Import Notification model from global_settings app
        Notification = apps.get_model('global_settings', 'Notification')
        
        # Count unread notifications for the current user or all users
        user_notifications = Notification.objects.filter(
            is_read=False,
            recipient=request.user
        ).count()
        
        all_user_notifications = Notification.objects.filter(
            is_read=False, 
            all_users=True
        ).count()
        
        context['unread_notification_count'] = user_notifications + all_user_notifications

    return context