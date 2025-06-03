def hrm_menu_context(request):
    """
    Context processor for HRM app to provide menu visibility flags.
    """
    context = {
        'show_hrm_menu': False,
        'show_payroll_menu': False,
    }

    if not request.user.is_authenticated:
        return context

    # Set HRM menu visibility if user has any HRM permission
    context['show_hrm_menu'] = any([
        request.user.has_perm('Hrm.view_employee'),
        request.user.has_perm('Hrm.view_employeeseparation'),
        request.user.has_perm('Hrm.view_department'),
        request.user.has_perm('Hrm.view_designation'),
        request.user.has_perm('Hrm.view_location'),
        request.user.has_perm('Hrm.view_userlocation'),
        request.user.has_perm('Hrm.view_locationattendance'),
        request.user.has_perm('Hrm.view_shift'),
        request.user.has_perm('Hrm.view_roster'),
        request.user.has_perm('Hrm.view_rosterassignment'),
        request.user.has_perm('Hrm.view_leavetype'),
        request.user.has_perm('Hrm.view_leaveapplication'),
        request.user.has_perm('Hrm.view_shortleaveapplication'),
        request.user.has_perm('Hrm.view_leavebalance'),
        request.user.has_perm('Hrm.view_holiday'),
        request.user.has_perm('Hrm.view_zkdevice'),
        request.user.has_perm('Hrm.view_zkattendancelog'),
        request.user.has_perm('Hrm.view_zkuser'),
    ])

    # Set Payroll menu visibility if user has any Payroll permission
    context['show_payroll_menu'] = any([
        request.user.has_perm('Hrm.view_salarycomponent'),
        request.user.has_perm('Hrm.view_employeesalarystructure'),
        request.user.has_perm('Hrm.view_salarymonth'),
        request.user.has_perm('Hrm.view_employeesalary'),
        request.user.has_perm('Hrm.view_bonussetup'),
        request.user.has_perm('Hrm.view_bonusmonth'),
        request.user.has_perm('Hrm.view_employeebonus'),
        request.user.has_perm('Hrm.view_advancesetup'),
        request.user.has_perm('Hrm.view_employeeadvance'),
        request.user.has_perm('Hrm.view_advanceinstallment'),
    ])

    return context