from django.urls import path,include
from . import views

app_name = 'BusinessPartnerMasterData'

urlpatterns = [
    # Business Partner URLs (existing)
    path('', views.BusinessPartnerListView.as_view(), name='business_partner_list'),
    path('create/', views.BusinessPartnerCreateView.as_view(), name='business_partner_create'),
    path('<int:pk>/update/', views.BusinessPartnerUpdateView.as_view(), name='business_partner_update'),
    path('<int:pk>/delete/', views.BusinessPartnerDeleteView.as_view(), name='business_partner_delete'),
    path('<int:pk>/', views.BusinessPartnerDetailView.as_view(), name='business_partner_detail'),
    path('export-csv/', views.BusinessPartnerExportView.as_view(), name='export_business_partners_csv'),
    path('bulk-delete/', views.BusinessPartnerBulkDeleteView.as_view(), name='bulk_delete_business_partners'),
    path('print/', views.BusinessPartnerPrintView.as_view(), name='business_partner_print'),
    path('<int:pk>/print/', views.BusinessPartnerPrintView.as_view(), name='business_partner_print_detail'),
    
    # Financial Information URLs
    path('financial-information/', views.FinancialInformationListView.as_view(), name='financial_information_list'),
    path('financial-information/create/', views.FinancialInformationCreateView.as_view(), name='financial_information_create'),
    path('financial-information/<int:pk>/update/', views.FinancialInformationUpdateView.as_view(), name='financial_information_update'),
    path('financial-information/<int:pk>/delete/', views.FinancialInformationDeleteView.as_view(), name='financial_information_delete'),
    path('financial-information/<int:pk>/', views.FinancialInformationDetailView.as_view(), name='financial_information_detail'),
    
    # Contact Information URLs
    path('contact-information/', views.ContactInformationListView.as_view(), name='contact_information_list'),
    path('contact-information/create/', views.ContactInformationCreateView.as_view(), name='contact_information_create'),
    path('contact-information/<int:pk>/update/', views.ContactInformationUpdateView.as_view(), name='contact_information_update'),
    path('contact-information/<int:pk>/delete/', views.ContactInformationDeleteView.as_view(), name='contact_information_delete'),
    path('contact-information/<int:pk>/', views.ContactInformationDetailView.as_view(), name='contact_information_detail'),
    
    # Address URLs
    path('address/', views.AddressListView.as_view(), name='address_list'),
    path('address/create/', views.AddressCreateView.as_view(), name='address_create'),
    path('address/<int:pk>/update/', views.AddressUpdateView.as_view(), name='address_update'),
    path('address/<int:pk>/delete/', views.AddressDeleteView.as_view(), name='address_delete'),
    path('address/<int:pk>/', views.AddressDetailView.as_view(), name='address_detail'),
    
    # Contact Person URLs
    path('contact-person/', views.ContactPersonListView.as_view(), name='contact_person_list'),
    path('contact-person/create/', views.ContactPersonCreateView.as_view(), name='contact_person_create'),
    path('contact-person/<int:pk>/update/', views.ContactPersonUpdateView.as_view(), name='contact_person_update'),
    path('contact-person/<int:pk>/delete/', views.ContactPersonDeleteView.as_view(), name='contact_person_delete'),
    path('contact-person/<int:pk>/', views.ContactPersonDetailView.as_view(), name='contact_person_detail'),


    # path('api/business-partner/', include('BusinessPartnerMasterData.api.urls', namespace='businesspartner_api')),

    path('api/', include('BusinessPartnerMasterData.api.urls', namespace='businesspartner_api')),

]