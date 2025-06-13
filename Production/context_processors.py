def production_menu_context(request):
    """
    Context processor for Production app to provide menu visibility flag.
    """
    context = {
        'show_production_menu': False,
    }

    if not request.user.is_authenticated:
        return context

    # Set menu visibility if user has any permission
    context['show_production_menu'] = any([
        request.user.has_perm('Production.view_billofmaterials'),
        request.user.has_perm('Production.view_productionorder'),
        request.user.has_perm('Production.view_productionreceipt'),
        request.user.has_perm('Production.view_productionissue'),
    ])

    return context