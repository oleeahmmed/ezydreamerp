/**
 * Item Autocomplete - Handles searching and autocompleting item information
 * 
 * This script:
 * 1. Adds autocomplete functionality to item code and name fields
 * 2. Fetches item data from the server
 * 3. Populates row fields with selected item data
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get references to the form elements
    const formsetBody = document.getElementById('formsetBody');
    
    // Set up event delegation for item code inputs
    if (formsetBody) {
        // Listen for input events on item code inputs
        formsetBody.addEventListener('input', function(e) {
            if (e.target.classList.contains('item-code-input')) {
                handleItemCodeInput(e.target);
            }
        });
        
        // Listen for blur events on item code inputs
        formsetBody.addEventListener('blur', function(e) {
            if (e.target.classList.contains('item-code-input')) {
                validateItemCode(e.target);
            }
        }, true);
    }
    
    // Handle item code input
    function handleItemCodeInput(input) {
        const itemCode = input.value.trim();
        
        // Clear any existing dropdown
        const existingDropdown = document.querySelector('.item-dropdown');
        if (existingDropdown) {
            existingDropdown.remove();
        }
        
        // Only search if we have at least 2 characters
        if (itemCode.length < 2) return;
        
        // Search for items
        searchItems(itemCode, function(items) {
            if (items.length > 0) {
                showItemDropdown(items, input);
            }
        });
    }
    
    // Validate item code on blur
    function validateItemCode(input) {
        const itemCode = input.value.trim();
        
        if (itemCode) {
            // Find the row
            const row = input.closest('.formset-row');
            
            // Fetch item details
            fetch(`/inventory/api/items/by-code/${itemCode}/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Item not found');
                    }
                    return response.json();
                })
                .then(data => {
                    // Populate row with item data
                    populateRowWithItemData(row, data);
                })
                .catch(error => {
                    console.error('Error fetching item details:', error);
                });
        }
    }
    
    // Search items by query
    function searchItems(query, callback) {
        fetch(`/inventory/api/items/search/?query=${encodeURIComponent(query)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                callback(data.items);
            })
            .catch(error => {
                console.error('Error searching items:', error);
                callback([]);
            });
    }
    
    // Show dropdown with search results
    function showItemDropdown(items, input) {
        // Create dropdown element
        const dropdown = document.createElement('div');
        dropdown.className = 'item-dropdown absolute z-50 bg-[hsl(var(--background))] border border-[hsl(var(--border))] rounded-md shadow-lg max-h-60 overflow-y-auto';
        
        // Position dropdown
        const rect = input.getBoundingClientRect();
        dropdown.style.width = `${rect.width}px`;
        dropdown.style.left = `${rect.left}px`;
        dropdown.style.top = `${rect.bottom + window.scrollY}px`;
        
        // Add items to dropdown
        items.forEach(item => {
            const option = document.createElement('div');
            option.className = 'p-2 hover:bg-[hsl(var(--accent))] cursor-pointer text-sm';
            option.textContent = `${item.code} - ${item.name}`;
            
            option.addEventListener('click', function() {
                // Set the item code in the input
                input.value = item.code;
                
                // Find the row
                const row = input.closest('.formset-row');
                
                // Populate row with item data
                populateRowWithItemData(row, item);
                
                // Remove dropdown
                dropdown.remove();
            });
            
            dropdown.appendChild(option);
        });
        
        // Add dropdown to document
        document.body.appendChild(dropdown);
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function closeDropdown(e) {
            if (!dropdown.contains(e.target) && e.target !== input) {
                dropdown.remove();
                document.removeEventListener('click', closeDropdown);
            }
        });
    }
    
    // Populate row with item data
    function populateRowWithItemData(row, item) {
        if (!row) return;
        
        // Get all the inputs in the row
        const itemNameInput = row.querySelector('.item-name-input');
        const unitInput = row.querySelector('.unit-input');
        const unitPriceInput = row.querySelector('.unit-price-input');
        const quantityInput = row.querySelector('.quantity-input');
        const totalInput = row.querySelector('.total-input');
        
        // Update the inputs with item data
        if (itemNameInput) {
            itemNameInput.value = item.name;
        }
        
        if (unitInput) {
            unitInput.value = item.uom || 'Pcs';
        }
        
        if (unitPriceInput && (!unitPriceInput.value || parseFloat(unitPriceInput.value) === 0)) {
            unitPriceInput.value = item.standard_price || '0.00';
        }
        
        // Set default quantity if empty
        if (quantityInput && (!quantityInput.value || parseFloat(quantityInput.value) === 0)) {
            quantityInput.value = '1';
        }
        
        // Calculate row total
        if (window.calculateRowTotal) {
            window.calculateRowTotal(row);
        } else {
            // Fallback calculation if the global function isn't available
            if (quantityInput && unitPriceInput && totalInput) {
                const quantity = parseFloat(quantityInput.value) || 0;
                const unitPrice = parseFloat(unitPriceInput.value) || 0;
                totalInput.value = (quantity * unitPrice).toFixed(2);
            }
        }
    }
});