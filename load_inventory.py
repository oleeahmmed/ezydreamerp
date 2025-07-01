import os
import django

# ✅ SETUP DJANGO ENVIRONMENT
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from Inventory.models import UnitOfMeasure, Warehouse, ItemGroup, Item, ItemWarehouseInfo
from django.utils import timezone
from decimal import Decimal

print("🔄 Loading demo data for Inventory...")

# STEP 1: Units of Measure
uom_list = [
    {"code": "PCS", "name": "Pieces"},
    {"code": "KG", "name": "Kilogram"},
    {"code": "GM", "name": "Gram"},
    {"code": "LTR", "name": "Liter"},
    {"code": "MTR", "name": "Meter"},
    {"code": "BOX", "name": "Box"},
    {"code": "CTN", "name": "Carton"},
    {"code": "DOZ", "name": "Dozen"},
    {"code": "SET", "name": "Set"},
    {"code": "UNIT", "name": "Unit"},
]

created_uoms = {}
for uom in uom_list:
    obj, created = UnitOfMeasure.objects.get_or_create(
        code=uom["code"],
        defaults={"name": uom["name"]}
    )
    created_uoms[uom["code"]] = obj
    status = "✅ Created" if created else "⏩ Already exists"
    print(f"{status}: {uom['name']} ({uom['code']})")

# STEP 2: Warehouses
warehouse_list = [
    {
        "code": "MAIN",
        "name": "Main Warehouse",
        "is_default": True,
        "address": "123 Main Street, Dhaka, Bangladesh",
        "contact_person": "Rahim Ahmed",
        "contact_phone": "+880-1712-345678"
    },
    {
        "code": "CTG",
        "name": "Chittagong Warehouse",
        "is_default": False,
        "address": "45 Port Road, Chittagong, Bangladesh",
        "contact_person": "Kamal Hossain",
        "contact_phone": "+880-1812-987654"
    },
    {
        "code": "SYL",
        "name": "Sylhet Warehouse",
        "is_default": False,
        "address": "78 Tea Garden Road, Sylhet, Bangladesh",
        "contact_person": "Jamal Uddin",
        "contact_phone": "+880-1912-876543"
    }
]

created_warehouses = {}
for wh in warehouse_list:
    obj, created = Warehouse.objects.get_or_create(
        code=wh["code"],
        defaults={
            "name": wh["name"],
            "is_default": wh["is_default"],
            "address": wh["address"],
            "contact_person": wh["contact_person"],
            "contact_phone": wh["contact_phone"]
        }
    )
    created_warehouses[wh["code"]] = obj
    status = "✅ Created" if created else "⏩ Already exists"
    print(f"{status}: {wh['name']} ({wh['code']})")

# STEP 3: Item Groups
item_groups = [
    {"code": "ELEC", "name": "Electronics", "parent": None, "description": "Electronic items and gadgets"},
    {"code": "FURN", "name": "Furniture", "parent": None, "description": "Furniture items"},
    {"code": "STAT", "name": "Stationery", "parent": None, "description": "Office stationery items"},
    {"code": "ELEC-MOB", "name": "Mobile Phones", "parent": "ELEC", "description": "Mobile phones and accessories"},
    {"code": "ELEC-COMP", "name": "Computers", "parent": "ELEC", "description": "Computers and accessories"},
    {"code": "FURN-OFF", "name": "Office Furniture", "parent": "FURN", "description": "Office furniture items"},
    {"code": "FURN-HOME", "name": "Home Furniture", "parent": "FURN", "description": "Home furniture items"},
]

created_groups = {}
# First pass - create all groups without parents
for group in item_groups:
    if group["parent"] is None:
        obj, created = ItemGroup.objects.get_or_create(
            code=group["code"],
            defaults={
                "name": group["name"],
                "description": group["description"]
            }
        )
        created_groups[group["code"]] = obj
        status = "✅ Created" if created else "⏩ Already exists"
        print(f"{status}: {group['name']} ({group['code']})")

