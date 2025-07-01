from .sales_employee_views import (
  SalesEmployeeListView, SalesEmployeeCreateView, SalesEmployeeUpdateView,
  SalesEmployeeDetailView, SalesEmployeeDeleteView, SalesEmployeeExportView,
  SalesEmployeeBulkDeleteView
)

from .sales_quotation_views import (
  SalesQuotationListView, SalesQuotationCreateView, SalesQuotationUpdateView,
  SalesQuotationDetailView, SalesQuotationDeleteView, SalesQuotationExportView,
  SalesQuotationPrintView, SalesQuotationBulkDeleteView
)

from .sales_order_views import (
  SalesOrderListView, SalesOrderCreateView, SalesOrderUpdateView,
  SalesOrderDetailView, SalesOrderDeleteView, SalesOrderExportView,
  SalesOrderPrintView, SalesOrderBulkDeleteView
)

from .delivery_views import (
  DeliveryListView, DeliveryCreateView, DeliveryUpdateView,
  DeliveryDetailView, DeliveryDeleteView, DeliveryExportView,
  DeliveryBulkDeleteView,DeliveryPrintView
)

from .return_views import (
  ReturnListView, ReturnCreateView, ReturnUpdateView,
  ReturnDetailView, ReturnDeleteView, ReturnExportView,
  ReturnBulkDeleteView
)

from .arinvoice_views import (
  ARInvoiceListView, ARInvoiceCreateView, ARInvoiceUpdateView,
  ARInvoiceDetailView, ARInvoiceDeleteView, ARInvoiceExportView,
  ARInvoiceBulkDeleteView, ARInvoicePrintView
)

from .conversion_views import (
  ConvertQuotationToOrderView, ConvertOrderToDeliveryView,
  ConvertDeliveryToReturnView, ConvertOrderToInvoiceView,
  ConvertDeliveryToInvoiceView
)

# Import the dashboard view
from .dashboard_views import SalesDashboardView
from .dashboard_chart_views import SalesDashboardChartView
from .freeitem_views import (
    FreeItemDiscountListView, FreeItemDiscountCreateView, FreeItemDiscountUpdateView,
    FreeItemDiscountDetailView, FreeItemDiscountDeleteView,
    FreeItemDiscountExportView, FreeItemDiscountBulkDeleteView,
)