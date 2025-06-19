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
from .utils import validate_sales_order_line_stock 

class SalesEmployee(BaseModel):
    """Sales employee model linked to user account"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sales_employee',
        verbose_name=_("User")
    )
    name = models.CharField(_("Name"), max_length=100)
    position = models.CharField(_("Position"), max_length=100, blank=True, null=True)
    department = models.CharField(_("Department"), max_length=100, blank=True, null=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True, null=True)
    notes = models.TextField(_("Notes"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Sales Employee")
        verbose_name_plural = _("Sales Employees")
        
    def __str__(self):
        return f"{self.name}"
    
    def save(self, *args, **kwargs):
        # If email is not provided, use the user's email
        if not self.email and self.user and self.user.email:
            self.email = self.user.email
            
        # If name is not provided, use the user's name
        if not self.name and self.user:
            self.name = f"{self.user.first_name} {self.user.last_name}".strip()
            if not self.name:
                self.name = self.user.username
                
        super().save(*args, **kwargs)

# --- Sales Quotation Model ---
class SalesQuotation(BaseModel):
    """Sales quotation document for potential customers"""
    
    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Open', _('Open')),
        ('Sent', _('Sent')),
        ('Expired', _('Expired')),
        ('Converted', _('Converted to Order')),
        ('Closed', _('Closed')),
        ('Cancelled', _('Cancelled')),
    ]
    
    document_no = models.CharField(_("Document No"), max_length=50, unique=True, blank=True, null=True)
    document_date = models.DateField(_("Document Date"), default=timezone.now)
    valid_until = models.DateField(_("Valid Until"), null=True, blank=True)
    customer = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT, limit_choices_to={'bp_type': 'C'}, verbose_name=_("Customer"))
    
    # Financial information
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=18, decimal_places=6, default=0)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=18, decimal_places=6, default=0)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    
    # Payment information
    payable_amount = models.DecimalField(_("Payable Amount"), max_digits=18, decimal_places=6, default=0)
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=18, decimal_places=6, default=0)
    due_amount = models.DecimalField(_("Due Amount"), max_digits=18, decimal_places=6, default=0)
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True, null=True)
    payment_reference = models.CharField(_("Payment Reference"), max_length=100, blank=True, null=True)
    payment_date = models.DateField(_("Payment Date"), blank=True, null=True)

    # Additional information
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')
    sales_employee = models.ForeignKey(
        SalesEmployee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='sales_quotations',
        verbose_name=_("Sales Employee")
    )
    
    class Meta:
        verbose_name = _("Sales Quotation")
        verbose_name_plural = _("Sales Quotations")
        ordering = ['-document_date', '-created_at'] # Added ordering for consistency
    
    def __str__(self):
        return f"SQ-{self.document_no or self.id}" # Consistent document numbering

    def save(self, *args, **kwargs):
        # Generate document_no if not already set
        if not self.document_no:
            year = datetime.datetime.now().year
            last_sq = SalesQuotation.objects.filter(document_no__startswith=f'SQ-{year}-').order_by('-id').first()
            if last_sq:
                last_num = int(last_sq.document_no.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.document_no = f'SQ-{year}-{new_num:04d}'

        # Calculate Total Amount from Lines (assuming lines are already added or will be calculated by signals/utilities)
        if self.pk:  # Only if the object is saved (otherwise no lines exist)
            lines_total = Decimal(0)
            for line in self.lines.all():
                lines_total += (line.quantity * line.unit_price)
            self.total_amount = lines_total.quantize(Decimal('0.000001')) # Ensure Decimal precision

        # Calculate payable amount
        if self.total_amount is not None and self.tax_amount is not None and self.discount_amount is not None:
            self.payable_amount = (self.total_amount + self.tax_amount) - self.discount_amount
            self.payable_amount = self.payable_amount.quantize(Decimal('0.000001'))
        
        # Calculate due amount
        if self.payable_amount is not None and self.paid_amount is not None:
            self.due_amount = self.payable_amount - self.paid_amount
            self.due_amount = self.due_amount.quantize(Decimal('0.000001'))
            

        
        super().save(*args, **kwargs)


class SalesQuotationLine(BaseModel):
    """Line items for sales quotation"""
    
    quotation = models.ForeignKey(SalesQuotation, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Quotation"))
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Sales Quotation Line")
        verbose_name_plural = _("Sales Quotation Lines")
    
    def __str__(self):
        return f"{self.quotation.id} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity * self.unit_price).quantize(Decimal('0.000001'))
        super().save(*args, **kwargs)

# --- Sales Order Model ---
class SalesOrder(BaseModel):
    """Represents a confirmed sales order for a customer"""

    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Open', _('Open')),
        ('Partially Delivered', _('Partially Delivered')),
        ('Delivered', _('Delivered')),
        ('Partially Invoiced', _('Partially Invoiced')),
        ('Invoiced', _('Invoiced')),
        ('Closed', _('Closed')),
        ('Cancelled', _('Cancelled')),
    ]

    document_no = models.CharField(_("Document No"), max_length=50, unique=True, blank=True, null=True)
    document_date = models.DateField(_("Document Date"), default=timezone.now)
    delivery_date = models.DateField(_("Delivery Date"), null=True, blank=True)
    customer = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT, limit_choices_to={'bp_type': 'C'}, verbose_name=_("Customer"))
    
    # Financial information
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=18, decimal_places=6, default=0) # Kept 6 decimal places for consistency
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=18, decimal_places=6, default=0) # Kept 6 decimal places for consistency
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0) # Kept 6 decimal places for consistency
    
    # Payment information
    payable_amount = models.DecimalField(_("Payable Amount"), max_digits=18, decimal_places=6, default=0) # Kept 6 decimal places for consistency
    paid_amount = models.DecimalField(_("Paid Amount"), max_digits=18, decimal_places=6, default=0) # Kept 6 decimal places for consistency
    due_amount = models.DecimalField(_("Due Amount"), max_digits=18, decimal_places=6, default=0) # Kept 6 decimal places for consistency
    payment_method = models.CharField(_("Payment Method"), max_length=50, blank=True, null=True)
    payment_reference = models.CharField(_("Payment Reference"), max_length=100, blank=True, null=True)
    payment_date = models.DateField(_("Payment Date"), blank=True, null=True)
    
    # Additional Info
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='Draft')
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    sales_employee = models.ForeignKey(SalesEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders', verbose_name=_("Sales Employee"))
    quotation = models.ForeignKey(
        'SalesQuotation',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sales_orders'
    )
    
    class Meta:
        verbose_name = _("Sales Order")
        verbose_name_plural = _("Sales Orders")
        ordering = ['-document_date', '-created_at'] 

    def __str__(self):
        return f"SO-{self.document_no or self.id}" 

    def save(self, *args, **kwargs):
        # Generate document_no if not already set
        if not self.document_no:
            year = datetime.datetime.now().year
            last_so = SalesOrder.objects.filter(document_no__startswith=f'SO-{year}-').order_by('-id').first()
            if last_so:
                last_num = int(last_so.document_no.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.document_no = f'SO-{year}-{new_num:04d}'

        # ✅ Calculate Total Amount from Lines
        if self.pk:  
            lines_total = Decimal(0)
            for line in self.lines.all():
                lines_total += (line.quantity * line.unit_price)
            self.total_amount = lines_total.quantize(Decimal('0.000001')) # Ensure Decimal precision
        # ✅ Calculate payable amount
        if self.total_amount is not None and self.tax_amount is not None and self.discount_amount is not None:
            self.payable_amount = (self.total_amount + self.tax_amount) - self.discount_amount
            self.payable_amount = self.payable_amount.quantize(Decimal('0.000001'))
        # ✅ Calculate due amount
        if self.payable_amount is not None and self.paid_amount is not None:
            self.due_amount = self.payable_amount - self.paid_amount
            self.due_amount = self.due_amount.quantize(Decimal('0.000001'))
        super().save(*args, **kwargs)



# Keep the SalesOrderLine class as is
class SalesOrderLine(BaseModel):
    """Line items for Sales Order"""

    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Order"))
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)


    def __str__(self):
        return f"{self.item_name} - {self.quantity} units"
    def clean(self):
        super().clean()
        # Call the utility function for stock validation
        validate_sales_order_line_stock(self)
    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity * self.unit_price).quantize(Decimal('0.000001'))
  
        super().save(*args, **kwargs)

class Delivery(BaseModel):
    """Delivery document for shipping items to customers"""
    
    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Open', _('Open')),
        ('Partially Delivered', _('Partially Delivered')),
        ('Delivered', _('Delivered')),
        ('Closed', _('Closed')),
        ('Cancelled', _('Cancelled')),
    ]
    
    document_date = models.DateField(_("Document Date"), default=timezone.now)
    posting_date = models.DateField(_("Posting Date"), default=timezone.now)
    customer = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT, limit_choices_to={'bp_type': 'C'}, verbose_name=_("Customer"))
    contact_person = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Contact Person"))
    shipping_address = models.ForeignKey(
        Address, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='delivery_shipping_address',
        verbose_name=_("Shipping Address")
    )
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries', verbose_name=_("Sales Order"))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Currency"))
    payment_terms = models.ForeignKey(PaymentTerms, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Payment Terms"))    
    # Financial information
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=18, decimal_places=2, default=0)
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
    sales_employee = models.ForeignKey(
        SalesEmployee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='deliveries',
        verbose_name=_("Sales Employee")
    )
    # Delivery-specific fields
    deliveryemployee = models.CharField(_("Delivery Employee"), max_length=100, blank=True, null=True)
    delivery_method = models.CharField(_("Delivery Method"), max_length=50, choices=[('Car', _('Car')), ('Lorry', _('Lorry')), ('Van', _('Van')), ('Bike', _('Bike'))], blank=True, null=True)
    driver_name = models.CharField(_("Driver Name"), max_length=100, blank=True, null=True)
    vehicle_number = models.CharField(_("Vehicle Number"), max_length=50, blank=True, null=True)
    expected_delivery_date = models.DateField(_("Expected Delivery Date"), blank=True, null=True)
    actual_delivery_date = models.DateField(_("Actual Delivery Date"), blank=True, null=True)
    tracking_number = models.CharField(_("Tracking Number"), max_length=100, blank=True, null=True)
    delivery_notes = models.TextField(_("Delivery Notes"), blank=True, null=True)
    delivery_area = models.CharField(_("Delivery Area"), max_length=100, blank=True, null=True)  

        
    class Meta:
        verbose_name = _("Delivery")
        verbose_name_plural = _("Deliveries")
    
    def __str__(self):
        return f"Delivery #{self.id} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        # Use customer's default values if not specified
        if not self.currency and self.customer and self.customer.currency:
            self.currency = self.customer.currency
            
        if not self.contact_person and self.customer:
            # Try to get default contact person
            try:
                default_contact = self.customer.contact_persons.filter(is_default=True).first()
                if default_contact:
                    self.contact_person = default_contact
            except Exception:
                pass
                
        if not self.shipping_address and self.customer:
            # Try to get default shipping address
            try:
                default_shipping = self.customer.addresses.filter(address_type='S', is_default=True).first()
                if default_shipping:
                    self.shipping_address = default_shipping
            except Exception:
                pass
        # Calculate payable amount
        if self.total_amount is not None and self.discount_amount is not None:
            self.payable_amount = self.total_amount - self.discount_amount
        
        # Calculate due amount
        if self.payable_amount is not None and self.paid_amount is not None:
            self.due_amount = self.payable_amount - self.paid_amount                
        super().save(*args, **kwargs)

# Keep the DeliveryLine class as is
class DeliveryLine(BaseModel):
    """Line items for delivery document"""
    
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Delivery"))
    sales_order_line = models.ForeignKey(SalesOrderLine, on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_lines', verbose_name=_("Sales Order Line"))
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Delivery Line")
        verbose_name_plural = _("Delivery Lines")
    
    def __str__(self):
        return f"Delivery #{self.delivery.id} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity * self.unit_price).quantize(Decimal('0.000001'))
        super().save(*args, **kwargs)

class Return(BaseModel):
    """Return document for items returned by customers"""
    
    STATUS_CHOICES = [
        ('Draft', _('Draft')),
        ('Open', _('Open')),
        ('Returned', _('Returned')),
        ('Closed', _('Closed')),
        ('Cancelled', _('Cancelled')),
    ]
    
    document_date = models.DateField(_("Document Date"), default=timezone.now)
    posting_date = models.DateField(_("Posting Date"), default=timezone.now)
    customer = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT, limit_choices_to={'bp_type': 'C'}, verbose_name=_("Customer"))
    contact_person = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Contact Person"))
    return_address = models.ForeignKey(
        Address, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='return_address',
        verbose_name=_("Return Address")
    )
    delivery = models.ForeignKey(Delivery, on_delete=models.SET_NULL, null=True, blank=True, related_name='returns', verbose_name=_("Delivery"))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Currency"))
    payment_terms = models.ForeignKey(PaymentTerms, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Payment Terms"))   
    # Financial information
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=18, decimal_places=2, default=0)
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
    sales_employee = models.ForeignKey(
        SalesEmployee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='returns',
        verbose_name=_("Sales Employee")
    )
    
    class Meta:
        verbose_name = _("Return")
        verbose_name_plural = _("Returns")
    
    def __str__(self):
        return f"Return #{self.id} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        # Use customer's default values if not specified
        if not self.contact_person and self.customer:
            # Try to get default contact person
            try:
                default_contact = self.customer.contact_persons.filter(is_default=True).first()
                if default_contact:
                    self.contact_person = default_contact
            except Exception:
                pass
                
        if not self.return_address and self.customer:
            # Try to get default shipping address as return address
            try:
                default_shipping = self.customer.addresses.filter(address_type='S', is_default=True).first()
                if default_shipping:
                    self.return_address = default_shipping
            except Exception:
                pass
        # Calculate payable amount
        if self.total_amount is not None and self.discount_amount is not None:
            self.payable_amount = self.total_amount - self.discount_amount
        
        # Calculate due amount
        if self.payable_amount is not None and self.paid_amount is not None:
            self.due_amount = self.payable_amount - self.paid_amount
                            
        super().save(*args, **kwargs)

# Keep the ReturnLine class as is
class ReturnLine(BaseModel):
    """Line items for return document"""
    
    return_doc = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Return"))
    delivery_line = models.ForeignKey(DeliveryLine, on_delete=models.SET_NULL, null=True, blank=True, related_name='return_lines', verbose_name=_("Delivery Line"))
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Return Line")
        verbose_name_plural = _("Return Lines")
    
    def __str__(self):
        return f"Return #{self.return_doc.id} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity * self.unit_price).quantize(Decimal('0.000001'))
        super().save(*args, **kwargs)

class ARInvoice(BaseModel):
    """Accounts Receivable Invoice for customer billing"""
    
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
    customer = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT, limit_choices_to={'bp_type': 'C'}, verbose_name=_("Customer"))
    contact_person = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Contact Person"))
    billing_address = models.ForeignKey(
        Address, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='invoice_billing_address',
        verbose_name=_("Billing Address")
    )
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name=_("Sales Order"))
    delivery = models.ForeignKey(Delivery, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name=_("Delivery"))
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_("Currency"))
    payment_terms = models.ForeignKey(PaymentTerms, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Payment Terms"))
    
    # Financial information
    discount_amount = models.DecimalField(_("Discount Amount"), max_digits=18, decimal_places=2, default=0,null=True, blank=True)
    tax_amount = models.DecimalField(_("Tax Amount"), max_digits=18, decimal_places=2, default=0,null=True, blank=True)
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
    sales_employee = models.ForeignKey(
        SalesEmployee, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='invoices',
        verbose_name=_("Sales Employee")
    )
    
    class Meta:
        verbose_name = _("AR Invoice")
        verbose_name_plural = _("AR Invoices")
    
    def __str__(self):
        return f"Invoice #{self.id} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        # Use customer's default values if not specified
        if not self.currency and self.customer and self.customer.currency:
            self.currency = self.customer.currency
            
        if not self.payment_terms and self.customer and self.customer.payment_terms:
            self.payment_terms = self.customer.payment_terms
            
        # Calculate due date if not provided
        if not self.due_date and self.document_date and self.payment_terms:
            self.due_date = self.document_date + datetime.timedelta(days=self.payment_terms.days)
        
        if not self.contact_person and self.customer:
            # Try to get default contact person
            try:
                default_contact = self.customer.contact_persons.filter(is_default=True).first()
                if default_contact:
                    self.contact_person = default_contact
            except Exception:
                pass
                
        if not self.billing_address and self.customer:
            # Try to get default billing address
            try:
                default_billing = self.customer.addresses.filter(address_type='B', is_default=True).first()
                if default_billing:
                    self.billing_address = default_billing
            except Exception:
                pass
        
        # Calculate due amount
        if self.payable_amount is not None and self.paid_amount is not None:
            self.due_amount = self.payable_amount - self.paid_amount
        
        super().save(*args, **kwargs)

class ARInvoiceLine(BaseModel):
    """Line items for AR Invoice"""
    
    invoice = models.ForeignKey(ARInvoice, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Invoice"))
    sales_order_line = models.ForeignKey(SalesOrderLine, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_lines', verbose_name=_("Sales Order Line"))
    delivery_line = models.ForeignKey(DeliveryLine, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice_lines', verbose_name=_("Delivery Line"))
    item_code = models.CharField(_("Item Code"), max_length=50)
    item_name = models.CharField(_("Item Name"), max_length=100)
    quantity = models.DecimalField(_("Quantity"), max_digits=18, decimal_places=6)
    unit_price = models.DecimalField(_("Unit Price"), max_digits=18, decimal_places=6)
    total_amount = models.DecimalField(_("Total Amount"), max_digits=18, decimal_places=6, default=0)
    uom = models.CharField(_("UOM"), max_length=20, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    
    class Meta:
        verbose_name = _("AR Invoice Line")
        verbose_name_plural = _("AR Invoice Lines")
    
    def __str__(self):
        return f"Invoice #{self.invoice.id} - {self.item_name}"
    
    def save(self, *args, **kwargs):
        self.total_amount = Decimal(self.quantity * self.unit_price).quantize(Decimal('0.000001'))
        super().save(*args, **kwargs)
        
class FreeItemDiscount(BaseModel):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='buy_item_discounts')
    buy_quantity = models.PositiveIntegerField()
    free_item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='free_item_discounts')
    free_quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"Buy {self.buy_quantity} of {self.item.name} get {self.free_quantity} of {self.free_item.name} free"
