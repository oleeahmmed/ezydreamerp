def business_partner_menu_context(request):
    """
    Context processor for BusinessPartnerMasterData app to provide menu visibility flag.
    """
    context = {
        'show_business_partner_menu': False,
    }

    if not request.user.is_authenticated:
        return context

    # Set menu visibility if user has any permission
    context['show_business_partner_menu'] = any([
        request.user.has_perm('BusinessPartnerMasterData.view_businesspartner'),
        request.user.has_perm('BusinessPartnerMasterData.view_businesspartnergroup'),
        request.user.has_perm('BusinessPartnerMasterData.view_financialinformation'),
        request.user.has_perm('BusinessPartnerMasterData.view_contactinformation'),
        request.user.has_perm('BusinessPartnerMasterData.view_address'),
        request.user.has_perm('BusinessPartnerMasterData.view_contactperson'),
    ])

    return context