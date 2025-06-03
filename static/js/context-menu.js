/**
 * Context Menu - Handles right-click context menu for formset rows
 * 
 * This script provides a reusable context menu implementation that can be
 * used across different forms with Django formsets.
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get context menu element
    const contextMenu = document.getElementById('contextMenu');
    
    if (!contextMenu) return;
    
    // Current row reference
    let currentRow = null;
    
    // Add event listeners to formset body for right-click
    const formsetBody = document.getElementById('formsetBody');
    if (formsetBody) {
        formsetBody.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            
            // Find the closest row
            const row = e.target.closest('.formset-row');
            if (row) {
                // Store reference to current row
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
    
    // Add Row Above button
    const addRowAboveBtn = document.getElementById('addRowAboveBtn');
    if (addRowAboveBtn) {
        addRowAboveBtn.addEventListener('click', function() {
            if (currentRow && window.addRowAbove) {
                window.addRowAbove(currentRow);
            }
        });
    }
    
    // Add Row Below button
    const addRowBelowBtn = document.getElementById('addRowBelowBtn');
    if (addRowBelowBtn) {
        addRowBelowBtn.addEventListener('click', function() {
            if (currentRow && window.addRowBelow) {
                window.addRowBelow(currentRow);
            }
        });
    }
    
    // Delete Row button
    const deleteRowBtn = document.getElementById('deleteRowBtn');
    if (deleteRowBtn) {
        deleteRowBtn.addEventListener('click', function() {
            if (currentRow && window.deleteRow) {
                window.deleteRow(currentRow);
            }
        });
    }
    
    // Hide context menu
    function hideContextMenu() {
        contextMenu.classList.add('hidden');
        document.removeEventListener('click', hideContextMenu);
    }
    
    // Hide context menu on scroll
    document.addEventListener('scroll', function() {
        hideContextMenu();
    }, { passive: true });
    
    // Expose functions globally
    window.showContextMenu = function(e, row) {
        currentRow = row;
        contextMenu.style.left = `${e.pageX}px`;
        contextMenu.style.top = `${e.pageY}px`;
        contextMenu.classList.remove('hidden');
        document.addEventListener('click', hideContextMenu);
    };
    
    window.hideContextMenu = hideContextMenu;
});