from django.db import models
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from Inventory.models import BaseModel, Item, Warehouse, InventoryTransaction, UnitOfMeasure

class BOMType(models.TextChoices):
    PRODUCTION = 'Production', _('Production')
    SALES = 'Sales', _('Sales')
    ASSEMBLY = 'Assembly', _('Assembly')
    TEMPLATE = 'Template', _('Template')

class BillOfMaterials(BaseModel):
    """Bill of Materials (BOM) for manufacturing products"""
    
    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Active', _('Active')),
        ('Inactive', _('Inactive')),
    ]
    
    code = models.CharField(_("BOM Code"), max_length=20, unique=True)
    name = models.CharField(_("BOM Name"), max_length=100)
    product = models.ForeignKey(
        Item, 
        on_delete=models.CASCADE, 
        related_name='product_boms',
        verbose_name=_("Product")
    )
    bom_type = models.CharField(
        _("BOM Type"), 
        max_length=20, 
        choices=BOMType.choices, 
        default=BOMType.PRODUCTION
    )
    uom = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name='boms',
        verbose_name=_("UoM")
    )
    x_quantity = models.DecimalField(
        _("X Quantity"), 
        max_digits=18, 
        decimal_places=6, 
        default=1
    )
    project = models.CharField(_("Project"), max_length=100, blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')
    
    # Cost fields
    total_component_value = models.DecimalField(
        _("Total Component Value"), 
        max_digits=18, 
        decimal_places=2, 
        default=0
    )
    other_cost_percentage = models.DecimalField(
        _("Other Cost %"), 
        max_digits=5, 
        decimal_places=2, 
        default=0
    )
    additional_cost = models.DecimalField(
        _("Additional Cost"), 
        max_digits=18, 
        decimal_places=2, 
        default=0
    )
    total_after_discount = models.DecimalField(
        _("Total After Discount"), 
        max_digits=18, 
        decimal_places=2, 
        default=0
    )
    
    class Meta:
        verbose_name = _("Bill of Materials")
        verbose_name_plural = _("Bills of Materials")
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def calculate_totals(self):
        """Calculate the total costs based on components"""
        # Calculate total component value
        self.total_component_value = sum(
            component.total for component in self.components.all()
        )
        
        # Calculate additional cost based on percentage
        if self.other_cost_percentage > 0:
            self.additional_cost = self.total_component_value * (self.other_cost_percentage / 100)
        
        # Calculate total after discount
        self.total_after_discount = self.total_component_value + self.additional_cost
        
        self.save()


class BOMComponent(BaseModel):
    """Components required for a Bill of Materials"""
    
    bom = models.ForeignKey(
        BillOfMaterials, 
        on_delete=models.CASCADE, 
        related_name='components',
        verbose_name=_("Bill of Materials")
    )
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)    
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit = models.CharField(_("Unit"), max_length=20, blank=True, null=True)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6, default=0)
    total = models.DecimalField(_("Total"), max_digits=18, decimal_places=6, default=0)
    
    class Meta:
        verbose_name = _("BOM Component")
        verbose_name_plural = _("BOM Components")
    
    def __str__(self):
        return f"{self.bom.code} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        # Calculate total based on quantity and unit price
        self.total = (self.quantity * self.unit_price)
        super().save(*args, **kwargs)
        
        # Update BOM totals
        self.bom.calculate_totals()


class ProductionOrder(BaseModel):
    """Production order for manufacturing products"""
    
    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Released', _('Released')),
        ('In Process', _('In Process')),
        ('Completed', _('Completed')),
        ('Cancelled', _('Cancelled')),
    ]
    
    order_number = models.CharField(_("Order Number"), max_length=20, unique=True, blank=True, null=True)
    document_date = models.DateField(_("Document Date"), default=timezone.now)
    product = models.ForeignKey(
        Item, 
        on_delete=models.PROTECT, 
        related_name='production_orders',
        verbose_name=_("Product")
    )
    bom = models.ForeignKey(
        BillOfMaterials, 
        on_delete=models.PROTECT, 
        related_name='production_orders',
        verbose_name=_("Bill of Materials")
    )
    warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.PROTECT, 
        related_name='production_orders',
        verbose_name=_("Warehouse")
    )
    
    planned_quantity = models.DecimalField(_("Planned Quantity"), max_digits=18, decimal_places=6)
    produced_quantity = models.DecimalField(_("Produced Quantity"), max_digits=18, decimal_places=6, default=0)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Production Order")
        verbose_name_plural = _("Production Orders")
    
    def __str__(self):
        return f"PO {self.order_number or self.id}"
    
    def save(self, *args, **kwargs):
        # Generate order number if not provided
        if not self.order_number and not self.pk:
            last_order = ProductionOrder.objects.order_by('-id').first()
            if last_order:
                last_id = last_order.id
            else:
                last_id = 0
            self.order_number = f"PO{last_id + 1:06d}"
            
        super().save(*args, **kwargs)
    def get_completion_percentage(self):
        if self.planned_quantity and self.planned_quantity > 0:
            return (self.produced_quantity / self.planned_quantity) * 100
        return 0

class ProductionOrderComponent(BaseModel):
    """Components required for a production order"""
    
    production_order = models.ForeignKey(
        ProductionOrder, 
        on_delete=models.CASCADE, 
        related_name='components',
        verbose_name=_("Production Order")
    )
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    planned_quantity = models.DecimalField(_("Planned Quantity"), max_digits=18, decimal_places=6)
    issued_quantity = models.DecimalField(_("Issued Quantity"), max_digits=18, decimal_places=6, default=0)
    
    class Meta:
        verbose_name = _("Production Order Component")
        verbose_name_plural = _("Production Order Components")
    
    def __str__(self):
        return f"{self.production_order.order_number} - {self.item_name}"


