def purchase_menu_context(request):
    """
    Context processor for Purchase app to provide menu visibility flag.
    """
    context = {
        'show_purchase_menu': False,
    }

    if not request.user.is_authenticated:
        return context

    # Set menu visibility if user has any permission
    context['show_purchase_menu'] = any([
        request.user.has_perm('Purchase.view_purchasequotation'),
        request.user.has_perm('Purchase.view_purchaseorder'),
        request.user.has_perm('Purchase.view_goodsreceiptpo'),
        request.user.has_perm('Purchase.view_goodsreturn'),
        request.user.has_perm('Purchase.view_apinvoice'),
    ])

    return context