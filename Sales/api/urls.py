# Sales/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SalesEmployeeViewSet,
    SalesOrderStatusViewSet,
    SalesQuotationViewSet,
    SalesOrderViewSet,
    DeliveryViewSet,
    ReturnViewSet,
    ARInvoiceViewSet
)
from .views import SalesOrderToDeliveryAPIView, DeliveryToReturnAPIView,DeliveryToARInvoiceAPIView
from .views import SalesEmployeeSummaryAPIView

app_name = 'sales_api'

# Create a router and register our viewsets with it
router = DefaultRouter()
# router.register(r'sales-employees', SalesEmployeeViewSet)
router.register(r'sales-quotations', SalesQuotationViewSet)
router.register(r'sales-orders', SalesOrderViewSet)
router.register(r'deliveries', DeliveryViewSet)
router.register(r'returns', ReturnViewSet)
router.register(r'ar-invoices', ARInvoiceViewSet)
router.register(r'sales-status', SalesOrderStatusViewSet, basename='sales-order-status')


# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
    path('convert-order-to-delivery/', SalesOrderToDeliveryAPIView.as_view(), name='convert-order-to-delivery'),
    path('convert-delivery-to-return/', DeliveryToReturnAPIView.as_view(), name='convert-delivery-to-return'),
    path('convert-delivery-to-invoice/', DeliveryToARInvoiceAPIView.as_view(), name='convert-delivery-to-invoice'),    
    path('sales-employee-summary/', SalesEmployeeSummaryAPIView.as_view(), name='sales-employee-summary'),
   
]