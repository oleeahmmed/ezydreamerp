# BusinessPartnerMasterData/api/serializers.py
from rest_framework import serializers
from ..models import (
    BusinessPartner, 
    BusinessPartnerGroup,
    FinancialInformation,
    ContactInformation,
    Address,
    ContactPerson
)

class BusinessPartnerGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessPartnerGroup
        fields = ['id', 'name', 'description']

class AddressSerializer(serializers.ModelSerializer):
    address_type_display = serializers.CharField(source='get_address_type_display', read_only=True)
    
    class Meta:
        model = Address
        fields = [
            'id', 'business_partner', 'address_type', 'address_type_display',
            'street', 'city', 'state', 'zip_code', 'country', 'is_default'
        ]

class ContactPersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactPerson
        fields = [
            'id', 'business_partner', 'name', 'position', 
            'phone', 'mobile', 'email', 'is_default'
        ]

class FinancialInformationSerializer(serializers.ModelSerializer):
    payment_terms_name = serializers.CharField(source='payment_terms.name', read_only=True)
    
    class Meta:
        model = FinancialInformation
        fields = [
            'id', 'business_partner', 'credit_limit', 'balance', 
            'payment_terms', 'payment_terms_name'
        ]

class ContactInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInformation
        fields = [
            'id', 'business_partner', 'phone', 'mobile', 
            'email', 'website', 'federal_tax_id'
        ]

class BusinessPartnerListSerializer(serializers.ModelSerializer):
    """Serializer for list view with limited fields"""
    group_name = serializers.CharField(source='group.name', read_only=True)
    bp_type_display = serializers.CharField(source='get_bp_type_display', read_only=True)
    
    class Meta:
        model = BusinessPartner
        fields = [
            'id', 'code', 'name', 'bp_type', 'bp_type_display',
            'group', 'group_name', 'active', 'phone', 'email','latitude','longitude', 'google_place_id'
        ]

class BusinessPartnerDetailSerializer(serializers.ModelSerializer):
    """Serializer for detail view with all fields and related data"""
    group_name = serializers.CharField(source='group.name', read_only=True)
    bp_type_display = serializers.CharField(source='get_bp_type_display', read_only=True)
    currency_name = serializers.CharField(source='currency.name', read_only=True)
    payment_terms_name = serializers.CharField(source='payment_terms.name', read_only=True)
    addresses = AddressSerializer(many=True, read_only=True)
    contact_persons = ContactPersonSerializer(many=True, read_only=True)
    
    class Meta:
        model = BusinessPartner
        fields = [
            'id', 'code', 'name', 'bp_type', 'bp_type_display', 'group', 'group_name',
            'currency', 'currency_name', 'active', 'credit_limit', 'balance',
            'payment_terms', 'payment_terms_name', 'phone', 'mobile', 'email',
            'website', 'federal_tax_id', 'default_billing_street', 'default_billing_city',
            'default_billing_state', 'default_billing_zip_code', 'default_billing_country',
            'default_shipping_street', 'default_shipping_city', 'default_shipping_state',
            'default_shipping_zip_code', 'default_shipping_country', 'default_contact_name',
            'default_contact_position', 'default_contact_phone', 'default_contact_mobile',
            'default_contact_email', 'addresses', 'contact_persons','latitude','longitude', 'google_place_id'
        ]

class BusinessPartnerCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessPartner
        fields = [
            'code', 'name', 'bp_type', 'group', 'currency', 'active',
            'credit_limit', 'balance', 'payment_terms', 'phone', 'mobile',
            'email', 'website', 'federal_tax_id', 'default_billing_street',
            'default_billing_city', 'default_billing_state', 'default_billing_zip_code',
            'default_billing_country', 'default_shipping_street', 'default_shipping_city',
            'default_shipping_state', 'default_shipping_zip_code', 'default_shipping_country',
            'default_contact_name', 'default_contact_position', 'default_contact_phone',
            'default_contact_mobile', 'default_contact_email', 'latitude','longitude', 'google_place_id'
        ]