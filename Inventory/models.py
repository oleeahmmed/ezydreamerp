from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from PIL import Image
import os
class BaseModel(models.Model):
    """Base model with common fields for all models."""
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True
        verbose_name = _("Base Model")
        verbose_name_plural = _("Base Models")

    def save(self, *args, **kwargs):
        if not self.pk: self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

class UnitOfMeasure(BaseModel):
    """Unit of measure for items"""
    code = models.CharField(_("Code"), max_length=20, unique=True)
    name = models.CharField(_("Name"), max_length=100)

    class Meta:
        verbose_name = _("Unit of Measure")
        verbose_name_plural = _("Units of Measure")

    def __str__(self): return f"{self.name}"

class Warehouse(BaseModel):
    """Warehouse for storing inventory"""
    code = models.CharField(_("Code"), max_length=8, unique=True)
    name = models.CharField(_("Name"), max_length=100)
    is_default = models.BooleanField(_("Is Default"), default=False)
    address = models.TextField(_("Address"), blank=True, null=True)
    contact_person = models.CharField(_("Contact Person"), max_length=100, blank=True, null=True)
    contact_phone = models.CharField(_("Contact Phone"), max_length=20, blank=True, null=True)
    notes = models.TextField(_("Notes"), blank=True, null=True)

    class Meta:
        verbose_name = _("Warehouse")
        verbose_name_plural = _("Warehouses")

    def __str__(self): return f"{self.name}"

    def save(self, *args, **kwargs):
        if self.is_default: Warehouse.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
        if Warehouse.objects.count() == 1:
            self.is_default = True
            super().save(update_fields=['is_default'])

class ItemGroup(BaseModel):
    """Hierarchical grouping of items"""
    code = models.CharField(_("Code"), max_length=20, unique=True)
    name = models.CharField(_("Name"), max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name=_("Parent Group"))
    description = models.TextField(_("Description"), blank=True, null=True)

    class Meta:
        verbose_name = _("Item Group")
        verbose_name_plural = _("Item Groups")

    def __str__(self): return f"{self.name}"
    
    def get_full_path(self):
        if self.parent: return f"{self.parent.get_full_path()} > {self.name}"
        return self.name

