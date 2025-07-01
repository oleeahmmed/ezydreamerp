from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _

from Inventory.models import BaseModel, Item, Warehouse, InventoryTransaction
from BusinessPartnerMasterData.models import BusinessPartner, Address, ContactPerson
from global_settings.models import Currency, PaymentTerms

class PurchaseQuotation(BaseModel):
    """Purchase quotation document for potential vendors"""
    
    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Open', _('Open')),
        ('Sent', _('Sent')),
        ('Expired', _('Expired')),
        ('Converted', _('Converted to Order')),
        ('Closed', _('Closed')),
        ('Cancelled', _('Cancelled')),
    ]
    
    document_date = models.DateField(_("Document Date"), default=timezone.now)
    valid_until = models.DateField(_("Valid Until"), null=True, blank=True)
    vendor = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT, limit_choices_to={'bp_type': 'S'}, verbose_name=_("Vendor"))
    contact_person = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Contact Person"))
    billing_address = models.ForeignKey(
        Address, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='purchase',
        verbose_name=_("Billing Address")
    )
    shipping_address = models.ForeignKey(
        Address, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='purchase_quotation_shipping_address',
        verbose_name=_("Shipping Address")
    )
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Currency"))
    payment_terms = models.ForeignKey(PaymentTerms, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Payment Terms"))
    
    # Financial information
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=18, decimal_places=2,blank=True, null=True,default=0)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=2, default=0)
    
    # Payment information
    payable_amount = models.DecimalField(_("Payable Amount"), max_digits=18, decimal_places=2, default=0)
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=18, decimal_places=2, default=0)
    due_amount = models.DecimalField(_("Due Amount"), max_digits=18, decimal_places=2, default=0)
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True, null=True)
    payment_reference = models.CharField(_("Payment Reference"), max_length=100, blank=True, null=True)
    payment_date = models.DateField(_("Payment Date"), blank=True, null=True)

    # Additional information
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')
    purchasing_employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='purchase_quotations',
        verbose_name=_("Purchasing Employee")
    )
    
    class Meta:
        verbose_name = _("Purchase Quotation")
        verbose_name_plural = _("Purchase Quotations")
    
    def __str__(self):
        return f"PQ {self.id}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class PurchaseQuotationLine(BaseModel):
    """Line items for purchase quotation"""
    
    quotation = models.ForeignKey(PurchaseQuotation, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Quotation"))
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Purchase Quotation Line")
        verbose_name_plural = _("Purchase Quotation Lines")
    
    def __str__(self):
        return f"{self.quotation.id} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity * self.unit_price).quantize(Decimal('0.000001'))
        super().save(*args, **kwargs)

class PurchaseOrder(BaseModel):
    """Represents a confirmed purchase order for a vendor"""

    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Open', _('Open')),
        ('Partially Received', _('Partially Received')),
        ('Received', _('Received')),
        ('Partially Invoiced', _('Partially Invoiced')),
        ('Invoiced', _('Invoiced')),
        ('Closed', _('Closed')),
        ('Cancelled', _('Cancelled')),
    ]

    document_date = models.DateField(_("Document Date"), default=timezone.now)
    delivery_date = models.DateField(_("Delivery Date"), null=True, blank=True)
    vendor = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT, limit_choices_to={'bp_type': 'S'}, verbose_name=_("Vendor"))
    contact_person = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Contact Person"))
    billing_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_order_billing', verbose_name=_("Billing Address"))
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_order_shipping', verbose_name=_("Shipping Address"))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Currency"))
    payment_terms = models.ForeignKey(PaymentTerms, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Payment Terms"))
    
    # Financial information
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=18, decimal_places=2,blank=True, null=True,default=0)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=2, default=0)
    
    # Payment information
    payable_amount = models.DecimalField(_("Payable Amount"), max_digits=18, decimal_places=2, default=0)
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=18, decimal_places=2, default=0)
    due_amount = models.DecimalField(_("Due Amount"), max_digits=18, decimal_places=2, default=0)
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True, null=True)
    payment_reference = models.CharField(_("Payment Reference"), max_length=100, blank=True, null=True)
    payment_date = models.DateField(_("Payment Date"), blank=True, null=True)

    # Additional Info
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    purchasing_employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_orders', verbose_name=_("Purchasing Employee"))

    class Meta:
        verbose_name = _("Purchase Order")
        verbose_name_plural = _("Purchase Orders")

    def __str__(self):
        return f"Purchase Order #{self.id} - {self.vendor.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class PurchaseOrderLine(BaseModel):
    """Line items for Purchase Order"""

    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Order"))
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Purchase Order Line")
        verbose_name_plural = _("Purchase Order Lines")

    def __str__(self):
        return f"{self.item_name} - {self.quantity} units"

    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity * self.unit_price).quantize(Decimal('0.000001'))
        super().save(*args, **kwargs)

