from .bom_views import (
    BillOfMaterialsListView, BillOfMaterialsCreateView, BillOfMaterialsUpdateView,
    BillOfMaterialsDetailView, BillOfMaterialsDeleteView, BillOfMaterialsExportView,
    BillOfMaterialsBulkDeleteView
)

from .production_order_views import (
    ProductionOrderListView, ProductionOrderCreateView, ProductionOrderUpdateView,
    ProductionOrderDetailView, ProductionOrderDeleteView, ProductionOrderExportView,
    ProductionOrderBulkDeleteView,ProductBOMsAPIView, ProductInfoAPIView,BOMComponentsAPIView
)

from .production_receipt_views import (
    ProductionReceiptListView, ProductionReceiptCreateView, ProductionReceiptUpdateView,
    ProductionReceiptDetailView, ProductionReceiptDeleteView, ProductionReceiptExportView,
    ProductionReceiptBulkDeleteView, ProductionReceiptPrintView
)

from .production_issue_views import (
    ProductionIssueListView, ProductionIssueCreateView, ProductionIssueUpdateView,
    ProductionIssueDetailView, ProductionIssueDeleteView, ProductionIssueExportView,
    ProductionIssueBulkDeleteView, ProductionIssuePrintView
)

from .dashboard_views import ProductionDashboardView

