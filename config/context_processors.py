from django.apps import apps
from django.urls import reverse, NoReverseMatch

def app_menu_context(request):
    """
    Context processor that provides menu visibility flags based on user permissions.
    This determines which menu items should be shown in the sidebar.
    """
    # Initialize all menu visibility flags as False by default
    context = {
        # Main menu sections
        'show_dashboard_link': False,
        'show_permission_menu': False,
        'show_business_partner_menu': False,
        'show_inventory_menu': False,
        'show_sales_menu': False,
        'show_purchase_menu': False,
        'show_finance_menu': False,
        'show_hrm_menu': False,
        'show_payroll_menu': False,
        'show_banking_menu': False,
        'show_global_settings_menu': False,
        
        # Permission-specific flags
        'can_view_user': False,
        'can_view_group': False,
        'can_view_permission': False,
        
        # Business Partner permissions
        'can_view_businesspartner': False,
        
        # Inventory permissions
        'can_view_unitofmeasure': False,
        'can_view_itemgroup': False,
        'can_view_warehouse': False,
        'can_view_item': False,
        'can_view_itemwarehouseinfo': False,
        'can_view_inventorytransaction': False,
        'can_view_goodsreceipt': False,
        
        # HRM submenu permissions
        'can_view_employee': False,
        'can_view_employee_separation': False,
        'can_view_department': False,
        'can_view_designation': False,
        'can_view_location': False,
        'can_view_user_location': False,
        'can_view_location_attendance': False,
        'can_view_shift': False,
        'can_view_roster': False,
        'can_view_roster_assignment': False,
        'can_view_leave_type': False,
        'can_view_leave_application': False,
        'can_view_short_leave_application': False,
        'can_view_leave_balance': False,
        'can_view_holiday': False,
        'can_view_zkdevice': False,  # Added for ZK Devices
        'can_view_zkattendancelog': False,  # Added for ZK Attendance Logs
        'can_view_zkuser': False,  # Added for ZK Users
        
        # Payroll submenu permissions
        'can_view_salary_component': False,
        'can_view_employee_salary_structure': False,
        'can_view_salary_month': False,
        'can_view_employee_salary': False,
        'can_view_bonus_setup': False,
        'can_view_bonus_month': False,
        'can_view_employee_bonus': False,
        'can_view_advance_setup': False,
        'can_view_employee_advance': False,
        'can_view_advance_installment': False,        
    }

    # Only check permissions for authenticated users
    if not request.user.is_authenticated:
        return context
    
    # Set individual permission flags
    # Auth permissions
    context['can_view_user'] = request.user.has_perm('auth.view_user')
    context['can_view_group'] = request.user.has_perm('auth.view_group')
    context['can_view_permission'] = request.user.has_perm('auth.view_permission')
    
    # Business Partner permissions
    context['can_view_businesspartner'] = request.user.has_perm('BusinessPartnerMasterData.view_businesspartner')
    
    # Inventory permissions
    context['can_view_unitofmeasure'] = request.user.has_perm('Inventory.view_unitofmeasure')
    context['can_view_itemgroup'] = request.user.has_perm('Inventory.view_itemgroup')
    context['can_view_warehouse'] = request.user.has_perm('Inventory.view_warehouse')
    context['can_view_item'] = request.user.has_perm('Inventory.view_item')
    context['can_view_itemwarehouseinfo'] = request.user.has_perm('Inventory.view_itemwarehouseinfo')
    context['can_view_inventorytransaction'] = request.user.has_perm('Inventory.view_inventorytransaction')
    context['can_view_goodsreceipt'] = request.user.has_perm('Inventory.view_goodsreceipt')
    
    # HRM permissions
    context['can_view_employee'] = request.user.has_perm('Hrm.view_employee')
    context['can_view_employee_separation'] = request.user.has_perm('Hrm.view_employeeseparation')
    context['can_view_department'] = request.user.has_perm('Hrm.view_department')
    context['can_view_designation'] = request.user.has_perm('Hrm.view_designation')
    context['can_view_location'] = request.user.has_perm('Hrm.view_location')
    context['can_view_user_location'] = request.user.has_perm('Hrm.view_userlocation')
    context['can_view_location_attendance'] = request.user.has_perm('Hrm.view_locationattendance')
    context['can_view_shift'] = request.user.has_perm('Hrm.view_shift')
    context['can_view_roster'] = request.user.has_perm('Hrm.view_roster')
    context['can_view_roster_assignment'] = request.user.has_perm('Hrm.view_rosterassignment')
    context['can_view_leave_type'] = request.user.has_perm('Hrm.view_leavetype')
    context['can_view_leave_application'] = request.user.has_perm('Hrm.view_leaveapplication')
    context['can_view_short_leave_application'] = request.user.has_perm('Hrm.view_shortleaveapplication')
    context['can_view_leave_balance'] = request.user.has_perm('Hrm.view_leavebalance')
    context['can_view_holiday'] = request.user.has_perm('Hrm.view_holiday')
    context['can_view_zkdevice'] = request.user.has_perm('Hrm.view_zkdevice')  # Added
    context['can_view_zkattendancelog'] = request.user.has_perm('Hrm.view_zkattendancelog')  # Added
    context['can_view_zkuser'] = request.user.has_perm('Hrm.view_zkuser')  # Added
    
    # Payroll permissions
    context['can_view_salary_component'] = request.user.has_perm('Hrm.view_salarycomponent')
    context['can_view_employee_salary_structure'] = request.user.has_perm('Hrm.view_employeesalarystructure')
    context['can_view_salary_month'] = request.user.has_perm('Hrm.view_salarymonth')
    context['can_view_employee_salary'] = request.user.has_perm('Hrm.view_employeesalary')
    context['can_view_bonus_setup'] = request.user.has_perm('Hrm.view_bonussetup')
    context['can_view_bonus_month'] = request.user.has_perm('Hrm.view_bonusmonth')
    context['can_view_employee_bonus'] = request.user.has_perm('Hrm.view_employeebonus')
    context['can_view_advance_setup'] = request.user.has_perm('Hrm.view_advancesetup')
    context['can_view_employee_advance'] = request.user.has_perm('Hrm.view_employeeadvance')
    context['can_view_advance_installment'] = request.user.has_perm('Hrm.view_advanceinstallment')
    
    # Check if dashboard URL exists and is accessible
    try:
        reverse('permission:dashboard')
        context['show_dashboard_link'] = True
    except NoReverseMatch:
        pass
    
    # Check installed apps and set menu visibility based on permissions
    
    # Permission menu
    if apps.is_installed('permission'):
        context['show_permission_menu'] = any([
            context['can_view_user'],
            context['can_view_group'],
            context['can_view_permission']
        ])
    
    # Global Settings menu
    if apps.is_installed('global_settings'):
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
    
    # Finance menu
    if apps.is_installed('Finance'):
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
    
    # Business Partner menu
    if apps.is_installed('BusinessPartnerMasterData'):
        context['show_business_partner_menu'] = any([
            context['can_view_businesspartner'],
            request.user.has_perm('BusinessPartnerMasterData.view_businesspartnergroup'),
            request.user.has_perm('BusinessPartnerMasterData.view_financialinformation'),
            request.user.has_perm('BusinessPartnerMasterData.view_contactinformation'),
            request.user.has_perm('BusinessPartnerMasterData.view_address'),
            request.user.has_perm('BusinessPartnerMasterData.view_contactperson')
        ])
    
    # Inventory menu
    if apps.is_installed('Inventory'):
        context['show_inventory_menu'] = any([
            context['can_view_item'],
            context['can_view_warehouse'],
            context['can_view_itemgroup'],
            context['can_view_unitofmeasure'],
            context['can_view_inventorytransaction'],
            context['can_view_goodsreceipt'],
            request.user.has_perm('Inventory.view_goodsissue'),
            request.user.has_perm('Inventory.view_inventorytransfer'),
            request.user.has_perm('Inventory.view_inventorycount'),
            request.user.has_perm('Inventory.view_batchmaster'),
            request.user.has_perm('Inventory.view_serialnumber'),
            context['can_view_itemwarehouseinfo'],
        ])
    
    # Sales menu
    if apps.is_installed('Sales'):
        context['show_sales_menu'] = any([
            request.user.has_perm('Sales.view_salesquotation'),
            request.user.has_perm('Sales.view_salesorder'),
            request.user.has_perm('Sales.view_delivery'),
            request.user.has_perm('Sales.view_return'),
            request.user.has_perm('Sales.view_arinvoice'),
            request.user.has_perm('Sales.view_salesemployee'),
            request.user.has_perm('Sales.view_freeitemdiscount'),
        ])
    
    # Purchase menu
    if apps.is_installed('Purchase'):
        context['show_purchase_menu'] = any([
            request.user.has_perm('Purchase.view_purchasequotation'),
            request.user.has_perm('Purchase.view_purchaseorder'),
            request.user.has_perm('Purchase.view_goodsreceiptpo'),
            request.user.has_perm('Purchase.view_goodsreturn'),
            request.user.has_perm('Purchase.view_apinvoice')
        ])
    
    # Check if HRM app is installed
    if apps.is_installed('Hrm'):
        # Set HRM menu visibility based on any of these permission groups
        context['show_hrm_menu'] = any([
            context['can_view_employee'],
            context['can_view_employee_separation'],
            context['can_view_department'],
            context['can_view_designation'],
            context['can_view_location'],
            context['can_view_user_location'],
            context['can_view_location_attendance'],
            context['can_view_shift'],
            context['can_view_roster'],
            context['can_view_roster_assignment'],
            context['can_view_leave_type'],
            context['can_view_leave_application'],
            context['can_view_short_leave_application'],
            context['can_view_leave_balance'],
            context['can_view_holiday'],
            context['can_view_zkdevice'],  # Added
            context['can_view_zkattendancelog'],  # Added
            context['can_view_zkuser'],  # Added
        ])
        
        # Set Payroll menu visibility based on any of these permission groups
        context['show_payroll_menu'] = any([
            context['can_view_salary_component'],
            context['can_view_employee_salary_structure'],
            context['can_view_salary_month'],
            context['can_view_employee_salary'],
            context['can_view_bonus_setup'],
            context['can_view_bonus_month'],
            context['can_view_employee_bonus'],
            context['can_view_advance_setup'],
            context['can_view_employee_advance'],
            context['can_view_advance_installment'],
        ])
    
    # Banking menu
    if apps.is_installed('Banking'):
        context['show_banking_menu'] = any([
            request.user.has_perm('Banking.view_payment'),
            request.user.has_perm('Banking.view_paymentmethod'),
        ])
    
    return context

def notification_processor(request):
    """
    Context processor to add unread notification count to all templates.
    """
    unread_notification_count = 0
    
    if request.user.is_authenticated and apps.is_installed('global_settings'):
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
        
        unread_notification_count = user_notifications + all_user_notifications
    
    return {
        'unread_notification_count': unread_notification_count
    }