class Item(BaseModel):
    """Item master data"""

    # Basic Information
    code = models.CharField(_("Code"), max_length=50, unique=True)
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True, null=True)
    item_group = models.ForeignKey('ItemGroup', on_delete=models.PROTECT, related_name='items', verbose_name=_("Item Group"))
    image = models.ImageField(upload_to="items/",null=True, blank=True,default="")

    # Unit of Measure fields
    inventory_uom = models.ForeignKey('UnitOfMeasure', on_delete=models.PROTECT, related_name='inventory_items', verbose_name=_("Inventory UOM"))
    purchase_uom = models.ForeignKey('UnitOfMeasure', on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_items', verbose_name=_("Purchase UOM"))
    sales_uom = models.ForeignKey('UnitOfMeasure', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_items', verbose_name=_("Sales UOM"))

    # Item Type Flags
    is_inventory_item = models.BooleanField(_("Is Inventory Item"), default=True)
    is_sales_item = models.BooleanField(_("Is Sales Item"), default=True)
    is_purchase_item = models.BooleanField(_("Is Purchase Item"), default=True)
    is_service = models.BooleanField(_("Is Service"), default=False)

    # Warehouse Information
    default_warehouse = models.ForeignKey('Warehouse', on_delete=models.SET_NULL, null=True, blank=True, related_name='default_items', verbose_name=_("Default Warehouse"))
    minimum_stock = models.DecimalField(_("Minimum Stock"), max_digits=18, decimal_places=6, default=0, blank=True, null=True)
    maximum_stock = models.DecimalField(_("Maximum Stock"), max_digits=18, decimal_places=6, default=0, blank=True, null=True)
    reorder_point = models.DecimalField(_("Reorder Point"), max_digits=18, decimal_places=6, default=0, blank=True, null=True)

    # Physical Attributes
    barcode = models.CharField(_("Barcode"), max_length=50, blank=True, null=True)
    weight = models.DecimalField(_("Weight"), max_digits=10, decimal_places=3, null=True, blank=True)
    volume = models.DecimalField(_("Volume"), max_digits=10, decimal_places=3, null=True, blank=True)
    image_url = models.URLField(_("Image URL"), blank=True, null=True)

    # Price and Cost fields
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6, default=0, blank=True, null=True)
    item_cost = models.DecimalField(_("Item Cost"), max_digits=18, decimal_places=6, default=0, blank=True, null=True)
    purchase_price = models.DecimalField(_("Purchase Price"), max_digits=18, decimal_places=6, default=0, blank=True, null=True)
    selling_price = models.DecimalField(_("Selling Price"), max_digits=18, decimal_places=6, default=0, blank=True, null=True)
    markup_percentage = models.DecimalField(_("Markup Percentage"), max_digits=10, decimal_places=2, default=0, blank=True, null=True)
    discount_percentage = models.DecimalField(_("Discount Percentage"), max_digits=10, decimal_places=2, default=0, blank=True, null=True)

    class Meta:
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
        ]
        verbose_name = _("Item")
        verbose_name_plural = _("Items")

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        """Ensure default warehouse and UOM are set properly before saving."""
        if not self.purchase_uom:
            self.purchase_uom = self.inventory_uom
        if not self.sales_uom:
            self.sales_uom = self.inventory_uom

        # Assign first active warehouse as default if not set
        if not self.default_warehouse:
            first_warehouse = Warehouse.objects.filter(is_active=True).order_by('id').first()
            if first_warehouse:
                self.default_warehouse = first_warehouse            
        super().save(*args, **kwargs)  # Save first to get the image path

        # Ensure an image is uploaded
        if self.image:
            img_path = self.image.path
            img = Image.open(img_path)

            # Resize if the image is larger than 800x800
            max_size = (800, 800)
            img.thumbnail(max_size, Image.LANCZOS)

            # Save back to the same path with compression
            img.save(img_path, format=img.format, quality=80, optimize=True)
    @property
    def warehouse_info_data(self):
        """Retrieve warehouse info for the default warehouse if available."""
        return self.warehouse_info.filter(warehouse=self.default_warehouse).first()

    @property
    def in_stock(self):
        return getattr(self.warehouse_info_data, 'in_stock', 0)

    @property
    def committed(self):
        return getattr(self.warehouse_info_data, 'committed', 0)

    @property
    def ordered(self):
        return getattr(self.warehouse_info_data, 'ordered', 0)

    @property
    def available(self):
        return getattr(self.warehouse_info_data, 'available', 0)


class ItemWarehouseInfo(BaseModel):
    """Item quantity information per warehouse"""
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='warehouse_info', verbose_name=_("Item"))
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='item_info', verbose_name=_("Warehouse"))
    in_stock = models.DecimalField(_("In Stock"), max_digits=18, decimal_places=6, default=0)
    committed = models.DecimalField(_("Committed"), max_digits=18, decimal_places=6, default=0)
    ordered = models.DecimalField(_("Ordered"), max_digits=18, decimal_places=6, default=0)
    available = models.DecimalField(_("Available"), max_digits=18, decimal_places=6, default=0)
    min_stock = models.DecimalField(_("Minimum Stock"), max_digits=18, decimal_places=6, null=True, blank=True)
    max_stock = models.DecimalField(_("Maximum Stock"), max_digits=18, decimal_places=6, null=True, blank=True)
    reorder_point = models.DecimalField(_("Reorder Point"), max_digits=18, decimal_places=6, default=0, blank=True, null=True)

    class Meta:
        unique_together = ('item', 'warehouse')
        verbose_name = _("Item Warehouse Info")
        verbose_name_plural = _("Item Warehouse Info")

    def __str__(self): 
        return f"{self.item.code} - {self.warehouse.code}"

    def calculate_available(self):
        """Calculate available stock dynamically"""
        return self.in_stock - self.committed

    def update_available(self):
        """Update the available quantity based on the calculated method"""
        self.available = self.calculate_available()
        self.save(update_fields=['available', 'updated_at'])
        
    def save(self, *args, **kwargs):
        """Override save to ensure available stock is always updated"""
        # Avoid recursive call by checking if 'available' is already being updated
        if 'update_fields' not in kwargs or 'available' not in kwargs['update_fields']:
            self.available = self.calculate_available()
        super().save(*args, **kwargs)

