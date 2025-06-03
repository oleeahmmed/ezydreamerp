from django.urls import path
from .views import (
    # Purchase Quotation views
    PurchaseQuotationListView, PurchaseQuotationCreateView, PurchaseQuotationUpdateView,
    PurchaseQuotationDetailView, PurchaseQuotationDeleteView, PurchaseQuotationExportView,
    PurchaseQuotationPrintView, PurchaseQuotationBulkDeleteView, ConvertQuotationToOrderView,
    
    # Purchase Order views
    PurchaseOrderListView, PurchaseOrderCreateView, PurchaseOrderUpdateView,
    PurchaseOrderDetailView, PurchaseOrderDeleteView, PurchaseOrderExportView,
    PurchaseOrderPrintView, PurchaseOrderBulkDeleteView,
    
    # Goods Receipt PO views
    GoodsReceiptPoListView, GoodsReceiptPoCreateView, GoodsReceiptPoUpdateView,
    GoodsReceiptPoDetailView, GoodsReceiptPoDeleteView, GoodsReceiptPoExportView,
    GoodsReceiptPoBulkDeleteView,
    
    # Goods Return views
    GoodsReturnListView, GoodsReturnCreateView, GoodsReturnUpdateView,
    GoodsReturnDetailView, GoodsReturnDeleteView, GoodsReturnExportView,
    GoodsReturnBulkDeleteView,
    
    # AP Invoice views
    APInvoiceListView, APInvoiceCreateView, APInvoiceUpdateView,
    APInvoiceDetailView, APInvoiceDeleteView, APInvoiceExportView,
    APInvoiceBulkDeleteView, APInvoicePrintView,
    
    # Conversion views
    ConvertQuotationToOrderView, ConvertOrderToGoodsReceiptView, 
    ConvertOrderToReturnView, ConvertOrderToInvoiceView
)

app_name = 'Purchase'

urlpatterns = [
    # Purchase Quotation URLs
    path('purchase-quotation/', PurchaseQuotationListView.as_view(), name='purchase_quotation_list'),
    path('purchase-quotation/create/', PurchaseQuotationCreateView.as_view(), name='purchase_quotation_create'),
    path('purchase-quotation/<int:pk>/update/', PurchaseQuotationUpdateView.as_view(), name='purchase_quotation_update'),
    path('purchase-quotation/<int:pk>/delete/', PurchaseQuotationDeleteView.as_view(), name='purchase_quotation_delete'),
    path('purchase-quotation/<int:pk>/', PurchaseQuotationDetailView.as_view(), name='purchase_quotation_detail'),
    path('purchase-quotation/<int:pk>/print/', PurchaseQuotationPrintView.as_view(), name='purchase_quotation_print'),
    path('purchase-quotation/export/', PurchaseQuotationExportView.as_view(), name='purchase_quotation_export'),
    path('purchase-quotation/bulk-delete/', PurchaseQuotationBulkDeleteView.as_view(), name='purchase_quotation_bulk_delete'),
    path('purchase-quotation/<int:pk>/convert-to-order/', ConvertQuotationToOrderView.as_view(), name='convert_quotation_to_order'),
    
    # Purchase Order URLs
    path('purchase-order/', PurchaseOrderListView.as_view(), name='purchase_order_list'),
    path('purchase-order/create/', PurchaseOrderCreateView.as_view(), name='purchase_order_create'),
    path('purchase-order/<int:pk>/update/', PurchaseOrderUpdateView.as_view(), name='purchase_order_update'),
    path('purchase-order/<int:pk>/delete/', PurchaseOrderDeleteView.as_view(), name='purchase_order_delete'),
    path('purchase-order/<int:pk>/', PurchaseOrderDetailView.as_view(), name='purchase_order_detail'),
    path('purchase-order/<int:pk>/print/', PurchaseOrderPrintView.as_view(), name='purchase_order_print'),
    path('purchase-order/export/', PurchaseOrderExportView.as_view(), name='purchase_order_export'),
    path('purchase-order/bulk-delete/', PurchaseOrderBulkDeleteView.as_view(), name='purchase_order_bulk_delete'),
    path('purchase-order/<int:pk>/convert-to-goods-receipt/', ConvertOrderToGoodsReceiptView.as_view(), name='convert_order_to_goods_receipt'),
    path('purchase-order/<int:pk>/convert-to-invoice/', ConvertOrderToInvoiceView.as_view(), name='convert_order_to_invoice'),
    path('purchase-order/<int:pk>/convert-to-return/', ConvertOrderToReturnView.as_view(), name='convert_order_to_return'),
    
    # Goods Receipt PO URLs
    path('goods-receipt/', GoodsReceiptPoListView.as_view(), name='goods_receipt_list'),
    path('goods-receipt/create/', GoodsReceiptPoCreateView.as_view(), name='goods_receipt_create'),
    path('goods-receipt/<int:pk>/update/', GoodsReceiptPoUpdateView.as_view(), name='goods_receipt_update'),
    path('goods-receipt/<int:pk>/delete/', GoodsReceiptPoDeleteView.as_view(), name='goods_receipt_delete'),
    path('goods-receipt/<int:pk>/', GoodsReceiptPoDetailView.as_view(), name='goods_receipt_detail'),
    path('goods-receipt/export/', GoodsReceiptPoExportView.as_view(), name='goods_receipt_export'),
    path('goods-receipt/bulk-delete/', GoodsReceiptPoBulkDeleteView.as_view(), name='goods_receipt_bulk_delete'),
    
    # Goods Return URLs
    path('goods-return/', GoodsReturnListView.as_view(), name='goods_return_list'),
    path('goods-return/create/', GoodsReturnCreateView.as_view(), name='goods_return_create'),
    path('goods-return/<int:pk>/update/', GoodsReturnUpdateView.as_view(), name='goods_return_update'),
    path('goods-return/<int:pk>/delete/', GoodsReturnDeleteView.as_view(), name='goods_return_delete'),
    path('goods-return/<int:pk>/', GoodsReturnDetailView.as_view(), name='goods_return_detail'),
    path('goods-return/export/', GoodsReturnExportView.as_view(), name='goods_return_export'),
    path('goods-return/bulk-delete/', GoodsReturnBulkDeleteView.as_view(), name='goods_return_bulk_delete'),
    
    # AP Invoice URLs
    path('apinvoice/', APInvoiceListView.as_view(), name='apinvoice_list'),
    path('apinvoice/create/', APInvoiceCreateView.as_view(), name='apinvoice_create'),
    path('apinvoice/<int:pk>/update/', APInvoiceUpdateView.as_view(), name='apinvoice_update'),
    path('apinvoice/<int:pk>/delete/', APInvoiceDeleteView.as_view(), name='apinvoice_delete'),
    path('apinvoice/<int:pk>/', APInvoiceDetailView.as_view(), name='apinvoice_detail'),
    path('apinvoice/<int:pk>/print/', APInvoicePrintView.as_view(), name='apinvoice_print'),
    path('apinvoice/export/', APInvoiceExportView.as_view(), name='apinvoice_export'),
    path('apinvoice/bulk-delete/', APInvoiceBulkDeleteView.as_view(), name='apinvoice_bulk_delete'),
]