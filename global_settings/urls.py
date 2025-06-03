from django.urls import path
from . import views

app_name = 'global_settings'

urlpatterns = [
    # Currency URLs
    path('currency/', views.CurrencyCrudView.as_view(), name='currency_list'),
    path('currency/create/', views.CurrencyCrudView.as_view(), {'action': 'create'}, name='currency_create'),
    path('currency/<int:pk>/', views.CurrencyCrudView.as_view(), {'action': 'detail'}, name='currency_detail'),
    path('currency/<int:pk>/update/', views.CurrencyCrudView.as_view(), {'action': 'update'}, name='currency_update'),
    path('currency/<int:pk>/delete/', views.CurrencyCrudView.as_view(), {'action': 'delete'}, name='currency_delete'),
    path('currency/print/', views.CurrencyCrudView.as_view(), {'action': 'print'}, name='currency_print'),

    # Payment Terms URLs
    path('payment-terms/', views.PaymentTermsCrudView.as_view(), name='payment_terms_list'),
    path('payment-terms/create/', views.PaymentTermsCrudView.as_view(), {'action': 'create'}, name='payment_terms_create'),
    path('payment-terms/<int:pk>/', views.PaymentTermsCrudView.as_view(), {'action': 'detail'}, name='payment_terms_detail'),
    path('payment-terms/<int:pk>/update/', views.PaymentTermsCrudView.as_view(), {'action': 'update'}, name='payment_terms_update'),
    path('payment-terms/<int:pk>/delete/', views.PaymentTermsCrudView.as_view(), {'action': 'delete'}, name='payment_terms_delete'),
    path('payment-terms/print/', views.PaymentTermsCrudView.as_view(), {'action': 'print'}, name='payment_terms_print'),

    # Company Info URLs
    path('company-info/', views.CompanyInfoCrudView.as_view(), name='company_info_list'),
    path('company-info/create/', views.CompanyInfoCrudView.as_view(), {'action': 'create'}, name='company_info_create'),
    path('company-info/<int:pk>/', views.CompanyInfoCrudView.as_view(), {'action': 'detail'}, name='company_info_detail'),
    path('company-info/<int:pk>/update/', views.CompanyInfoCrudView.as_view(), {'action': 'update'}, name='company_info_update'),
    path('company-info/<int:pk>/delete/', views.CompanyInfoCrudView.as_view(), {'action': 'delete'}, name='company_info_delete'),
    path('company-info/print/', views.CompanyInfoCrudView.as_view(), {'action': 'print'}, name='company_info_print'),

    # Localization URLs
    path('localization/', views.LocalizationCrudView.as_view(), name='localization_list'),
    path('localization/create/', views.LocalizationCrudView.as_view(), {'action': 'create'}, name='localization_create'),
    path('localization/<int:pk>/', views.LocalizationCrudView.as_view(), {'action': 'detail'}, name='localization_detail'),
    path('localization/<int:pk>/update/', views.LocalizationCrudView.as_view(), {'action': 'update'}, name='localization_update'),
    path('localization/<int:pk>/delete/', views.LocalizationCrudView.as_view(), {'action': 'delete'}, name='localization_delete'),
    path('localization/print/', views.LocalizationCrudView.as_view(), {'action': 'print'}, name='localization_print'),

    # Accounting URLs
    path('accounting/', views.AccountingCrudView.as_view(), name='accounting_list'),
    path('accounting/create/', views.AccountingCrudView.as_view(), {'action': 'create'}, name='accounting_create'),
    path('accounting/<int:pk>/', views.AccountingCrudView.as_view(), {'action': 'detail'}, name='accounting_detail'),
    path('accounting/<int:pk>/update/', views.AccountingCrudView.as_view(), {'action': 'update'}, name='accounting_update'),
    path('accounting/<int:pk>/delete/', views.AccountingCrudView.as_view(), {'action': 'delete'}, name='accounting_delete'),
    path('accounting/print/', views.AccountingCrudView.as_view(), {'action': 'print'}, name='accounting_print'),

    # User Settings URLs
    path('user-settings/', views.UserSettingsCrudView.as_view(), name='user_settings_list'),
    path('user-settings/create/', views.UserSettingsCrudView.as_view(), {'action': 'create'}, name='user_settings_create'),
    path('user-settings/<int:pk>/', views.UserSettingsCrudView.as_view(), {'action': 'detail'}, name='user_settings_detail'),
    path('user-settings/<int:pk>/update/', views.UserSettingsCrudView.as_view(), {'action': 'update'}, name='user_settings_update'),
    path('user-settings/<int:pk>/delete/', views.UserSettingsCrudView.as_view(), {'action': 'delete'}, name='user_settings_delete'),
    path('user-settings/print/', views.UserSettingsCrudView.as_view(), {'action': 'print'}, name='user_settings_print'),

    # Email Settings URLs
    path('email-settings/', views.EmailSettingsCrudView.as_view(), name='email_settings_list'),
    path('email-settings/create/', views.EmailSettingsCrudView.as_view(), {'action': 'create'}, name='email_settings_create'),
    path('email-settings/<int:pk>/', views.EmailSettingsCrudView.as_view(), {'action': 'detail'}, name='email_settings_detail'),
    path('email-settings/<int:pk>/update/', views.EmailSettingsCrudView.as_view(), {'action': 'update'}, name='email_settings_update'),
    path('email-settings/<int:pk>/delete/', views.EmailSettingsCrudView.as_view(), {'action': 'delete'}, name='email_settings_delete'),
    path('email-settings/print/', views.EmailSettingsCrudView.as_view(), {'action': 'print'}, name='email_settings_print'),

    # Tax Settings URLs
    path('tax-settings/', views.TaxSettingsCrudView.as_view(), name='tax_settings_list'),
    path('tax-settings/create/', views.TaxSettingsCrudView.as_view(), {'action': 'create'}, name='tax_settings_create'),
    path('tax-settings/<int:pk>/', views.TaxSettingsCrudView.as_view(), {'action': 'detail'}, name='tax_settings_detail'),
    path('tax-settings/<int:pk>/update/', views.TaxSettingsCrudView.as_view(), {'action': 'update'}, name='tax_settings_update'),
    path('tax-settings/<int:pk>/delete/', views.TaxSettingsCrudView.as_view(), {'action': 'delete'}, name='tax_settings_delete'),
    path('tax-settings/print/', views.TaxSettingsCrudView.as_view(), {'action': 'print'}, name='tax_settings_print'),

    # Payment Settings URLs
    path('payment-settings/', views.PaymentSettingsCrudView.as_view(), name='payment_settings_list'),
    path('payment-settings/create/', views.PaymentSettingsCrudView.as_view(), {'action': 'create'}, name='payment_settings_create'),
    path('payment-settings/<int:pk>/', views.PaymentSettingsCrudView.as_view(), {'action': 'detail'}, name='payment_settings_detail'),
    path('payment-settings/<int:pk>/update/', views.PaymentSettingsCrudView.as_view(), {'action': 'update'}, name='payment_settings_update'),
    path('payment-settings/<int:pk>/delete/', views.PaymentSettingsCrudView.as_view(), {'action': 'delete'}, name='payment_settings_delete'),
    path('payment-settings/print/', views.PaymentSettingsCrudView.as_view(), {'action': 'print'}, name='payment_settings_print'),

    # Backup Settings URLs
    path('backup-settings/', views.BackupSettingsCrudView.as_view(), name='backup_settings_list'),
    path('backup-settings/create/', views.BackupSettingsCrudView.as_view(), {'action': 'create'}, name='backup_settings_create'),
    path('backup-settings/<int:pk>/', views.BackupSettingsCrudView.as_view(), {'action': 'detail'}, name='backup_settings_detail'),
    path('backup-settings/<int:pk>/update/', views.BackupSettingsCrudView.as_view(), {'action': 'update'}, name='backup_settings_update'),
    path('backup-settings/<int:pk>/delete/', views.BackupSettingsCrudView.as_view(), {'action': 'delete'}, name='backup_settings_delete'),
    path('backup-settings/print/', views.BackupSettingsCrudView.as_view(), {'action': 'print'}, name='backup_settings_print'),

    # General Settings URLs
    path('general-settings/', views.GeneralSettingsCrudView.as_view(), name='general_settings_list'),
    path('general-settings/create/', views.GeneralSettingsCrudView.as_view(), {'action': 'create'}, name='general_settings_create'),
    path('general-settings/<int:pk>/', views.GeneralSettingsCrudView.as_view(), {'action': 'detail'}, name='general_settings_detail'),
    path('general-settings/<int:pk>/update/', views.GeneralSettingsCrudView.as_view(), {'action': 'update'}, name='general_settings_update'),
    path('general-settings/<int:pk>/delete/', views.GeneralSettingsCrudView.as_view(), {'action': 'delete'}, name='general_settings_delete'),
    path('general-settings/print/', views.GeneralSettingsCrudView.as_view(), {'action': 'print'}, name='general_settings_print'),

    # Notification URLs
    path('notification/', views.NotificationCrudView.as_view(), name='notification_list'),
    path('notification/create/', views.NotificationCrudView.as_view(), {'action': 'create'}, name='notification_create'),
    path('notification/<int:pk>/', views.NotificationCrudView.as_view(), {'action': 'detail'}, name='notification_detail'),
    path('notification/<int:pk>/update/', views.NotificationCrudView.as_view(), {'action': 'update'}, name='notification_update'),
    path('notification/<int:pk>/delete/', views.NotificationCrudView.as_view(), {'action': 'delete'}, name='notification_delete'),
    path('notification/print/', views.NotificationCrudView.as_view(), {'action': 'print'}, name='notification_print'),
    
    # Mark notification as read
    path('notification/<int:pk>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
        # API endpoint for notifications
    path('api/notifications/', views.get_user_notifications, name='get_user_notifications'),
]