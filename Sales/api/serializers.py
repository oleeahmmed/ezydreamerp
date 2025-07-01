# Sales/api/serializers.py
from rest_framework import serializers
from ..models import (
    SalesEmployee,
    SalesQuotation, SalesQuotationLine,
    SalesOrder, SalesOrderLine,
    Delivery, DeliveryLine,
    Return, ReturnLine,
    ARInvoice, ARInvoiceLine
)
from django.utils import timezone

import datetime
class SalesEmployeeSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = SalesEmployee
        fields = [
            'id', 'user', 'user_username', 'name', 'position', 
            'department', 'phone', 'email', 'notes', 'is_active'
        ]

# Sales Quotation Serializers
class SalesQuotationLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesQuotationLine
        fields = [
            'id', 'quotation', 'item_code', 'item_name', 'quantity',
            'unit_price', 'total_amount', 'uom', 'remarks', 'is_active'
        ]

class SalesQuotationListSerializer(serializers.ModelSerializer):
    """Serializer for list view with limited fields"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    sales_employee_name = serializers.CharField(source='sales_employee.name', read_only=True)
    
    class Meta:
        model = SalesQuotation
        fields = [
            'id', 'document_date', 'valid_until', 'customer', 'customer_name',
            'sales_employee', 'sales_employee_name', 'status', 'total_amount', 'is_active'
        ]

class SalesQuotationDetailSerializer(serializers.ModelSerializer):
    """Serializer for detail view with all fields and related data"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    contact_person_name = serializers.CharField(source='contact_person.name', read_only=True)
    billing_address_display = serializers.SerializerMethodField()
    shipping_address_display = serializers.SerializerMethodField()
    currency_name = serializers.CharField(source='currency.name', read_only=True)
    payment_terms_name = serializers.CharField(source='payment_terms.name', read_only=True)
    sales_employee_name = serializers.CharField(source='sales_employee.name', read_only=True)
    lines = SalesQuotationLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = SalesQuotation
        fields = [
            'id', 'document_date', 'valid_until', 'customer', 'customer_name',
            'contact_person', 'contact_person_name', 'billing_address', 'billing_address_display',
            'shipping_address', 'shipping_address_display', 'currency', 'currency_name',
            'payment_terms', 'payment_terms_name', 'discount_amount', 'tax_amount',
            'total_amount', 'payable_amount', 'paid_amount', 'due_amount',
            'payment_method', 'payment_reference', 'payment_date', 'remarks',
            'status', 'sales_employee', 'sales_employee_name', 'created_at',
            'updated_at', 'is_active', 'lines'
        ]
    
    def get_billing_address_display(self, obj):
        if obj.billing_address:
            addr = obj.billing_address
            return f"{addr.street}, {addr.city}, {addr.state}, {addr.zip_code}, {addr.country}"
        return ""
    
    def get_shipping_address_display(self, obj):
        if obj.shipping_address:
            addr = obj.shipping_address
            return f"{addr.street}, {addr.city}, {addr.state}, {addr.zip_code}, {addr.country}"
        return ""

class SalesQuotationCreateUpdateSerializer(serializers.ModelSerializer):
    lines = SalesQuotationLineSerializer(many=True)
    
    class Meta:
        model = SalesQuotation
        fields = [
            'document_date', 'valid_until', 'customer', 'contact_person',
            'billing_address', 'shipping_address', 'currency', 'payment_terms',
            'discount_amount', 'tax_amount', 'remarks', 'status',
            'sales_employee', 'lines'
        ]
    
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        quotation = SalesQuotation.objects.create(**validated_data)
        
        # Calculate total amount from lines
        total_amount = 0
        
        for line_data in lines_data:
            line = SalesQuotationLine.objects.create(quotation=quotation, **line_data)
            total_amount += line.total_amount
        
        # Update quotation with calculated values
        quotation.total_amount = total_amount
        quotation.payable_amount = total_amount - quotation.discount_amount
        quotation.due_amount = quotation.payable_amount - quotation.paid_amount
        quotation.save()
        
        return quotation
    
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        
        # Update quotation fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if lines_data is not None:
            # Delete existing lines
            instance.lines.all().delete()
            
            # Create new lines
            total_amount = 0
            for line_data in lines_data:
                line = SalesQuotationLine.objects.create(quotation=instance, **line_data)
                total_amount += line.total_amount
            
            # Update quotation with calculated values
            instance.total_amount = total_amount
            instance.payable_amount = total_amount - instance.discount_amount
            instance.due_amount = instance.payable_amount - instance.paid_amount
        
        instance.save()
        return instance

