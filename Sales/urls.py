from django.urls import path,include
from .views import (
  # Sales Employee views
  SalesEmployeeListView, SalesEmployeeCreateView, SalesEmployeeUpdateView,
  SalesEmployeeDetailView, SalesEmployeeDeleteView, SalesEmployeeExportView,
  SalesEmployeeBulkDeleteView,

  # Sales Quotation views
  SalesQuotationListView, SalesQuotationCreateView, SalesQuotationUpdateView,
  SalesQuotationDetailView, SalesQuotationDeleteView, SalesQuotationExportView,
  SalesQuotationPrintView, SalesQuotationBulkDeleteView,
  
  # Sales Order views
  SalesOrderListView, SalesOrderCreateView, SalesOrderUpdateView,
  SalesOrderDetailView, SalesOrderDeleteView, SalesOrderExportView,
  SalesOrderPrintView, SalesOrderBulkDeleteView,
  
  # Delivery views
  DeliveryListView, DeliveryCreateView, DeliveryUpdateView,
  DeliveryDetailView, DeliveryDeleteView, DeliveryExportView,DeliveryPrintView,
  DeliveryBulkDeleteView,
  
  # Return views
  ReturnListView, ReturnCreateView, ReturnUpdateView,
  ReturnDetailView, ReturnDeleteView, ReturnExportView,
  ReturnBulkDeleteView,
  
  # AR Invoice views
  ARInvoiceListView, ARInvoiceCreateView, ARInvoiceUpdateView,
  ARInvoiceDetailView, ARInvoiceDeleteView, ARInvoiceExportView,
  ARInvoiceBulkDeleteView, ARInvoicePrintView,
  
  # Conversion views
  ConvertQuotationToOrderView, ConvertOrderToDeliveryView,
  ConvertDeliveryToReturnView, ConvertOrderToInvoiceView,
  ConvertDeliveryToInvoiceView,
  demo_views,
  # Dashboard views
  SalesDashboardView, SalesDashboardChartView,
  
    FreeItemDiscountListView, FreeItemDiscountCreateView, FreeItemDiscountUpdateView,
    FreeItemDiscountDetailView, FreeItemDiscountDeleteView,
    FreeItemDiscountExportView, FreeItemDiscountBulkDeleteView,

)
from .views.sales_report_views import (
  SalesQuotationReportView,
  SalesQuotationReportDetailsView,
    SalesReportListView,
    SalesReportView,
    SalesReportDetailsView,
    DeliveryReportView,
    DeliveryReportDetailsView,
    ReturnReportView,
    ReturnReportDetailsView,
    ARInvoiceReportView,
    ARInvoiceReportDetailsView,
    MenuPageView
)
from .views.sales_employee_sales_report import SalesEmployeeSalesReportView

app_name = 'Sales'