# Second pass - create groups with parents
for group in item_groups:
    if group["parent"] is not None:
        parent = created_groups.get(group["parent"])
        if parent:
            obj, created = ItemGroup.objects.get_or_create(
                code=group["code"],
                defaults={
                    "name": group["name"],
                    "parent": parent,
                    "description": group["description"]
                }
            )
            created_groups[group["code"]] = obj
            status = "✅ Created" if created else "⏩ Already exists"
            print(f"{status}: {group['name']} ({group['code']}) - Parent: {parent.name}")

# STEP 4: Items
items_list = [
    {
        "code": "PHONE-001",
        "name": "Smartphone X1",
        "description": "Latest smartphone with advanced features",
        "item_group": created_groups["ELEC-MOB"],
        "inventory_uom": created_uoms["PCS"],
        "purchase_uom": created_uoms["PCS"],
        "sales_uom": created_uoms["PCS"],
        "default_warehouse": created_warehouses["MAIN"],
        "barcode": "8901234567890",
        "unit_price": Decimal("25000.00"),
        "item_cost": Decimal("20000.00"),
        "selling_price": Decimal("25000.00"),
        "minimum_stock": Decimal("10"),
        "maximum_stock": Decimal("100"),
        "reorder_point": Decimal("20")
    },
    {
        "code": "LAPTOP-001",
        "name": "Business Laptop Pro",
        "description": "High-performance laptop for business use",
        "item_group": created_groups["ELEC-COMP"],
        "inventory_uom": created_uoms["PCS"],
        "purchase_uom": created_uoms["PCS"],
        "sales_uom": created_uoms["PCS"],
        "default_warehouse": created_warehouses["MAIN"],
        "barcode": "8901234567891",
        "unit_price": Decimal("65000.00"),
        "item_cost": Decimal("55000.00"),
        "selling_price": Decimal("65000.00"),
        "minimum_stock": Decimal("5"),
        "maximum_stock": Decimal("50"),
        "reorder_point": Decimal("10")
    },
    {
        "code": "DESK-001",
        "name": "Executive Desk",
        "description": "Premium executive office desk",
        "item_group": created_groups["FURN-OFF"],
        "inventory_uom": created_uoms["PCS"],
        "purchase_uom": created_uoms["PCS"],
        "sales_uom": created_uoms["PCS"],
        "default_warehouse": created_warehouses["MAIN"],
        "barcode": "8901234567892",
        "unit_price": Decimal("15000.00"),
        "item_cost": Decimal("12000.00"),
        "selling_price": Decimal("15000.00"),
        "minimum_stock": Decimal("2"),
        "maximum_stock": Decimal("20"),
        "reorder_point": Decimal("5")
    },
    {
        "code": "CHAIR-001",
        "name": "Ergonomic Office Chair",
        "description": "Comfortable ergonomic chair for office use",
        "item_group": created_groups["FURN-OFF"],
        "inventory_uom": created_uoms["PCS"],
        "purchase_uom": created_uoms["PCS"],
        "sales_uom": created_uoms["PCS"],
        "default_warehouse": created_warehouses["MAIN"],
        "barcode": "8901234567893",
        "unit_price": Decimal("8000.00"),
        "item_cost": Decimal("6500.00"),
        "selling_price": Decimal("8000.00"),
        "minimum_stock": Decimal("5"),
        "maximum_stock": Decimal("50"),
        "reorder_point": Decimal("10")
    },
    {
        "code": "SOFA-001",
        "name": "3-Seater Sofa",
        "description": "Comfortable 3-seater sofa for home",
        "item_group": created_groups["FURN-HOME"],
        "inventory_uom": created_uoms["PCS"],
        "purchase_uom": created_uoms["PCS"],
        "sales_uom": created_uoms["PCS"],
        "default_warehouse": created_warehouses["MAIN"],
        "barcode": "8901234567894",
        "unit_price": Decimal("25000.00"),
        "item_cost": Decimal("20000.00"),
        "selling_price": Decimal("25000.00"),
        "minimum_stock": Decimal("2"),
        "maximum_stock": Decimal("20"),
        "reorder_point": Decimal("5")
    },
    {
        "code": "PEN-001",
        "name": "Ballpoint Pen",
        "description": "Standard ballpoint pen",
        "item_group": created_groups["STAT"],
        "inventory_uom": created_uoms["DOZ"],
        "purchase_uom": created_uoms["BOX"],
        "sales_uom": created_uoms["PCS"],
        "default_warehouse": created_warehouses["MAIN"],
        "barcode": "8901234567895",
        "unit_price": Decimal("15.00"),
        "item_cost": Decimal("10.00"),
        "selling_price": Decimal("15.00"),
        "minimum_stock": Decimal("100"),
        "maximum_stock": Decimal("1000"),
        "reorder_point": Decimal("200")
    }
]