# Sales Order Serializers
class SalesOrderLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesOrderLine
        fields = [
            'id', 'order', 'item_code', 'item_name', 'quantity',
            'unit_price', 'total_amount', 'uom', 'remarks'
        ]

        extra_kwargs = {
            'order': {'required': False},  # Make order field not required
        }

class SalesOrderListSerializer(serializers.ModelSerializer):
    """Serializer for list view with limited fields"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    sales_employee_name = serializers.CharField(source='sales_employee.name', read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'document_date', 'delivery_date', 'customer', 'customer_name',
            'sales_employee', 'sales_employee_name', 'status', 'total_amount', 'is_active'
        ]



class SalesOrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for detail view with all fields and related data"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    contact_person_name = serializers.CharField(source='contact_person.name', read_only=True)
    billing_address_display = serializers.SerializerMethodField()
    shipping_address_display = serializers.SerializerMethodField()
    currency_name = serializers.CharField(source='currency.name', read_only=True)
    payment_terms_name = serializers.CharField(source='payment_terms.name', read_only=True)
    sales_employee_name = serializers.CharField(source='sales_employee.name', read_only=True)
    sales_employee_phone = serializers.CharField(source='sales_employee.phone', read_only=True)    
    lines = SalesOrderLineSerializer(many=True, read_only=True)

    # BusinessPartner fields
    customer_latitude = serializers.DecimalField(source='customer.latitude', max_digits=13, decimal_places=10, read_only=True)
    customer_longitude = serializers.DecimalField(source='customer.longitude', max_digits=13, decimal_places=10, read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    customer_mobile = serializers.CharField(source='customer.mobile', read_only=True)
    customer_email = serializers.EmailField(source='customer.email', read_only=True)

    class Meta:
        model = SalesOrder
        fields = [
            'id', 'document_date', 'delivery_date', 'customer', 'customer_name',
            'contact_person', 'contact_person_name', 'billing_address', 'billing_address_display',
            'shipping_address', 'shipping_address_display', 'currency', 'currency_name',
            'payment_terms', 'payment_terms_name', 'discount_amount', 'tax_amount',
            'total_amount', 'payable_amount', 'paid_amount', 'due_amount',
            'payment_method', 'payment_reference', 'payment_date', 'remarks',
            'status', 'sales_employee', 'sales_employee_name', 'created_at',
            'updated_at', 'is_active', 'lines',
            'customer_latitude', 'customer_longitude', 'customer_phone',
            'customer_mobile', 'customer_email','sales_employee_phone'
        ]
    def get_billing_address_display(self, obj):
        if obj.billing_address:
            addr = obj.billing_address
            return f"{addr.street}, {addr.city}, {addr.state}, {addr.zip_code}, {addr.country}"
        return ""
    
    def get_shipping_address_display(self, obj):
        if obj.shipping_address:
            addr = obj.shipping_address
            return f"{addr.street}, {addr.city}, {addr.state}, {addr.zip_code}, {addr.country}"
        return ""

class SalesOrderCreateUpdateSerializer(serializers.ModelSerializer):
    lines = SalesOrderLineSerializer(many=True)
    
    class Meta:
        model = SalesOrder
        fields = [
            'document_date', 'delivery_date', 'customer', 'contact_person',
            'billing_address', 'shipping_address', 'currency', 'payment_terms',
            'discount_amount', 'tax_amount', 'remarks', 'status',
            'sales_employee', 'lines'
        ]
    
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        order = SalesOrder.objects.create(**validated_data)
        
        # Calculate total amount from lines
        total_amount = 0
        
        for line_data in lines_data:
            line = SalesOrderLine.objects.create(order=order, **line_data)
            total_amount += line.total_amount
        
        # Update order with calculated values
        order.total_amount = total_amount
        order.payable_amount = total_amount - order.discount_amount
        order.due_amount = order.payable_amount - order.paid_amount
        order.save()
        
        return order
    
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        
        # Update order fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if lines_data is not None:
            # Delete existing lines
            instance.lines.all().delete()
            
            # Create new lines
            total_amount = 0
            for line_data in lines_data:
                line = SalesOrderLine.objects.create(order=instance, **line_data)
                total_amount += line.total_amount
            
            # Update order with calculated values
            instance.total_amount = total_amount
            instance.payable_amount = total_amount - instance.discount_amount
            instance.due_amount = instance.payable_amount - instance.paid_amount
        
        instance.save()
        return instance

# Delivery Serializers
class DeliveryLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryLine
        fields = [
            'id', 'delivery', 'sales_order_line', 'item_code', 'item_name', 
            'quantity', 'unit_price', 'total_amount', 'uom', 'remarks', 'is_active'
        ]

class DeliveryListSerializer(serializers.ModelSerializer):
    """Serializer for list view with limited fields"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    sales_employee_name = serializers.CharField(source='sales_employee.name', read_only=True)
    
    class Meta:
        model = Delivery
        fields = [
            'id', 'document_date', 'posting_date', 'customer', 'customer_name',
            'sales_order', 'sales_employee', 'sales_employee_name', 
            'status', 'total_amount', 'is_active'
        ]

