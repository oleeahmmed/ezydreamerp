from django.urls import path
from .views import (
    PaymentMethodListView, PaymentMethodCreateView, PaymentMethodUpdateView,
    PaymentMethodDetailView, PaymentMethodDeleteView, PaymentMethodExportView,
    PaymentMethodBulkDeleteView, PaymentListView, PaymentCreateView,
    PaymentUpdateView, PaymentDetailView, PaymentDeleteView,
    PaymentExportView, PaymentBulkDeleteView, PaymentPrintView
)

app_name = 'Banking'

urlpatterns = [
    # Payment Method URLs
    path('payment-method/', PaymentMethodListView.as_view(), name='payment_method_list'),
    path('payment-method/create/', PaymentMethodCreateView.as_view(), name='payment_method_create'),
    path('payment-method/<int:pk>/update/', PaymentMethodUpdateView.as_view(), name='payment_method_update'),
    path('payment-method/<int:pk>/delete/', PaymentMethodDeleteView.as_view(), name='payment_method_delete'),
    path('payment-method/<int:pk>/', PaymentMethodDetailView.as_view(), name='payment_method_detail'),
    path('payment-method/export/', PaymentMethodExportView.as_view(), name='payment_method_export'),
    path('payment-method/bulk-delete/', PaymentMethodBulkDeleteView.as_view(), name='payment_method_bulk_delete'),
    
    # Payment URLs
    path('payment/', PaymentListView.as_view(), name='payment_list'),
    path('payment/create/', PaymentCreateView.as_view(), name='payment_create'),
    path('payment/<int:pk>/update/', PaymentUpdateView.as_view(), name='payment_update'),
    path('payment/<int:pk>/delete/', PaymentDeleteView.as_view(), name='payment_delete'),
    path('payment/<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
    path('payment/<int:pk>/print/', PaymentPrintView.as_view(), name='payment_print'),
    path('payment/export/', PaymentExportView.as_view(), name='payment_export'),
    path('payment/bulk-delete/', PaymentBulkDeleteView.as_view(), name='payment_bulk_delete'),
]

