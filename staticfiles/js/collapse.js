/**
 * Simple Collapse - Minimal collapsible elements
 * Just add data-collapse-toggle="target-id" to any clickable element
 * and it will toggle the element with id="target-id"
 */
document.addEventListener('DOMContentLoaded', function() {
    // Handle clicks on any element with data-collapse-toggle attribute
    document.addEventListener('click', function(event) {
        const toggle = event.target.closest('[data-collapse-toggle]');
        if (toggle) {
            const targetId = toggle.getAttribute('data-collapse-toggle');
            const target = document.getElementById(targetId);
            
            if (target) {
                // Toggle the collapsed state
                const isCollapsed = target.classList.contains('collapsed');
                
                // Get the arrow icon
                let arrow = toggle.querySelector('.collapse-arrow');
                
                // Create arrow icon if it doesn't exist
                if (!arrow) {
                    arrow = document.createElement('span');
                    arrow.className = 'collapse-arrow ml-auto inline-block transition-transform duration-300';
                    arrow.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    `;
                    toggle.appendChild(arrow);
                }
                
                if (isCollapsed) {
                    // Expand
                    target.classList.remove('collapsed');
                    target.style.height = target.scrollHeight + 'px';
                    arrow.style.transform = 'rotate(0deg)';
                    
                    // After animation, set height to auto
                    setTimeout(() => {
                        target.style.height = 'auto';
                    }, 300);
                } else {
                    // Collapse
                    target.style.height = target.scrollHeight + 'px';
                    target.classList.add('collapsed');
                    arrow.style.transform = 'rotate(-90deg)';
                    
                    // Trigger reflow
                    target.offsetHeight;
                    
                    // Animate to 0
                    target.style.height = '0';
                }
            }
        }
    });
    
    // Initialize all collapsible elements
    document.querySelectorAll('[data-collapse-toggle]').forEach(toggle => {
        const targetId = toggle.getAttribute('data-collapse-toggle');
        const target = document.getElementById(targetId);
        
        if (target) {
            // Add necessary styles
            target.style.overflow = 'hidden';
            target.style.transition = 'height 0.3s ease';
            
            // Add arrow icon
            if (!toggle.querySelector('.collapse-arrow')) {
                const arrow = document.createElement('span');
                arrow.className = 'collapse-arrow ml-auto inline-block transition-transform duration-300';
                arrow.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                `;
                toggle.appendChild(arrow);
            }
            
            // Make all collapsible elements collapsed by default
            target.classList.add('collapsed');
            target.style.height = '0';
            const arrow = toggle.querySelector('.collapse-arrow');
            if (arrow) {
                arrow.style.transform = 'rotate(-90deg)';
            }
        }
    });
});