class DeliveryDetailSerializer(serializers.ModelSerializer):
    """Serializer for detail view with all fields and related data"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    contact_person_name = serializers.CharField(source='contact_person.name', read_only=True)
    shipping_address_display = serializers.SerializerMethodField()
    currency_name = serializers.CharField(source='currency.name', read_only=True)
    payment_terms_name = serializers.CharField(source='payment_terms.name', read_only=True)
    sales_employee_name = serializers.CharField(source='sales_employee.name', read_only=True)
    lines = DeliveryLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = Delivery
        fields = [
            'id', 'document_date', 'posting_date', 'customer', 'customer_name',
            'contact_person', 'contact_person_name', 'shipping_address', 'shipping_address_display',
            'sales_order', 'currency', 'currency_name', 'payment_terms', 'payment_terms_name',
            'discount_amount', 'tax_amount', 'total_amount', 'payable_amount',
            'paid_amount', 'due_amount', 'payment_method', 'payment_reference',
            'payment_date', 'remarks', 'status', 'sales_employee', 'sales_employee_name',
            'deliveryemployee', 'created_at', 'updated_at', 'is_active', 'lines'
        ]
    
    def get_shipping_address_display(self, obj):
        if obj.shipping_address:
            addr = obj.shipping_address
            return f"{addr.street}, {addr.city}, {addr.state}, {addr.zip_code}, {addr.country}"
        return ""

class DeliveryCreateUpdateSerializer(serializers.ModelSerializer):
    lines = DeliveryLineSerializer(many=True)
    
    class Meta:
        model = Delivery
        fields = [
            'document_date', 'posting_date', 'customer', 'contact_person',
            'shipping_address', 'sales_order', 'currency', 'payment_terms',
            'discount_amount', 'tax_amount', 'remarks', 'status',
            'sales_employee', 'deliveryemployee', 'lines'
        ]
    
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        delivery = Delivery.objects.create(**validated_data)
        
        # Calculate total amount from lines
        total_amount = 0
        
        for line_data in lines_data:
            line = DeliveryLine.objects.create(delivery=delivery, **line_data)
            total_amount += line.total_amount
        
        # Update delivery with calculated values
        delivery.total_amount = total_amount
        delivery.payable_amount = total_amount - delivery.discount_amount
        delivery.due_amount = delivery.payable_amount - delivery.paid_amount
        delivery.save()
        
        return delivery
    
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        
        # Update delivery fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if lines_data is not None:
            # Delete existing lines
            instance.lines.all().delete()
            
            # Create new lines
            total_amount = 0
            for line_data in lines_data:
                line = DeliveryLine.objects.create(delivery=instance, **line_data)
                total_amount += line.total_amount
            
            # Update delivery with calculated values
            instance.total_amount = total_amount
            instance.payable_amount = total_amount - instance.discount_amount
            instance.due_amount = instance.payable_amount - instance.paid_amount
        
        instance.save()
        return instance

# Return Serializers
class ReturnLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnLine
        fields = [
            'id', 'return_doc', 'delivery_line', 'item_code', 'item_name', 
            'quantity', 'unit_price', 'total_amount', 'uom', 'remarks', 'is_active'
        ]

class ReturnListSerializer(serializers.ModelSerializer):
    """Serializer for list view with limited fields"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    sales_employee_name = serializers.CharField(source='sales_employee.name', read_only=True)
    
    class Meta:
        model = Return
        fields = [
            'id', 'document_date', 'posting_date', 'customer', 'customer_name',
            'delivery', 'sales_employee', 'sales_employee_name', 
            'status', 'total_amount', 'is_active'
        ]

