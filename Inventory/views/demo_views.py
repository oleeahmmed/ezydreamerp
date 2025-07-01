from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.views import View
from django.utils import timezone
from django import forms
import django.db.transaction as db_transaction
from decimal import Decimal
import logging
from Inventory.models import UnitOfMeasure, Warehouse, ItemGroup, Item, ItemWarehouseInfo, InventoryTransaction, GoodsReceipt, GoodsReceiptLine, GoodsIssue, GoodsIssueLine, InventoryTransfer, InventoryTransferLine

# Set up logging
logger = logging.getLogger(__name__)

class DemoConfigForm(forms.Form):
    """Form for managing demo data import/delete with configuration options"""
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
        label='Include Sample Transactions (Goods Receipt, Goods Issue, Inventory Transfer)'
    )

class DemoAccessMixin(LoginRequiredMixin, PermissionRequiredMixin):
    login_url = '/login/'
    raise_exception = True

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You don't have permission to access this page.")
            raise PermissionDenied
        return super().handle_no_permission()

class DemoConfigView(DemoAccessMixin, View):
    template_name = 'inventory/demo_config.html'
    permission_required = 'Inventory.change_item'
    form_class = DemoConfigForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {
            'form': form,
            'screen_title': 'Sample Data Setup',
            'subtitle_title': 'Import or delete sample data for the inventory module',
            'cancel_url': reverse_lazy('Inventory:item_list'),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            include_transactions = form.cleaned_data['include_transactions']
            
            try:
                if action == 'import':
                    with db_transaction.atomic():
                        logger.info("Starting demo data import. include_transactions: %s", include_transactions)
                        
                        # Initialize transaction counts
                        transaction_counts = {
                            'unit_of_measure': 0,
                            'warehouse': 0,
                            'item_group': 0,
                            'item': 0,
                            'item_warehouse_info': 0,
                            'inventory_transaction': 0,
                            'goods_receipt': 0,
                            'goods_receipt_line': 0,
                            'goods_issue': 0,
                            'goods_issue_line': 0,
                            'inventory_transfer': 0,
                            'inventory_transfer_line': 0,
                        }

                        # Unit of Measure
                        try:
                            uom_kg, created = UnitOfMeasure.objects.get_or_create(
                                code='KG',
                                defaults={'name': 'Kilogram'}
                            )
                            if created:
                                transaction_counts['unit_of_measure'] += 1
                            logger.info("UnitOfMeasure KG created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create UnitOfMeasure KG: %s", str(e))
                            raise

                        try:
                            uom_unit, created = UnitOfMeasure.objects.get_or_create(
                                code='UNIT',
                                defaults={'name': 'Unit'}
                            )
                            if created:
                                transaction_counts['unit_of_measure'] += 1
                            logger.info("UnitOfMeasure UNIT created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create UnitOfMeasure UNIT: %s", str(e))
                            raise

                        # Warehouse
                        try:
                            main_warehouse, created = Warehouse.objects.get_or_create(
                                code='WH001',
                                defaults={
                                    'name': 'Main Warehouse',
                                    'is_default': True,
                                    'address': '123 Main St, Dhaka',
                                    'contact_person': 'John Doe',
                                    'contact_phone': '+8801234567890'
                                }
                            )
                            if created:
                                transaction_counts['warehouse'] += 1
                            logger.info("Main Warehouse created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Main Warehouse: %s", str(e))
                            raise

                        try:
                            branch_warehouse, created = Warehouse.objects.get_or_create(
                                code='WH002',
                                defaults={
                                    'name': 'Branch Warehouse',
                                    'is_default': False,
                                    'address': '456 Branch Rd, Chittagong',
                                    'contact_person': 'Jane Smith',
                                    'contact_phone': '+8809876543210'
                                }
                            )
                            if created:
                                transaction_counts['warehouse'] += 1
                            logger.info("Branch Warehouse created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Branch Warehouse: %s", str(e))
                            raise

                        # Item Group
                        try:
                            electronics_group, created = ItemGroup.objects.get_or_create(
                                code='ELEC',
                                defaults={'name': 'Electronics', 'description': 'Electronic items'}
                            )
                            if created:
                                transaction_counts['item_group'] += 1
                            logger.info("Electronics ItemGroup created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Electronics ItemGroup: %s", str(e))
                            raise

                        try:
                            furniture_group, created = ItemGroup.objects.get_or_create(
                                code='FURN',
                                defaults={'name': 'Furniture', 'description': 'Furniture items'}
                            )
                            if created:
                                transaction_counts['item_group'] += 1
                            logger.info("Furniture ItemGroup created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Furniture ItemGroup: %s", str(e))
                            raise

                        # Item
                        try:
                            laptop, created = Item.objects.get_or_create(
                                code='ITEM001',
                                defaults={
                                    'name': 'Laptop',
                                    'item_group': electronics_group,
                                    'inventory_uom': uom_unit,
                                    'purchase_uom': uom_unit,
                                    'sales_uom': uom_unit,
                                    'is_inventory_item': True,
                                    'is_sales_item': True,
                                    'is_purchase_item': True,
                                    'default_warehouse': main_warehouse,
                                    'unit_price': Decimal('50000.00'),
                                    'item_cost': Decimal('40000.00'),
                                    'selling_price': Decimal('55000.00'),
                                    'purchase_price': Decimal('40000.00'),
                                    'minimum_stock': Decimal('5.0'),
                                    'reorder_point': Decimal('10.0')
                                }
                            )
                            if created:
                                transaction_counts['item'] += 1
                            logger.info("Laptop Item created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Laptop Item: %s", str(e))
                            raise

                        try:
                            chair, created = Item.objects.get_or_create(
                                code='ITEM002',
                                defaults={
                                    'name': 'Office Chair',
                                    'item_group': furniture_group,
                                    'inventory_uom': uom_unit,
                                    'purchase_uom': uom_unit,
                                    'sales_uom': uom_unit,
                                    'is_inventory_item': True,
                                    'is_sales_item': True,
                                    'is_purchase_item': True,
                                    'default_warehouse': branch_warehouse,
                                    'unit_price': Decimal('5000.00'),
                                    'item_cost': Decimal('4000.00'),
                                    'selling_price': Decimal('5500.00'),
                                    'purchase_price': Decimal('4000.00'),
                                    'minimum_stock': Decimal('10.0'),
                                    'reorder_point': Decimal('20.0')
                                }
                            )
                            if created:
                                transaction_counts['item'] += 1
                            logger.info("Chair Item created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Chair Item: %s", str(e))
                            raise

                        # ItemWarehouseInfo
                        try:
                            laptop_warehouse_info, created = ItemWarehouseInfo.objects.get_or_create(
                                item=laptop,
                                warehouse=main_warehouse,
                                defaults={
                                    'in_stock': Decimal('50.0'),
                                    'committed': Decimal('5.0'),
                                    'ordered': Decimal('10.0'),
                                    'min_stock': Decimal('5.0'),
                                    'reorder_point': Decimal('10.0')
                                }
                            )
                            if created:
                                transaction_counts['item_warehouse_info'] += 1
                            logger.info("Laptop ItemWarehouseInfo created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Laptop ItemWarehouseInfo: %s", str(e))
                            raise

                        try:
                            chair_warehouse_info, created = ItemWarehouseInfo.objects.get_or_create(
                                item=chair,
                                warehouse=branch_warehouse,
                                defaults={
                                    'in_stock': Decimal('100.0'),
                                    'committed': Decimal('10.0'),
                                    'ordered': Decimal('20.0'),
                                    'min_stock': Decimal('10.0'),
                                    'reorder_point': Decimal('20.0')
                                }
                            )
                            if created:
                                transaction_counts['item_warehouse_info'] += 1
                            logger.info("Chair ItemWarehouseInfo created: %s", created)
                        except Exception as e:
                            logger.error("Failed to create Chair ItemWarehouseInfo: %s", str(e))
                            raise

                        if include_transactions:
                            logger.info("Importing transaction data (Goods Receipt, Goods Issue, Inventory Transfer)")

                            # Inventory Transaction (Purchase)
                            try:
                                inv_transaction, created = InventoryTransaction.objects.get_or_create(
                                    item_code=laptop.code,
                                    item_name=laptop.name,
                                    warehouse=main_warehouse,
                                    transaction_type='PURCHASE',
                                    reference='PO001',
                                    defaults={
                                        'quantity': Decimal('20.0'),
                                        'unit_price': Decimal('40000.00'),
                                        'transaction_date': timezone.now(),
                                        'notes': 'Purchased laptops'
                                    }
                                )
                                if created:
                                    transaction_counts['inventory_transaction'] += 1
                                logger.info("InventoryTransaction (Purchase, PO001) created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create InventoryTransaction (Purchase): %s", str(e))
                                raise

                            # Goods Receipt (Laptop Purchase)
                            try:
                                goods_receipt, created = GoodsReceipt.objects.get_or_create(
                                    supplier_document='INV001',
                                    defaults={
                                        'document_date': timezone.now().date(),
                                        'posting_date': timezone.now().date(),
                                        'supplier': 'Tech Supplier Ltd',
                                        'status': 'Posted',
                                        'total_amount': Decimal('800000.00'),
                                        'payable_amount': Decimal('800000.00'),
                                        'due_amount': Decimal('800000.00'),
                                        'remarks': 'Received laptops for main warehouse'
                                    }
                                )
                                if created:
                                    transaction_counts['goods_receipt'] += 1
                                logger.info("GoodsReceipt (Laptop, INV001) created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create GoodsReceipt (Laptop): %s", str(e))
                                raise

                            try:
                                goods_receipt_line, created = GoodsReceiptLine.objects.get_or_create(
                                    goods_receipt=goods_receipt,
                                    item_code=laptop.code,
                                    item_name=laptop.name,
                                    quantity=Decimal('20.0'),
                                    defaults={
                                        'unit_price': Decimal('40000.00'),
                                        'uom': uom_unit.code,
                                        'remarks': 'Received laptops'
                                    }
                                )
                                if created:
                                    transaction_counts['goods_receipt_line'] += 1
                                logger.info("GoodsReceiptLine (Laptop) created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create GoodsReceiptLine (Laptop): %s", str(e))
                                raise

                            # Goods Receipt (Chair Purchase)
                            try:
                                goods_receipt2, created = GoodsReceipt.objects.get_or_create(
                                    supplier_document='INV002',
                                    defaults={
                                        'document_date': timezone.now().date(),
                                        'posting_date': timezone.now().date(),
                                        'supplier': 'Furniture Co.',
                                        'status': 'Posted',
                                        'total_amount': Decimal('100000.00'),
                                        'payable_amount': Decimal('100000.00'),
                                        'due_amount': Decimal('100000.00'),
                                        'remarks': 'Received chairs for branch warehouse'
                                    }
                                )
                                if created:
                                    transaction_counts['goods_receipt'] += 1
                                logger.info("GoodsReceipt (Chair, INV002) created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create GoodsReceipt (Chair): %s", str(e))
                                raise

                            try:
                                goods_receipt_line2, created = GoodsReceiptLine.objects.get_or_create(
                                    goods_receipt=goods_receipt2,
                                    item_code=chair.code,
                                    item_name=chair.name,
                                    quantity=Decimal('20.0'),
                                    defaults={
                                        'unit_price': Decimal('5000.00'),
                                        'uom': uom_unit.code,
                                        'remarks': 'Received office chairs'
                                    }
                                )
                                if created:
                                    transaction_counts['goods_receipt_line'] += 1
                                logger.info("GoodsReceiptLine (Chair) created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create GoodsReceiptLine (Chair): %s", str(e))
                                raise

                            # Goods Issue (Laptop Sale)
                            try:
                                goods_issue, created = GoodsIssue.objects.get_or_create(
                                    reference_document='SO001',
                                    defaults={
                                        'document_date': timezone.now().date(),
                                        'posting_date': timezone.now().date(),
                                        'recipient': 'Customer A',
                                        'status': 'Posted',
                                        'total_amount': Decimal('55000.00'),
                                        'payable_amount': Decimal('55000.00'),
                                        'due_amount': Decimal('55000.00'),
                                        'remarks': 'Sold laptop to customer'
                                    }
                                )
                                if created:
                                    transaction_counts['goods_issue'] += 1
                                logger.info("GoodsIssue (Laptop, SO001) created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create GoodsIssue (Laptop): %s", str(e))
                                raise

                            try:
                                goods_issue_line, created = GoodsIssueLine.objects.get_or_create(
                                    goods_issue=goods_issue,
                                    item_code=laptop.code,
                                    item_name=laptop.name,
                                    quantity=Decimal('1.0'),
                                    defaults={
                                        'unit_price': Decimal('55000.00'),
                                        'uom': uom_unit.code,
                                        'remarks': 'Sold laptop to customer'
                                    }
                                )
                                if created:
                                    transaction_counts['goods_issue_line'] += 1
                                logger.info("GoodsIssueLine (Laptop) created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create GoodsIssueLine (Laptop): %s", str(e))
                                raise

                            # Goods Issue (Chair Sale)
                            try:
                                goods_issue2, created = GoodsIssue.objects.get_or_create(
                                    reference_document='SO002',
                                    defaults={
                                        'document_date': timezone.now().date(),
                                        'posting_date': timezone.now().date(),
                                        'recipient': 'Customer B',
                                        'status': 'Posted',
                                        'total_amount': Decimal('11000.00'),
                                        'payable_amount': Decimal('11000.00'),
                                        'due_amount': Decimal('11000.00'),
                                        'remarks': 'Sold chairs to customer'
                                    }
                                )
                                if created:
                                    transaction_counts['goods_issue'] += 1
                                logger.info("GoodsIssue (Chair, SO002) created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create GoodsIssue (Chair): %s", str(e))
                                raise

                            try:
                                goods_issue_line2, created = GoodsIssueLine.objects.get_or_create(
                                    goods_issue=goods_issue2,
                                    item_code=chair.code,
                                    item_name=chair.name,
                                    quantity=Decimal('2.0'),
                                    defaults={
                                        'unit_price': Decimal('5500.00'),
                                        'uom': uom_unit.code,
                                        'remarks': 'Sold office chairs'
                                    }
                                )
                                if created:
                                    transaction_counts['goods_issue_line'] += 1
                                logger.info("GoodsIssueLine (Chair) created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create GoodsIssueLine (Chair): %s", str(e))
                                raise

                            # Inventory Transfer (Laptop Transfer)
                            try:
                                inventory_transfer, created = InventoryTransfer.objects.get_or_create(
                                    reference_document='TR001',
                                    from_warehouse=main_warehouse,
                                    to_warehouse=branch_warehouse,
                                    defaults={
                                        'document_date': timezone.now().date(),
                                        'posting_date': timezone.now().date(),
                                        'status': 'Posted',
                                        'total_amount': Decimal('50000.00'),
                                        'remarks': 'Transferred laptops to branch'
                                    }
                                )
                                if created:
                                    transaction_counts['inventory_transfer'] += 1
                                logger.info("InventoryTransfer (Laptop, TR001) created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create InventoryTransfer (Laptop): %s", str(e))
                                raise

                            try:
                                inventory_transfer_line, created = InventoryTransferLine.objects.get_or_create(
                                    inventory_transfer=inventory_transfer,
                                    item_code=laptop.code,
                                    item_name=laptop.name,
                                    from_warehouse=main_warehouse,
                                    to_warehouse=branch_warehouse,
                                    quantity=Decimal('1.0'),
                                    defaults={
                                        'unit_price': Decimal('50000.00'),
                                        'uom': uom_unit.code,
                                        'remarks': 'Transferred laptops'
                                    }
                                )
                                if created:
                                    transaction_counts['inventory_transfer_line'] += 1
                                logger.info("InventoryTransferLine (Laptop) created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create InventoryTransferLine (Laptop): %s", str(e))
                                raise

                            # Inventory Transfer (Chair Transfer)
                            try:
                                inventory_transfer2, created = InventoryTransfer.objects.get_or_create(
                                    reference_document='TR002',
                                    from_warehouse=branch_warehouse,
                                    to_warehouse=main_warehouse,
                                    defaults={
                                        'document_date': timezone.now().date(),
                                        'posting_date': timezone.now().date(),
                                        'status': 'Posted',
                                        'total_amount': Decimal('10000.00'),
                                        'remarks': 'Transferred chairs to main warehouse'
                                    }
                                )
                                if created:
                                    transaction_counts['inventory_transfer'] += 1
                                logger.info("InventoryTransfer (Chair, TR002) created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create InventoryTransfer (Chair): %s", str(e))
                                raise

                            try:
                                inventory_transfer_line2, created = InventoryTransferLine.objects.get_or_create(
                                    inventory_transfer=inventory_transfer2,
                                    item_code=chair.code,
                                    item_name=chair.name,
                                    from_warehouse=branch_warehouse,
                                    to_warehouse=main_warehouse,
                                    quantity=Decimal('2.0'),
                                    defaults={
                                        'unit_price': Decimal('5000.00'),
                                        'uom': uom_unit.code,
                                        'remarks': 'Transferred chairs'
                                    }
                                )
                                if created:
                                    transaction_counts['inventory_transfer_line'] += 1
                                logger.info("InventoryTransferLine (Chair) created: %s", created)
                            except Exception as e:
                                logger.error("Failed to create InventoryTransferLine (Chair): %s", str(e))
                                raise

                        # Prepare success message with counts
                        success_message = (
                            f"ডেমো ডেটা সফলভাবে ইম্পোর্ট করা হয়েছে। "
                            f"তৈরি করা হয়েছে: {transaction_counts['unit_of_measure']} UnitOfMeasure, "
                            f"{transaction_counts['warehouse']} Warehouse, "
                            f"{transaction_counts['item_group']} ItemGroup, "
                            f"{transaction_counts['item']} Item, "
                            f"{transaction_counts['item_warehouse_info']} ItemWarehouseInfo, "
                            f"{transaction_counts['inventory_transaction']} InventoryTransaction, "
                            f"{transaction_counts['goods_receipt']} GoodsReceipt, "
                            f"{transaction_counts['goods_receipt_line']} GoodsReceiptLine, "
                            f"{transaction_counts['goods_issue']} GoodsIssue, "
                            f"{transaction_counts['goods_issue_line']} GoodsIssueLine, "
                            f"{transaction_counts['inventory_transfer']} InventoryTransfer, "
                            f"{transaction_counts['inventory_transfer_line']} InventoryTransferLine রেকর্ড।"
                        )
                        messages.success(request, success_message)
                        logger.info(success_message)

                elif action == 'delete':
                    with db_transaction.atomic():
  
                    
                        transfer_lines_deleted = InventoryTransferLine.objects.all().delete()[0]
                        transfer_deleted = InventoryTransfer.objects.all().delete()[0]
                        issue_lines_deleted = GoodsIssueLine.objects.all().delete()[0]
                        issue_deleted = GoodsIssue.objects.all().delete()[0]
                        receipt_lines_deleted = GoodsReceiptLine.objects.all().delete()[0]
                        receipt_deleted = GoodsReceipt.objects.all().delete()[0]
                        inventory_transactions_deleted = InventoryTransaction.objects.all().delete()[0]
                        item_warehouse_info_deleted = ItemWarehouseInfo.objects.all().delete()[0]
                        item_deleted = Item.objects.all().delete()[0]
                        item_group_deleted = ItemGroup.objects.all().delete()[0]
                        warehouse_deleted = Warehouse.objects.all().delete()[0]
                        uom_deleted = UnitOfMeasure.objects.all().delete()[0]

                        success_message = (
                            f"ডেমো ডেটা সফলভাবে মুছে ফেলা হয়েছে। "
                            f"মুছে ফেলা হয়েছে: {transfer_lines_deleted} InventoryTransferLine, {transfer_deleted} InventoryTransfer, "
                            f"{issue_lines_deleted} GoodsIssueLine, {issue_deleted} GoodsIssue, "
                            f"{receipt_lines_deleted} GoodsReceiptLine, {receipt_deleted} GoodsReceipt, "
                            f"{inventory_transactions_deleted} InventoryTransaction, {item_warehouse_info_deleted} ItemWarehouseInfo, "
                            f"{item_deleted} Item, {item_group_deleted} ItemGroup, {warehouse_deleted} Warehouse, "
                            f"{uom_deleted} UnitOfMeasure রেকর্ড।"
                        )
                        messages.success(request, success_message)
                        logger.info(success_message)




            except Exception as e:
                error_message = (
                    f"{'ইম্পোর্ট' if action == 'import' else 'ডিলিট'} অ্যাকশন সম্পাদনে ত্রুটি: {str(e)}"
                )
                logger.error(error_message)
                messages.error(request, error_message)
                return redirect('Inventory:demo_config')

        else:
            messages.error(request, "অবৈধ ফর্ম সাবমিশন। দয়া করে ফিল্ডগুলো চেক করুন।")

        return redirect('Inventory:demo_config')