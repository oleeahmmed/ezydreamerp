/**
 * Mobile Item Search Modal - Provides a mobile-optimized modal interface for searching and selecting items
 * 
 * Features:
 * 1. Adds a search icon to mobile item code inputs
 * 2. Opens a fullscreen modal with all items when clicked
 * 3. Allows searching/filtering items in the modal
 * 4. Fills the item code input when an item is selected
 * 5. Optimized for touch interactions on mobile devices
 */
document.addEventListener('DOMContentLoaded', function() {
    // Create mobile modal HTML structure once and append to body
    const mobileModalHTML = `
    <div id="mobileItemSearchModal" class="fixed inset-0 z-[9999] hidden bg-[hsl(var(--background))] flex flex-col">
        <div class="p-3 border-b border-[hsl(var(--border))] flex items-center justify-between">
            <h3 class="text-lg font-semibold text-[hsl(var(--foreground))]">Search Items</h3>
            <button type="button" id="mobileItemSearchModalClose" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-[hsl(var(--accent))]">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-5 h-5">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
        <div class="p-3 border-b border-[hsl(var(--border))]">
            <div class="relative">
                <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-5 h-5 text-[hsl(var(--muted-foreground))]">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                </div>
                <input type="text" id="mobileItemSearchInput" class="w-full pl-10 pr-4 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]" placeholder="Search by item code or name...">
            </div>
        </div>
        <div class="flex-1 overflow-y-auto p-1" id="mobileItemSearchResults">
            <div class="flex items-center justify-center h-full text-[hsl(var(--muted-foreground))]">
                Loading items...
            </div>
        </div>
        <div class="p-3 border-t border-[hsl(var(--border))] text-xs text-[hsl(var(--muted-foreground))] text-center">
            <span id="mobileItemCount">0</span> items found
        </div>
    </div>
    `;
    
    // Append modal to body
    const mobileModalContainer = document.createElement('div');
    mobileModalContainer.innerHTML = mobileModalHTML;
    document.body.appendChild(mobileModalContainer.firstElementChild);
    
    // Get modal elements
    const mobileModal = document.getElementById('mobileItemSearchModal');
    const mobileModalClose = document.getElementById('mobileItemSearchModalClose');
    const mobileSearchInput = document.getElementById('mobileItemSearchInput');
    const mobileSearchResults = document.getElementById('mobileItemSearchResults');
    const mobileItemCount = document.getElementById('mobileItemCount');
    
    // Current active input field that triggered the modal
    let currentMobileInputField = null;
    
    // Add search icon to all mobile item code inputs
    function addSearchIconToMobileInputs() {
        const mobileFormsetContainer = document.getElementById('mobileFormsetContainer');
        if (!mobileFormsetContainer) return;
        
        const itemCodeInputs = mobileFormsetContainer.querySelectorAll('.item-code-input');
        
        itemCodeInputs.forEach(input => {
            // Skip if already has search icon
            if (input.parentElement.querySelector('.mobile-item-search-icon')) return;
            
            // Create wrapper if input is not already wrapped
            let wrapper = input.parentElement;
            if (!wrapper.classList.contains('mobile-item-input-wrapper')) {
                wrapper = document.createElement('div');
                wrapper.className = 'mobile-item-input-wrapper relative';
                input.parentNode.insertBefore(wrapper, input);
                wrapper.appendChild(input);
            }
            
            // Add search icon
            const searchIcon = document.createElement('button');
            searchIcon.type = 'button';
            searchIcon.className = 'mobile-item-search-icon absolute right-2 top-1/2 transform -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-full hover:bg-[hsl(var(--accent))] transition-colors';
            searchIcon.setAttribute('data-input-id', input.id);
            searchIcon.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-4 h-4 text-[hsl(var(--muted-foreground))]">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
            `;
            
            wrapper.appendChild(searchIcon);
            
            // Adjust input padding to make room for icon
            input.style.paddingRight = '2.5rem';
        });
    }
    
    // Open modal and load items
    function openMobileModal() {
        mobileModal.classList.remove('hidden');
        mobileSearchInput.value = '';
        mobileSearchInput.focus();
        loadMobileItems(''); // Load all items by default
    }
    
    // Close modal
    function closeMobileModal() {
        mobileModal.classList.add('hidden');
        mobileSearchResults.innerHTML = '';
        currentMobileInputField = null;
    }
    
    // Load items from API
    function loadMobileItems(query = '') {
        mobileSearchResults.innerHTML = '<div class="flex items-center justify-center h-32 text-[hsl(var(--muted-foreground))]">Loading items...</div>';
        
        // Construct the URL with query parameters
        const url = `/inventory/api/items/search/?query=${encodeURIComponent(query)}`;
        
        // Make the AJAX request
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                renderMobileItems(data.items);
                mobileItemCount.textContent = data.items.length;
            })
            .catch(error => {
                console.error('Error loading items:', error);
                mobileSearchResults.innerHTML = `
                    <div class="flex items-center justify-center h-32 text-[hsl(var(--destructive))]">
                        Error loading items. Please try again.
                    </div>
                `;
                mobileItemCount.textContent = '0';
            });
    }
    
    // Render items in the modal
    function renderMobileItems(items) {
        if (items.length === 0) {
            mobileSearchResults.innerHTML = `
                <div class="flex items-center justify-center h-32 text-[hsl(var(--muted-foreground))]">
                    No items found. Try a different search term.
                </div>
            `;
            return;
        }
        
        let html = '<div class="grid grid-cols-1 gap-1 p-2">';
        
        items.forEach(item => {
            html += `
                <div class="mobile-item-result flex items-center p-3 rounded-md hover:bg-[hsl(var(--accent))] active:bg-[hsl(var(--accent))] cursor-pointer transition-colors" 
                     data-item-code="${item.code}" 
                     data-item-name="${item.name}"
                     data-item-uom="${item.uom || ''}"
                     data-item-stock="${item.stock || '0.00'}"
                     data-item-price="${item.unit_price || '0.00'}">
                    <div class="flex-1">
                        <div class="font-medium text-[hsl(var(--foreground))]">${item.code}</div>
                        <div class="text-sm text-[hsl(var(--muted-foreground))]">${item.name}</div>
                    </div>
                    <div class="text-right">
                        <div class="text-sm font-medium text-[hsl(var(--foreground))]">Stock: ${item.stock || '0.00'}</div>
                        <div class="text-xs text-[hsl(var(--muted-foreground))]">${item.uom || 'N/A'}</div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        mobileSearchResults.innerHTML = html;
        
        // Add click event to item results
        const itemResults = mobileSearchResults.querySelectorAll('.mobile-item-result');
        itemResults.forEach(result => {
            result.addEventListener('click', function() {
                selectMobileItem(this);
            });
        });
    }
    
    // Select an item from the modal
    function selectMobileItem(itemElement) {
        if (!currentMobileInputField) return;
        
        const itemCode = itemElement.getAttribute('data-item-code');
        const itemName = itemElement.getAttribute('data-item-name');
        const itemUom = itemElement.getAttribute('data-item-uom');
        const itemStock = itemElement.getAttribute('data-item-stock');
        const itemPrice = itemElement.getAttribute('data-item-price');
        
        // Set the item code in the input field
        currentMobileInputField.value = itemCode;
        
        // Find the row containing the input
        const row = currentMobileInputField.closest('.mobile-formset-row');
        if (row) {
            // Update other fields in the row
            const itemNameInput = row.querySelector('.item-name-input');
            const stockInput = row.querySelector('.stock-input');
            const uomInput = row.querySelector('.uom-input');
            const unitPriceInput = row.querySelector('.unit-price-input');
            const quantityInput = row.querySelector('.quantity-input');
            
            if (itemNameInput) {
                itemNameInput.value = itemName;
                itemNameInput.setAttribute('data-original-value', itemName);
            }
            
            if (stockInput) stockInput.value = itemStock;
            if (uomInput) uomInput.value = itemUom;
            
            // Only set unit price if it's empty or zero
            if (unitPriceInput && (!unitPriceInput.value || parseFloat(unitPriceInput.value) === 0)) {
                unitPriceInput.value = itemPrice;
            }
            
            // Set focus to quantity input if it exists and is empty
            if (quantityInput && (!quantityInput.value || parseFloat(quantityInput.value) === 0)) {
                quantityInput.value = "1.00";
                quantityInput.focus();
                quantityInput.select();
            }
            
            // Trigger change events to update calculations
            if (unitPriceInput) {
                const event = new Event('input', { bubbles: true });
                unitPriceInput.dispatchEvent(event);
            }
            
            // Store original value for validation
            currentMobileInputField.setAttribute('data-original-value', itemCode);
        }
        
        closeMobileModal();
    }
    
    // Event listeners for modal
    mobileModalClose.addEventListener('click', closeMobileModal);
    
    // Search input event
    mobileSearchInput.addEventListener('input', function() {
        const query = this.value.trim();
        loadMobileItems(query);
    });
    
    // Close modal on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !mobileModal.classList.contains('hidden')) {
            closeMobileModal();
        }
    });
    
    // Use event delegation for search icon clicks
    document.addEventListener('click', function(e) {
        // Check if the click was on a search icon or its child (the SVG)
        const searchIcon = e.target.closest('.mobile-item-search-icon');
        if (searchIcon) {
            // Find the associated input field
            const wrapper = searchIcon.closest('.mobile-item-input-wrapper');
            if (wrapper) {
                const input = wrapper.querySelector('.item-code-input');
                if (input) {
                    currentMobileInputField = input;
                    openMobileModal();
                    e.preventDefault();
                    e.stopPropagation();
                }
            }
        }
    });
    
    // Initialize search icons for existing rows
    addSearchIconToMobileInputs();
    
    // Run addSearchIconToMobileInputs periodically to catch any new rows
    setInterval(addSearchIconToMobileInputs, 500);
    
    // Set up a mutation observer to detect when new rows are added
    const mobileFormsetContainer = document.getElementById('mobileFormsetContainer');
    if (mobileFormsetContainer) {
        const observer = new MutationObserver(function(mutations) {
            let needsUpdate = false;
            
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    needsUpdate = true;
                }
            });
            
            if (needsUpdate) {
                // Add a small delay to ensure DOM is fully updated
                setTimeout(addSearchIconToMobileInputs, 10);
            }
        });
        
        observer.observe(mobileFormsetContainer, { 
            childList: true, 
            subtree: true 
        });
    }
});