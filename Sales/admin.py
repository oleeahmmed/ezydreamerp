from django.contrib import admin
from .models import (
    SalesEmployee,
    SalesQuotation, SalesQuotationLine,
    SalesOrder, SalesOrderLine,
    Delivery, DeliveryLine,
    Return, ReturnLine,
    ARInvoice, ARInvoiceLine
)

@admin.register(SalesEmployee)
class SalesEmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'department', 'email', 'phone')
    search_fields = ('name', 'email', 'phone', 'user__username')

class SalesQuotationLineInline(admin.TabularInline):
    model = SalesQuotationLine
    extra = 0

@admin.register(SalesQuotation)
class SalesQuotationAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'document_date', 'status', 'payable_amount', 'paid_amount', 'due_amount')
    search_fields = ('customer__name',)
    inlines = [SalesQuotationLineInline]

class SalesOrderLineInline(admin.TabularInline):
    model = SalesOrderLine
    extra = 0

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'document_date', 'status', 'payable_amount', 'paid_amount', 'due_amount')
    search_fields = ('customer__name',)
    inlines = [SalesOrderLineInline]

class DeliveryLineInline(admin.TabularInline):
    model = DeliveryLine
    extra = 0

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'document_date', 'status', 'delivery_method', 'driver_name')
    search_fields = ('customer__name',)
    inlines = [DeliveryLineInline]

class ReturnLineInline(admin.TabularInline):
    model = ReturnLine
    extra = 0

@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'document_date', 'status', 'return_reason')
    search_fields = ('customer__name',)
    inlines = [ReturnLineInline]

class ARInvoiceLineInline(admin.TabularInline):
    model = ARInvoiceLine
    extra = 0

@admin.register(ARInvoice)
class ARInvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'document_date', 'status', 'payable_amount', 'paid_amount', 'due_amount')
    search_fields = ('customer__name',)
    inlines = [ARInvoiceLineInline]