class ReturnDetailSerializer(serializers.ModelSerializer):
    """Serializer for detail view with all fields and related data"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    contact_person_name = serializers.CharField(source='contact_person.name', read_only=True)
    return_address_display = serializers.SerializerMethodField()
    currency_name = serializers.CharField(source='currency.name', read_only=True)
    payment_terms_name = serializers.CharField(source='payment_terms.name', read_only=True)
    sales_employee_name = serializers.CharField(source='sales_employee.name', read_only=True)
    lines = ReturnLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = Return
        fields = [
            'id', 'document_date', 'posting_date', 'customer', 'customer_name',
            'contact_person', 'contact_person_name', 'return_address', 'return_address_display',
            'delivery', 'currency', 'currency_name', 'payment_terms', 'payment_terms_name',
            'discount_amount', 'tax_amount', 'total_amount', 'payable_amount',
            'paid_amount', 'due_amount', 'payment_method', 'payment_reference',
            'payment_date', 'return_reason', 'remarks', 'status', 'sales_employee', 
            'sales_employee_name', 'created_at', 'updated_at', 'is_active', 'lines'
        ]
    
    def get_return_address_display(self, obj):
        if obj.return_address:
            addr = obj.return_address
            return f"{addr.street}, {addr.city}, {addr.state}, {addr.zip_code}, {addr.country}"
        return ""

class ReturnCreateUpdateSerializer(serializers.ModelSerializer):
    lines = ReturnLineSerializer(many=True)
    
    class Meta:
        model = Return
        fields = [
            'document_date', 'posting_date', 'customer', 'contact_person',
            'return_address', 'delivery', 'currency', 'payment_terms',
            'discount_amount', 'tax_amount', 'return_reason', 'remarks', 'status',
            'sales_employee', 'lines'
        ]
    
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        return_doc = Return.objects.create(**validated_data)
        
        # Calculate total amount from lines
        total_amount = 0
        
        for line_data in lines_data:
            line = ReturnLine.objects.create(return_doc=return_doc, **line_data)
            total_amount += line.total_amount
        
        # Update return with calculated values
        return_doc.total_amount = total_amount
        return_doc.payable_amount = total_amount - return_doc.discount_amount
        return_doc.due_amount = return_doc.payable_amount - return_doc.paid_amount
        return_doc.save()
        
        return return_doc
    
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        
        # Update return fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if lines_data is not None:
            # Delete existing lines
            instance.lines.all().delete()
            
            # Create new lines
            total_amount = 0
            for line_data in lines_data:
                line = ReturnLine.objects.create(return_doc=instance, **line_data)
                total_amount += line.total_amount
            
            # Update return with calculated values
            instance.total_amount = total_amount
            instance.payable_amount = total_amount - instance.discount_amount
            instance.due_amount = instance.payable_amount - instance.paid_amount
        
        instance.save()
        return instance

# AR Invoice Serializers
class ARInvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = ARInvoiceLine
        fields = [
            'id', 'invoice', 'sales_order_line', 'delivery_line', 'item_code', 
            'item_name', 'quantity', 'unit_price', 'total_amount', 'uom', 
            'remarks', 'is_active'
        ]

class ARInvoiceListSerializer(serializers.ModelSerializer):
    """Serializer for list view with limited fields"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    sales_employee_name = serializers.CharField(source='sales_employee.name', read_only=True)
    
    class Meta:
        model = ARInvoice
        fields = [
            'id', 'document_date', 'posting_date', 'due_date', 'customer', 'customer_name',
            'sales_order', 'delivery', 'sales_employee', 'sales_employee_name', 
            'status', 'total_amount', 'is_active'
        ]

