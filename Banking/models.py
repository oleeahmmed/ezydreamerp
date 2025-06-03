from django.db import models
from global_settings.models import Currency
from BusinessPartnerMasterData.models import BusinessPartner
from Finance.models import ChartOfAccounts
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import datetime
from Sales.models import SalesOrder  
from django.core.exceptions import ValidationError
from Banking.utils.payment_utils import validate_payment_amount, calculate_remaining_balance,set_business_partner
class BaseModel(models.Model):
    """Base model with common fields for all models."""
    created_at = models.DateTimeField(_("Created At"), default=timezone.now)
    updated_at = models.DateTimeField(_("Updated At"), default=timezone.now)
    
    class Meta:
        abstract = True
        verbose_name = _("Base Model")
        verbose_name_plural = _("Base Models")
class PaymentMethod(BaseModel):
    """
    Represents payment methods such as Bank Transfer, Cash, Credit Card, etc.
    """
    name = models.CharField(_("Payment Method"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)

    class Meta:
        verbose_name = _("Payment Method")
        verbose_name_plural = _("Payment Methods")

    def __str__(self):
        return self.name

class Payment(BaseModel):
    """
    Handles both Incoming and Outgoing Payments.
    """
    PAYMENT_TYPE_CHOICES = [
        ('incoming', _("Incoming Payment")),  # From Customer
        ('outgoing', _("Outgoing Payment"))   # To Supplier
    ]
    
    doc_num = models.CharField(_("Document Number"), max_length=20, unique=True)
    business_partner = models.ForeignKey(BusinessPartner, on_delete=models.PROTECT, verbose_name=_("Business Partner"))
    payment_type = models.CharField(_("Payment Type"), max_length=10, choices=PAYMENT_TYPE_CHOICES)
    amount = models.DecimalField(_("Amount"), max_digits=15, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name=_("Currency"))
    payment_date = models.DateField(_("Payment Date"))
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, verbose_name=_("Payment Method"))
    sales_order = models.ForeignKey(
        SalesOrder,  # Assuming the SalesOrder model is in the Sales module
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name=_("Sales Order")
    )    
    reference = models.CharField(_("Reference"), max_length=100, blank=True, null=True)
    remarks = models.TextField(_("Remarks"), blank=True, null=True)
    is_reconciled = models.BooleanField(_("Is Reconciled"), default=False)

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")

    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.doc_num}"
    def save(self, *args, **kwargs):
        """
        Custom save method for the Payment model.
        
        This method ensures that the business partner is set from the associated 
        sales order, validates that the payment amount doesn't exceed the sales 
        order total, and calculates the remaining balance before saving the Payment.
        """
        
        # Ensure the business partner is set from the associated sales order if it's not already set
        self = set_business_partner(self)
        
        # Validate that the payment amount does not exceed the total amount of the associated sales order
        if not validate_payment_amount(self.sales_order, self.amount):
            raise ValidationError('Payment exceeds the sales order total amount.')
        
        # Calculate the remaining balance of the sales order after applying this payment
        remaining_balance = calculate_remaining_balance(self.sales_order)
        print(f"Remaining balance for payment: {remaining_balance}")  # Optional: For debugging purposes, you can log this
        
        # Proceed with the saving of the payment instance
        super().save(*args, **kwargs)
class PaymentLine(BaseModel):
    """
    Represents the detailed line items for payments (can be multiple for partial payments).
    """
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='payment_lines', verbose_name=_("Payment"))
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.PROTECT, verbose_name=_("Account"))
    amount = models.DecimalField(_("Amount"), max_digits=15, decimal_places=2)
    description = models.CharField(_("Description"), max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _("Payment Line")
        verbose_name_plural = _("Payment Lines")

    def __str__(self):
        return f"{self.payment.doc_num} - {self.account.name}"