created_items = {}
for item_data in items_list:
    item, created = Item.objects.get_or_create(
        code=item_data["code"],
        defaults={
            "name": item_data["name"],
            "description": item_data["description"],
            "item_group": item_data["item_group"],
            "inventory_uom": item_data["inventory_uom"],
            "purchase_uom": item_data["purchase_uom"],
            "sales_uom": item_data["sales_uom"],
            "default_warehouse": item_data["default_warehouse"],
            "barcode": item_data["barcode"],
            "unit_price": item_data["unit_price"],
            "item_cost": item_data["item_cost"],
            "selling_price": item_data["selling_price"],
            "minimum_stock": item_data["minimum_stock"],
            "maximum_stock": item_data["maximum_stock"],
            "reorder_point": item_data["reorder_point"]
        }
    )
    created_items[item_data["code"]] = item
    status = "✅ Created" if created else "⏩ Already exists"
    print(f"{status}: {item_data['name']} ({item_data['code']})")

# STEP 5: Item Warehouse Info
for item_code, item in created_items.items():
    # Add stock to main warehouse
    main_wh = created_warehouses["MAIN"]
    initial_stock = item.minimum_stock * 2  # Just a simple calculation for demo data
    
    item_wh_info, created = ItemWarehouseInfo.objects.get_or_create(
        item=item,
        warehouse=main_wh,
        defaults={
            "in_stock": initial_stock,
            "committed": Decimal("0"),
            "ordered": Decimal("0"),
            "min_stock": item.minimum_stock,
            "max_stock": item.maximum_stock,
            "reorder_point": item.reorder_point
        }
    )
    
    if not created:
        # Update stock if it already exists
        item_wh_info.in_stock = initial_stock
        item_wh_info.min_stock = item.minimum_stock
        item_wh_info.max_stock = item.maximum_stock
        item_wh_info.reorder_point = item.reorder_point
        item_wh_info.save()
    
    status = "✅ Created" if created else "⏩ Updated"
    print(f"{status}: Warehouse Info for {item.name} at {main_wh.name} - Stock: {initial_stock}")
    
    # Add some stock to other warehouses (less than main)
    for wh_code in ["CTG", "SYL"]:
        wh = created_warehouses[wh_code]
        secondary_stock = item.minimum_stock * 1  # Less stock in secondary warehouses
        
        item_wh_info, created = ItemWarehouseInfo.objects.get_or_create(
            item=item,
            warehouse=wh,
            defaults={
                "in_stock": secondary_stock,
                "committed": Decimal("0"),
                "ordered": Decimal("0"),
                "min_stock": item.minimum_stock / 2,  # Lower minimums for secondary warehouses
                "max_stock": item.maximum_stock / 2,
                "reorder_point": item.reorder_point / 2
            }
        )
        
        if not created:
            # Update stock if it already exists
            item_wh_info.in_stock = secondary_stock
            item_wh_info.min_stock = item.minimum_stock / 2
            item_wh_info.max_stock = item.maximum_stock / 2
            item_wh_info.reorder_point = item.reorder_point / 2
            item_wh_info.save()
        
        status = "✅ Created" if created else "⏩ Updated"
        print(f"{status}: Warehouse Info for {item.name} at {wh.name} - Stock: {secondary_stock}")

print("✅ Inventory demo data loaded successfully.")