class ARInvoiceDetailSerializer(serializers.ModelSerializer):
    """Serializer for detail view with all fields and related data"""
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    contact_person_name = serializers.CharField(source='contact_person.name', read_only=True)
    billing_address_display = serializers.SerializerMethodField()
    currency_name = serializers.CharField(source='currency.name', read_only=True)
    payment_terms_name = serializers.CharField(source='payment_terms.name', read_only=True)
    sales_employee_name = serializers.CharField(source='sales_employee.name', read_only=True)
    lines = ARInvoiceLineSerializer(many=True, read_only=True)
    
    class Meta:
        model = ARInvoice
        fields = [
            'id', 'document_date', 'posting_date', 'due_date', 'customer', 'customer_name',
            'contact_person', 'contact_person_name', 'billing_address', 'billing_address_display',
            'sales_order', 'delivery', 'currency', 'currency_name', 'payment_terms', 'payment_terms_name',
            'discount_amount', 'tax_amount', 'total_amount', 'payable_amount',
            'paid_amount', 'due_amount', 'payment_method', 'payment_reference',
            'payment_date', 'remarks', 'status', 'sales_employee', 'sales_employee_name',
            'created_at', 'updated_at', 'is_active', 'lines'
        ]
    
    def get_billing_address_display(self, obj):
        if obj.billing_address:
            addr = obj.billing_address
            return f"{addr.street}, {addr.city}, {addr.state}, {addr.zip_code}, {addr.country}"
        return ""

class ARInvoiceCreateUpdateSerializer(serializers.ModelSerializer):
    lines = ARInvoiceLineSerializer(many=True)
    
    class Meta:
        model = ARInvoice
        fields = [
            'document_date', 'posting_date', 'due_date', 'customer', 'contact_person',
            'billing_address', 'sales_order', 'delivery', 'currency', 'payment_terms',
            'discount_amount', 'tax_amount', 'remarks', 'status',
            'sales_employee', 'lines'
        ]
    
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        invoice = ARInvoice.objects.create(**validated_data)
        
        # Calculate total amount from lines
        total_amount = 0
        
        for line_data in lines_data:
            line = ARInvoiceLine.objects.create(invoice=invoice, **line_data)
            total_amount += line.total_amount
        
        # Update invoice with calculated values
        invoice.total_amount = total_amount
        invoice.payable_amount = total_amount - invoice.discount_amount
        invoice.due_amount = invoice.payable_amount - invoice.paid_amount
        invoice.save()
        
        return invoice
    
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        
        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if lines_data is not None:
            # Delete existing lines
            instance.lines.all().delete()
            
            # Create new lines
            total_amount = 0
            for line_data in lines_data:
                line = ARInvoiceLine.objects.create(invoice=instance, **line_data)
                total_amount += line.total_amount
            
            # Update invoice with calculated values
            instance.total_amount = total_amount
            instance.payable_amount = total_amount - instance.discount_amount
            instance.due_amount = instance.payable_amount - instance.paid_amount
        
        instance.save()
        return instance
    
    

# Add this to your existing serializers.py file

