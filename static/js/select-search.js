/**
 * Converts a select element into a searchable dropdown while keeping the UI clean.
 * @param {string} selector - The ID or name of the select element to convert.
 */
function makeSelectSearchable(selector) {
    // Find the select element by ID
    let select = document.getElementById(selector);
    
    // If not found by ID, try by name
    if (!select) {
        select = document.querySelector(`[name="${selector}"]`);
    }
    
    // If still not found, try with Django's id_prefix
    if (!select && !selector.startsWith('id_')) {
        select = document.getElementById(`id_${selector}`);
    }
    
    // If select element is not found or is not a select element, exit
    if (!select || select.tagName !== 'SELECT') {
        console.error(`Select element not found: ${selector}`);
        return;
    }

    // Create wrapper div to maintain existing form structure
    const wrapper = document.createElement('div');
    wrapper.className = 'relative';

    // Create search input with same styling as text inputs
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = select.className; // Apply same styles as the original select
    searchInput.placeholder = select.options[0]?.text || 'Select an option';
    searchInput.setAttribute('autocomplete', 'off');

    // Set default selected value
    if (select.selectedIndex > 0) {
        searchInput.value = select.options[select.selectedIndex].text;
    }

    // Create dropdown container (Initially Hidden)
    const dropdown = document.createElement('div');
    dropdown.className = 'absolute left-0 mt-1 w-full bg-white border-2 border-[hsl(var(--border))] rounded-md shadow-lg z-50 hidden';

    // Populate dropdown with options (only show first 5 initially)
    Array.from(select.options).forEach((option, index) => {
        if (option.value) {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'px-3 py-2 hover:bg-[hsl(var(--primary))] hover:text-white cursor-pointer transition-all';
            optionDiv.textContent = option.text;
            optionDiv.dataset.value = option.value;

            // Handle click event to update selection
            optionDiv.addEventListener('click', () => {
                select.value = option.value;
                searchInput.value = option.text;
                dropdown.classList.add('hidden');

                // Trigger change event
                const event = new Event('change', { bubbles: true });
                select.dispatchEvent(event);
            });

            // Only show first 5 items initially
            if (index < 5) {
                dropdown.appendChild(optionDiv);
            }
        }
    });

    // Show dropdown only when typing (or clicking input)
    searchInput.addEventListener('focus', () => {
        dropdown.classList.remove('hidden');
    });

    // Filter options when typing
    searchInput.addEventListener('input', () => {
        const searchText = searchInput.value.toLowerCase();
        dropdown.innerHTML = ''; // Clear previous options

        let count = 0;
        Array.from(select.options).forEach(option => {
            const optionText = option.textContent || option.innerText;
            if (option.value && optionText.toLowerCase().includes(searchText)) {
                const optionDiv = document.createElement('div');
                optionDiv.className = 'px-3 py-2 hover:bg-[hsl(var(--primary))] hover:text-white cursor-pointer transition-all';
                optionDiv.textContent = option.text;
                optionDiv.dataset.value = option.value;

                optionDiv.addEventListener('click', () => {
                    select.value = option.value;
                    searchInput.value = option.text;
                    dropdown.classList.add('hidden');

                    const event = new Event('change', { bubbles: true });
                    select.dispatchEvent(event);
                });

                dropdown.appendChild(optionDiv);
                count++;
            }
        });

        if (count === 0) {
            dropdown.classList.add('hidden'); // Hide if no results found
        } else {
            dropdown.classList.remove('hidden');
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) {
            dropdown.classList.add('hidden');
        }
    });

    // Insert elements into the DOM while keeping the form structure
    wrapper.appendChild(searchInput);
    wrapper.appendChild(dropdown);
    select.parentNode.insertBefore(wrapper, select);
    select.style.display = 'none'; // Hide the original select
}
