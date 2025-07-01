
from django.conf.urls.static import static
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.utils.translation import gettext_lazy as _

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Import custom authentication views
from .authentication import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView
)

# Define tag groups for hierarchical organization
TAGS = [
    # Authentication Tags
    {'name': 'Authentication', 'description': 'Authentication endpoints for obtaining and managing JWT tokens'},
    
    # Sales Module Tags
    {'name': 'Sales', 'description': 'All operations related to the Sales module'},
    {'name': 'Sales Quotations', 'description': 'Manage sales quotations sent to potential customers'},
    {'name': 'Sales Orders', 'description': 'Manage confirmed customer orders'},
    {'name': 'Deliveries', 'description': 'Manage shipments of goods to customers'},
    {'name': 'Returns', 'description': 'Manage goods returned by customers'},
    {'name': 'AR Invoices', 'description': 'Manage invoices sent to customers'},
    {'name': 'Sales Employees', 'description': 'Manage sales staff information'},
    
    # Business Partner Module Tags
    {'name': 'Business Partners', 'description': 'All operations related to the Business Partners module'},
    {'name': 'Business Partner Master', 'description': 'Manage business partner master data'},
    {'name': 'Business Partner Groups', 'description': 'Manage business partner groups for categorization'},
    {'name': 'Addresses', 'description': 'Manage business partner addresses'},
    {'name': 'Contact Persons', 'description': 'Manage business partner contact persons'},
    {'name': 'Financial Information', 'description': 'Manage business partner financial information'},
    {'name': 'Contact Information', 'description': 'Manage business partner contact information'},
    
    # Inventory Module Tags
    {'name': 'Inventory', 'description': 'All operations related to the Inventory module'},
    {'name': 'Items', 'description': 'Manage inventory items'},
    {'name': 'Item Groups', 'description': 'Manage item groups for categorization'},
    {'name': 'Warehouses', 'description': 'Manage warehouses for inventory storage'},
    {'name': 'Inventory Transactions', 'description': 'Manage inventory transactions'},
    {'name': 'Goods Receipt', 'description': 'Manage goods receipt documents'},
    {'name': 'Goods Issue', 'description': 'Manage goods issue documents'},
    {'name': 'Inventory Transfers', 'description': 'Manage inventory transfers between warehouses'},
]

schema_view = get_schema_view(
   openapi.Info(
      title="Yash Global ERP API",
      default_version='v1',
      description="""
      # Yash Global ERP API Documentation
      This API provides access to the Yash Global ERP system, allowing you to manage:
      * Business Partners (Customers and Suppliers)
      * Inventory (Items, Warehouses, Transactions)
      * Sales Documents (Quotations, Orders, Deliveries, Returns, Invoices)
      * Purchase Documents
      * Finance Operations
      * Human Resources
      * Banking Operations

      ## Authentication
      All API endpoints require JWT authentication. To authenticate:
      1. Obtain a token by sending a POST request to `/api/token/` with your username and password
      2. Include the token in the Authorization header of all requests: `Authorization: Bearer <your_token>`

      ## Permissions
      Access to endpoints is controlled by Django's permission system. Users can only access data they have permission to view.
      """,
      terms_of_service="https://www.yashglobalsdnbhd.com/terms/",
      contact=openapi.Contact(email="contact@yashglobalsdnbhd.com"),
      license=openapi.License(name="Proprietary License"),
      x_tagGroups=[
          {
              'name': 'Authentication',
              'tags': ['Authentication']
          },
          {
              'name': 'Sales',
              'tags': [
                  'Sales',
                  'Sales Quotations',
                  'Sales Orders',
                  'Deliveries',
                  'Returns',
                  'AR Invoices',
                  'Sales Employees'
              ]
          },
          {
              'name': 'Business Partners',
              'tags': [
                  'Business Partners',
                  'Business Partner Master',
                  'Business Partner Groups',
                  'Addresses',
                  'Contact Persons',
                  'Financial Information',
                  'Contact Information'
              ]
          },
          {
              'name': 'Inventory',
              'tags': [
                  'Inventory',
                  'Items',
                  'Item Groups',
                  'Warehouses',
                  'Inventory Transactions',
                  'Goods Receipt',
                  'Goods Issue',
                  'Inventory Transfers'
              ]
          }
      ],
      tags=TAGS
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

from django.contrib import admin
from django.urls import path, include, re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    
    # Use custom authentication views with better documentation
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),      # login
    path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),      # refresh
    path('api/token/verify/', CustomTokenVerifyView.as_view(), name='token_verify'), 
    
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('ckeditor5/', include('django_ckeditor_5.urls')),  

    path('', include('permission.urls')),
    path('settings/', include('global_settings.urls')),
    path('business-partners/', include('BusinessPartnerMasterData.urls')),      
    path('inventory/', include('Inventory.urls')),
    path('sales/', include('Sales.urls')),  
    path('purchase/', include('Purchase.urls')),  
    path('finance/', include('Finance.urls')),  
    path('hrm/', include('Hrm.urls')),  
    path('banking/', include('Banking.urls',namespace='banking')),  
    path('production/', include('Production.urls')),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

