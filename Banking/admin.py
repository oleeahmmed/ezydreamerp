# Banking/admin.py
from django.contrib import admin
from .models import PaymentMethod, Payment, PaymentLine # আপনার মডেলগুলি আমদানি করুন

# PaymentMethod মডেল নিবন্ধন করুন
@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('created_at', 'updated_at')

# Payment মডেল নিবন্ধন করুন
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('doc_num', 'business_partner', 'payment_type', 'amount', 'currency', 'payment_date', 'payment_method', 'sales_order', 'is_reconciled')
    search_fields = ('doc_num', 'business_partner__name', 'reference')
    list_filter = ('payment_type', 'payment_date', 'payment_method', 'is_reconciled', 'currency')
    raw_id_fields = ('business_partner', 'currency', 'payment_method', 'sales_order') # ForeignKey fields for better handling in admin
    readonly_fields = ('created_at', 'updated_at') # Add read-only fields
    fieldsets = (
        (None, {
            'fields': ('doc_num', 'business_partner', 'payment_type', 'amount', 'currency', 'payment_date', 'payment_method', 'sales_order'),
        }),
        ('Additional Information', {
            'fields': ('reference', 'remarks', 'is_reconciled'),
            'classes': ('collapse',), # You can collapse this section
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

# PaymentLine মডেল নিবন্ধন করুন
@admin.register(PaymentLine)
class PaymentLineAdmin(admin.ModelAdmin):
    list_display = ('payment', 'account', 'amount', 'description', 'created_at', 'updated_at')
    search_fields = ('payment__doc_num', 'account__name', 'description')
    list_filter = ('account', 'created_at', 'updated_at')
    raw_id_fields = ('payment', 'account') # ForeignKey fields for better handling in admin
    readonly_fields = ('created_at', 'updated_at')