class InventoryTransaction(BaseModel):
    """Records inventory transactions such as purchases, sales, transfers, and adjustments."""
    
    TRANSACTION_TYPES = [
        ('PURCHASE', _('Purchase')),
        ('SALE', _('Sale')),
        ('TRANSFER', _('Transfer')),
        ('ADJUSTMENT', _('Adjustment')),
        ('RETURN', _('Return')),
        ('ISSUE', _('Issue')),
        ('DELIVERY', _('Delivery')),
        ('RECEIPT', _('Receipt')),
    ]
    
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    warehouse = models.ForeignKey('Warehouse', on_delete=models.CASCADE, related_name='transactions', verbose_name=_("Warehouse"))
    transaction_type = models.CharField(_("Transaction Type"), max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6, default=Decimal('0.00'))
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, editable=False)
    reference = models.CharField(_("Reference"), max_length=100, blank=True, null=True, help_text=_("Reference to invoice, PO, or document."))
    transaction_date = models.DateTimeField(_("Transaction Date"), default=timezone.now)
    notes = models.TextField(_("Notes"), blank=True, null=True)



    class Meta:
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_date']),
            models.Index(fields=['item_code']),
            models.Index(fields=['warehouse']),
        ]
        verbose_name = _("Inventory Transaction")
        verbose_name_plural = _("Inventory Transactions")

    def __str__(self):
        return f"{self.transaction_type} - {self.item_code} ({self.quantity}) at {self.warehouse.name}"

    def save(self, *args, **kwargs):
        """Ensure total amount is calculated before saving."""
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

 

class GoodsReceipt(BaseModel):
    """Document for receiving inventory"""
    
    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Posted', _('Posted')),
        ('Cancelled', _('Cancelled')),
    ]

    document_date = models.DateField(_("Document Date"), default=timezone.now)
    posting_date = models.DateField(_("Posting Date"), default=timezone.now)
    supplier = models.CharField(_("Supplier"), max_length=100, blank=True, null=True)
    supplier_document = models.CharField(_("Supplier Document"), max_length=50, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')

    # Financial information 
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=18, decimal_places=2, default=0)
    freight_amount = models.DecimalField(_("Freight Amount"), max_digits=18, decimal_places=2, default=0)
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=18, decimal_places=2, default=0)
    payable_amount = models.DecimalField(_("Payable Amount"), max_digits=18, decimal_places=2, default=0)
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=18, decimal_places=2, default=0)
    due_amount = models.DecimalField(_("Due Amount"), max_digits=18, decimal_places=2, default=0)
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True, null=True)
    payment_reference = models.CharField(_("Payment Reference"), max_length=100, blank=True, null=True)
    payment_date = models.DateField(_("Payment Date"), blank=True, null=True)
    warehouse = models.ForeignKey('Warehouse', on_delete=models.PROTECT,blank=True, null=True, related_name='goods_receipts', verbose_name=_("Warehouse"))
    class Meta:
        verbose_name = _("Goods Receipt")
        verbose_name_plural = _("Goods Receipts")
    def __str__(self):
            return f"GR {self.id}"

    def set_default_warehouse(self):
        """Set warehouse based on the default_warehouse of the first item in GoodsReceiptLine."""
        if not self.warehouse and self.pk:  # Ensure instance is saved
            first_line = self.lines.first()
            if first_line:
                try:
                    item = Item.objects.get(code=first_line.item_code)
                    if item.default_warehouse:
                        self.warehouse = item.default_warehouse
                    else:
                        default_warehouse = Warehouse.objects.filter(is_default=True, is_active=True).first()
                        if default_warehouse:
                            self.warehouse = default_warehouse
                    self.save(update_fields=['warehouse'])  # Save only the warehouse field
                except Item.DoesNotExist:
                    pass

    def save(self, *args, **kwargs):
        """Save the instance without accessing related objects prematurely."""
        super().save(*args, **kwargs)