class SalesOrderToDeliverySerializer(serializers.Serializer):
    """
    Serializer for converting a sales order to a delivery.
    Only requires the sales_order_id to perform the conversion.
    """
    sales_order_id = serializers.IntegerField()
    
    def validate_sales_order_id(self, value):
        """
        Validate that the sales order exists and can be converted to a delivery.
        """
        try:
            order = SalesOrder.objects.get(pk=value)
            
            # Check if order can be converted
            if order.status in ['Cancelled', 'Closed']:
                raise serializers.ValidationError(
                    f"Sales Order {order.pk} cannot be converted because it is {order.status}."
                )
                
            # Check if there are any items left to deliver
            delivered_quantities = {}
            for delivery in order.deliveries.all():
                for line in delivery.lines.all():
                    key = (line.item_code, line.uom)
                    delivered_quantities[key] = delivered_quantities.get(key, 0) + line.quantity
            
            any_to_deliver = False
            for o_line in order.lines.all():
                key = (o_line.item_code, o_line.uom)
                already_delivered = delivered_quantities.get(key, 0)
                remaining_qty = o_line.quantity - already_delivered
                if remaining_qty > 0:
                    any_to_deliver = True
                    break
            
            if not any_to_deliver:
                raise serializers.ValidationError(
                    f"All items in Sales Order {order.pk} have already been delivered."
                )
                
            return value
        except SalesOrder.DoesNotExist:
            raise serializers.ValidationError("Sales Order does not exist.")
    
    def create(self, validated_data):
        """
        Create a delivery from a sales order.
        """
        sales_order_id = validated_data.get('sales_order_id')
        order = SalesOrder.objects.get(pk=sales_order_id)
        
        # Calculate delivered quantities
        delivered_quantities = {}
        for delivery in order.deliveries.all():
            for line in delivery.lines.all():
                key = (line.item_code, line.uom)
                delivered_quantities[key] = delivered_quantities.get(key, 0) + line.quantity
        
        # Create delivery
        delivery = Delivery.objects.create(
            document_date=timezone.now().date(),
            posting_date=timezone.now().date(),
            customer=order.customer,
            contact_person=order.contact_person,
            shipping_address=order.shipping_address,
            sales_order=order,
            currency=order.currency,
            payment_terms=order.payment_terms,
            discount_amount=order.discount_amount,
            remarks=f"Delivery for Sales Order #{order.pk}",
            sales_employee=order.sales_employee,
            status='Open',
            paid_amount=order.paid_amount,
            payment_method=order.payment_method,
            payment_reference=order.payment_reference,
            payment_date=order.payment_date
        )
        
        # Create delivery lines from order lines for remaining quantities
        total_delivery_amount = 0
        
        for o_line in order.lines.all():
            key = (o_line.item_code, o_line.uom)
            already_delivered = delivered_quantities.get(key, 0)
            remaining_qty = o_line.quantity - already_delivered
            
            if remaining_qty > 0:
                delivery_line = DeliveryLine.objects.create(
                    delivery=delivery,
                    sales_order_line=o_line,
                    item_code=o_line.item_code,
                    item_name=o_line.item_name,
                    quantity=remaining_qty,
                    unit_price=o_line.unit_price,
                    uom=o_line.uom,
                    remarks=o_line.remarks,
                    is_active=True
                )
                total_delivery_amount += delivery_line.quantity * delivery_line.unit_price
        
        # Update delivery total amount and calculate payable and due amounts
        delivery.total_amount = total_delivery_amount
        delivery.payable_amount = delivery.total_amount - delivery.discount_amount
        delivery.due_amount = delivery.payable_amount - delivery.paid_amount
        delivery.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])
        
        # Update order status
        all_delivered = True
        for o_line in order.lines.all():
            key = (o_line.item_code, o_line.uom)
            already_delivered = delivered_quantities.get(key, 0) + remaining_qty
            if already_delivered < o_line.quantity:
                all_delivered = False
                break
        
        order.status = 'Delivered' if all_delivered else 'Partially Delivered'
        order.save(update_fields=['status'])
        
        return delivery