class ProductionReceipt(BaseModel):
    """Receipt of finished goods from production"""
    
    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Posted', _('Posted')),
        ('Cancelled', _('Cancelled')),
    ]
    
    receipt_number = models.CharField(_("Receipt Number"), max_length=20, unique=True, blank=True, null=True)
    document_date = models.DateField(_("Document Date"), default=timezone.now)
    production_order = models.ForeignKey(
        'ProductionOrder', 
        on_delete=models.PROTECT, 
        related_name='receipts',
        verbose_name=_("Production Order")
    )
    warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.PROTECT, 
        related_name='production_receipts',
        verbose_name=_("Warehouse")
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Production Receipt")
        verbose_name_plural = _("Production Receipts")
    
    def __str__(self):
        return f"PR {self.receipt_number or self.id}"
    
    def save(self, *args, **kwargs):
        # Generate receipt number if not provided
        if not self.receipt_number and not self.pk:
            last_receipt = ProductionReceipt.objects.order_by('-id').first()
            if last_receipt:
                last_id = last_receipt.id
            else:
                last_id = 0
            self.receipt_number = f"PR{last_id + 1:06d}"
            
        super().save(*args, **kwargs)
        
        # Update produced quantity in production order when status is Posted
        if self.status == 'Posted' and self.production_order:
            with transaction.atomic():
                total_quantity = sum(line.quantity for line in self.lines.all())
                self.production_order.produced_quantity += total_quantity
                self.production_order.save(update_fields=['produced_quantity'])

    def clean(self):
        """Validate that total quantity doesn't exceed remaining production order quantity"""
        if self.production_order and self.pk:
            total_quantity = sum(line.quantity for line in self.lines.all())
            remaining_quantity = self.production_order.planned_quantity - self.production_order.produced_quantity
            if total_quantity > remaining_quantity:
                raise ValidationError(
                    f"Total quantity ({total_quantity}) exceeds remaining quantity to produce ({remaining_quantity})"
                )

class ProductionReceiptLine(BaseModel):
    """Line items for production receipt"""
    
    receipt = models.ForeignKey(
        ProductionReceipt, 
        on_delete=models.CASCADE, 
        related_name='lines',
        verbose_name=_("Production Receipt")
    )
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Production Receipt Line")
        verbose_name_plural = _("Production Receipt Lines")
    
    def __str__(self):
        return f"{self.receipt.receipt_number} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        # Validate item_code and auto-populate item_name and uom
        try:
            item = Item.objects.get(code=self.item_code)
            self.item_name = item.name
            if not self.uom and item.sales_uom:
                self.uom = item.sales_uom.name
        except Item.DoesNotExist:
            raise ValidationError(f"Item with code {self.item_code} does not exist")
        
        super().save(*args, **kwargs)
        
        # Trigger parent receipt save to update production order
        if self.receipt.status == 'Posted':
            self.receipt.save()


class ProductionIssue(BaseModel):
    """Issue of components to production"""
    
    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Posted', _('Posted')),
        ('Cancelled', _('Cancelled')),
    ]
    
    issue_number = models.CharField(_("Issue Number"), max_length=20, unique=True, blank=True, null=True)
    document_date = models.DateField(_("Document Date"), default=timezone.now)
    production_order = models.ForeignKey(
        ProductionOrder, 
        on_delete=models.PROTECT, 
        related_name='issues',
        verbose_name=_("Production Order")
    )
    warehouse = models.ForeignKey(
        Warehouse, 
        on_delete=models.PROTECT, 
        related_name='production_issues',
        verbose_name=_("Warehouse")
    )
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Production Issue")
        verbose_name_plural = _("Production Issues")
    
    def __str__(self):
        return f"PI {self.issue_number or self.id}"
    
    def save(self, *args, **kwargs):
        # Generate issue number if not provided
        if not self.issue_number and not self.pk:
            last_issue = ProductionIssue.objects.order_by('-id').first()
            if last_issue:
                last_id = last_issue.id
            else:
                last_id = 0
            self.issue_number = f"PI{last_id + 1:06d}"
            
        super().save(*args, **kwargs)


class ProductionIssueLine(BaseModel):
    """Line items for production issue"""
    
    issue = models.ForeignKey(
        ProductionIssue, 
        on_delete=models.CASCADE, 
        related_name='lines',
        verbose_name=_("Production Issue")
    )
    component = models.ForeignKey(
        ProductionOrderComponent, 
        on_delete=models.PROTECT, 
        related_name='issue_lines',
        verbose_name=_("Production Order Component")
    )
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    
    class Meta:
        verbose_name = _("Production Issue Line")
        verbose_name_plural = _("Production Issue Lines")
    
    def __str__(self):
        return f"{self.issue.issue_number} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        # Update item_code and item_name if not provided
        if not self.item_code and self.component:
            self.item_code = self.component.item_code
            
        if not self.item_name and self.component:
            self.item_name = self.component.item_name
            
        super().save(*args, **kwargs)
        
        # Update issued quantity in production order component
        if self.issue.status == 'Posted' and self.component:
            with transaction.atomic():
                self.component.issued_quantity += self.quantity
                self.component.save(update_fields=['issued_quantity'])