urlpatterns = [

    

  # Sales Employee URLs
  path('sales-employee/', SalesEmployeeListView.as_view(), name='sales_employee_list'),
  path('sales-employee/create/', SalesEmployeeCreateView.as_view(), name='sales_employee_create'),
  path('sales-employee/<int:pk>/update/', SalesEmployeeUpdateView.as_view(), name='sales_employee_update'),
  path('sales-employee/<int:pk>/delete/', SalesEmployeeDeleteView.as_view(), name='sales_employee_delete'),
  path('sales-employee/<int:pk>/', SalesEmployeeDetailView.as_view(), name='sales_employee_detail'),
  path('sales-employee/export/', SalesEmployeeExportView.as_view(), name='sales_employee_export'),
  path('sales-employee/bulk-delete/', SalesEmployeeBulkDeleteView.as_view(), name='sales_employee_bulk_delete'),
  
  # Sales Quotation URLs
  path('sales-quotation/', SalesQuotationListView.as_view(), name='sales_quotation_list'),
  path('sales-quotation/create/', SalesQuotationCreateView.as_view(), name='sales_quotation_create'),
  path('sales-quotation/<int:pk>/update/', SalesQuotationUpdateView.as_view(), name='sales_quotation_update'),
  path('sales-quotation/<int:pk>/delete/', SalesQuotationDeleteView.as_view(), name='sales_quotation_delete'),
  path('sales-quotation/<int:pk>/', SalesQuotationDetailView.as_view(), name='sales_quotation_detail'),
  path('sales-quotation/<int:pk>/print/', SalesQuotationPrintView.as_view(), name='sales_quotation_print'),
  path('sales-quotation/export/', SalesQuotationExportView.as_view(), name='sales_quotation_export'),
  path('sales-quotation/bulk-delete/', SalesQuotationBulkDeleteView.as_view(), name='sales_quotation_bulk_delete'),
  path('sales-quotation/<int:pk>/convert-to-order/', ConvertQuotationToOrderView.as_view(), name='convert_quotation_to_order'),
  
  # Sales Order URLs
  path('sales-order/', SalesOrderListView.as_view(), name='sales_order_list'),
  path('sales-order/create/', SalesOrderCreateView.as_view(), name='sales_order_create'),
  path('sales-order/<int:pk>/update/', SalesOrderUpdateView.as_view(), name='sales_order_update'),
  path('sales-order/<int:pk>/delete/', SalesOrderDeleteView.as_view(), name='sales_order_delete'),
  path('sales-order/<int:pk>/', SalesOrderDetailView.as_view(), name='sales_order_detail'),
  path('sales-order/<int:pk>/print/', SalesOrderPrintView.as_view(), name='sales_order_print'),
  path('sales-order/export/', SalesOrderExportView.as_view(), name='sales_order_export'),
  path('sales-order/bulk-delete/', SalesOrderBulkDeleteView.as_view(), name='sales_order_bulk_delete'),
  path('sales-order/<int:pk>/convert-to-delivery/', ConvertOrderToDeliveryView.as_view(), name='convert_order_to_delivery'),
  path('sales-order/<int:pk>/convert-to-invoice/', ConvertOrderToInvoiceView.as_view(), name='convert_order_to_invoice'),
  
  # Delivery URLs
  path('delivery/', DeliveryListView.as_view(), name='delivery_list'),
  path('delivery/create/', DeliveryCreateView.as_view(), name='delivery_create'),
  path('delivery/<int:pk>/update/', DeliveryUpdateView.as_view(), name='delivery_update'),
  path('delivery/<int:pk>/delete/', DeliveryDeleteView.as_view(), name='delivery_delete'),
  path('delivery/<int:pk>/', DeliveryDetailView.as_view(), name='delivery_detail'),
  path('delivery/export/', DeliveryExportView.as_view(), name='delivery_export'),
  path('delivery/bulk-delete/', DeliveryBulkDeleteView.as_view(), name='delivery_bulk_delete'),
  path('delivery/<int:pk>/convert-to-return/', ConvertDeliveryToReturnView.as_view(), name='convert_delivery_to_return'),
  path('delivery/<int:pk>/convert-to-invoice/', ConvertDeliveryToInvoiceView.as_view(), name='convert_delivery_to_invoice'),
  path('delivery/<int:pk>/print/', DeliveryPrintView.as_view(), name='delivery_print'),

  # Return URLs
  path('return/', ReturnListView.as_view(), name='return_list'),
  path('return/create/', ReturnCreateView.as_view(), name='return_create'),
  path('return/<int:pk>/update/', ReturnUpdateView.as_view(), name='return_update'),
  path('return/<int:pk>/delete/', ReturnDeleteView.as_view(), name='return_delete'),
  path('return/<int:pk>/', ReturnDetailView.as_view(), name='return_detail'),
  path('return/export/', ReturnExportView.as_view(), name='return_export'),
  path('return/bulk-delete/', ReturnBulkDeleteView.as_view(), name='return_bulk_delete'),
  
  # AR Invoice URLs
  path('arinvoice/', ARInvoiceListView.as_view(), name='arinvoice_list'),
  path('arinvoice/create/', ARInvoiceCreateView.as_view(), name='arinvoice_create'),
  path('arinvoice/<int:pk>/update/', ARInvoiceUpdateView.as_view(), name='arinvoice_update'),
  path('arinvoice/<int:pk>/delete/', ARInvoiceDeleteView.as_view(), name='arinvoice_delete'),
  path('arinvoice/<int:pk>/', ARInvoiceDetailView.as_view(), name='arinvoice_detail'),
  path('arinvoice/<int:pk>/print/', ARInvoicePrintView.as_view(), name='arinvoice_print'),
  path('arinvoice/export/', ARInvoiceExportView.as_view(), name='arinvoice_export'),
  path('arinvoice/bulk-delete/', ARInvoiceBulkDeleteView.as_view(), name='arinvoice_bulk_delete'),
  path('demo/config/', demo_views.SalesDemoConfigView.as_view(), name='demo_config'),


  path('api/sales/', include('Sales.api.urls', namespace='sales_api')),

  
  path('reports/', SalesReportListView.as_view(), name='sales_report_list'),

    # Sales Quotation Report URLs
  path('reports/sales-quotation/', SalesQuotationReportView.as_view(), name='sales_quotation_report'),
  path('reports/sales-quotation/details/', SalesQuotationReportDetailsView.as_view(), name='sales_quotation_report_details'),
  path('reports/sales/', SalesReportView.as_view(), name='sales_report'),
  path('reports/sales/details/', SalesReportDetailsView.as_view(), name='sales_report_details'),

    # Delivery Report URLs
  path('reports/delivery/', DeliveryReportView.as_view(), name='delivery_report'),
  path('reports/delivery/details/', DeliveryReportDetailsView.as_view(), name='delivery_report_details'),

  # Return Report URLs
  path('reports/return/', ReturnReportView.as_view(), name='return_report'),
  path('reports/return/details/', ReturnReportDetailsView.as_view(), name='return_report_details'),

  # AR Invoice Report URLs
  path('reports/ar-invoice/', ARInvoiceReportView.as_view(), name='ar_invoice_report'),
  path('reports/ar-invoice/details/', ARInvoiceReportDetailsView.as_view(), name='ar_invoice_report_details'),

  path('reports/sales-employee-summary/', SalesEmployeeSalesReportView.as_view(), name='sales_employee_sales_summary'),
  path('menu/', MenuPageView.as_view(), name='menu_page'),
  # Chart Dashboard URLs
  path('dashboard/chart/daily/', SalesDashboardChartView.as_view(), {'period': 'daily'}, name='dashboard_chart_daily'),
  path('dashboard/chart/monthly/', SalesDashboardChartView.as_view(), {'period': 'monthly'}, name='dashboard_chart_monthly'),
  path('dashboard/chart/', SalesDashboardChartView.as_view(), name='dashboard_chart'),
  
    # Dashboard URLs
  path('dashboard/daily/', SalesDashboardView.as_view(), {'period': 'daily'}, name='dashboard_daily'),
  path('dashboard/monthly/', SalesDashboardView.as_view(), {'period': 'monthly'}, name='dashboard_monthly'),
  path('dashboard/', SalesDashboardView.as_view(), name='dashboard'),

  
  path('free-item-discount/', FreeItemDiscountListView.as_view(), name='freeitemdiscount_list'),
  path('free-item-discount/create/', FreeItemDiscountCreateView.as_view(), name='freeitemdiscount_create'),
  path('free-item-discount/<int:pk>/update/', FreeItemDiscountUpdateView.as_view(), name='freeitemdiscount_update'),
  path('free-item-discount/<int:pk>/', FreeItemDiscountDetailView.as_view(), name='freeitemdiscount_detail'),
  path('free-item-discount/<int:pk>/delete/', FreeItemDiscountDeleteView.as_view(), name='freeitemdiscount_delete'),
  path('free-item-discount/export/', FreeItemDiscountExportView.as_view(), name='freeitemdiscount_export'),
  path('free-item-discount/bulk-delete/', FreeItemDiscountBulkDeleteView.as_view(), name='freeitemdiscount_bulk_delete'),
  
]

