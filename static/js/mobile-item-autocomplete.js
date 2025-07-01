/**
 * Mobile Item Autocomplete - Ensures mobile autocomplete works like desktop
 * 
 * This script:
 * 1. Enhances mobile autocomplete functionality for item code and name fields
 * 2. Ensures proper positioning of dropdowns on mobile devices
 * 3. Improves touch interaction for selecting items
 * 4. Syncs data between mobile and desktop views
 */
document.addEventListener("DOMContentLoaded", () => {
  console.log("Mobile item autocomplete script loaded");

  const mobileFormsetContainer = document.getElementById("mobileFormsetContainer");
  
  if (!mobileFormsetContainer) {
    console.log("Mobile formset container not found");
    return;
  }

  // Enhance mobile dropdown positioning
  function showMobileSearchDropdown(items, inputElement, isCodeInput) {
    // Remove any existing dropdowns
    hideSearchDropdowns();

    // Find the row
    const row = inputElement.closest(".mobile-formset-row");
    if (!row) {
      console.error("Could not find parent mobile row");
      return;
    }

    // Create dropdown element
    const dropdown = document.createElement("div");
    dropdown.className =
      "item-search-dropdown fixed z-[9999] bg-[hsl(var(--background))] border border-[hsl(var(--border))] rounded-lg shadow-lg w-[90%] max-h-[300px] overflow-y-auto";

    // Position dropdown below the input
    const rect = inputElement.getBoundingClientRect();
    
    // Center the dropdown horizontally on mobile
    const viewportWidth = window.innerWidth;
    dropdown.style.left = `${(viewportWidth - (viewportWidth * 0.9)) / 2}px`;
    dropdown.style.top = `${rect.bottom + window.scrollY + 5}px`;
    dropdown.style.width = "90%";

    // Add items to dropdown
    if (items.length === 0) {
      const noResults = document.createElement("div");
      noResults.className = "px-4 py-3 text-sm text-[hsl(var(--muted-foreground))]";
      noResults.textContent = "No items found";
      dropdown.appendChild(noResults);
    } else {
      items.forEach((item) => {
        const option = document.createElement("div");
        option.className = "px-4 py-3 hover:bg-[hsl(var(--accent))] active:bg-[hsl(var(--accent))] cursor-pointer text-sm flex justify-between";

        // Display format depends on which input field triggered the search
        if (isCodeInput) {
          option.innerHTML = `
            <span class="font-medium">${item.code}</span>
            <span class="text-[hsl(var(--muted-foreground))]">${item.name}</span>
          `;
        } else {
          option.innerHTML = `
            <span class="font-medium">${item.name}</span>
            <span class="text-[hsl(var(--muted-foreground))]">${item.code}</span>
          `;
        }

        // Add touch-friendly event listeners
        option.addEventListener("touchstart", function() {
          this.classList.add("bg-[hsl(var(--accent))]");
        });
        
        option.addEventListener("touchend", function() {
          this.classList.remove("bg-[hsl(var(--accent))]");
          populateRowWithItemData(row, item);
          hideSearchDropdowns();
        });
        
        option.addEventListener("click", function() {
          populateRowWithItemData(row, item);
          hideSearchDropdowns();
        });

        dropdown.appendChild(option);
      });
    }

    // Add dropdown to the document
    document.body.appendChild(dropdown);

    // Adjust dropdown position if it goes off screen
    const dropdownRect = dropdown.getBoundingClientRect();
    const viewportHeight = window.innerHeight;

    if (dropdownRect.bottom > viewportHeight) {
      dropdown.style.top = `${rect.top + window.scrollY - dropdownRect.height - 5}px`;
    }
  }

  // Hide all search dropdowns
  function hideSearchDropdowns() {
    const dropdowns = document.querySelectorAll(".item-search-dropdown");
    dropdowns.forEach((dropdown) => dropdown.remove());
  }

  // Populate row with item data
  function populateRowWithItemData(row, item) {
    if (!row) {
      console.error("Row is null or undefined");
      return;
    }

    console.log("Populating mobile row with item data:", item);

    // Get all the inputs in the row
    const itemCodeInput = row.querySelector(".item-code-input");
    const itemNameInput = row.querySelector(".item-name-input");
    const stockInput = row.querySelector(".stock-input");
    const uomInput = row.querySelector(".uom-input");
    const unitPriceInput = row.querySelector(".unit-price-input");
    const quantityInput = row.querySelector(".quantity-input");
    const totalAmountInput = row.querySelector(".total-amount-input");

    // Populate the fields with item data
    if (itemCodeInput) {
      itemCodeInput.value = item.code;
      itemCodeInput.setAttribute("data-original-value", item.code);
    }

    if (itemNameInput) {
      itemNameInput.value = item.name;
      itemNameInput.setAttribute("data-original-value", item.name);
    }

    if (stockInput) stockInput.value = item.stock || "0.00";
    if (uomInput) uomInput.value = item.uom || "";

    // Only set unit price if it's empty or zero
    if (unitPriceInput && (!unitPriceInput.value || Number.parseFloat(unitPriceInput.value) === 0)) {
      unitPriceInput.value = item.unit_price || "0.00";
    }

    // Set focus to quantity input if it exists and is empty
    if (quantityInput && (!quantityInput.value || Number.parseFloat(quantityInput.value) === 0)) {
      quantityInput.value = "1.00";
      quantityInput.focus();
      quantityInput.select();
    }

    // Trigger change events to update calculations
    if (unitPriceInput) {
      const event = new Event("input", { bubbles: true });
      unitPriceInput.dispatchEvent(event);
    }
    
    // Sync with desktop view
    const formsetBody = document.getElementById("formsetBody");
    if (formsetBody) {
      const index = row.dataset.index;
      const desktopRow = formsetBody.querySelector(`.formset-row[data-index="${index}"]`);
      if (desktopRow) {
        syncRowData(row, desktopRow);
      }
    }
  }
  
  // Sync data between mobile and desktop rows
  function syncRowData(sourceRow, targetRow) {
    const fields = ['item-code-input', 'item-name-input', 'quantity-input', 'unit-price-input', 'uom-input', 'stock-input', 'total-amount-input'];
    
    fields.forEach(fieldClass => {
      const sourceInput = sourceRow.querySelector(`.${fieldClass}`);
      const targetInput = targetRow.querySelector(`.${fieldClass}`);
      
      if (sourceInput && targetInput) {
        targetInput.value = sourceInput.value;
        
        // Also sync data attributes
        if (sourceInput.hasAttribute('data-original-value')) {
          targetInput.setAttribute('data-original-value', sourceInput.getAttribute('data-original-value'));
        }
      }
    });
  }

  // Search items by query
  function searchItems(query, callback) {
    // Construct the URL with query parameters
    const url = `/inventory/api/items/search/?query=${encodeURIComponent(query)}`;

    console.log("Mobile sending request to:", url);

    // Make the AJAX request
    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        console.log("Mobile received data:", data);
        callback(data.items);
      })
      .catch((error) => {
        console.error("Error searching items from mobile:", error);
        callback([]);
      });
  }

  // Handle mobile input events with debounce
  let debounceTimer;
  mobileFormsetContainer.addEventListener("input", (e) => {
    if (e.target.classList.contains("item-code-input") || e.target.classList.contains("item-name-input")) {
      const input = e.target;
      const searchTerm = input.value.trim();
      const isCodeInput = input.classList.contains("item-code-input");

      console.log(`Mobile ${isCodeInput ? "code" : "name"} input changed:`, searchTerm);
      hideSearchDropdowns();

      // Clear previous timer
      clearTimeout(debounceTimer);

      // Set new timer to delay the search
      if (searchTerm.length >= 2) {
        debounceTimer = setTimeout(() => {
          console.log("Mobile searching for items:", searchTerm);
          searchItems(searchTerm, (items) => {
            if (items.length > 0) {
              showMobileSearchDropdown(items, input, isCodeInput);
            }
          });
        }, 300); // 300ms debounce
      }
    }
  });

  // Handle mobile touch events
  document.addEventListener("touchstart", (e) => {
    if (
      !e.target.closest(".item-search-dropdown") &&
      !e.target.classList.contains("item-code-input") &&
      !e.target.classList.contains("item-name-input")
    ) {
      hideSearchDropdowns();
    }
  }, { passive: true });

  // Handle scroll events on mobile
  document.addEventListener(
    "scroll",
    () => {
      const activeDropdown = document.querySelector(".item-search-dropdown");
      if (activeDropdown) {
        const relatedInput = document.activeElement;
        if (
          relatedInput &&
          (relatedInput.classList.contains("item-code-input") || relatedInput.classList.contains("item-name-input"))
        ) {
          const rect = relatedInput.getBoundingClientRect();
          activeDropdown.style.top = `${rect.bottom + window.scrollY + 5}px`;
        } else {
          hideSearchDropdowns();
        }
      }
    },
    { passive: true },
  );

  console.log("Mobile item autocomplete initialization complete");
});