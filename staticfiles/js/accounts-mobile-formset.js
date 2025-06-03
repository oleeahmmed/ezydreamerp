/**
 * Accounts Mobile Formset Handler - Manages mobile view formset operations for journal entries
 * 
 * Features:
 * 1. Handles adding rows above/below in mobile view
 * 2. Handles deleting rows in mobile view
 * 3. Manages the mobile context menu
 * 4. Syncs changes between mobile and desktop views
 * 5. Supports searchable dropdowns for account and cost center fields
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
                
                // Apply searchable to new account select
                const newAccountSelect = newMobileRow.querySelector('.account-select');
                if (newAccountSelect && typeof makeSelectSearchable === 'function') {
                    makeSelectSearchable(newAccountSelect.getAttribute('name'));
                }
                
                // Apply searchable to new cost center select
                const newCostCenterSelect = newMobileRow.querySelector('.cost-center-select');
                if (newCostCenterSelect && typeof makeSelectSearchable === 'function') {
                    makeSelectSearchable(newCostCenterSelect.getAttribute('name'));
                }
                
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
                
                // Apply searchable to new account select
                const newAccountSelect = newRow.querySelector('.account-select');
                if (newAccountSelect && typeof makeSelectSearchable === 'function') {
                    makeSelectSearchable(newAccountSelect.getAttribute('name'));
                }
                
                // Apply searchable to new cost center select
                const newCostCenterSelect = newRow.querySelector('.cost-center-select');
                if (newCostCenterSelect && typeof makeSelectSearchable === 'function') {
                    makeSelectSearchable(newCostCenterSelect.getAttribute('name'));
                }
                
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
                
                // Apply searchable to new account select
                const newAccountSelect = newRow.querySelector('.account-select');
                if (newAccountSelect && typeof makeSelectSearchable === 'function') {
                    makeSelectSearchable(newAccountSelect.getAttribute('name'));
                }
                
                // Apply searchable to new cost center select
                const newCostCenterSelect = newRow.querySelector('.cost-center-select');
                if (newCostCenterSelect && typeof makeSelectSearchable === 'function') {
                    makeSelectSearchable(newCostCenterSelect.getAttribute('name'));
                }
                
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
                const accountSelect = mobileRow.querySelector('.account-select');
                const descriptionInput = mobileRow.querySelector('input[name$="-description"]');
                const debitInput = mobileRow.querySelector('.debit-amount-input');
                const creditInput = mobileRow.querySelector('.credit-amount-input');
                const costCenterSelect = mobileRow.querySelector('.cost-center-select');
                
                if (accountSelect) {
                    const desktopAccountSelect = desktopRow.querySelector('td:nth-child(1) select');
                    if (desktopAccountSelect) {
                        desktopAccountSelect.value = accountSelect.value;
                    }
                }
                
                if (descriptionInput) {
                    const desktopDescriptionInput = desktopRow.querySelector('td:nth-child(2) input');
                    if (desktopDescriptionInput) {
                        desktopDescriptionInput.value = descriptionInput.value;
                    }
                }
                
                if (debitInput) {
                    const desktopDebitInput = desktopRow.querySelector('td:nth-child(3) input');
                    if (desktopDebitInput) {
                        desktopDebitInput.value = debitInput.value;
                    }
                }
                
                if (creditInput) {
                    const desktopCreditInput = desktopRow.querySelector('td:nth-child(4) input');
                    if (desktopCreditInput) {
                        desktopCreditInput.value = creditInput.value;
                    }
                }
                
                if (costCenterSelect) {
                    const desktopCostCenterSelect = desktopRow.querySelector('td:nth-child(5) select');
                    if (desktopCostCenterSelect) {
                        desktopCostCenterSelect.value = costCenterSelect.value;
                    }
                }
                
                // Add to desktop
                formsetBody.appendChild(desktopRow);
                setupDesktopRowEventListeners(desktopRow);
                
                // Apply searchable to new account select
                const newAccountSelect = desktopRow.querySelector('.account-select');
                if (newAccountSelect && typeof makeSelectSearchable === 'function') {
                    makeSelectSearchable(newAccountSelect.getAttribute('name'));
                }
                
                // Apply searchable to new cost center select
                const newCostCenterSelect = desktopRow.querySelector('.cost-center-select');
                if (newCostCenterSelect && typeof makeSelectSearchable === 'function') {
                    makeSelectSearchable(newCostCenterSelect.getAttribute('name'));
                }
            }
        });
        
        reindexDesktopForms();
        calculateDifference();
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

        // Calculate difference
        const debitInput = row.querySelector('.debit-amount-input');
        const creditInput = row.querySelector('.credit-amount-input');

        if (debitInput && creditInput) {
            // Allow both debit and credit to have values
            debitInput.addEventListener('input', function() {
                calculateDifference();
                syncForms();
            });

            creditInput.addEventListener('input', function() {
                calculateDifference();
                syncForms();
            });
        }
    }
    
    // Calculate difference between total debit and total credit
    function calculateDifference() {
        const totalDebitField = document.querySelector('[name$="-total_debit"]');
        const totalCreditField = document.querySelector('[name$="-total_credit"]');
        const differenceField = document.getElementById('difference');
        
        if (totalDebitField && totalCreditField && differenceField) {
            const totalDebit = parseFloat(totalDebitField.value) || 0;
            const totalCredit = parseFloat(totalCreditField.value) || 0;
            
            // Calculate difference
            const difference = Math.abs(totalDebit - totalCredit).toFixed(2);
            differenceField.value = difference;
            
            // Highlight difference if not balanced
            if (parseFloat(difference) > 0.01) {
                differenceField.classList.add('bg-red-50', 'text-red-600');
            } else {
                differenceField.classList.remove('bg-red-50', 'text-red-600');
            }
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
                
                // Apply searchable to new account select
                const newAccountSelect = mobileRow.querySelector('.account-select');
                if (newAccountSelect && typeof makeSelectSearchable === 'function') {
                    makeSelectSearchable(newAccountSelect.getAttribute('name'));
                }
                
                // Apply searchable to new cost center select
                const newCostCenterSelect = mobileRow.querySelector('.cost-center-select');
                if (newCostCenterSelect && typeof makeSelectSearchable === 'function') {
                    makeSelectSearchable(newCostCenterSelect.getAttribute('name'));
                }
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
        
        // Create content container
        const contentDiv = document.createElement('div');
        contentDiv.className = 'space-y-2';
        
        // Account and Description
        const accountDescDiv = document.createElement('div');
        accountDescDiv.className = 'grid grid-cols-1 gap-2';
        
        // Account select
        const accountSelectCell = desktopRow.querySelector('td:nth-child(1)');
        if (accountSelectCell) {
            const accountSelect = accountSelectCell.querySelector('select');
            if (accountSelect) {
                const accountDiv = document.createElement('div');
                accountDiv.innerHTML = `
                    <label class="text-xs font-medium mb-1 block">Account</label>
                `;
                
                // Clone the select element
                const accountSelectClone = accountSelect.cloneNode(true);
                accountSelectClone.className = 'premium-input w-full px-2 py-1 text-sm border rounded-md bg-[hsl(var(--background))] account-select';
                accountDiv.appendChild(accountSelectClone);
                accountDescDiv.appendChild(accountDiv);
            }
        }
        
        // Description input
        const descriptionCell = desktopRow.querySelector('td:nth-child(2)');
        if (descriptionCell) {
            const descriptionInput = descriptionCell.querySelector('input');
            if (descriptionInput) {
                const descriptionDiv = document.createElement('div');
                descriptionDiv.innerHTML = `
                    <label class="text-xs font-medium mb-1 block">Description</label>
                `;
                
                // Clone the input element
                const descriptionInputClone = descriptionInput.cloneNode(true);
                descriptionInputClone.className = 'premium-input w-full px-2 py-1 text-sm border rounded-md bg-[hsl(var(--background))]';
                descriptionDiv.appendChild(descriptionInputClone);
                accountDescDiv.appendChild(descriptionDiv);
            }
        }
        
        contentDiv.appendChild(accountDescDiv);
        
        // Debit and Credit
        const debitCreditDiv = document.createElement('div');
        debitCreditDiv.className = 'grid grid-cols-2 gap-2';
        
        // Debit input
        const debitCell = desktopRow.querySelector('td:nth-child(3)');
        if (debitCell) {
            const debitInput = debitCell.querySelector('input');
            if (debitInput) {
                const debitDiv = document.createElement('div');
                debitDiv.innerHTML = `
                    <label class="text-xs font-medium mb-1 block">Debit Amount</label>
                `;
                
                // Clone the input element
                const debitInputClone = debitInput.cloneNode(true);
                debitInputClone.className = 'premium-input w-full px-2 py-1 text-sm border rounded-md bg-[hsl(var(--background))] debit-amount-input';
                debitDiv.appendChild(debitInputClone);
                debitCreditDiv.appendChild(debitDiv);
            }
        }
        
        // Credit input
        const creditCell = desktopRow.querySelector('td:nth-child(4)');
        if (creditCell) {
            const creditInput = creditCell.querySelector('input');
            if (creditInput) {
                const creditDiv = document.createElement('div');
                creditDiv.innerHTML = `
                    <label class="text-xs font-medium mb-1 block">Credit Amount</label>
                `;
                
                // Clone the input element
                const creditInputClone = creditInput.cloneNode(true);
                creditInputClone.className = 'premium-input w-full px-2 py-1 text-sm border rounded-md bg-[hsl(var(--background))] credit-amount-input';
                creditDiv.appendChild(creditInputClone);
                debitCreditDiv.appendChild(creditDiv);
            }
        }
        
        contentDiv.appendChild(debitCreditDiv);
        
        // Cost Center
        const costCenterCell = desktopRow.querySelector('td:nth-child(5)');
        if (costCenterCell) {
            const costCenterSelect = costCenterCell.querySelector('select');
            if (costCenterSelect) {
                const costCenterDiv = document.createElement('div');
                costCenterDiv.innerHTML = `
                    <label class="text-xs font-medium mb-1 block">Cost Center</label>
                `;
                
                // Clone the select element
                const costCenterSelectClone = costCenterSelect.cloneNode(true);
                costCenterSelectClone.className = 'premium-input w-full px-2 py-1 text-sm border rounded-md bg-[hsl(var(--background))] cost-center-select';
                costCenterDiv.appendChild(costCenterSelectClone);
                contentDiv.appendChild(costCenterDiv);
            }
        }
        
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
                
                // Sync account select
                const desktopAccountSelect = row.querySelector('td:nth-child(1) select');
                const mobileAccountSelect = mobileRow.querySelector('.account-select');
                if (desktopAccountSelect && mobileAccountSelect) {
                    mobileAccountSelect.value = desktopAccountSelect.value;
                }
                
                // Sync description input
                const desktopDescriptionInput = row.querySelector('td:nth-child(2) input');
                const mobileDescriptionInput = mobileRow.querySelector('input[name$="-description"]');
                if (desktopDescriptionInput && mobileDescriptionInput) {
                    mobileDescriptionInput.value = desktopDescriptionInput.value;
                }
                
                // Sync debit input
                const desktopDebitInput = row.querySelector('td:nth-child(3) input');
                const mobileDebitInput = mobileRow.querySelector('.debit-amount-input');
                if (desktopDebitInput && mobileDebitInput) {
                    mobileDebitInput.value = desktopDebitInput.value;
                }
                
                // Sync credit input
                const desktopCreditInput = row.querySelector('td:nth-child(4) input');
                const mobileCreditInput = mobileRow.querySelector('.credit-amount-input');
                if (desktopCreditInput && mobileCreditInput) {
                    mobileCreditInput.value = desktopCreditInput.value;
                }
                
                // Sync cost center select
                const desktopCostCenterSelect = row.querySelector('td:nth-child(5) select');
                const mobileCostCenterSelect = mobileRow.querySelector('.cost-center-select');
                if (desktopCostCenterSelect && mobileCostCenterSelect) {
                    mobileCostCenterSelect.value = desktopCostCenterSelect.value;
                }
                
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
        const debitInput = row.querySelector('.debit-amount-input');
        const creditInput = row.querySelector('.credit-amount-input');
        
        if (debitInput && creditInput) {
            debitInput.addEventListener('input', function() {
                calculateDifference();
                syncDesktopFromMobile();
            });
            
            creditInput.addEventListener('input', function() {
                calculateDifference();
                syncDesktopFromMobile();
            });
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