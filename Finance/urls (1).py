from django.urls import path
from .views import (
    # Account Type views
    AccountTypeListView, AccountTypeCreateView, AccountTypeUpdateView,
    AccountTypeDetailView, AccountTypeDeleteView, AccountTypeExportView,
    AccountTypePrintView, AccountTypePrintDetailView, AccountTypeBulkDeleteView,
    
    # Account views
    AccountListView, AccountCreateView, AccountUpdateView,
    AccountDetailView, AccountDeleteView, AccountExportView,
    AccountPrintView, AccountPrintDetailView, AccountBulkDeleteView,
    
    # Journal Entry views
    JournalEntryListView, JournalEntryCreateView, JournalEntryUpdateView,
    JournalEntryDetailView, JournalEntryDeleteView, JournalEntryExportView,
    JournalEntryPrintView, JournalEntryPrintDetailView, JournalEntryBulkDeleteView,
    
    # General Ledger views
    GeneralLedgerListView, GeneralLedgerCreateView, GeneralLedgerUpdateView,
    GeneralLedgerDetailView, GeneralLedgerDeleteView, GeneralLedgerExportView,
    GeneralLedgerPrintView, GeneralLedgerPrintDetailView, GeneralLedgerBulkDeleteView,
    
    # Cost Center views
    CostCenterListView, CostCenterCreateView, CostCenterUpdateView,
    CostCenterDetailView, CostCenterDeleteView, CostCenterExportView,
    CostCenterPrintView, CostCenterPrintDetailView, CostCenterBulkDeleteView,
)

app_name = 'Finance'

urlpatterns = [
    # Account Type URLs
    path('account-types/', AccountTypeListView.as_view(), name='account_type_list'),
    path('account-types/create/', AccountTypeCreateView.as_view(), name='account_type_create'),
    path('account-types/<int:pk>/', AccountTypeDetailView.as_view(), name='account_type_detail'),
    path('account-types/<int:pk>/update/', AccountTypeUpdateView.as_view(), name='account_type_update'),
    path('account-types/<int:pk>/delete/', AccountTypeDeleteView.as_view(), name='account_type_delete'),
    path('account-types/export/', AccountTypeExportView.as_view(), name='account_type_export'),
    path('account-types/print/', AccountTypePrintView.as_view(), name='account_type_print_list'),
    path('account-types/<int:pk>/print/', AccountTypePrintDetailView.as_view(), name='account_type_print_detail'),
    path('account-types/bulk-delete/', AccountTypeBulkDeleteView.as_view(), name='account_type_bulk_delete'),
    
    # Account URLs
    path('accounts/', AccountListView.as_view(), name='account_list'),
    path('accounts/create/', AccountCreateView.as_view(), name='account_create'),
    path('accounts/<int:pk>/', AccountDetailView.as_view(), name='account_detail'),
    path('accounts/<int:pk>/update/', AccountUpdateView.as_view(), name='account_update'),
    path('accounts/<int:pk>/delete/', AccountDeleteView.as_view(), name='account_delete'),
    path('accounts/export/', AccountExportView.as_view(), name='account_export'),
    path('accounts/print/', AccountPrintView.as_view(), name='account_print_list'),
    path('accounts/<int:pk>/print/', AccountPrintDetailView.as_view(), name='account_print_detail'),
    path('accounts/bulk-delete/', AccountBulkDeleteView.as_view(), name='account_bulk_delete'),
    
    # Journal Entry URLs
    path('journal-entries/', JournalEntryListView.as_view(), name='journal_entry_list'),
    path('journal-entries/create/', JournalEntryCreateView.as_view(), name='journal_entry_create'),
    path('journal-entries/<int:pk>/', JournalEntryDetailView.as_view(), name='journal_entry_detail'),
    path('journal-entries/<int:pk>/update/', JournalEntryUpdateView.as_view(), name='journal_entry_update'),
    path('journal-entries/<int:pk>/delete/', JournalEntryDeleteView.as_view(), name='journal_entry_delete'),
    path('journal-entries/export/', JournalEntryExportView.as_view(), name='journal_entry_export'),
    path('journal-entries/print/', JournalEntryPrintView.as_view(), name='journal_entry_print_list'),
    path('journal-entries/<int:pk>/print/', JournalEntryPrintDetailView.as_view(), name='journal_entry_print_detail'),
    path('journal-entries/bulk-delete/', JournalEntryBulkDeleteView.as_view(), name='journal_entry_bulk_delete'),
    
    # General Ledger URLs
    path('general-ledger/', GeneralLedgerListView.as_view(), name='general_ledger_list'),
    path('general-ledger/create/', GeneralLedgerCreateView.as_view(), name='general_ledger_create'),
    path('general-ledger/<int:pk>/', GeneralLedgerDetailView.as_view(), name='general_ledger_detail'),
    path('general-ledger/<int:pk>/update/', GeneralLedgerUpdateView.as_view(), name='general_ledger_update'),
    path('general-ledger/<int:pk>/delete/', GeneralLedgerDeleteView.as_view(), name='general_ledger_delete'),
    path('general-ledger/export/', GeneralLedgerExportView.as_view(), name='general_ledger_export'),
    path('general-ledger/print/', GeneralLedgerPrintView.as_view(), name='general_ledger_print_list'),
    path('general-ledger/<int:pk>/print/', GeneralLedgerPrintDetailView.as_view(), name='general_ledger_print_detail'),
    path('general-ledger/bulk-delete/', GeneralLedgerBulkDeleteView.as_view(), name='general_ledger_bulk_delete'),
    
    # Cost Center URLs
    path('cost-centers/', CostCenterListView.as_view(), name='cost_center_list'),
    path('cost-centers/create/', CostCenterCreateView.as_view(), name='cost_center_create'),
    path('cost-centers/<int:pk>/', CostCenterDetailView.as_view(), name='cost_center_detail'),
    path('cost-centers/<int:pk>/update/', CostCenterUpdateView.as_view(), name='cost_center_update'),
    path('cost-centers/<int:pk>/delete/', CostCenterDeleteView.as_view(), name='cost_center_delete'),
    path('cost-centers/export/', CostCenterExportView.as_view(), name='cost_center_export'),
    path('cost-centers/print/', CostCenterPrintView.as_view(), name='cost_center_print_list'),
    path('cost-centers/<int:pk>/print/', CostCenterPrintDetailView.as_view(), name='cost_center_print_detail'),
    path('cost-centers/bulk-delete/', CostCenterBulkDeleteView.as_view(), name='cost_center_bulk_delete'),
]