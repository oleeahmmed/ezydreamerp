/**
 * Mobile Formset Handler - Manages mobile view formset operations
 * 
 * Features:
 * 1. Handles adding rows above/below in mobile view
 * 2. Handles deleting rows in mobile view
 * 3. Manages the mobile context menu
 * 4. Syncs changes between mobile and desktop views
 */
document.addEventListener('DOMContentLoaded', function() {
    // Mobile elements
    const mobileFormsetContainer = document.getElementById('mobileFormsetContainer');
    const mobileContextMenu = document.getElementById('mobileContextMenu');
    const mobileAddRowAboveBtn = document.getElementById('mobileAddRowAboveBtn');
    const mobileAddRowBelowBtn = document.getElementById('mobileAddRowBelowBtn');
    const mobileDeleteRowBtn = document.getElementById('mobileDeleteRowBtn');
    const addRowBtn = document.getElementById('addRowBtn');
    const totalForms = document.querySelector('[name$="-TOTAL_FORMS"]');
    
    let currentMobileRow = null;
    
    // Handle mobile context menu buttons
    if (mobileFormsetContainer) {
        setupMobileContextMenuButtons();
        
        // Initial setup for existing rows
        setupMobileEventListeners();
    }
    
    // Add row at the end for mobile
    if (addRowBtn) {
        addRowBtn.addEventListener('click', function() {
            // Add to mobile view
            if (mobileFormsetContainer) {
                const newMobileRow = createEmptyMobileRow();
                mobileFormsetContainer.appendChild(newMobileRow);
                reindexMobileForms();
                setupMobileRowEventListeners(newMobileRow);
                
                // Update total forms count
                if (totalForms) {
                    totalForms.value = mobileFormsetContainer.querySelectorAll('.mobile-formset-row').length;
                }
            }
        });
    }
    
    // Mobile: Add row above current row
    if (mobileAddRowAboveBtn) {
        mobileAddRowAboveBtn.addEventListener('click', function() {
            if (currentMobileRow && mobileFormsetContainer) {
                const newRow = createEmptyMobileRow();
                currentMobileRow.parentNode.insertBefore(newRow, currentMobileRow);
                mobileContextMenu.style.display = 'none';
                reindexMobileForms();
                setupMobileRowEventListeners(newRow);
                
                // Sync with desktop view
                syncDesktopFromMobile();
            }
        });
    }
    
    // Mobile: Add row below current row
    if (mobileAddRowBelowBtn) {
        mobileAddRowBelowBtn.addEventListener('click', function() {
            if (currentMobileRow && mobileFormsetContainer) {
                const newRow = createEmptyMobileRow();
                currentMobileRow.parentNode.insertBefore(newRow, currentMobileRow.nextSibling);
                mobileContextMenu.style.display = 'none';
                reindexMobileForms();
                setupMobileRowEventListeners(newRow);
                
                // Sync with desktop view
                syncDesktopFromMobile();
            }
        });
    }
    
    // Mobile: Delete current row
    if (mobileDeleteRowBtn) {
        mobileDeleteRowBtn.addEventListener('click', function() {
            if (currentMobileRow && mobileFormsetContainer && mobileFormsetContainer.querySelectorAll('.mobile-formset-row').length > 1) {
                const deleteCheckbox = currentMobileRow.querySelector('.delete-checkbox');
                if (deleteCheckbox) {
                    deleteCheckbox.checked = true;
                    currentMobileRow.style.display = 'none';
                } else {
                    currentMobileRow.remove();
                }
                mobileContextMenu.style.display = 'none';
                reindexMobileForms();
                
                // Sync with desktop view
                syncDesktopFromMobile();
            }
        });
    }
    
    // Hide context menus on click outside
    document.addEventListener('click', function(e) {
        if (mobileContextMenu && !mobileContextMenu.contains(e.target)) {
            mobileContextMenu.style.display = 'none';
        }
    });
    
    // Hide context menus on scroll
    document.addEventListener('scroll', function() {
        if (mobileContextMenu) {
            mobileContextMenu.style.display = 'none';
        }
    });
    
    // Setup context menu buttons for all mobile rows
    function setupMobileContextMenuButtons() {
        const mobileContextBtns = mobileFormsetContainer.querySelectorAll('.mobile-context-btn');
        mobileContextBtns.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                const mobileRow = e.target.closest('.mobile-formset-row');
                if (mobileRow) {
                    currentMobileRow = mobileRow;
                    
                    // Get button position
                    const rect = btn.getBoundingClientRect();
                    
                    // Position menu and show
                    mobileContextMenu.style.left = `${rect.right}px`;
                    mobileContextMenu.style.top = `${rect.bottom}px`;
                    mobileContextMenu.style.display = 'block';
                }
            });
        });
    }
    
    // Reindex mobile forms
    function reindexMobileForms() {
        if (!mobileFormsetContainer || !totalForms) return;
        
        const rows = mobileFormsetContainer.querySelectorAll('.mobile-formset-row');
        rows.forEach((row, index) => {
            row.querySelectorAll('input, select').forEach(element => {
                updateFormIndex(element, index);
            });
        });
        totalForms.value = rows.length;
    }
    
    // Update form indices
    function updateFormIndex(element, index) {
        if (element.id) {
            element.id = element.id.replace(/-\d+-/, `-${index}-`);
        }
        if (element.name) {
            element.name = element.name.replace(/-\d+-/, `-${index}-`);
        }
    }
    
    // Create a new mobile row
    function createEmptyMobileRow() {
        if (!mobileFormsetContainer) return null;
        
        const template = mobileFormsetContainer.querySelector('.mobile-formset-row').cloneNode(true);
        template.querySelectorAll('input:not([type="hidden"]):not([readonly]), select').forEach(input => {
            if (input.type === 'checkbox') {
                input.checked = false;
            } else {
                input.value = '';
            }
        });
        const idField = template.querySelector('input[name$="-id"]');
        if (idField) {
            idField.value = '';
        }
        return template;
    }
    
    // Sync desktop view from mobile changes
    function syncDesktopFromMobile() {
        const formsetBody = document.getElementById('formsetBody');
        if (!formsetBody || !mobileFormsetContainer) return;
        
        // Get all form data from mobile view
        const mobileRows = mobileFormsetContainer.querySelectorAll('.mobile-formset-row');
        
        // Clear desktop rows and rebuild
        while (formsetBody.firstChild) {
            formsetBody.removeChild(formsetBody.firstChild);
        }
        
        // Create desktop rows based on mobile
        mobileRows.forEach((mobileRow, index) => {
            if (mobileRow.style.display !== 'none') {
                // Create a new desktop row
                const desktopRow = createDesktopRow();
                
                // Sync field values
                const fields = ['item-code', 'item-name', 'quantity', 'unit-price', 'stock', 'uom', 'total-amount'];
                fields.forEach((field, fieldIndex) => {
                    const mobileInput = mobileRow.querySelector(`.${field}-input`);
                    const desktopInput = desktopRow.querySelector(`td:nth-child(${fieldIndex + 1}) input`);
                    
                    if (mobileInput && desktopInput) {
                        desktopInput.value = mobileInput.value;
                    }
                });
                
                // Add to desktop
                formsetBody.appendChild(desktopRow);
                setupDesktopRowEventListeners(desktopRow);
            }
        });
        
        reindexDesktopForms();
    }
    
    // Create a new desktop row
    function createDesktopRow() {
        const formsetBody = document.getElementById('formsetBody');
        if (!formsetBody) return null;
        
        const template = formsetBody.querySelector('tr.formset-row').cloneNode(true);
        template.querySelectorAll('input:not([type="hidden"]):not([readonly]), select').forEach(input => {
            if (input.type === 'checkbox') {
                input.checked = false;
            } else {
                input.value = '';
            }
        });
        const idField = template.querySelector('input[name$="-id"]');
        if (idField) {
            idField.value = '';
        }
        return template;
    }
    
    // Reindex desktop forms
    function reindexDesktopForms() {
        const formsetBody = document.getElementById('formsetBody');
        if (!formsetBody || !totalForms) return;
        
        const rows = formsetBody.querySelectorAll('tr.formset-row');
        rows.forEach((row, index) => {
            row.querySelectorAll('input, select').forEach(element => {
                updateFormIndex(element, index);
            });
        });
        totalForms.value = rows.length;
    }
    
    // Setup desktop row event listeners
    function setupDesktopRowEventListeners(row) {
        const deleteBtn = row.querySelector('.delete-row');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function() {
                const formsetBody = document.getElementById('formsetBody');
                if (formsetBody && formsetBody.querySelectorAll('tr.formset-row').length > 1) {
                    const deleteCheckbox = row.querySelector('.delete-checkbox');
                    if (deleteCheckbox) {
                        deleteCheckbox.checked = true;
                        row.style.display = 'none';
                    } else {
                        row.remove();
                    }
                    reindexDesktopForms();
                    
                    // Sync with mobile view
                    rebuildMobileView();
                }
            });
        }

        const quantityInput = row.querySelector('td:nth-child(3) input');
        const unitPriceInput = row.querySelector('td:nth-child(4) input');
        const totalAmountInput = row.querySelector('td:nth-child(7) input');

        if (quantityInput && unitPriceInput && totalAmountInput) {
            const calculateTotal = function() {
                const quantity = parseFloat(quantityInput.value) || 0;
                const unitPrice = parseFloat(unitPriceInput.value) || 0;
                totalAmountInput.value = (quantity * unitPrice).toFixed(2);
            };

            quantityInput.addEventListener('input', function() {
                calculateTotal();
                syncForms();
            });
            unitPriceInput.addEventListener('input', function() {
                calculateTotal();
                syncForms();
            });
            calculateTotal();
        }
    }
    
    // Rebuild mobile view based on desktop
    function rebuildMobileView() {
        const formsetBody = document.getElementById('formsetBody');
        if (!formsetBody || !mobileFormsetContainer) return;
        
        // Clear mobile container
        mobileFormsetContainer.innerHTML = '';
        
        // Clone management form
        const managementForm = document.querySelector('[name$="-TOTAL_FORMS"]').parentNode.cloneNode(true);
        mobileFormsetContainer.appendChild(managementForm);
        
        // Get all visible desktop rows
        const desktopRows = formsetBody.querySelectorAll('tr.formset-row');
        
        // Create mobile rows based on desktop
        desktopRows.forEach((row, index) => {
            if (row.style.display !== 'none') {
                const mobileRow = createMobileRow(row, index);
                mobileFormsetContainer.appendChild(mobileRow);
            }
        });
        
        // Setup event listeners for new mobile rows
        setupMobileEventListeners();
    }
    
    // Create a new mobile row based on desktop row
    function createMobileRow(desktopRow, index) {
        const template = document.createElement('div');
        template.className = 'p-3 border border-[hsl(var(--border))] rounded-lg mobile-formset-row relative';
        
        // Add context menu button
        template.innerHTML = `
            <button type="button" class="mobile-context-btn absolute top-2 right-2 w-6 h-6 rounded-full bg-[hsl(var(--muted))] flex items-center justify-center">
                <svg class="w-4 h-4 text-[hsl(var(--muted-foreground))]" viewBox="0 0 24 24" fill="none">
                    <path d="M12 5V5.01M12 12V12.01M12 19V19.01M12 6C11.4477 6 11 5.55228 11 5C11 4.44772 11.4477 4 12 4C12.5523 4 13 4.44772 13 5C13 5.55228 12.5523 6 12 6ZM12 13C11.4477 13 11 12.5523 11 12C11 11.4477 11.4477 11 12 11C12.5523 11 13 11.4477 13 12C13 12.5523 12.5523 13 12 13ZM12 20C11.4477 20 11 19.5523 11 19C11 18.4477 11.4477 18 12 18C12.5523 18 13 18.4477 13 19C13 19.5523 12.5523 20 12 20Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
        `;
        
        // Copy hidden fields
        const idField = desktopRow.querySelector('input[name$="-id"]');
        if (idField) {
            const idClone = idField.cloneNode(true);
            template.appendChild(idClone);
        }
        
        const inventoryField = desktopRow.querySelector('input[name$="-is_inventory_item"]');
        if (inventoryField) {
            const inventoryClone = inventoryField.cloneNode(true);
            template.appendChild(inventoryClone);
        }
        
        // Create content container
        const contentDiv = document.createElement('div');
        contentDiv.className = 'space-y-2';
        
        // Item Code and Name
        const itemCodeNameDiv = document.createElement('div');
        itemCodeNameDiv.className = 'grid grid-cols-2 gap-2';
        itemCodeNameDiv.innerHTML = `
            <div>
                <label class="text-xs font-medium mb-1 block">Item Code</label>
                <input type="text" name="${desktopRow.querySelector('td:nth-child(1) input').name}" 
                    value="${desktopRow.querySelector('td:nth-child(1) input').value}" 
                    class="w-full px-2 py-1 text-sm border rounded-md bg-[hsl(var(--background))] item-code-input">
            </div>
            <div>
                <label class="text-xs font-medium mb-1 block">Item Name</label>
                <input type="text" name="${desktopRow.querySelector('td:nth-child(2) input').name}" 
                    value="${desktopRow.querySelector('td:nth-child(2) input').value}"
                    class="w-full px-2 py-1 text-sm border rounded-md bg-[hsl(var(--background))] item-name-input">
            </div>
        `;
        contentDiv.appendChild(itemCodeNameDiv);
        
        // Quantity and Price
        const quantityPriceDiv = document.createElement('div');
        quantityPriceDiv.className = 'grid grid-cols-2 gap-2';
        quantityPriceDiv.innerHTML = `
            <div>
                <label class="text-xs font-medium mb-1 block">Quantity</label>
                <input type="number" name="${desktopRow.querySelector('td:nth-child(3) input').name}" 
                    value="${desktopRow.querySelector('td:nth-child(3) input').value}"
                    class="w-full px-2 py-1 text-sm border rounded-md bg-[hsl(var(--background))] quantity-input">
            </div>
            <div>
                <label class="text-xs font-medium mb-1 block">Unit Price</label>
                <input type="number" name="${desktopRow.querySelector('td:nth-child(4) input').name}" 
                    value="${desktopRow.querySelector('td:nth-child(4) input').value}"
                    class="w-full px-2 py-1 text-sm border rounded-md bg-[hsl(var(--background))] unit-price-input">
            </div>
        `;
        contentDiv.appendChild(quantityPriceDiv);
        
        // Stock and UOM
        const stockUomDiv = document.createElement('div');
        stockUomDiv.className = 'grid grid-cols-2 gap-2';
        stockUomDiv.innerHTML = `
            <div>
                <label class="text-xs font-medium mb-1 block">Stock</label>
                <input type="number" name="stock_quantity" readonly
                    value="${desktopRow.querySelector('td:nth-child(5) input').value}"
                    class="w-full px-2 py-1 text-sm border rounded-md bg-[hsl(var(--muted))] stock-input">
            </div>
            <div>
                <label class="text-xs font-medium mb-1 block">UOM</label>
                <input type="text" name="${desktopRow.querySelector('td:nth-child(6) input').name}" 
                    value="${desktopRow.querySelector('td:nth-child(6) input').value}"
                    class="w-full px-2 py-1 text-sm border rounded-md bg-[hsl(var(--background))] uom-input">
            </div>
        `;
        contentDiv.appendChild(stockUomDiv);
        
        // Total Amount
        const totalAmountDiv = document.createElement('div');
        totalAmountDiv.className = 'border-t pt-2 mt-2';
        totalAmountDiv.innerHTML = `
            <div class="flex justify-between items-center">
                <label class="text-xs font-medium">Total Amount:</label>
                <input type="number" name="${desktopRow.querySelector('td:nth-child(7) input').name}" 
                    value="${desktopRow.querySelector('td:nth-child(7) input').value}" readonly
                    class="w-24 px-2 py-1 text-sm border rounded-md bg-[hsl(var(--muted))] text-right font-medium total-amount-input">
            </div>
        `;
        contentDiv.appendChild(totalAmountDiv);
        
        // Delete Button
        const deleteDiv = document.createElement('div');
        deleteDiv.className = 'flex justify-end mt-2';
        
        // Get delete checkbox
        const deleteCheckbox = desktopRow.querySelector('.delete-checkbox');
        if (deleteCheckbox) {
            const deleteCheckboxClone = deleteCheckbox.cloneNode(true);
            deleteDiv.appendChild(deleteCheckboxClone);
        }
        
        deleteDiv.innerHTML += `
            <button type="button" class="delete-row inline-flex items-center px-2 py-1 text-xs font-medium text-red-600 hover:text-red-700">
                <svg class="w-4 h-4 mr-1" viewBox="0 0 24 24" fill="none">
                    <path d="M19 7L18.1327 19.1425C18.0579 20.1891 17.187 21 16.1378 21H7.86224C6.81296 21 5.94208 20.1891 5.86732 19.1425L5 7M10 11V17M14 11V17M15 7V4C15 3.44772 14.5523 3 14 3H10C9.44772 3 9 3.44772 9 4V7M4 7H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Delete
            </button>
        `;
        contentDiv.appendChild(deleteDiv);
        
        template.appendChild(contentDiv);
        return template;
    }
    
    // Sync forms between mobile and desktop
    function syncForms() {
        const formsetBody = document.getElementById('formsetBody');
        if (!formsetBody || !mobileFormsetContainer) return;
        
        // Get all form data from desktop view
        const desktopRows = formsetBody.querySelectorAll('tr.formset-row');
        const mobileRows = mobileFormsetContainer.querySelectorAll('.mobile-formset-row');
        
        // If counts don't match, we need to sync
        if (desktopRows.length !== mobileRows.length) {
            // Rebuild mobile view based on desktop
            rebuildMobileView();
        } else {
            // Sync values between views
            desktopRows.forEach((row, index) => {
                const mobileRow = mobileRows[index];
                
                // Sync each field
                const fields = ['item-code', 'item-name', 'quantity', 'unit-price', 'stock', 'uom', 'total-amount'];
                fields.forEach(field => {
                    const desktopInput = row.querySelector(`.${field}-input`);
                    const mobileInput = mobileRow.querySelector(`.${field}-input`);
                    
                    if (desktopInput && mobileInput) {
                        // Sync from desktop to mobile
                        mobileInput.value = desktopInput.value;
                    }
                });
                
                // Sync delete checkbox
                const desktopDeleteCheckbox = row.querySelector('.delete-checkbox');
                const mobileDeleteCheckbox = mobileRow.querySelector('.delete-checkbox');
                if (desktopDeleteCheckbox && mobileDeleteCheckbox) {
                    mobileDeleteCheckbox.checked = desktopDeleteCheckbox.checked;
                    if (desktopDeleteCheckbox.checked) {
                        mobileRow.style.display = 'none';
                    }
                }
            });
        }
    }
    
    function setupMobileRowEventListeners(row) {
        // Setup context menu button
        const contextBtn = row.querySelector('.mobile-context-btn');
        if (contextBtn) {
            contextBtn.addEventListener('click', function(e) {
                e.preventDefault();
                currentMobileRow = row;
                
                // Get button position
                const rect = contextBtn.getBoundingClientRect();
                
                // Position menu and show
                mobileContextMenu.style.left = `${rect.right}px`;
                mobileContextMenu.style.top = `${rect.bottom}px`;
                mobileContextMenu.style.display = 'block';
            });
        }
        
        // Setup delete button
        const deleteBtn = row.querySelector('.delete-row');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function() {
                if (mobileFormsetContainer.querySelectorAll('.mobile-formset-row').length > 1) {
                    const deleteCheckbox = row.querySelector('.delete-checkbox');
                    if (deleteCheckbox) {
                        deleteCheckbox.checked = true;
                        row.style.display = 'none';
                    } else {
                        row.remove();
                    }
                    reindexMobileForms();
                    
                    // Sync with desktop view
                    syncDesktopFromMobile();
                }
            });
        }
        
        // Setup calculation
        const quantityInput = row.querySelector('.quantity-input');
        const unitPriceInput = row.querySelector('.unit-price-input');
        const totalAmountInput = row.querySelector('.total-amount-input');
        
        if (quantityInput && unitPriceInput && totalAmountInput) {
            const calculateTotal = function() {
                const quantity = parseFloat(quantityInput.value) || 0;
                const unitPrice = parseFloat(unitPriceInput.value) || 0;
                totalAmountInput.value = (quantity * unitPrice).toFixed(2);
            };
            
            quantityInput.addEventListener('input', function() {
                calculateTotal();
                syncDesktopFromMobile();
            });
            unitPriceInput.addEventListener('input', function() {
                calculateTotal();
                syncDesktopFromMobile();
            });
            calculateTotal();
        }
    }
    
    function setupMobileEventListeners() {
        const mobileRows = mobileFormsetContainer.querySelectorAll('.mobile-formset-row');
        mobileRows.forEach(row => {
            setupMobileRowEventListeners(row);
        });
    }
    
    // Set up a mutation observer to detect when new rows are added
    const observer = new MutationObserver(function(mutations) {
        let needsUpdate = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                needsUpdate = true;
            }
        });
        
        if (needsUpdate && mobileFormsetContainer) {
            // Add a small delay to ensure DOM is fully updated
            setTimeout(setupMobileContextMenuButtons, 10);
        }
    });
    
    if (mobileFormsetContainer) {
        observer.observe(mobileFormsetContainer, { 
            childList: true, 
            subtree: true 
        });
    }
});