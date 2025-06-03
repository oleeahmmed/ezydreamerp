/**
 * Formset Cleanup - Automatically removes empty rows before form submission
 * 
 * This script:
 * 1. Checks for empty rows before form submission
 * 2. Marks empty rows for deletion
 * 3. Ensures only valid data is submitted
 */
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('bomForm');
    
    if (form) {
        form.addEventListener('submit', function(event) {
            // Prevent default form submission
            event.preventDefault();
            
            // Get all formset rows
            const rows = document.querySelectorAll('#formsetBody .formset-row');
            
            // Check each row
            rows.forEach(row => {
                // Get key fields
                const itemCodeInput = row.querySelector('.item-code-input');
                const itemNameInput = row.querySelector('.item-name-input');
                const quantityInput = row.querySelector('.quantity-input');
                
                // Check if the row is empty or incomplete
                const isEmpty = (
                    (!itemCodeInput || itemCodeInput.value.trim() === '') &&
                    (!itemNameInput || itemNameInput.value.trim() === '') &&
                    (!quantityInput || quantityInput.value.trim() === '' || parseFloat(quantityInput.value) === 0)
                );
                
                if (isEmpty) {
                    // Mark row for deletion
                    const deleteCheckbox = row.querySelector('.delete-checkbox');
                    if (deleteCheckbox) {
                        deleteCheckbox.checked = true;
                        row.style.display = 'none';
                    }
                }
            });
            
            // Submit the form
            form.submit();
        });
    }
});