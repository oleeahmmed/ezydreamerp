/**
 * Production Order BOM Selection Handler
 * 
 * This script handles the automatic population of production order components
 * when a Bill of Materials (BOM) is selected.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get references to form elements
    const bomSelect = document.getElementById('id_bom');
    const productSelect = document.getElementById('id_product');
    const plannedQuantityInput = document.getElementById('id_planned_quantity');
    
    // Handle BOM selection change
    if (bomSelect) {
        bomSelect.addEventListener('change', function() {
            const bomId = this.value;
            if (bomId) {
                // Get planned quantity
                const plannedQty = plannedQuantityInput ? parseFloat(plannedQuantityInput.value) || 1 : 1;
                
                // Show loading indicator
                const loadingIndicator = document.createElement('div');
                loadingIndicator.id = 'bom-loading-indicator';
                loadingIndicator.className = 'fixed top-0 left-0 w-full h-full flex items-center justify-center bg-black bg-opacity-50 z-50';
                loadingIndicator.innerHTML = `
                    <div class="bg-white p-4 rounded-lg shadow-lg flex items-center">
                        <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-[hsl(var(--primary))]" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Loading BOM components...</span>
                    </div>
                `;
                document.body.appendChild(loadingIndicator);
                
                // Fetch BOM details from server
                fetch(`/production/api/bom/${bomId}/details/?planned_quantity=${plannedQty}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.success) {
                            // Set product
                            if (productSelect && data.product_id) {
                                productSelect.value = data.product_id;
                                
                                // Trigger change event for any dependent fields
                                const event = new Event('change', { bubbles: true });
                                productSelect.dispatchEvent(event);
                            }
                            
                            // Clear existing components
                            clearComponentRows();
                            
                            // Add components from BOM
                            if (data.components && data.components.length > 0) {
                                data.components.forEach(component => {
                                    // Trigger custom event to add a new row with component data
                                    const event = new CustomEvent('addComponentRow', {
                                        detail: {
                                            itemCode: component.item_code,
                                            itemName: component.item_name,
                                            quantity: component.quantity
                                        }
                                    });
                                    document.dispatchEvent(event);
                                });
                            }
                            
                            // Show success message
                            showToast('BOM components loaded successfully', 'success');
                        } else {
                            console.error('Error fetching BOM details:', data.error);
                            showToast(`Error loading BOM components: ${data.error}`, 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching BOM details:', error);
                        showToast(`Error loading BOM components: ${error.message}`, 'error');
                    })
                    .finally(() => {
                        // Remove loading indicator
                        const loadingIndicator = document.getElementById('bom-loading-indicator');
                        if (loadingIndicator) {
                            loadingIndicator.remove();
                        }
                    });
            }
        });
    }
    
    // Handle planned quantity change to update component quantities
    if (plannedQuantityInput && bomSelect) {
        plannedQuantityInput.addEventListener('change', function() {
            const bomId = bomSelect.value;
            if (bomId) {
                // Trigger BOM selection change to recalculate quantities
                const event = new Event('change', { bubbles: true });
                bomSelect.dispatchEvent(event);
            }
        });
    }
    
    // Function to clear all component rows
    function clearComponentRows() {
        // Trigger custom event to clear all rows
        const event = new CustomEvent('clearComponentRows');
        document.dispatchEvent(event);
    }
    
    // Function to show toast messages
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 p-4 rounded shadow-md z-50 ${type === 'error' ? 'bg-red-100 border-l-4 border-red-500 text-red-700' : 'bg-green-100 border-l-4 border-green-500 text-green-700'}`;
        toast.innerHTML = `
            <div class="flex items-center">
                <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${type === 'error' ? 'M6 18L18 6M6 6l12 12' : 'M5 13l4 4L19 7'}"></path>
                </svg>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(toast);
        
        // Remove toast after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
    
    // Listen for custom events from the main script
    document.addEventListener('addComponentRow', function(e) {
        // This event is handled by the main script
        console.log('Adding component row:', e.detail);
    });
    
    document.addEventListener('clearComponentRows', function() {
        // This event is handled by the main script
        console.log('Clearing component rows');
    });
});