class DeliveryToReturnSerializer(serializers.Serializer):
    """
    Serializer for converting a delivery to a return.
    Only requires the delivery_id to perform the conversion.
    """
    delivery_id = serializers.IntegerField()
    return_reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_delivery_id(self, value):
        """
        Validate that the delivery exists and can be converted to a return.
        """
        try:
            delivery = Delivery.objects.get(pk=value)
            
            # Check if delivery can be converted
            if delivery.status in ['Cancelled', 'Closed']:
                raise serializers.ValidationError(
                    f"Delivery {delivery.pk} cannot be converted because it is {delivery.status}."
                )
                
            # Check if there are any items left to return
            returned_quantities = {}
            for return_doc in Return.objects.filter(delivery=delivery):
                for line in return_doc.lines.all():
                    key = (line.item_code, line.uom)
                    returned_quantities[key] = returned_quantities.get(key, 0) + line.quantity
            
            any_to_return = False
            for d_line in delivery.lines.all():
                key = (d_line.item_code, d_line.uom)
                already_returned = returned_quantities.get(key, 0)
                remaining_qty = d_line.quantity - already_returned
                if remaining_qty > 0:
                    any_to_return = True
                    break
            
            if not any_to_return:
                raise serializers.ValidationError(
                    f"All items in Delivery {delivery.pk} have already been returned."
                )
                
            return value
        except Delivery.DoesNotExist:
            raise serializers.ValidationError("Delivery does not exist.")
    
    def create(self, validated_data):
        """
        Create a return from a delivery.
        """
        delivery_id = validated_data.get('delivery_id')
        return_reason = validated_data.get('return_reason', '')
        delivery = Delivery.objects.get(pk=delivery_id)
        
        # Calculate returned quantities
        returned_quantities = {}
        for return_doc in Return.objects.filter(delivery=delivery):
            for line in return_doc.lines.all():
                key = (line.item_code, line.uom)
                returned_quantities[key] = returned_quantities.get(key, 0) + line.quantity
        
        # Create return
        return_doc = Return.objects.create(
            document_date=timezone.now().date(),
            posting_date=timezone.now().date(),
            customer=delivery.customer,
            contact_person=delivery.contact_person,
            return_address=delivery.shipping_address,
            delivery=delivery,
            currency=delivery.currency,
            payment_terms=delivery.payment_terms,
            discount_amount=delivery.discount_amount,
            return_reason=return_reason,
            remarks=f"Return for Delivery #{delivery.pk}",
            sales_employee=delivery.sales_employee,
            status='Open',
            paid_amount=delivery.paid_amount,
            payment_method=delivery.payment_method,
            payment_reference=delivery.payment_reference,
            payment_date=delivery.payment_date
        )
        
        # Create return lines from delivery lines for remaining quantities
        total_return_amount = 0
        
        for d_line in delivery.lines.all():
            key = (d_line.item_code, d_line.uom)
            already_returned = returned_quantities.get(key, 0)
            remaining_qty = d_line.quantity - already_returned
            
            if remaining_qty > 0:
                return_line = ReturnLine.objects.create(
                    return_doc=return_doc,
                    delivery_line=d_line,
                    item_code=d_line.item_code,
                    item_name=d_line.item_name,
                    quantity=remaining_qty,
                    unit_price=d_line.unit_price,
                    uom=d_line.uom,
                    remarks=d_line.remarks,
                    is_active=True
                )
                total_return_amount += return_line.quantity * return_line.unit_price
        
        # Update return total amount and calculate payable and due amounts
        return_doc.total_amount = total_return_amount
        return_doc.payable_amount = return_doc.total_amount - return_doc.discount_amount
        return_doc.due_amount = return_doc.payable_amount - return_doc.paid_amount
        return_doc.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])
        
        return return_doc        


