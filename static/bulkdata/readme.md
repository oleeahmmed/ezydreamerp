## ⚙️ রান করার নিয়ম

### 🔹 ধাপ ১: ফাইলটি প্রজেক্ট রুটে রাখো

```
your_project/
├── manage.py
├── load_business_partners.py ✅ (এখানে)
```

### 🔹 ধাপ ২: রান করো Django Shell দিয়ে

```bash
# For BusinessPartnerMasterData
python load_business_partners.py

# For Inventory

python load_inventory.py
# For Finance

python load_finance_demo_data.py

# For Hrm
python load_hrm_demo_data.py

```

📥 এটি রান করার পর ম্যাসেজ আসবে:

```kotlin
✅ Demo data loaded successfully.
```
