from django.urls import path, include
from .views import (
    # BOM views
    BillOfMaterialsListView, BillOfMaterialsCreateView, BillOfMaterialsUpdateView,
    BillOfMaterialsDetailView, BillOfMaterialsDeleteView, BillOfMaterialsExportView,
    BillOfMaterialsBulkDeleteView,
    
    # Production Receipt views
    ProductionReceiptListView, ProductionReceiptCreateView, ProductionReceiptUpdateView,
    ProductionReceiptDetailView, ProductionReceiptDeleteView, ProductionReceiptExportView,
    ProductionReceiptBulkDeleteView, ProductionReceiptPrintView,
    
    # Production Issue views
    ProductionIssueListView, ProductionIssueCreateView, ProductionIssueUpdateView,
    ProductionIssueDetailView, ProductionIssueDeleteView, ProductionIssueExportView,
    ProductionIssueBulkDeleteView, ProductionIssuePrintView,
    
    # Dashboard views
    ProductionDashboardView,
    
    # API views
    ProductBOMsAPIView, ProductInfoAPIView
)
from .views.production_order_views import (
    ProductionOrderListView, ProductionOrderCreateView, ProductionOrderUpdateView,
    ProductionOrderDetailView, ProductionOrderDeleteView, ProductionOrderExportView,
    ProductionOrderBulkDeleteView, BOMComponentsAPIView
)

app_name = 'Production'

urlpatterns = [
    # Dashboard URLs
    path('dashboard/daily/', ProductionDashboardView.as_view(), {'period': 'daily'}, name='dashboard_daily'),
    path('dashboard/weekly/', ProductionDashboardView.as_view(), {'period': 'weekly'}, name='dashboard_weekly'),
    path('dashboard/monthly/', ProductionDashboardView.as_view(), {'period': 'monthly'}, name='dashboard_monthly'),
    path('dashboard/', ProductionDashboardView.as_view(), name='dashboard'),
    
    # Bill of Materials URLs
    path('bom/', BillOfMaterialsListView.as_view(), name='bill_of_materials_list'),
    path('bom/create/', BillOfMaterialsCreateView.as_view(), name='bom_create'),
    path('bom/<int:pk>/update/', BillOfMaterialsUpdateView.as_view(), name='bom_update'),
    path('bom/<int:pk>/delete/', BillOfMaterialsDeleteView.as_view(), name='bom_delete'),
    path('bom/<int:pk>/', BillOfMaterialsDetailView.as_view(), name='bill_of_materials_detail'),
    path('bom/export/', BillOfMaterialsExportView.as_view(), name='bom_export'),
    path('bom/bulk-delete/', BillOfMaterialsBulkDeleteView.as_view(), name='bom_bulk_delete'),
    path('bom/<int:pk>/print/', BillOfMaterialsDetailView.as_view(), name='production_receipt_print'),

    # Production Order URLs
    path('production/orders/', ProductionOrderListView.as_view(), name='production_order_list'),
    path('production/orders/create/', ProductionOrderCreateView.as_view(), name='production_order_create'),
    path('production-orders/<int:pk>/', ProductionOrderDetailView.as_view(), name='production_order_detail'),
    path('production-orders/<int:pk>/update/', ProductionOrderUpdateView.as_view(), name='production_order_update'),
    path('production-orders/<int:pk>/delete/', ProductionOrderDeleteView.as_view(), name='production_order_delete'),
    path('production-orders/export/', ProductionOrderExportView.as_view(), name='production_order_export'),
    path('production-orders/bulk-delete/', ProductionOrderBulkDeleteView.as_view(), name='production_order_bulk_delete'),
    # Production Receipt URLs
    path('receipt/', ProductionReceiptListView.as_view(), name='production_receipt_list'),
    path('receipt/create/', ProductionReceiptCreateView.as_view(), name='production_receipt_create'),
    path('receipt/<int:pk>/update/', ProductionReceiptUpdateView.as_view(), name='production_receipt_update'),
    path('receipt/<int:pk>/delete/', ProductionReceiptDeleteView.as_view(), name='production_receipt_delete'),
    path('receipt/<int:pk>/', ProductionReceiptDetailView.as_view(), name='production_receipt_detail'),
    path('receipt/<int:pk>/print/', ProductionReceiptPrintView.as_view(), name='production_receipt_print'),
    path('receipt/export/', ProductionReceiptExportView.as_view(), name='production_receipt_export'),
    path('receipt/bulk-delete/', ProductionReceiptBulkDeleteView.as_view(), name='production_receipt_bulk_delete'),
    
    # Production Issue URLs
    path('issue/', ProductionIssueListView.as_view(), name='production_issue_list'),
    path('issue/create/', ProductionIssueCreateView.as_view(), name='production_issue_create'),
    path('issue/<int:pk>/update/', ProductionIssueUpdateView.as_view(), name='production_issue_update'),
    path('issue/<int:pk>/delete/', ProductionIssueDeleteView.as_view(), name='production_issue_delete'),
    path('issue/<int:pk>/', ProductionIssueDetailView.as_view(), name='production_issue_detail'),
    path('issue/<int:pk>/print/', ProductionIssuePrintView.as_view(), name='production_issue_print'),
    path('issue/export/', ProductionIssueExportView.as_view(), name='production_issue_export'),
    path('issue/bulk-delete/', ProductionIssueBulkDeleteView.as_view(), name='production_issue_bulk_delete'),
    
    # API URLs for auto-fill functionality
    path('api/product/<int:product_id>/boms/', ProductBOMsAPIView.as_view(), name='product_boms_api'),
    path('api/bom/<int:bom_id>/components/', BOMComponentsAPIView.as_view(), name='bom_components_api'),
    path('api/product/<int:product_id>/info/', ProductInfoAPIView.as_view(), name='product_info_api'),
]
