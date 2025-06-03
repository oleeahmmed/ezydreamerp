def sales_menu_context(request):
    """
    Context processor for Sales app to provide menu visibility flag.
    """
    context = {
        'show_sales_menu': False,
    }

    if not request.user.is_authenticated:
        return context

    # Set menu visibility if user has any permission
    context['show_sales_menu'] = any([
        request.user.has_perm('Sales.view_salesquotation'),
        request.user.has_perm('Sales.view_salesorder'),
        request.user.has_perm('Sales.view_delivery'),
        request.user.has_perm('Sales.view_return'),
        request.user.has_perm('Sales.view_arinvoice'),
        request.user.has_perm('Sales.view_salesemployee'),
        request.user.has_perm('Sales.view_freeitemdiscount'),
    ])

    return context