class GoodsReceiptPo(BaseModel):
    """Goods Receipt PO document for receiving items from vendors"""
    
    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Open', _('Open')),
        ('Partially Received', _('Partially Received')),
        ('Received', _('Received')),
        ('Closed', _('Closed')),
        ('Cancelled', _('Cancelled')),
    ]
    
    document_date = models.DateField(_("Document Date"), default=timezone.now)
    posting_date = models.DateField(_("Posting Date"), default=timezone.now)
    vendor = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT, limit_choices_to={'bp_type': 'S'}, verbose_name=_("Vendor"))
    contact_person = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Contact Person"))
    shipping_address = models.ForeignKey(
        Address, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='goods_receipt_shipping_address',
        verbose_name=_("Shipping Address")
    )
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='goods_receipts', verbose_name=_("Purchase Order"))
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Warehouse"))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Currency"))
    payment_terms = models.ForeignKey(PaymentTerms, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Payment Terms"))
    
    # Financial information
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=18, decimal_places=2,blank=True, null=True,default=0)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=2, default=0)
    
    # Payment information
    payable_amount = models.DecimalField(_("Payable Amount"), max_digits=18, decimal_places=2, default=0)
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=18, decimal_places=2, default=0)
    due_amount = models.DecimalField(_("Due Amount"), max_digits=18, decimal_places=2, default=0)
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True, null=True)
    payment_reference = models.CharField(_("Payment Reference"), max_length=100, blank=True, null=True)
    payment_date = models.DateField(_("Payment Date"), blank=True, null=True)
    
    # Additional information
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')
    purchasing_employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='goods_receipts',
        verbose_name=_("Purchasing Employee")
    )
    
    class Meta:
        verbose_name = _("Goods Receipt PO")
        verbose_name_plural = _("Goods Receipt POs")
    
    def __str__(self):
        return f"Goods Receipt #{self.id} - {self.vendor.name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class GoodsReceiptPoLine(BaseModel):
    """Line items for goods receipt document"""
    
    goods_receipt = models.ForeignKey(GoodsReceiptPo, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Goods Receipt"))
    purchase_order_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.SET_NULL, null=True, blank=True, related_name='goods_receipt_lines', verbose_name=_("Purchase Order Line"))
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Goods Receipt PO Line")
        verbose_name_plural = _("Goods Receipt PO Lines")
    
    def __str__(self):
        return f"Goods Receipt #{self.goods_receipt.id} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity * self.unit_price).quantize(Decimal('0.000001'))
        super().save(*args, **kwargs)

