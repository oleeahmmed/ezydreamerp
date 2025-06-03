from django.contrib import admin
from .models import BusinessPartner, BusinessPartnerGroup

# Register BusinessPartner model
@admin.register(BusinessPartner)
class BusinessPartnerAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'bp_type', 'active', 'group', 'currency', 'credit_limit', 'balance')
    list_filter = ('bp_type', 'active', 'group')
    search_fields = ('code', 'name', 'email', 'phone')
    ordering = ('code',)
    fields = ('code', 'name', 'bp_type', 'group', 'currency', 'active', 'credit_limit', 'balance', 'payment_terms', 'phone', 'mobile', 'email', 'website', 'latitude', 'longitude', 'google_place_id')

# Register BusinessPartnerGroup model if you want to manage groups in the admin
@admin.register(BusinessPartnerGroup)
class BusinessPartnerGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
