"""
Django Signals for Finance and Sales Modules
Lazy imports for safety and performance
"""

def register_signals():
    """Register all signals lazily"""
    try:
        # Import and register sales signals
        from . import sales_signals
        print("✅ Sales signals registered")

        # Import and register journal entry signals  
        from . import journal_entry_signals
        print("✅ Journal Entry signals registered")
        
        # Import and register finance signals
        from . import finance_signals
        print("✅ Finance signals registered")
        
    except ImportError as e:
        print(f"❌ Error importing signals: {e}")

# Auto-register signals when module is imported
register_signals()
