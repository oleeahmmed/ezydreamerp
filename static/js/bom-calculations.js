/**
 * BOM Calculations - Handles calculations for Bill of Materials
 * 
 * This script handles:
 * 1. Row total calculations
 * 2. Summary calculations (total component value, additional cost, etc.)
 * 3. Automatic updates when values change
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get references to the form elements
    const formsetBody = document.getElementById('formsetBody');
    const totalComponentValueInput = document.getElementById('id_total_component_value');
    const otherCostPercentageInput = document.getElementById('id_other_cost_percentage');
    const additionalCostInput = document.getElementById('id_additional_cost');
    const totalAfterDiscountInput = document.getElementById('id_total_after_discount');
    
    // Initialize calculations for existing rows
    initializeRowCalculations();
    
    // Calculate initial totals
    calculateTotals();
    
    // Listen for changes on other cost percentage
    if (otherCostPercentageInput) {
        otherCostPercentageInput.addEventListener('input', calculateTotals);
    }
    
    // Listen for row changed events
    document.addEventListener('rowChanged', calculateTotals);
    
    // Initialize calculations for all rows
    function initializeRowCalculations() {
        const rows = document.querySelectorAll('#formsetBody .formset-row');
        rows.forEach(row => {
            setupRowCalculations(row);
        });
    }
    
    // Setup calculations for a single row
    function setupRowCalculations(row) {
        const quantityInput = row.querySelector('.quantity-input');
        const unitPriceInput = row.querySelector('.unit-price-input');
        const totalInput = row.querySelector('.total-input');
        
        if (quantityInput && unitPriceInput && totalInput) {
            // Calculate total when quantity changes
            quantityInput.addEventListener('input', function() {
                calculateRowTotal(row);
            });
            
            // Calculate total when unit price changes
            unitPriceInput.addEventListener('input', function() {
                calculateRowTotal(row);
            });
            
            // Initial calculation for this row
            calculateRowTotal(row);
        }
    }
    
    // Calculate the total for a single row
    function calculateRowTotal(row) {
        const quantityInput = row.querySelector('.quantity-input');
        const unitPriceInput = row.querySelector('.unit-price-input');
        const totalInput = row.querySelector('.total-input');
        
        if (quantityInput && unitPriceInput && totalInput) {
            const quantity = parseFloat(quantityInput.value) || 0;
            const unitPrice = parseFloat(unitPriceInput.value) || 0;
            
            const total = quantity * unitPrice;
            totalInput.value = total.toFixed(2);
            
            // Recalculate all totals
            calculateTotals();
        }
    }
    
    // Calculate all summary totals
    function calculateTotals() {
        // Calculate total component value
        let totalComponentValue = 0;
        
        document.querySelectorAll('.formset-row:not([style*="display: none"]) .total-input').forEach(input => {
            totalComponentValue += parseFloat(input.value) || 0;
        });
        
        // Update total component value field
        if (totalComponentValueInput) {
            totalComponentValueInput.value = totalComponentValue.toFixed(2);
        }
        
        // Calculate additional cost
        if (otherCostPercentageInput && additionalCostInput) {
            const otherCostPercentage = parseFloat(otherCostPercentageInput.value) || 0;
            const additionalCost = totalComponentValue * (otherCostPercentage / 100);
            additionalCostInput.value = additionalCost.toFixed(2);
        }
        
        // Calculate total after discount
        if (totalAfterDiscountInput && additionalCostInput) {
            const additionalCost = parseFloat(additionalCostInput.value) || 0;
            const totalAfterDiscount = totalComponentValue + additionalCost;
            totalAfterDiscountInput.value = totalAfterDiscount.toFixed(2);
        }
    }
    
    // Set up a mutation observer to detect when new rows are added
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                // Check each added node
                mutation.addedNodes.forEach(node => {
                    // If it's a formset row, set up calculations
                    if (node.nodeType === 1 && node.classList.contains('formset-row')) {
                        setupRowCalculations(node);
                    }
                });
                // Recalculate totals after rows are added
                calculateTotals();
            }
        });
    });
    
    // Start observing the formset body for added nodes
    if (formsetBody) {
        observer.observe(formsetBody, { childList: true });
    }
    
    // Listen for delete row events
    document.addEventListener('click', e => {
        if (e.target.closest('.delete-row')) {
            // Use setTimeout to ensure the row is hidden before recalculating
            setTimeout(calculateTotals, 10);
        }
    });
    
    // Expose functions globally
    window.calculateRowTotal = calculateRowTotal;
    window.calculateTotals = calculateTotals;
});