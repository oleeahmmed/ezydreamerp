from django.db import models
from global_settings.models import Currency
from BusinessPartnerMasterData.models import BusinessPartner
from django.utils import timezone
import datetime
from django.utils.translation import gettext_lazy as _

class BaseModel(models.Model):
    """Base model with common fields for all models."""
    created_at = models.DateTimeField(_("Created At"), default=timezone.now)
    updated_at = models.DateTimeField(_("Updated At"), default=timezone.now)
    
    class Meta:
        abstract = True
        verbose_name = _("Base Model")
        verbose_name_plural = _("Base Models")

class AccountType(BaseModel):
    code = models.CharField(_("Code"), max_length=10, unique=True)
    name = models.CharField(_("Name"), max_length=100)
    is_debit = models.BooleanField(_("Is Debit"), default=True)

    class Meta:
        verbose_name = _("Account Type")
        verbose_name_plural = _("Account Types")

    def __str__(self):
        return f"{self.code} - {self.name}"

class ChartOfAccounts(BaseModel):
    code = models.CharField(_("Code"), max_length=20, unique=True)
    name = models.CharField(_("Name"), max_length=100)
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT, verbose_name=_("Account Type"))
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name=_("Parent Account"))
    is_active = models.BooleanField(_("Is Active"), default=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name=_("Currency"))

    class Meta:
        verbose_name = _("Chart of Accounts")
        verbose_name_plural = _("Chart of Accounts")

    def __str__(self):
        return f"{self.code} - {self.name}"

class JournalEntry(BaseModel):
    doc_num = models.CharField(_("Document Number"), max_length=20, unique=True)
    posting_date = models.DateField(_("Posting Date"))
    reference = models.CharField(_("Reference"), max_length=100, blank=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    is_posted = models.BooleanField(_("Is Posted"), default=False)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name=_("Currency"))
    total_debit = models.DecimalField(_("Total Debit"), max_digits=15, decimal_places=2, default=0)
    total_credit = models.DecimalField(_("Total Credit"), max_digits=15, decimal_places=2, default=0)
    cost_center = models.ForeignKey('CostCenter', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Cost Center"))

    class Meta:
        verbose_name = _("Journal Entry")
        verbose_name_plural = _("Journal Entries")

    def __str__(self):
        return f"JE-{self.doc_num}"

class JournalEntryLine(BaseModel):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines', verbose_name=_("Journal Entry"))
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.PROTECT, verbose_name=_("Account"))
    debit_amount = models.DecimalField(_("Debit Amount"), max_digits=15, decimal_places=2, default=0)
    credit_amount = models.DecimalField(_("Credit Amount"), max_digits=15, decimal_places=2, default=0)
    description = models.CharField(_("Description"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Journal Entry Line")
        verbose_name_plural = _("Journal Entry Lines")

    def __str__(self):
        return f"JE-{self.journal_entry.doc_num} - {self.account.code}"

class GeneralLedger(BaseModel):
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.PROTECT, verbose_name=_("Account"))
    posting_date = models.DateField(_("Posting Date"))
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, verbose_name=_("Journal Entry")) 
    debit_amount = models.DecimalField(_("Debit Amount"), max_digits=15, decimal_places=2, default=0)
    credit_amount = models.DecimalField(_("Credit Amount"), max_digits=15, decimal_places=2, default=0)
    balance = models.DecimalField(_("Balance"), max_digits=15, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name=_("Currency"))
    cost_center = models.ForeignKey('CostCenter', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Cost Center"))

    class Meta:
        verbose_name = _("General Ledger")
        verbose_name_plural = _("General Ledger")

    def __str__(self):
        return f"{self.account.code} - {self.posting_date}"

class CostCenter(BaseModel):
    """Cost centers for cost accounting"""
    code = models.CharField(_("Code"), max_length=20, unique=True)
    name = models.CharField(_("Name"), max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name=_("Parent Cost Center"))
    is_active = models.BooleanField(_("Is Active"), default=True)
    
    class Meta:
        verbose_name = _("Cost Center")
        verbose_name_plural = _("Cost Centers")

    def __str__(self):
        return f"{self.code} - {self.name}"