def finance_menu_context(request):
    """
    Context processor for Finance app to provide menu visibility flag.
    """
    context = {
        'show_finance_menu': False,
    }

    if not request.user.is_authenticated:
        return context

    # Set menu visibility if user has any permission
    context['show_finance_menu'] = any([
        request.user.has_perm('Finance.view_account'),
        request.user.has_perm('Finance.view_accounttype'),
        request.user.has_perm('Finance.view_journalentry'),
        request.user.has_perm('Finance.view_payment'),
        request.user.has_perm('Finance.view_bankreconciliation'),
        request.user.has_perm('Finance.view_financialreport'),
        request.user.has_perm('Finance.view_taxreport'),
        request.user.has_perm('Finance.view_budget'),
        request.user.has_perm('Finance.view_generalledger'),
    ])

    return context