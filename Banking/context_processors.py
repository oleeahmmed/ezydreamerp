def banking_menu_context(request):
    """
    Context processor for Banking app to provide menu visibility flag.
    """
    context = {
        'show_banking_menu': False,
    }

    if not request.user.is_authenticated:
        return context

    # Set menu visibility if user has any permission
    context['show_banking_menu'] = any([
        request.user.has_perm('Banking.view_payment'),
        request.user.has_perm('Banking.view_paymentmethod'),
    ])

    return context