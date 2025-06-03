/**
 * Formset Manager - Handles Django formset operations
 * 
 * Features:
 * - Add new rows
 * - Delete rows
 * - Context menu for row operations
 * - Supports both desktop and mobile views
 */
function initFormsetManager(config) {
    // Default configuration
    const settings = {
        formsetBodyId: 'formsetBody',
        addRowBtnId: 'addRowBtn',
        contextMenuId: 'contextMenu',
        totalFormsName: 'form-TOTAL_FORMS',
        rowSelector: '.formset-row',
        deleteCheckboxSelector: '.delete-checkbox',
        deleteRowBtnSelector: '.delete-row',
        ...config
    };
    
    // Get DOM elements
    const formsetBody = document.getElementById(settings.formsetBodyId);
    const totalForms = document.querySelector(`[name$="${settings.totalFormsName}"]`);
    const addRowBtn = document.getElementById(settings.addRowBtnId);
    const contextMenu = document.getElementById(settings.contextMenuId);
    
    // Current row for context menu
    let currentRow = null;
    
    // Add Row button
    if (addRowBtn) {
        addRowBtn.addEventListener('click', function() {
            addNewRow();
        });
    }
    
    // Setup context menu for rows
    if (formsetBody) {
        formsetBody.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            const row = e.target.closest(settings.rowSelector);
            if (row) {
                currentRow = row;
                
                // Position and show context menu
                contextMenu.style.left = `${e.pageX}px`;
                contextMenu.style.top = `${e.pageY}px`;
                contextMenu.classList.remove('hidden');
                
                // Add event listener to hide menu when clicking elsewhere
                document.addEventListener('click', hideContextMenu);
            }
        });
    }
    
    // Context menu actions
    if (contextMenu) {
        // Add Row Above
        const addRowAboveBtn = document.getElementById('addRowAboveBtn');
        if (addRowAboveBtn) {
            addRowAboveBtn.addEventListener('click', function() {
                if (currentRow) {
                    const newRow = addNewRow();
                    currentRow.parentNode.insertBefore(newRow, currentRow);
                    hideContextMenu();
                }
            });
        }
        
        // Add Row Below
        const addRowBelowBtn = document.getElementById('addRowBelowBtn');
        if (addRowBelowBtn) {
            addRowBelowBtn.addEventListener('click', function() {
                if (currentRow) {
                    const newRow = addNewRow();
                    if (currentRow.nextSibling) {
                        currentRow.parentNode.insertBefore(newRow, currentRow.nextSibling);
                    } else {
                        currentRow.parentNode.appendChild(newRow);
                    }
                    hideContextMenu();
                }
            });
        }
        
        // Delete Row
        const deleteRowBtn = document.getElementById('deleteRowBtn');
        if (deleteRowBtn) {
            deleteRowBtn.addEventListener('click', function() {
                if (currentRow) {
                    const deleteCheckbox = currentRow.querySelector(settings.deleteCheckboxSelector);
                    if (deleteCheckbox) {
                        deleteCheckbox.checked = true;
                        currentRow.style.display = 'none';
                        
                        // Trigger calculations if needed
                        triggerCalculations();
                    }
                    hideContextMenu();
                }
            });
        }
    }
    
    // Hide context menu
    function hideContextMenu() {
        if (contextMenu) {
            contextMenu.classList.add('hidden');
            document.removeEventListener('click', hideContextMenu);
        }
    }
    
    // Function to add a new row
    function addNewRow() {
        // Get the template from the first row
        let template;
        
        if (formsetBody && formsetBody.querySelector(settings.rowSelector)) {
            template = formsetBody.querySelector(settings.rowSelector).cloneNode(true);
        }
        
        if (!template) {
            console.error("Could not find template row");
            return;
        }
        
        // Get current form count
        const currentFormCount = parseInt(totalForms.value);
        const newIndex = currentFormCount;
        
        // Update form indices
        template.querySelectorAll('input, select').forEach(input => {
            if (input.name) {
                input.name = input.name.replace(/-\d+-/, `-${newIndex}-`);
            }
            if (input.id) {
                input.id = input.id.replace(/-\d+-/, `-${newIndex}-`);
            }
            
            // Clear values except for hidden fields
            if (input.type !== 'hidden' && !input.classList.contains('delete-checkbox')) {
                if (input.classList.contains('quantity-input')) {
                    input.value = '1'; // Default quantity to 1
                } else if (input.classList.contains('unit-input')) {
                    input.value = 'Pcs'; // Default unit to Pcs
                } else if (input.classList.contains('unit-price-input')) {
                    input.value = '0'; // Default unit price to 0
                } else if (input.classList.contains('total-input')) {
                    input.value = '0.00'; // Default total to 0.00
                } else {
                    input.value = '';
                }
            }
        });
        
        // Reset DELETE checkbox
        const deleteCheckbox = template.querySelector(settings.deleteCheckboxSelector);
        if (deleteCheckbox) {
            deleteCheckbox.checked = false;
        }
        
        // Update data-index attribute
        template.dataset.index = newIndex;
        
        // Append to formset body
        formsetBody.appendChild(template);
        
        // Update the form count
        totalForms.value = currentFormCount + 1;
        
        // Initialize the new row with event handlers
        setupRowEventHandlers(template);
        
        return template;
    }
    
    // Setup event handlers for rows
    function setupRowEventHandlers(row) {
        // Setup delete button
        const deleteBtn = row.querySelector(settings.deleteRowBtnSelector);
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function() {
                const deleteCheckbox = row.querySelector(settings.deleteCheckboxSelector);
                if (deleteCheckbox) {
                    deleteCheckbox.checked = true;
                    row.style.display = 'none';
                    
                    // Trigger calculations
                    triggerCalculations();
                }
            });
        }
    }
    
    // Trigger calculations (if needed)
    function triggerCalculations() {
        // Create and dispatch a custom event
        const event = new CustomEvent("rowChanged");
        document.dispatchEvent(event);
    }
    
    // Initialize existing rows
    function initializeAllRows() {
        const rows = document.querySelectorAll(`#${settings.formsetBodyId} ${settings.rowSelector}`);
        rows.forEach(row => {
            setupRowEventHandlers(row);
        });
    }
    
    // Hide context menu on scroll
    document.addEventListener('scroll', function() {
        hideContextMenu();
    }, { passive: true });
    
    // Initialize
    initializeAllRows();
    
    // Return public methods
    return {
        addNewRow,
        hideContextMenu,
        triggerCalculations
    };
}