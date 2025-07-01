from django.db import models
from global_settings.models import (
    Currency, 
    PaymentTerms
)
from django.utils.translation import gettext_lazy as _
from django.db.models import Prefetch
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum

class BusinessPartnerGroup(models.Model):
    name = models.CharField(_("Name"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Business Partner Group")
        verbose_name_plural = _("Business Partner Groups")

    def __str__(self):
        return self.name

class BusinessPartner(models.Model):
    BP_TYPES = [
        ('C', _('Customer')),
        ('S', _('Supplier')),
        # ('L', 'Lead'),
    ]
    code = models.CharField(_("Code"), max_length=20, unique=True)
    name = models.CharField(_("Name"), max_length=100)
    bp_type = models.CharField(_("Type"), max_length=1, choices=BP_TYPES, default='C', null=True, blank=True)
    group = models.ForeignKey('BusinessPartnerGroup', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Group"))
    currency = models.ForeignKey('global_settings.Currency', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Currency"))
    active = models.BooleanField(_("Active"), default=True)
    
    # Financial Information fields
    credit_limit = models.DecimalField(_("Credit Limit"), max_digits=15, decimal_places=2, default=0, null=True, blank=True)
    balance = models.DecimalField(_("Balance"), max_digits=15, decimal_places=2, default=0, null=True, blank=True)
    payment_terms = models.ForeignKey('global_settings.PaymentTerms', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Payment Terms"), related_name='business_partners')
    
    # Contact Information fields
    phone = models.CharField(_("Phone"), max_length=20, blank=True, null=True)
    mobile = models.CharField(_("Mobile"), max_length=20, blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True, null=True)
    website = models.URLField(_("Website"), blank=True, null=True)
    federal_tax_id = models.CharField(_("Federal Tax ID"), max_length=20, blank=True, null=True)
    
    # Default Address fields
    default_billing_street = models.CharField(_("Billing Street"), max_length=100, blank=True, null=True)
    default_billing_city = models.CharField(_("Billing City"), max_length=50, blank=True, null=True)
    default_billing_state = models.CharField(_("Billing State"), max_length=50, blank=True, null=True)
    default_billing_zip_code = models.CharField(_("Billing ZIP Code"), max_length=20, blank=True, null=True)
    default_billing_country = models.CharField(_("Billing Country"), max_length=50, blank=True, null=True)
    
    default_shipping_street = models.CharField(_("Shipping Street"), max_length=100, blank=True, null=True)
    default_shipping_city = models.CharField(_("Shipping City"), max_length=50, blank=True, null=True)
    default_shipping_state = models.CharField(_("Shipping State"), max_length=50, blank=True, null=True)
    default_shipping_zip_code = models.CharField(_("Shipping ZIP Code"), max_length=20, blank=True, null=True)
    default_shipping_country = models.CharField(_("Shipping Country"), max_length=50, blank=True, null=True)
    
    # Default Contact Person fields
    default_contact_name = models.CharField(_("Contact Name"), max_length=100, blank=True, null=True)
    default_contact_position = models.CharField(_("Contact Position"), max_length=50, blank=True, null=True)
    default_contact_phone = models.CharField(_("Contact Phone"), max_length=20, blank=True, null=True)
    default_contact_mobile = models.CharField(_("Contact Mobile"), max_length=20, blank=True, null=True)
    default_contact_email = models.EmailField(_("Contact Email"), blank=True, null=True)
    # 🌍 Google Map Fields
    latitude = models.DecimalField(_("Latitude"), max_digits=13, decimal_places=10, blank=True, null=True)
    longitude = models.DecimalField(_("Longitude"), max_digits=13, decimal_places=10, blank=True, null=True)


    google_place_id = models.CharField(_("Google Place ID"), max_length=255, blank=True, null=True)
    class Meta:
        verbose_name = _("Business Partner")
        verbose_name_plural = _("Business Partners")
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['name']),
            models.Index(fields=['bp_type']),
            models.Index(fields=['active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"
    @property
    def total_sales_amount(self):
        """
        Calculates the total sales amount (sum of all related sales orders).
        Lazy import to avoid circular import issue.
        """
        from Sales.models import SalesOrder
        sales_orders = SalesOrder.objects.filter(customer=self)
        return sales_orders.aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0

    @property
    def total_deliveries(self):
        """
        Calculates the total amount of deliveries (sum of all related deliveries).
        Lazy import to avoid circular import issue.
        """
        from Sales.models import Delivery
        deliveries = Delivery.objects.filter(customer=self)
        return deliveries.aggregate(total_deliveries=Sum('total_amount'))['total_deliveries'] or 0

    @property
    def total_returns(self):
        """
        Calculates the total amount of returns (sum of all related returns).
        Lazy import to avoid circular import issue.
        """
        from Sales.models import Return
        returns = Return.objects.filter(customer=self)
        return returns.aggregate(total_returns=Sum('total_amount'))['total_returns'] or 0

    @property
    def total_invoices(self):
        """
        Calculates the total amount of invoices (sum of all related AR invoices).
        Lazy import to avoid circular import issue.
        """
        from Sales.models import ARInvoice
        invoices = ARInvoice.objects.filter(customer=self)
        return invoices.aggregate(total_invoices=Sum('total_amount'))['total_invoices'] or 0
    def __str__(self):
        return f"{self.code} - {self.name}"
    @property
    def total_incoming_payments(self):
        """
        Calculates the total incoming payments (sum of all related incoming payments).
        Lazy import to avoid circular import issue.
        """
        from Banking.models import Payment  # Lazy import
        incoming_payments = Payment.objects.filter(business_partner=self, payment_type='incoming')
        return incoming_payments.aggregate(total_incoming=Sum('amount'))['total_incoming'] or 0
    # Purchase-related properties
    @property
    def total_purchase_amount(self):
        """
        Calculates the total purchase amount (sum of all related purchase orders).
        Lazy import to avoid circular import issue.
        """
        from Purchase.models import PurchaseOrder  # Lazy import
        purchase_orders = PurchaseOrder.objects.filter(vendor=self)
        return purchase_orders.aggregate(total_purchase=Sum('total_amount'))['total_purchase'] or 0

    @property
    def total_purchase_goods_receipt(self):
        """
        Calculates the total amount of goods receipts (sum of all related goods receipts).
        Lazy import to avoid circular import issue.
        """
        from Purchase.models import GoodsReceiptPo  # Lazy import
        goods_receipts = GoodsReceiptPo.objects.filter(vendor=self)
        return goods_receipts.aggregate(total_goods_receipt=Sum('total_amount'))['total_goods_receipt'] or 0

    @property
    def total_purchase_ap_invoice(self):
        """
        Calculates the total amount of AP invoices (sum of all related AP invoices).
        Lazy import to avoid circular import issue.
        """
        from Purchase.models import APInvoice  # Lazy import
        ap_invoices = APInvoice.objects.filter(vendor=self)
        return ap_invoices.aggregate(total_ap_invoice=Sum('total_amount'))['total_ap_invoice'] or 0

    @property
    def total_purchase_return(self):
        """
        Calculates the total amount of purchase returns (sum of all related purchase returns).
        Lazy import to avoid circular import issue.
        """
        from Purchase.models import GoodsReturn  # Lazy import
        purchase_returns = GoodsReturn.objects.filter(vendor=self)
        return purchase_returns.aggregate(total_purchase_return=Sum('total_amount'))['total_purchase_return'] or 0
    @property
    def total_outgoing_payments(self):
        """
        Calculates the total outgoing payments (sum of all related outgoing payments).
        Lazy import to avoid circular import issue.
        """
        from Banking.models import Payment  # Lazy import
        outgoing_payments = Payment.objects.filter(business_partner=self, payment_type='outgoing')
        return outgoing_payments.aggregate(total_outgoing=Sum('amount'))['total_outgoing'] or 0


    @property
    def due_sales(self):
        """
        Calculates the due sales amount (total_sales_amount - total_incoming_payments).
        """
        due_sales = self.total_sales_amount - self.total_incoming_payments
        return due_sales if due_sales >= 0 else 0  # Ensure due sales is not negative    

    @property
    def due_purchase(self):
        """
        Calculates the due purchase amount (total_purchase_amount - total_outgoing_payments).
        """
        due_purchase = self.total_purchase_amount - self.total_outgoing_payments
        return due_purchase if due_purchase >= 0 else 0  # Ensure due purchase is not negative      
    @classmethod
    def get_for_list(cls):
        """Optimized method for list view"""
        return cls.objects.only(
            'id', 'code', 'name', 'bp_type', 'active', 'group'
        ).select_related('group')
    
    @classmethod
    def get_for_detail(cls, pk):
        """Optimized method for detail view"""
        return cls.objects.filter(pk=pk).select_related(
            'group', 
            'currency', 
            'financial_info', 
            'financial_info__payment_terms',
            'contact_info'
        ).prefetch_related(
            Prefetch('addresses', queryset=Address.objects.filter(is_default=True)),
            Prefetch('contact_persons', queryset=ContactPerson.objects.filter(is_default=True))
        ).first()
    
    def save(self, *args, **kwargs):
        # Create or update related models if they don't exist
        super().save(*args, **kwargs)
        
        # Ensure FinancialInformation exists
        financial_info, created = FinancialInformation.objects.get_or_create(
            business_partner=self,
            defaults={
                'credit_limit': self.credit_limit or 0,
                'balance': self.balance or 0,
                'payment_terms': self.payment_terms
            }
        )
        
        if not created:
            # Update existing financial info
            financial_info.credit_limit = self.credit_limit or 0
            financial_info.balance = self.balance or 0
            financial_info.payment_terms = self.payment_terms
            financial_info.save()
        
        # Ensure ContactInformation exists
        contact_info, created = ContactInformation.objects.get_or_create(
            business_partner=self,
            defaults={
                'phone': self.phone or '',
                'mobile': self.mobile or '',
                'email': self.email or '',
                'website': self.website or '',
                'federal_tax_id': self.federal_tax_id or ''
            }
        )
        
        if not created:
            # Update existing contact info
            contact_info.phone = self.phone or ''
            contact_info.mobile = self.mobile or ''
            contact_info.email = self.email or ''
            contact_info.website = self.website or ''
            contact_info.federal_tax_id = self.federal_tax_id or ''
            contact_info.save()
        
        # Create or update default billing address
        if self.default_billing_street:
            billing_address, created = Address.objects.get_or_create(
                business_partner=self,
                address_type='B',
                is_default=True,
                defaults={
                    'street': self.default_billing_street,
                    'city': self.default_billing_city or '',
                    'state': self.default_billing_state or '',
                    'zip_code': self.default_billing_zip_code or '',
                    'country': self.default_billing_country or ''
                }
            )
            
            if not created:
                # Update existing billing address
                billing_address.street = self.default_billing_street
                billing_address.city = self.default_billing_city or ''
                billing_address.state = self.default_billing_state or ''
                billing_address.zip_code = self.default_billing_zip_code or ''
                billing_address.country = self.default_billing_country or ''
                billing_address.save()
            
        # Create or update default shipping address
        if self.default_shipping_street:
            shipping_address, created = Address.objects.get_or_create(
                business_partner=self,
                address_type='S',
                is_default=True,
                defaults={
                    'street': self.default_shipping_street,
                    'city': self.default_shipping_city or '',
                    'state': self.default_shipping_state or '',
                    'zip_code': self.default_shipping_zip_code or '',
                    'country': self.default_shipping_country or ''
                }
            )
            
            if not created:
                # Update existing shipping address
                shipping_address.street = self.default_shipping_street
                shipping_address.city = self.default_shipping_city or ''
                shipping_address.state = self.default_shipping_state or ''
                shipping_address.zip_code = self.default_shipping_zip_code or ''
                shipping_address.country = self.default_shipping_country or ''
                shipping_address.save()
            
        # Create or update default contact person
        if self.default_contact_name:
            contact_person, created = ContactPerson.objects.get_or_create(
                business_partner=self,
                is_default=True,
                defaults={
                    'name': self.default_contact_name,
                    'position': self.default_contact_position or '',
                    'phone': self.default_contact_phone or '',
                    'mobile': self.default_contact_mobile or '',
                    'email': self.default_contact_email or ''
                }
            )
            
            if not created:
                # Update existing contact person
                contact_person.name = self.default_contact_name
                contact_person.position = self.default_contact_position or ''
                contact_person.phone = self.default_contact_phone or ''
                contact_person.mobile = self.default_contact_mobile or ''
                contact_person.email = self.default_contact_email or ''
                contact_person.save()

# Keep the existing models for backward compatibility
class FinancialInformation(models.Model):
    business_partner = models.OneToOneField(BusinessPartner, on_delete=models.CASCADE, related_name='financial_info', verbose_name=_("Business Partner"))
    credit_limit = models.DecimalField(_("Credit Limit"), max_digits=15, decimal_places=2, default=0)
    balance = models.DecimalField(_("Balance"), max_digits=15, decimal_places=2, default=0)
    payment_terms = models.ForeignKey('global_settings.PaymentTerms', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Payment Terms"))

    class Meta:
        verbose_name = _("Financial Information")
        verbose_name_plural = _("Financial Information")
        indexes = [
            models.Index(fields=['business_partner']),
        ]
        
    def save(self, *args, **kwargs):
        # Sync with BusinessPartner model
        super().save(*args, **kwargs)
        bp = self.business_partner
        bp.credit_limit = self.credit_limit
        bp.balance = self.balance
        bp.payment_terms = self.payment_terms
        # Use update to avoid recursive save
        BusinessPartner.objects.filter(pk=bp.pk).update(
            credit_limit=self.credit_limit,
            balance=self.balance,
            payment_terms=self.payment_terms
        )

class ContactInformation(models.Model):
    business_partner = models.OneToOneField(BusinessPartner, on_delete=models.CASCADE, related_name='contact_info', verbose_name=_("Business Partner"))
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    mobile = models.CharField(_("Mobile"), max_length=20, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    website = models.URLField(_("Website"), blank=True)
    federal_tax_id = models.CharField(_("Federal Tax ID"), max_length=20, blank=True)

    class Meta:
        verbose_name = _("Contact Information")
        verbose_name_plural = _("Contact Information")
        indexes = [
            models.Index(fields=['business_partner']),
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
        ]
        
    def save(self, *args, **kwargs):
        # Sync with BusinessPartner model
        super().save(*args, **kwargs)
        bp = self.business_partner
        # Use update to avoid recursive save
        BusinessPartner.objects.filter(pk=bp.pk).update(
            phone=self.phone,
            mobile=self.mobile,
            email=self.email,
            website=self.website,
            federal_tax_id=self.federal_tax_id
        )

class Address(models.Model):
    ADDRESS_TYPES = [
        ('B', _('Billing')),
        ('S', _('Shipping')),
    ]
    business_partner = models.ForeignKey(BusinessPartner, on_delete=models.CASCADE, related_name='addresses', verbose_name=_("Business Partner"))
    address_type = models.CharField(_("Address Type"), max_length=1, choices=ADDRESS_TYPES)
    street = models.CharField(_("Street"), max_length=100)
    city = models.CharField(_("City"), max_length=50)
    state = models.CharField(_("State"), max_length=50)
    zip_code = models.CharField(_("ZIP Code"), max_length=20)
    country = models.CharField(_("Country"), max_length=50)
    is_default = models.BooleanField(_("Is Default"), default=False)

    class Meta:
        verbose_name = _("Address")
        verbose_name_plural = _("Addresses")
        indexes = [
            models.Index(fields=['business_partner']),
            models.Index(fields=['address_type']),
            models.Index(fields=['is_default']),
            models.Index(fields=['country']),
            models.Index(fields=['city']),
        ]

    def __str__(self):
        return f"{self.business_partner.name} - {self.get_address_type_display()} Address"
        
    def save(self, *args, **kwargs):
        # Sync with BusinessPartner model if this is a default address
        super().save(*args, **kwargs)
        if self.is_default:
            bp = self.business_partner
            update_fields = {}
            
            if self.address_type == 'B':
                update_fields = {
                    'default_billing_street': self.street,
                    'default_billing_city': self.city,
                    'default_billing_state': self.state,
                    'default_billing_zip_code': self.zip_code,
                    'default_billing_country': self.country
                }
            elif self.address_type == 'S':
                update_fields = {
                    'default_shipping_street': self.street,
                    'default_shipping_city': self.city,
                    'default_shipping_state': self.state,
                    'default_shipping_zip_code': self.zip_code,
                    'default_shipping_country': self.country
                }
                
            # Use update to avoid recursive save
            if update_fields:
                BusinessPartner.objects.filter(pk=bp.pk).update(**update_fields)

class ContactPerson(models.Model):
    business_partner = models.ForeignKey(BusinessPartner, on_delete=models.CASCADE, related_name='contact_persons', verbose_name=_("Business Partner"))
    name = models.CharField(_("Name"), max_length=100)
    position = models.CharField(_("Position"), max_length=50, blank=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    mobile = models.CharField(_("Mobile"), max_length=20, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    is_default = models.BooleanField(_("Is Default"), default=False)

    class Meta:
        verbose_name = _("Contact Person")
        verbose_name_plural = _("Contact Persons")
        indexes = [
            models.Index(fields=['business_partner']),
            models.Index(fields=['is_default']),
            models.Index(fields=['name']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.business_partner.name} - {self.name}"
        
    def save(self, *args, **kwargs):
        # Sync with BusinessPartner model if this is a default contact
        super().save(*args, **kwargs)
        if self.is_default:
            bp = self.business_partner
            # Use update to avoid recursive save
            BusinessPartner.objects.filter(pk=bp.pk).update(
                default_contact_name=self.name,
                default_contact_position=self.position,
                default_contact_phone=self.phone,
                default_contact_mobile=self.mobile,
                default_contact_email=self.email
            )

@receiver(post_save, sender=Address)
def ensure_single_default_address(sender, instance, **kwargs):
    if instance.is_default:
        # Unset other defaults of the same type
        Address.objects.filter(
            business_partner=instance.business_partner,
            address_type=instance.address_type,
            is_default=True
        ).exclude(pk=instance.pk).update(is_default=False)

@receiver(post_save, sender=ContactPerson)
def ensure_single_default_contact(sender, instance, **kwargs):
    if instance.is_default:
        # Unset other defaults
        ContactPerson.objects.filter(
            business_partner=instance.business_partner,
            is_default=True
        ).exclude(pk=instance.pk).update(is_default=False)