class GoodsReceiptLine(BaseModel):
    goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Goods Receipt"))
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6, default=0)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)

    class Meta:
        verbose_name = _("Goods Receipt Line")
        verbose_name_plural = _("Goods Receipt Lines")

    def __str__(self):
        return f"{self.goods_receipt.id} - {self.item_code}"

    def save(self, *args, **kwargs):
        """Ensure total amount is calculated before saving."""
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class GoodsIssue(BaseModel):
    """Document for issuing inventory (e.g., for sales, internal use)"""

    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Posted', _('Posted')),
        ('Cancelled', _('Cancelled')),
    ]

    document_date = models.DateField(_("Document Date"), default=timezone.now)
    posting_date = models.DateField(_("Posting Date"), default=timezone.now)
    recipient = models.CharField(_("Recipient"), max_length=100, blank=True, null=True)
    reference_document = models.CharField(_("Reference Document"), max_length=50, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')

    # Financial information fields 
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=18, decimal_places=2, default=0)
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=18, decimal_places=2, default=0)
    payable_amount = models.DecimalField(_("Payable Amount"), max_digits=18, decimal_places=2, default=0)
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=18, decimal_places=2, default=0)
    due_amount = models.DecimalField(_("Due Amount"), max_digits=18, decimal_places=2, default=0)
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True, null=True)
    payment_reference = models.CharField(_("Payment Reference"), max_length=100, blank=True, null=True)
    payment_date = models.DateField(_("Payment Date"), blank=True, null=True)

    class Meta:
        verbose_name = _("Goods Issue")
        verbose_name_plural = _("Goods Issues")

    def __str__(self):
        return f"GI {self.id}"


class GoodsIssueLine(BaseModel):
    """Line items for goods issue"""
    goods_issue = models.ForeignKey(GoodsIssue, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Goods Issue"))
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6, default=0)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)

    class Meta:
        verbose_name = _("Goods Issue Line")
        verbose_name_plural = _("Goods Issue Lines")

    def __str__(self):
        return f"{self.goods_issue.id} - {self.item_code}"

    def save(self, *args, **kwargs):
        """Calculate total amount before saving."""
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class InventoryTransfer(BaseModel):
    """Document for transferring inventory between warehouses"""

    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Posted', _('Posted')),
        ('Cancelled', _('Cancelled')),
    ]

    document_date = models.DateField(_("Document Date"), default=timezone.now)
    posting_date = models.DateField(_("Posting Date"), default=timezone.now)
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='outgoing_transfers', verbose_name=_("From Warehouse"))
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='incoming_transfers', verbose_name=_("To Warehouse"))
    reference_document = models.CharField(_("Reference Document"), max_length=50, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')

    # Financial information 
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=18, decimal_places=2, default=0)
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=18, decimal_places=2, default=0)
    payable_amount = models.DecimalField(_("Payable Amount"), max_digits=18, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Inventory Transfer")
        verbose_name_plural = _("Inventory Transfers")

    def __str__(self):
        return f"IT {self.id}"


class InventoryTransferLine(BaseModel):
    """Line items for inventory transfer"""

    inventory_transfer = models.ForeignKey(InventoryTransfer, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Inventory Transfer"))
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6, default=0)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='outgoing_items', verbose_name=_("From Warehouse"))
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='incoming_items', verbose_name=_("To Warehouse"))
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)

    class Meta:
        verbose_name = _("Inventory Transfer Line")
        verbose_name_plural = _("Inventory Transfer Lines")

    def __str__(self):
        return f"{self.inventory_transfer.id} - {self.item_code}"

    def save(self, *args, **kwargs):
        """Calculate total amount before saving."""
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)