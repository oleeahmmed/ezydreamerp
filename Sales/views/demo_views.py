from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.views import View
from django.utils import timezone
from django import forms
from django.db import transaction
from decimal import Decimal
import logging
from datetime import timedelta

from Sales.models import (
    SalesEmployee, SalesQuotation, SalesQuotationLine, SalesOrder, SalesOrderLine,
    Delivery, DeliveryLine, Return, ReturnLine, ARInvoice, ARInvoiceLine
)
from BusinessPartnerMasterData.models import BusinessPartner, Address, ContactPerson
from Inventory.models import UnitOfMeasure, Warehouse, ItemGroup, Item
from django.contrib.auth.models import User

# Set up logging
logger = logging.getLogger(__name__)

class SalesDemoConfigForm(forms.Form):
    """Form for managing sales demo data import/delete with configuration options"""
    ACTION_CHOICES = (
        ('import', 'Import Demo Data'),
        ('delete', 'Delete Demo Data'),
    )
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'peer w-full px-3 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent premium-input text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))] focus:bg-[hsl(var(--accent))] appearance-none',
        }),
        label='Action'
    )
    
    include_transactions = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'sr-only peer',
        }),
        label='Include Sample Transactions (Quotations, Orders, Deliveries, Invoices, Returns)'
    )

class SalesDemoAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class SalesDemoConfigView(SalesDemoAccessMixin, View):
    template_name = 'sales/demo_config.html'
    permission_required = 'Sales.change_salesorder'
    form_class = SalesDemoConfigForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {
            'form': form,
            'screen_title': 'Sales Sample Data Setup',
            'subtitle_title': 'Import or delete sample data for the sales module',
            'cancel_url': reverse_lazy('Sales:sales_order_list'),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            include_transactions = form.cleaned_data['include_transactions']
            
            try:
                if action == 'import':
                    with transaction.atomic():
                        logger.info("Starting sales demo data import. include_transactions: %s", include_transactions)
                        
                        # Initialize transaction counts
                        transaction_counts = {
                            'sales_employee': 0,
                            'business_partner': 0,
                            'address': 0,
                            'contact_person': 0,
                            'sales_quotation': 0,
                            'sales_quotation_line': 0,
                            'sales_order': 0,
                            'sales_order_line': 0,
                            'delivery': 0,
                            'delivery_line': 0,
                            'ar_invoice': 0,
                            'ar_invoice_line': 0,
                            'return': 0,
                            'return_line': 0,
                        }

                        # Get required dependencies
                        try:
                            uom_unit = UnitOfMeasure.objects.filter(code='UNIT').first()
                            main_warehouse = Warehouse.objects.filter(code='WH001').first()
                            
                            if not uom_unit:
                                uom_unit = UnitOfMeasure.objects.create(code='UNIT', name='Unit')
                            if not main_warehouse:
                                main_warehouse = Warehouse.objects.create(
                                    code='WH001', 
                                    name='Main Warehouse',
                                    is_default=True
                                )
                        except Exception as e:
                            logger.error("Failed to get/create dependencies: %s", str(e))
                            raise

                        # Sales Employee
                        try:
                            # Get or create a user for sales employee
                            user, user_created = User.objects.get_or_create(
                                username='sales_demo_user',
                                defaults={
                                    'first_name': 'John',
                                    'last_name': 'Sales',
                                    'email': 'john.sales@company.com'
                                }
                            )
                            
                            sales_employee, created = SalesEmployee.objects.get_or_create(
                                user=user,
                                defaults={
                                    'name': 'John Sales',
                                    'position': 'Sales Executive',
                                    'department': 'Sales',
                                    'phone': '+8801234567890',
                                    'email': 'john.sales@company.com'
                                }
                            )
                            if created:
                                transaction_counts['sales_employee'] += 1
                            logger.info("SalesEmployee created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create SalesEmployee: %s", str(e))
                            raise

                        # Business Partners (Customers)
                        try:
                            customer1, created = BusinessPartner.objects.get_or_create(
                                code='CUST001',
                                defaults={
                                    'name': 'ABC Corporation',
                                    'bp_type': 'C',
                                    'phone': '+8801111111111',
                                    'email': 'contact@abccorp.com'
                                }
                            )
                            if created:
                                transaction_counts['business_partner'] += 1
                            logger.info("Customer1 created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Customer1: %s", str(e))
                            raise

                        try:
                            customer2, created = BusinessPartner.objects.get_or_create(
                                code='CUST002',
                                defaults={
                                    'name': 'XYZ Limited',
                                    'bp_type': 'C',
                                    'phone': '+8802222222222',
                                    'email': 'info@xyzltd.com'
                                }
                            )
                            if created:
                                transaction_counts['business_partner'] += 1
                            logger.info("Customer2 created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Customer2: %s", str(e))
                            raise

                        # Get Address model fields dynamically to avoid field name errors
                        address_fields = [f.name for f in Address._meta.get_fields()]
                        logger.info("Available Address fields: %s", address_fields)

                        # Addresses - using dynamic field mapping
                        try:
                            address1_data = {
                                'business_partner': customer1,
                                'address_type': 'B',
                                'is_default': True
                            }
                            
                            # Map common address field variations
                            if 'address_line_1' in address_fields:
                                address1_data['address_line_1'] = '123 Business Street'
                            elif 'address1' in address_fields:
                                address1_data['address1'] = '123 Business Street'
                            elif 'street' in address_fields:
                                address1_data['street'] = '123 Business Street'
                            elif 'address' in address_fields:
                                address1_data['address'] = '123 Business Street'
                                
                            if 'city' in address_fields:
                                address1_data['city'] = 'Dhaka'
                            if 'state' in address_fields:
                                address1_data['state'] = 'Dhaka'
                            if 'postal_code' in address_fields:
                                address1_data['postal_code'] = '1000'
                            elif 'zip_code' in address_fields:
                                address1_data['zip_code'] = '1000'
                            elif 'postcode' in address_fields:
                                address1_data['postcode'] = '1000'
                            if 'country' in address_fields:
                                address1_data['country'] = 'Bangladesh'

                            address1, created = Address.objects.get_or_create(
                                business_partner=customer1,
                                address_type='B',
                                defaults=address1_data
                            )
                            if created:
                                transaction_counts['address'] += 1
                            logger.info("Address1 created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Address1: %s", str(e))
                            # Create minimal address if detailed creation fails
                            try:
                                address1, created = Address.objects.get_or_create(
                                    business_partner=customer1,
                                    address_type='B',
                                    defaults={'is_default': True}
                                )
                                if created:
                                    transaction_counts['address'] += 1
                            except Exception as e2:
                                logger.error("Failed to create minimal Address1: %s", str(e2))
                                raise

                        try:
                            address2_data = {
                                'business_partner': customer2,
                                'address_type': 'B',
                                'is_default': True
                            }
                            
                            # Map common address field variations
                            if 'address_line_1' in address_fields:
                                address2_data['address_line_1'] = '456 Commerce Road'
                            elif 'address1' in address_fields:
                                address2_data['address1'] = '456 Commerce Road'
                            elif 'street' in address_fields:
                                address2_data['street'] = '456 Commerce Road'
                            elif 'address' in address_fields:
                                address2_data['address'] = '456 Commerce Road'
                                
                            if 'city' in address_fields:
                                address2_data['city'] = 'Chittagong'
                            if 'state' in address_fields:
                                address2_data['state'] = 'Chittagong'
                            if 'postal_code' in address_fields:
                                address2_data['postal_code'] = '4000'
                            elif 'zip_code' in address_fields:
                                address2_data['zip_code'] = '4000'
                            elif 'postcode' in address_fields:
                                address2_data['postcode'] = '4000'
                            if 'country' in address_fields:
                                address2_data['country'] = 'Bangladesh'

                            address2, created = Address.objects.get_or_create(
                                business_partner=customer2,
                                address_type='B',
                                defaults=address2_data
                            )
                            if created:
                                transaction_counts['address'] += 1
                            logger.info("Address2 created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Address2: %s", str(e))
                            # Create minimal address if detailed creation fails
                            try:
                                address2, created = Address.objects.get_or_create(
                                    business_partner=customer2,
                                    address_type='B',
                                    defaults={'is_default': True}
                                )
                                if created:
                                    transaction_counts['address'] += 1
                            except Exception as e2:
                                logger.error("Failed to create minimal Address2: %s", str(e2))
                                raise

                        # Contact Persons
                        try:
                            contact1, created = ContactPerson.objects.get_or_create(
                                business_partner=customer1,
                                name='Ahmed Rahman',
                                defaults={
                                    'position': 'Purchase Manager',
                                    'phone': '+8801111111111',
                                    'email': 'ahmed@abccorp.com',
                                    'is_default': True
                                }
                            )
                            if created:
                                transaction_counts['contact_person'] += 1
                            logger.info("Contact1 created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Contact1: %s", str(e))
                            raise

                        try:
                            contact2, created = ContactPerson.objects.get_or_create(
                                business_partner=customer2,
                                name='Fatima Khan',
                                defaults={
                                    'position': 'Procurement Head',
                                    'phone': '+8802222222222',
                                    'email': 'fatima@xyzltd.com',
                                    'is_default': True
                                }
                            )
                            if created:
                                transaction_counts['contact_person'] += 1
                            logger.info("Contact2 created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Contact2: %s", str(e))
                            raise

                        # Get sample items (assuming they exist from inventory demo)
                        try:
                            laptop = Item.objects.filter(code='ITEM001').first()
                            chair = Item.objects.filter(code='ITEM002').first()
                            
                            if not laptop:
                                # Create basic item if not exists
                                electronics_group, _ = ItemGroup.objects.get_or_create(
                                    code='ELEC',
                                    defaults={'name': 'Electronics'}
                                )
                                laptop = Item.objects.create(
                                    code='ITEM001',
                                    name='Laptop',
                                    item_group=electronics_group,
                                    inventory_uom=uom_unit,
                                    purchase_uom=uom_unit,
                                    sales_uom=uom_unit,
                                    is_inventory_item=True,
                                    is_sales_item=True,
                                    is_purchase_item=True,
                                    default_warehouse=main_warehouse,
                                    unit_price=Decimal('50000.00'),
                                    selling_price=Decimal('55000.00')
                                )
                            
                            if not chair:
                                furniture_group, _ = ItemGroup.objects.get_or_create(
                                    code='FURN',
                                    defaults={'name': 'Furniture'}
                                )
                                chair = Item.objects.create(
                                    code='ITEM002',
                                    name='Office Chair',
                                    item_group=furniture_group,
                                    inventory_uom=uom_unit,
                                    purchase_uom=uom_unit,
                                    sales_uom=uom_unit,
                                    is_inventory_item=True,
                                    is_sales_item=True,
                                    is_purchase_item=True,
                                    default_warehouse=main_warehouse,
                                    unit_price=Decimal('5000.00'),
                                    selling_price=Decimal('5500.00')
                                )
                        except Exception as e:
                            logger.error("Failed to get/create items: %s", str(e))
                            raise

                        if include_transactions:
                            logger.info("Importing sales transaction data")

                            # Sales Quotation
                            try:
                                quotation_data = {
                                    'customer': customer1,
                                    'document_date': timezone.now().date(),
                                    'valid_until': timezone.now().date() + timedelta(days=30),
                                    'contact_person': contact1,
                                    'billing_address': address1,
                                    'total_amount': Decimal('110000.00'),
                                    'payable_amount': Decimal('110000.00'),
                                    'due_amount': Decimal('110000.00'),
                                    'status': 'Open',
                                    'sales_employee': sales_employee,
                                    'remarks': 'Demo quotation for laptops and chairs'
                                }

                                quotation, created = SalesQuotation.objects.get_or_create(
                                    customer=customer1,
                                    document_date=timezone.now().date(),
                                    defaults=quotation_data
                                )
                                if created:
                                    transaction_counts['sales_quotation'] += 1
                                logger.info("SalesQuotation created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create SalesQuotation: %s", str(e))
                                raise

                            # Sales Quotation Lines
                            try:
                                quotation_line1, created = SalesQuotationLine.objects.get_or_create(
                                    quotation=quotation,
                                    item_code=laptop.code,
                                    item_name=laptop.name,
                                    quantity=Decimal('2.0'),
                                    defaults={
                                        'unit_price': Decimal('50000.00'),
                                        'uom': uom_unit.code,
                                        'remarks': 'High-performance laptops'
                                    }
                                )
                                if created:
                                    transaction_counts['sales_quotation_line'] += 1
                                logger.info("SalesQuotationLine1 created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create SalesQuotationLine1: %s", str(e))
                                raise

                            try:
                                quotation_line2, created = SalesQuotationLine.objects.get_or_create(
                                    quotation=quotation,
                                    item_code=chair.code,
                                    item_name=chair.name,
                                    quantity=Decimal('2.0'),
                                    defaults={
                                        'unit_price': Decimal('5000.00'),
                                        'uom': uom_unit.code,
                                        'remarks': 'Ergonomic office chairs'
                                    }
                                )
                                if created:
                                    transaction_counts['sales_quotation_line'] += 1
                                logger.info("SalesQuotationLine2 created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create SalesQuotationLine2: %s", str(e))
                                raise

                            # Sales Order
                            try:
                                sales_order, created = SalesOrder.objects.get_or_create(
                                    customer=customer1,
                                    document_date=timezone.now().date(),
                                    defaults={
                                        'delivery_date': timezone.now().date() + timedelta(days=7),
                                        'contact_person': contact1,
                                        'billing_address': address1,
                                        'shipping_address': address1,
                                        'total_amount': Decimal('55000.00'),
                                        'payable_amount': Decimal('55000.00'),
                                        'due_amount': Decimal('55000.00'),
                                        'status': 'Open',
                                        'sales_employee': sales_employee,
                                        'quotation': quotation,
                                        'remarks': 'Demo sales order from quotation'
                                    }
                                )
                                if created:
                                    transaction_counts['sales_order'] += 1
                                logger.info("SalesOrder created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create SalesOrder: %s", str(e))
                                raise

                            # Sales Order Line
                            try:
                                order_line, created = SalesOrderLine.objects.get_or_create(
                                    order=sales_order,
                                    item_code=laptop.code,
                                    item_name=laptop.name,
                                    quantity=Decimal('1.0'),
                                    defaults={
                                        'unit_price': Decimal('55000.00'),
                                        'uom': uom_unit.code,
                                        'remarks': 'Premium laptop for customer'
                                    }
                                )
                                if created:
                                    transaction_counts['sales_order_line'] += 1
                                logger.info("SalesOrderLine created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create SalesOrderLine: %s", str(e))
                                raise

                            # Delivery
                            try:
                                delivery, created = Delivery.objects.get_or_create(
                                    customer=customer1,
                                    document_date=timezone.now().date(),
                                    defaults={
                                        'posting_date': timezone.now().date(),
                                        'contact_person': contact1,
                                        'shipping_address': address1,
                                        'sales_order': sales_order,
                                        'total_amount': Decimal('55000.00'),
                                        'payable_amount': Decimal('55000.00'),
                                        'due_amount': Decimal('55000.00'),
                                        'status': 'Open',
                                        'sales_employee': sales_employee,
                                        'delivery_method': 'Van',
                                        'driver_name': 'Karim Ahmed',
                                        'vehicle_number': 'DHK-1234',
                                        'expected_delivery_date': timezone.now().date() + timedelta(days=1),
                                        'delivery_area': 'Dhaka',
                                        'remarks': 'Demo delivery for laptop'
                                    }
                                )
                                if created:
                                    transaction_counts['delivery'] += 1
                                logger.info("Delivery created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create Delivery: %s", str(e))
                                raise

                            # Delivery Line
                            try:
                                delivery_line, created = DeliveryLine.objects.get_or_create(
                                    delivery=delivery,
                                    sales_order_line=order_line,
                                    item_code=laptop.code,
                                    item_name=laptop.name,
                                    quantity=Decimal('1.0'),
                                    defaults={
                                        'unit_price': Decimal('55000.00'),
                                        'uom': uom_unit.code,
                                        'remarks': 'Delivered laptop to customer'
                                    }
                                )
                                if created:
                                    transaction_counts['delivery_line'] += 1
                                logger.info("DeliveryLine created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create DeliveryLine: %s", str(e))
                                raise

                            # AR Invoice
                            try:
                                ar_invoice, created = ARInvoice.objects.get_or_create(
                                    customer=customer1,
                                    document_date=timezone.now().date(),
                                    defaults={
                                        'posting_date': timezone.now().date(),
                                        'contact_person': contact1,
                                        'billing_address': address1,
                                        'sales_order': sales_order,
                                        'delivery': delivery,
                                        'total_amount': Decimal('55000.00'),
                                        'payable_amount': Decimal('55000.00'),
                                        'due_amount': Decimal('55000.00'),
                                        'status': 'Open',
                                        'sales_employee': sales_employee,
                                        'remarks': 'Demo invoice for delivered laptop'
                                    }
                                )
                                if created:
                                    transaction_counts['ar_invoice'] += 1
                                logger.info("ARInvoice created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create ARInvoice: %s", str(e))
                                raise

                            # AR Invoice Line
                            try:
                                invoice_line, created = ARInvoiceLine.objects.get_or_create(
                                    invoice=ar_invoice,
                                    sales_order_line=order_line,
                                    delivery_line=delivery_line,
                                    item_code=laptop.code,
                                    item_name=laptop.name,
                                    quantity=Decimal('1.0'),
                                    defaults={
                                        'unit_price': Decimal('55000.00'),
                                        'uom': uom_unit.code,
                                        'remarks': 'Invoice line for delivered laptop'
                                    }
                                )
                                if created:
                                    transaction_counts['ar_invoice_line'] += 1
                                logger.info("ARInvoiceLine created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create ARInvoiceLine: %s", str(e))
                                raise

                            # Return (Sample)
                            try:
                                return_doc, created = Return.objects.get_or_create(
                                    customer=customer2,
                                    document_date=timezone.now().date(),
                                    defaults={
                                        'posting_date': timezone.now().date(),
                                        'contact_person': contact2,
                                        'return_address': address2,
                                        'total_amount': Decimal('5500.00'),
                                        'payable_amount': Decimal('5500.00'),
                                        'due_amount': Decimal('5500.00'),
                                        'status': 'Open',
                                        'sales_employee': sales_employee,
                                        'return_reason': 'Defective product',
                                        'remarks': 'Demo return for defective chair'
                                    }
                                )
                                if created:
                                    transaction_counts['return'] += 1
                                logger.info("Return created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create Return: %s", str(e))
                                raise

                            # Return Line
                            try:
                                return_line, created = ReturnLine.objects.get_or_create(
                                    return_doc=return_doc,
                                    item_code=chair.code,
                                    item_name=chair.name,
                                    quantity=Decimal('1.0'),
                                    defaults={
                                        'unit_price': Decimal('5500.00'),
                                        'uom': uom_unit.code,
                                        'remarks': 'Returned defective chair'
                                    }
                                )
                                if created:
                                    transaction_counts['return_line'] += 1
                                logger.info("ReturnLine created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create ReturnLine: %s", str(e))
                                raise

                        # Prepare success message with counts
                        success_message = (
                            f"সেলস ডেমো ডেটা সফলভাবে ইম্পোর্ট করা হয়েছে। "
                            f"তৈরি করা হয়েছে: {transaction_counts['sales_employee']} SalesEmployee, "
                            f"{transaction_counts['business_partner']} BusinessPartner, "
                            f"{transaction_counts['address']} Address, "
                            f"{transaction_counts['contact_person']} ContactPerson, "
                            f"{transaction_counts['sales_quotation']} SalesQuotation, "
                            f"{transaction_counts['sales_quotation_line']} SalesQuotationLine, "
                            f"{transaction_counts['sales_order']} SalesOrder, "
                            f"{transaction_counts['sales_order_line']} SalesOrderLine, "
                            f"{transaction_counts['delivery']} Delivery, "
                            f"{transaction_counts['delivery_line']} DeliveryLine, "
                            f"{transaction_counts['ar_invoice']} ARInvoice, "
                            f"{transaction_counts['ar_invoice_line']} ARInvoiceLine, "
                            f"{transaction_counts['return']} Return, "
                            f"{transaction_counts['return_line']} ReturnLine রেকর্ড।"
                        )
                        messages.success(request, success_message)
                        logger.info(success_message)

                elif action == 'delete':
                    # Delete in reverse order to respect foreign key constraints
                    return_lines_deleted = ReturnLine.objects.all().delete()[0]
                    returns_deleted = Return.objects.all().delete()[0]
                    invoice_lines_deleted = ARInvoiceLine.objects.all().delete()[0]
                    invoices_deleted = ARInvoice.objects.all().delete()[0]
                    delivery_lines_deleted = DeliveryLine.objects.all().delete()[0]
                    deliveries_deleted = Delivery.objects.all().delete()[0]
                    order_lines_deleted = SalesOrderLine.objects.all().delete()[0]
                    orders_deleted = SalesOrder.objects.all().delete()[0]
                    quotation_lines_deleted = SalesQuotationLine.objects.all().delete()[0]
                    quotations_deleted = SalesQuotation.objects.all().delete()[0]
                    contacts_deleted = ContactPerson.objects.all().delete()[0]
                    addresses_deleted = Address.objects.all().delete()[0]
                    customers_deleted = BusinessPartner.objects.filter(bp_type='C').delete()[0]
                    employees_deleted = SalesEmployee.objects.all().delete()[0]

                    success_message = (
                        f"সেলস ডেমো ডেটা সফলভাবে মুছে ফেলা হয়েছে। "
                        f"মুছে ফেলা হয়েছে: {return_lines_deleted} ReturnLine, {returns_deleted} Return, "
                        f"{invoice_lines_deleted} ARInvoiceLine, {invoices_deleted} ARInvoice, "
                        f"{delivery_lines_deleted} DeliveryLine, {deliveries_deleted} Delivery, "
                        f"{order_lines_deleted} SalesOrderLine, {orders_deleted} SalesOrder, "
                        f"{quotation_lines_deleted} SalesQuotationLine, {quotations_deleted} SalesQuotation, "
                        f"{contacts_deleted} ContactPerson, {addresses_deleted} Address, "
                        f"{customers_deleted} BusinessPartner, {employees_deleted} SalesEmployee রেকর্ড।"
                    )
                    messages.success(request, success_message)
                    logger.info(success_message)

            except Exception as e:
                error_message = f"সেলস ডেমো ইম্পোর্ট অ্যাকশন সম্পাদনে ত্রুটি: {str(e)}"
                logger.error(error_message)
                messages.error(request, error_message)
                return redirect('Sales:sales_demo_config')

        else:
            messages.error(request, "অবৈধ ফর্ম সাবমিশন। দয়া করে ফিল্ডগুলো চেক করুন।")

        return redirect('Sales:sales_demo_config')
