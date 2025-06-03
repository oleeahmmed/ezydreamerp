def inventory_menu_context(request):
    """
    Context processor for Inventory app to provide menu visibility flag and permissions.
    """
    context = {
        'show_inventory_menu': False,
        'can_view_item': False,
        'can_view_warehouse': False,
        'can_view_itemgroup': False,
        'can_view_unitofmeasure': False,
        'can_view_inventorytransaction': False,
        'can_view_goodsreceipt': False,
        'can_view_goodsissue': False,
        'can_view_inventorytransfer': False,
        'can_view_itemwarehouseinfo': False,
    }

    if not request.user.is_authenticated:
        return context

    # Set individual permissions
    context['can_view_item'] = request.user.has_perm('Inventory.view_item')
    context['can_view_warehouse'] = request.user.has_perm('Inventory.view_warehouse')
    context['can_view_itemgroup'] = request.user.has_perm('Inventory.view_itemgroup')
    context['can_view_unitofmeasure'] = request.user.has_perm('Inventory.view_unitofmeasure')
    context['can_view_inventorytransaction'] = request.user.has_perm('Inventory.view_inventorytransaction')
    context['can_view_goodsreceipt'] = request.user.has_perm('Inventory.view_goodsreceipt')
    context['can_view_goodsissue'] = request.user.has_perm('Inventory.view_goodsissue')
    context['can_view_inventorytransfer'] = request.user.has_perm('Inventory.view_inventorytransfer')
    context['can_view_itemwarehouseinfo'] = request.user.has_perm('Inventory.view_itemwarehouseinfo')

    # Set menu visibility if user has any permission
    context['show_inventory_menu'] = any([
        context['can_view_item'],
        context['can_view_warehouse'],
        context['can_view_itemgroup'],
        context['can_view_unitofmeasure'],
        context['can_view_inventorytransaction'],
        context['can_view_goodsreceipt'],
        context['can_view_goodsissue'],
        context['can_view_inventorytransfer'],
        context['can_view_itemwarehouseinfo'],
    ])

    return context