from django.urls import path,include
from .views import  unit_of_measure_views, warehouse_views, item_group_views,item_views,item_warehouse_info_views,inventory_transaction_views,goods_receipt_views,goods_issue_views,inventory_transfer_views,inventory_report_views,demo_views

app_name = 'Inventory'

urlpatterns = [
    # Inventory Settings URLs
    # API URLs
    path('api/', include('Inventory.api.urls', namespace='inventory_api')),

    # Unit of Measure URLs
    path('uom/', unit_of_measure_views.UnitOfMeasureListView.as_view(), name='uom_list'),
    path('uom/create/', unit_of_measure_views.UnitOfMeasureCreateView.as_view(), name='uom_create'),
    path('uom/<int:pk>/update/', unit_of_measure_views.UnitOfMeasureUpdateView.as_view(), name='uom_update'),
    path('uom/<int:pk>/delete/', unit_of_measure_views.UnitOfMeasureDeleteView.as_view(), name='uom_delete'),
    path('uom/<int:pk>/', unit_of_measure_views.UnitOfMeasureDetailView.as_view(), name='uom_detail'),
    path('uom/<int:pk>/print/', unit_of_measure_views.UnitOfMeasurePrintView.as_view(), name='uom_print'),

    # Warehouse URLs
    path('warehouse/', warehouse_views.WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouse/create/', warehouse_views.WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouse/<int:pk>/update/', warehouse_views.WarehouseUpdateView.as_view(), name='warehouse_update'),
    path('warehouse/<int:pk>/delete/', warehouse_views.WarehouseDeleteView.as_view(), name='warehouse_delete'),
    path('warehouse/<int:pk>/', warehouse_views.WarehouseDetailView.as_view(), name='warehouse_detail'),
    path('warehouse/<int:pk>/print/', warehouse_views.WarehousePrintDetailView.as_view(), name='warehouse_print_detail'),
    path('warehouse/print/', warehouse_views.WarehousePrintView.as_view(), name='warehouse_print_list'),
    path('warehouse/export/', warehouse_views.WarehouseExportView.as_view(), name='warehouse_export'),
    path('warehouse/bulk-delete/', warehouse_views.WarehouseBulkDeleteView.as_view(), name='warehouse_bulk_delete'),

    # Item Group URLs
    path('item-group/', item_group_views.ItemGroupListView.as_view(), name='item_group_list'),
    path('item-group/create/', item_group_views.ItemGroupCreateView.as_view(), name='item_group_create'),
    path('item-group/<int:pk>/update/', item_group_views.ItemGroupUpdateView.as_view(), name='item_group_update'),
    path('item-group/<int:pk>/delete/', item_group_views.ItemGroupDeleteView.as_view(), name='item_group_delete'),
    path('item-group/<int:pk>/', item_group_views.ItemGroupDetailView.as_view(), name='item_group_detail'),
    path('item-group/<int:pk>/print/', item_group_views.ItemGroupPrintView.as_view(), name='item_group_print'),
    
    # Item URLs
    path('item/', item_views.ItemListView.as_view(), name='item_list'),
    path('item/all/', item_views.ItemAllListView.as_view(), name='item_all_list'),    
    path('item/create/', item_views.ItemCreateView.as_view(), name='item_create'),
    path('item/<int:pk>/update/', item_views.ItemUpdateView.as_view(), name='item_update'),
    path('item/<int:pk>/delete/', item_views.ItemDeleteView.as_view(), name='item_delete'),
    path('item/<int:pk>/', item_views.ItemDetailView.as_view(), name='item_detail'),    
    path('item/bulk-delete/', item_views.ItemBulkDeleteView.as_view(), name='item_bulk_delete'),
    path('item/export/', item_views.ItemExportView.as_view(), name='item_export'),
    path('item/<int:pk>/print/', item_views.ItemPrintDetailView.as_view(), name='item_print_detail'),
    path('item/print/', item_views.ItemPrintView.as_view(), name='item_print_list'),
    path('api/items/search/', item_views.ItemSearchAPIView.as_view(), name='item_search_api'),    
    # Item Warehouse Info URLs
    path('item-warehouse/', item_warehouse_info_views.ItemWarehouseInfoListView.as_view(), name='item_warehouse_info_list'),
    path('item-warehouse/create/', item_warehouse_info_views.ItemWarehouseInfoCreateView.as_view(), name='item_warehouse_info_create'),
    path('inveitem-warehousentory/<int:pk>/update/', item_warehouse_info_views.ItemWarehouseInfoUpdateView.as_view(), name='item_warehouse_info_update'),
    path('item-warehouse/<int:pk>/delete/', item_warehouse_info_views.ItemWarehouseInfoDeleteView.as_view(), name='item_warehouse_info_delete'),
    path('item-warehouse/<int:pk>/', item_warehouse_info_views.ItemWarehouseInfoDetailView.as_view(), name='item_warehouse_info_detail'),
    path('item-warehouse/bulk-delete/', item_warehouse_info_views.ItemWarehouseInfoBulkDeleteView.as_view(), name='item_warehouse_info_bulk_delete'),
    path('invenitem-warehousetory/export/', item_warehouse_info_views.ItemWarehouseInfoExportView.as_view(), name='item_warehouse_info_export'),
    path('item-warehouse/<int:pk>/print/', item_warehouse_info_views.ItemWarehouseInfoPrintDetailView.as_view(), name='item_warehouse_info_print_detail'),
    path('item-warehouse/print/', item_warehouse_info_views.ItemWarehouseInfoPrintView.as_view(), name='item_warehouse_info_print_list'),   
   
    # Inventory Transection URLs

    path('transaction/', inventory_transaction_views.InventoryTransactionListView.as_view(), name='inventory_transaction_list'),
    path('transaction/create/', inventory_transaction_views.InventoryTransactionCreateView.as_view(), name='inventory_transaction_create'),
    path('transaction/<int:pk>/update/', inventory_transaction_views.InventoryTransactionUpdateView.as_view(), name='inventory_transaction_update'),
    path('transaction/<int:pk>/delete/', inventory_transaction_views.InventoryTransactionDeleteView.as_view(), name='inventory_transaction_delete'),
    path('transaction/<int:pk>/', inventory_transaction_views.InventoryTransactionDetailView.as_view(), name='inventory_transaction_detail'),
    path('transaction/<int:pk>/print/', inventory_transaction_views.InventoryTransactionPrintDetailView.as_view(), name='inventory_transaction_print_detail'),
    path('transaction/print/', inventory_transaction_views.InventoryTransactionPrintView.as_view(), name='inventory_transaction_print_list'),
    path('transaction/export/', inventory_transaction_views.InventoryTransactionExportView.as_view(), name='inventory_transaction_export'),
    path('transaction/bulk-delete/', inventory_transaction_views.InventoryTransactionBulkDeleteView.as_view(), name='inventory_transaction_bulk_delete'),   

    # Goods Receipt URLs
    path('goods-receipt/', goods_receipt_views.GoodsReceiptListView.as_view(), name='goods_receipt_list'),
    path('goods-receipt/create/', goods_receipt_views.GoodsReceiptCreateView.as_view(), name='goods_receipt_create'),
    path('goods-receipt/<int:pk>/update/', goods_receipt_views.GoodsReceiptUpdateView.as_view(), name='goods_receipt_update'),
    path('goods-receipt/<int:pk>/delete/', goods_receipt_views.GoodsReceiptDeleteView.as_view(), name='goods_receipt_delete'),
    path('goods-receipt/<int:pk>/', goods_receipt_views.GoodsReceiptDetailView.as_view(), name='goods_receipt_detail'),
    path('goods-receipt/<int:pk>/print/', goods_receipt_views.GoodsReceiptPrintView.as_view(), name='goods_receipt_print'), 
    path('goods-receipt/export/', goods_receipt_views.GoodsReceiptExportView.as_view(), name='export_goods_receipt_csv'),
    path('goods-receipt/bulk-delete/', goods_receipt_views.GoodsReceiptBulkDeleteView.as_view(), name='bulk_delete_goods_receipts'),
    # Goods Issue URLs
    path('goods-issue/', goods_issue_views.GoodsIssueListView.as_view(), name='goods_issue_list'),
    path('goods-issue/create/', goods_issue_views.GoodsIssueCreateView.as_view(), name='goods_issue_create'),
    path('goods-issue/<int:pk>/update/', goods_issue_views.GoodsIssueUpdateView.as_view(), name='goods_issue_update'),
    path('goods-issue/<int:pk>/delete/', goods_issue_views.GoodsIssueDeleteView.as_view(), name='goods_issue_delete'),
    path('goods-issue/<int:pk>/', goods_issue_views.GoodsIssueDetailView.as_view(), name='goods_issue_detail'),
    path('goods-issue/<int:pk>/print/', goods_issue_views.GoodsIssuePrintView.as_view(), name='goods_issue_print'), 
    path('goods-issue/export/', goods_issue_views.GoodsIssueExportView.as_view(), name='export_goods_issue_csv'),
    path('goods-issue/bulk-delete/', goods_issue_views.GoodsIssueBulkDeleteView.as_view(), name='bulk_delete_goods_issues'),

    
    # Inventory Transfer URLs
    path('inventory-transfer/', inventory_transfer_views.InventoryTransferListView.as_view(), name='inventory_transfer_list'),
    path('inventory-transfer/create/', inventory_transfer_views.InventoryTransferCreateView.as_view(), name='inventory_transfer_create'),
    path('inventory-transfer/<int:pk>/update/', inventory_transfer_views.InventoryTransferUpdateView.as_view(), name='inventory_transfer_update'),
    path('inventory-transfer/<int:pk>/delete/', inventory_transfer_views.InventoryTransferDeleteView.as_view(), name='inventory_transfer_delete'),
    path('inventory-transfer/<int:pk>/', inventory_transfer_views.InventoryTransferDetailView.as_view(), name='inventory_transfer_detail'),
    path('inventory-transfer/<int:pk>/print/', inventory_transfer_views.InventoryTransferPrintView.as_view(), name='inventory_transfer_print'), 
    path('inventory-transfer/export/', inventory_transfer_views.InventoryTransferExportView.as_view(), name='export_inventory_transfer_csv'),
    path('inventory-transfer/bulk-delete/', inventory_transfer_views.InventoryTransferBulkDeleteView.as_view(), name='bulk_delete_inventory_transfers'),


    path('demo/config/', demo_views.DemoConfigView.as_view(), name='demo_config'),
    path('menu/', inventory_report_views.MenuPageView.as_view(), name='menu_page'),

    # Inventory Reports URLs
    path('reports/', inventory_report_views.InventoryReportListView.as_view(), name='inventory_report_list'),
    path('reports/current-stock/', inventory_report_views.CurrentStockReportView.as_view(), name='current_stock_report'),
    path('reports/stock-by-warehouse/', inventory_report_views.StockByWarehouseReportView.as_view(), name='stock_by_warehouse_report'),
    path('reports/reorder/', inventory_report_views.ReorderReportView.as_view(), name='reorder_report'),
    path('reports/overstock/', inventory_report_views.OverstockReportView.as_view(), name='overstock_report'),
    path('reports/goods-receipt-summary/', inventory_report_views.GoodsReceiptSummaryView.as_view(), name='goods_receipt_summary'),
    path('reports/pending-goods-receipt/', inventory_report_views.PendingGoodsReceiptView.as_view(), name='pending_goods_receipt'),
    path('reports/goods-issue-summary/', inventory_report_views.GoodsIssueSummaryView.as_view(), name='goods_issue_summary'),
    path('reports/inventory-consumption/', inventory_report_views.InventoryConsumptionReportView.as_view(), name='inventory_consumption_report'),
    path('reports/inventory-transactions-ledger/', inventory_report_views.InventoryTransactionsLedgerView.as_view(), name='inventory_transactions_ledger'),
    path('reports/inventory-valuation/', inventory_report_views.InventoryValuationReportView.as_view(), name='inventory_valuation_report'),
    path('reports/item-movement/', inventory_report_views.ItemMovementReportView.as_view(), name='item_movement_report'),
    path('reports/transfer-summary/', inventory_report_views.TransferSummaryView.as_view(), name='transfer_summary'),
    path('reports/pending-transfers/', inventory_report_views.PendingTransfersView.as_view(), name='pending_transfers'),
    path('reports/stock-adjustment-history/', inventory_report_views.StockAdjustmentHistoryView.as_view(), name='stock_adjustment_history'),
    path('reports/stock-below-minimum/', inventory_report_views.StockBelowMinimumView.as_view(), name='stock_below_minimum'),
    path('reports/negative-stock/', inventory_report_views.NegativeStockReportView.as_view(), name='negative_stock_report'),
    path('reports/zero-movement/', inventory_report_views.ZeroMovementReportView.as_view(), name='zero_movement_report'),
]