class DeliveryToARInvoiceSerializer(serializers.Serializer):
    """
    Serializer for converting a delivery to an AR Invoice.
    Only requires the delivery_id to perform the conversion.
    """
    delivery_id = serializers.IntegerField()
    
    def validate_delivery_id(self, value):
        """
        Validate that the delivery exists and can be converted to an invoice.
        """
        try:
            delivery = Delivery.objects.get(pk=value)
            
            # Check if delivery can be converted
            if delivery.status in ['Cancelled', 'Closed']:
                raise serializers.ValidationError(
                    f"Delivery {delivery.pk} cannot be converted because it is {delivery.status}."
                )
                
            # Check if there are any items left to invoice
            invoiced_quantities = {}
            for invoice in ARInvoice.objects.filter(delivery=delivery):
                for line in invoice.lines.all():
                    key = (line.item_code, line.uom)
                    invoiced_quantities[key] = invoiced_quantities.get(key, 0) + line.quantity
            
            any_to_invoice = False
            for d_line in delivery.lines.all():
                key = (d_line.item_code, d_line.uom)
                already_invoiced = invoiced_quantities.get(key, 0)
                remaining_qty = d_line.quantity - already_invoiced
                if remaining_qty > 0:
                    any_to_invoice = True
                    break
            
            if not any_to_invoice:
                raise serializers.ValidationError(
                    f"All items in Delivery {delivery.pk} have already been invoiced."
                )
                
            return value
        except Delivery.DoesNotExist:
            raise serializers.ValidationError("Delivery does not exist.")
    
    def create(self, validated_data):
        """
        Create an AR Invoice from a delivery.
        """
        delivery_id = validated_data.get('delivery_id')
        delivery = Delivery.objects.get(pk=delivery_id)
        
        # Calculate invoiced quantities
        invoiced_quantities = {}
        for invoice in ARInvoice.objects.filter(delivery=delivery):
            for line in invoice.lines.all():
                key = (line.item_code, line.uom)
                invoiced_quantities[key] = invoiced_quantities.get(key, 0) + line.quantity
        
        # Create invoice
        invoice = ARInvoice.objects.create(
            document_date=timezone.now().date(),
            posting_date=timezone.now().date(),
            due_date=timezone.now().date() + datetime.timedelta(days=30),  # Default 30 days
            customer=delivery.customer,
            contact_person=delivery.contact_person,
            billing_address=delivery.customer.addresses.filter(address_type='B', is_default=True).first(),
            delivery=delivery,
            sales_order=delivery.sales_order,
            currency=delivery.currency,
            payment_terms=delivery.payment_terms,
            discount_amount=delivery.discount_amount,
            remarks=f"Invoice for Delivery #{delivery.pk}",
            sales_employee=delivery.sales_employee,
            status='Open',
            paid_amount=delivery.paid_amount,
            payment_method=delivery.payment_method,
            payment_reference=delivery.payment_reference,
            payment_date=delivery.payment_date
        )
        
        # Create invoice lines from delivery lines for remaining quantities
        total_invoice_amount = 0
        
        for d_line in delivery.lines.all():
            key = (d_line.item_code, d_line.uom)
            already_invoiced = invoiced_quantities.get(key, 0)
            remaining_qty = d_line.quantity - already_invoiced
            
            if remaining_qty > 0:
                invoice_line = ARInvoiceLine.objects.create(
                    invoice=invoice,
                    delivery_line=d_line,
                    sales_order_line=d_line.sales_order_line,
                    item_code=d_line.item_code,
                    item_name=d_line.item_name,
                    quantity=remaining_qty,
                    unit_price=d_line.unit_price,
                    uom=d_line.uom,
                    remarks=d_line.remarks,
                    is_active=True
                )
                total_invoice_amount += invoice_line.quantity * invoice_line.unit_price
        
        # Update invoice total amount and calculate payable and due amounts
        invoice.total_amount = total_invoice_amount
        invoice.payable_amount = invoice.total_amount - invoice.discount_amount
        invoice.due_amount = invoice.payable_amount - invoice.paid_amount
        invoice.save(update_fields=['total_amount', 'payable_amount', 'due_amount'])
        
        # Update delivery status
        delivery.status = 'Invoiced'
        delivery.save(update_fields=['status'])
        
        return invoice        