class GoodsReturn(BaseModel):
    """Goods Return document for items returned to vendors"""
    
    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Open', _('Open')),
        ('Returned', _('Returned')),
        ('Closed', _('Closed')),
        ('Cancelled', _('Cancelled')),
    ]
    
    document_date = models.DateField(_("Document Date"), default=timezone.now)
    posting_date = models.DateField(_("Posting Date"), default=timezone.now)
    vendor = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT, limit_choices_to={'bp_type': 'S'}, verbose_name=_("Vendor"))
    contact_person = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Contact Person"))
    return_address = models.ForeignKey(
        Address, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='goods_return_address',
        verbose_name=_("Return Address")
    )
    goods_receipt = models.ForeignKey(GoodsReceiptPo, on_delete=models.SET_NULL, null=True, blank=True, related_name='goods_returns', verbose_name=_("Goods Receipt"))
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Warehouse"))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Currency"))
    payment_terms = models.ForeignKey(PaymentTerms, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Payment Terms"))
    
    # Financial information
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=18, decimal_places=2,blank=True, null=True,default=0)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=2, default=0)
    
    # Payment information
    payable_amount = models.DecimalField(_("Payable Amount"), max_digits=18, decimal_places=2, default=0)
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=18, decimal_places=2, default=0)
    due_amount = models.DecimalField(_("Due Amount"), max_digits=18, decimal_places=2, default=0)
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True, null=True)
    payment_reference = models.CharField(_("Payment Reference"), max_length=100, blank=True, null=True)
    payment_date = models.DateField(_("Payment Date"), blank=True, null=True)
    
    # Additional information
    return_reason = models.TextField(_("Return Reason"), blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')
    purchasing_employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='goods_returns',
        verbose_name=_("Purchasing Employee")
    )
    
    class Meta:
        verbose_name = _("Goods Return")
        verbose_name_plural = _("Goods Returns")
    
    def __str__(self):
        return f"Goods Return #{self.id} - {self.vendor.name}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class GoodsReturnLine(BaseModel):
    """Line items for goods return document"""
    
    goods_return = models.ForeignKey(GoodsReturn, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Goods Return"))
    goods_receipt_line = models.ForeignKey(GoodsReceiptPoLine, on_delete=models.SET_NULL, null=True, blank=True, related_name='goods_return_lines', verbose_name=_("Goods Receipt Line"))
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Goods Return Line")
        verbose_name_plural = _("Goods Return Lines")
    
    def __str__(self):
        return f"Goods Return #{self.goods_return.id} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity * self.unit_price).quantize(Decimal('0.000001'))
        super().save(*args, **kwargs)

class APInvoice(BaseModel):
    """Accounts Payable Invoice for vendor billing"""
    
    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Open', _('Open')),
        ('Partially Paid', _('Partially Paid')),
        ('Paid', _('Paid')),
        ('Overdue', _('Overdue')),
        ('Cancelled', _('Cancelled')),
    ]
    
    document_date = models.DateField(_("Document Date"), default=timezone.now)
    posting_date = models.DateField(_("Posting Date"), default=timezone.now)
    due_date = models.DateField(_("Due Date"), null=True, blank=True)
    vendor = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT, limit_choices_to={'bp_type': 'S'}, verbose_name=_("Vendor"))
    contact_person = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Contact Person"))
    billing_address = models.ForeignKey(
        Address, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='ap_invoice_billing_address',
        verbose_name=_("Billing Address")
    )
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name=_("Purchase Order"))
    goods_receipt = models.ForeignKey(GoodsReceiptPo, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name=_("Goods Receipt"))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Currency"))
    payment_terms = models.ForeignKey(PaymentTerms, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Payment Terms"))
    
    # Financial information
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=18, decimal_places=2,blank=True, null=True,default=0)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=2, default=0)
    
    # Payment information
    payable_amount = models.DecimalField(_("Payable Amount"), max_digits=18, decimal_places=2, default=0)
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=18, decimal_places=2, default=0)
    due_amount = models.DecimalField(_("Due Amount"), max_digits=18, decimal_places=2, default=0)
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True, null=True)
    payment_reference = models.CharField(_("Payment Reference"), max_length=100, blank=True, null=True)
    payment_date = models.DateField(_("Payment Date"), blank=True, null=True)
    
    # Additional information
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')
    purchasing_employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='ap_invoices',
        verbose_name=_("Purchasing Employee")
    )
    
    class Meta:
        verbose_name = _("AP Invoice")
        verbose_name_plural = _("AP Invoices")
    
    def __str__(self):
        return f"AP Invoice #{self.id} - {self.vendor.name}"
    
    def save(self, *args, **kwargs):
        # Calculate due date if not provided
        if not self.due_date and self.document_date and self.payment_terms:
            self.due_date = self.document_date + datetime.timedelta(days=self.payment_terms.days)
        
        super().save(*args, **kwargs)

class APInvoiceLine(BaseModel):
    """Line items for AP Invoice"""
    
    invoice = models.ForeignKey(APInvoice, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Invoice"))
    purchase_order_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_lines', verbose_name=_("Purchase Order Line"))
    goods_receipt_line = models.ForeignKey(GoodsReceiptPoLine, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_lines', verbose_name=_("Goods Receipt Line"))
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    
    class Meta:
        verbose_name = _("AP Invoice Line")
        verbose_name_plural = _("AP Invoice Lines")
    
    def __str__(self):
        return f"AP Invoice #{self.invoice.id} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity * self.unit_price).quantize(Decimal('0.000001'))
        super().save(*args, **kwargs)