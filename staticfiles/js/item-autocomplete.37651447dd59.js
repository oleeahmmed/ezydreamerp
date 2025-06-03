/**
 * Item Autocomplete - Handles searching and autocompleting item information in formset rows
 *
 * This script:
 * 1. Adds autocomplete functionality to item code and item name fields
 * 2. Fetches item data from the server when typing
 * 3. Populates row fields with selected item data
 * 4. Handles new rows added dynamically
 * 5. Auto-completes on blur if exact item code match exists
 * 6. Clears data if item code/name is changed to non-existent value
 */
document.addEventListener("DOMContentLoaded", () => {
  console.log("Item autocomplete script loaded")

  const formsetBody = document.getElementById("formsetBody");
  const mobileFormsetContainer = document.getElementById("mobileFormsetContainer");
  
  // Set up event delegation for item code and name inputs in desktop view
  if (formsetBody) {
    // Listen for input events on item code and name inputs
    formsetBody.addEventListener("input", (e) => {
      if (e.target.classList.contains("item-code-input") || e.target.classList.contains("item-name-input")) {
        handleItemSearch(e)
      }
    })

    // Listen for focus events to show dropdown if value already exists
    formsetBody.addEventListener(
      "focus",
      (e) => {
        if (
          (e.target.classList.contains("item-code-input") || e.target.classList.contains("item-name-input")) &&
          e.target.value.length >= 2
        ) {
          const searchTerm = e.target.value
          console.log(`Focus event on input with value: ${searchTerm}`)
          searchItems(searchTerm, (items) => {
            if (items.length > 0) {
              const isCodeInput = e.target.classList.contains("item-code-input")
              showSearchDropdown(items, e.target, isCodeInput)
            }
          })
        }
      },
      true,
    )

    // Listen for blur events on item code and name inputs
    formsetBody.addEventListener(
      "blur",
      (e) => {
        // Handle blur for item code input
        if (e.target.classList.contains("item-code-input")) {
          const itemCode = e.target.value.trim()
          if (itemCode.length > 0) {
            // Store original value to check if it changed
            const originalValue = e.target.getAttribute("data-original-value") || ""

            // If value changed, validate it
            if (originalValue !== itemCode) {
              validateItemCodeAndUpdate(itemCode, e.target)
            }
          }
        }

        // Handle blur for item name input
        if (e.target.classList.contains("item-name-input")) {
          const itemName = e.target.value.trim()
          if (itemName.length > 0) {
            // Store original value to check if it changed
            const originalValue = e.target.getAttribute("data-original-value") || ""

            // If value changed, validate it
            if (originalValue !== itemName) {
              validateItemNameAndUpdate(itemName, e.target)
            }
          }
        }
      },
      true,
    )
  }
  
  // Set up event delegation for mobile view
  if (mobileFormsetContainer) {
    // Listen for input events on item code and name inputs in mobile view
    mobileFormsetContainer.addEventListener("input", (e) => {
      if (e.target.classList.contains("item-code-input") || e.target.classList.contains("item-name-input")) {
        handleItemSearch(e)
      }
    })

    // Listen for focus events in mobile view
    mobileFormsetContainer.addEventListener(
      "focus",
      (e) => {
        if (
          (e.target.classList.contains("item-code-input") || e.target.classList.contains("item-name-input")) &&
          e.target.value.length >= 2
        ) {
          const searchTerm = e.target.value
          console.log(`Mobile focus event on input with value: ${searchTerm}`)
          searchItems(searchTerm, (items) => {
            if (items.length > 0) {
              const isCodeInput = e.target.classList.contains("item-code-input")
              showSearchDropdown(items, e.target, isCodeInput)
            }
          })
        }
      },
      true,
    )

    // Listen for blur events in mobile view
    mobileFormsetContainer.addEventListener(
      "blur",
      (e) => {
        // Handle blur for item code input
        if (e.target.classList.contains("item-code-input")) {
          const itemCode = e.target.value.trim()
          if (itemCode.length > 0) {
            // Store original value to check if it changed
            const originalValue = e.target.getAttribute("data-original-value") || ""

            // If value changed, validate it
            if (originalValue !== itemCode) {
              validateItemCodeAndUpdate(itemCode, e.target)
            }
          }
        }

        // Handle blur for item name input
        if (e.target.classList.contains("item-name-input")) {
          const itemName = e.target.value.trim()
          if (itemName.length > 0) {
            // Store original value to check if it changed
            const originalValue = e.target.getAttribute("data-original-value") || ""

            // If value changed, validate it
            if (originalValue !== itemName) {
              validateItemNameAndUpdate(itemName, e.target)
            }
          }
        }
      },
      true,
    )
  }

  // Handle clicks outside dropdowns to close them
  document.addEventListener("click", (e) => {
    if (
      !e.target.closest(".item-search-dropdown") &&
      !e.target.classList.contains("item-code-input") &&
      !e.target.classList.contains("item-name-input")
    ) {
      hideSearchDropdowns()
    }
  })

  // Validate item code and update row accordingly
  function validateItemCodeAndUpdate(itemCode, input) {
    console.log("Validating item code:", itemCode)

    // Make a request to search for exact item code match
    fetch(`/inventory/api/items/search/?query=${encodeURIComponent(itemCode)}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok")
        }
        return response.json()
      })
      .then((data) => {
        // Check if there's an exact match for the item code
        const exactMatch = data.items.find((item) => item.code.toLowerCase() === itemCode.toLowerCase())

        // Find the row - could be in desktop or mobile view
        const row = input.closest(".formset-row, .mobile-formset-row")

        if (exactMatch) {
          console.log("Found exact match for item code:", exactMatch)
          populateRowWithItemData(row, exactMatch)

          // Store the validated value
          input.setAttribute("data-original-value", exactMatch.code)

          // Also update the item name's original value
          const itemNameInput = row.querySelector(".item-name-input")
          if (itemNameInput) {
            itemNameInput.setAttribute("data-original-value", exactMatch.name)
          }
        } else {
          console.log("No exact match found for item code, clearing row data")
          clearRowItemData(row)
        }
      })
      .catch((error) => {
        console.error("Error validating item code:", error)
      })
  }

  // Validate item name and update row accordingly
  function validateItemNameAndUpdate(itemName, input) {
    console.log("Validating item name:", itemName)

    // Make a request to search for exact item name match
    fetch(`/inventory/api/items/search/?query=${encodeURIComponent(itemName)}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok")
        }
        return response.json()
      })
      .then((data) => {
        // Check if there's an exact match for the item name
        const exactMatch = data.items.find((item) => item.name.toLowerCase() === itemName.toLowerCase())

        // Find the row - could be in desktop or mobile view
        const row = input.closest(".formset-row, .mobile-formset-row")

        if (exactMatch) {
          console.log("Found exact match for item name:", exactMatch)
          populateRowWithItemData(row, exactMatch)

          // Store the validated value
          input.setAttribute("data-original-value", exactMatch.name)

          // Also update the item code's original value
          const itemCodeInput = row.querySelector(".item-code-input")
          if (itemCodeInput) {
            itemCodeInput.setAttribute("data-original-value", exactMatch.code)
          }
        } else {
          console.log("No exact match found for item name, clearing row data")
          clearRowItemData(row)
        }
      })
      .catch((error) => {
        console.error("Error validating item name:", error)
      })
  }

  // Clear all item-related data in a row
  function clearRowItemData(row) {
    // Keep the current value in the field that was just edited
    // but clear all other item-related fields

    const itemCodeInput = row.querySelector(".item-code-input")
    const itemNameInput = row.querySelector(".item-name-input")
    const stockInput = row.querySelector(".stock-input")
    const uomInput = row.querySelector(".uom-input")
    const unitPriceInput = row.querySelector(".unit-price-input") // Changed from unit-cost-input

    // Clear item name if we're validating item code
    if (document.activeElement !== itemNameInput && itemNameInput) {
      itemNameInput.value = ""
      itemNameInput.removeAttribute("data-original-value")
    }

    // Clear item code if we're validating item name
    if (document.activeElement !== itemCodeInput && itemCodeInput) {
      itemCodeInput.value = ""
      itemCodeInput.removeAttribute("data-original-value")
    }

    // Always clear these fields
    if (stockInput) stockInput.value = ""
    if (uomInput) uomInput.value = ""

    // Only clear unit price if it's not being edited
    if (unitPriceInput && document.activeElement !== unitPriceInput) {
      unitPriceInput.value = ""
    }
  }

  // Handle item search for both code and name inputs
  function handleItemSearch(e) {
    const input = e.target
    const searchTerm = input.value.trim()
    const isCodeInput = input.classList.contains("item-code-input")

    console.log(`Item ${isCodeInput ? "code" : "name"} input changed:`, searchTerm)
    hideSearchDropdowns()

    if (searchTerm.length >= 2) {
      console.log("Searching for items:", searchTerm)
      searchItems(searchTerm, (items) => {
        if (items.length > 0) {
          showSearchDropdown(items, input, isCodeInput)
        }
      })
    }
  }

  // Search items by query (both code and name)
  function searchItems(query, callback) {
    // Construct the URL with query parameters
    const url = `/inventory/api/items/search/?query=${encodeURIComponent(query)}`

    console.log("Sending request to:", url)

    // Make the AJAX request
    fetch(url)
      .then((response) => {
        console.log("Response status:", response.status)
        if (!response.ok) {
          throw new Error("Network response was not ok")
        }
        return response.json()
      })
      .then((data) => {
        console.log("Received data:", data)
        callback(data.items)
      })
      .catch((error) => {
        console.error("Error searching items:", error)
        callback([])
      })
  }

  // Show search dropdown with results
  function showSearchDropdown(items, inputElement, isCodeInput) {
    // Remove any existing dropdowns
    hideSearchDropdowns()

    // Find the row - could be in desktop or mobile view
    const row = inputElement.closest(".formset-row, .mobile-formset-row")
    if (!row) {
      console.error("Could not find parent row")
      return
    }

    // Create dropdown element
    const dropdown = document.createElement("div")
    dropdown.className =
      "item-search-dropdown fixed z-[9999] bg-[hsl(var(--background))] border border-[hsl(var(--border))] rounded-lg shadow-lg w-[300px] max-h-[300px] overflow-y-auto"

    // Position dropdown below the input
    const rect = inputElement.getBoundingClientRect()
    dropdown.style.left = `${rect.left}px`
    dropdown.style.top = `${rect.bottom + window.scrollY}px`

    // Add items to dropdown
    if (items.length === 0) {
      const noResults = document.createElement("div")
      noResults.className = "px-4 py-2 text-sm text-[hsl(var(--muted-foreground))]"
      noResults.textContent = "No items found"
      dropdown.appendChild(noResults)
    } else {
      items.forEach((item) => {
        const option = document.createElement("div")
        option.className = "px-4 py-2 hover:bg-[hsl(var(--accent))] cursor-pointer text-sm flex justify-between"

        // Display format depends on which input field triggered the search
        if (isCodeInput) {
          option.innerHTML = `
                        <span class="font-medium">${item.code}</span>
                        <span class="text-[hsl(var(--muted-foreground))]">${item.name}</span>
                    `
        } else {
          option.innerHTML = `
                        <span class="font-medium">${item.name}</span>
                        <span class="text-[hsl(var(--muted-foreground))]">${item.code}</span>
                    `
        }

        option.addEventListener("click", () => {
          populateRowWithItemData(row, item)
          hideSearchDropdowns()
        })

        dropdown.appendChild(option)
      })
    }

    // Add dropdown to the document
    document.body.appendChild(dropdown)

    // Adjust dropdown position if it goes off screen
    const dropdownRect = dropdown.getBoundingClientRect()
    const viewportHeight = window.innerHeight
    const viewportWidth = window.innerWidth

    if (dropdownRect.right > viewportWidth) {
      dropdown.style.left = `${viewportWidth - dropdownRect.width - 10}px`
    }

    if (dropdownRect.bottom > viewportHeight) {
      dropdown.style.top = `${rect.top + window.scrollY - dropdownRect.height}px`
    }
  }

  // Hide all search dropdowns
  function hideSearchDropdowns() {
    const dropdowns = document.querySelectorAll(".item-search-dropdown")
    dropdowns.forEach((dropdown) => dropdown.remove())
  }

  // Populate row with item data
  function populateRowWithItemData(row, item) {
    if (!row) {
      console.error("Row is null or undefined")
      return
    }

    console.log("Populating row with item data:", item)

    // Get all the inputs in the row
    const itemCodeInput = row.querySelector(".item-code-input")
    const itemNameInput = row.querySelector(".item-name-input")
    const stockInput = row.querySelector(".stock-input")
    const uomInput = row.querySelector(".uom-input")
    const unitPriceInput = row.querySelector(".unit-price-input")
    const quantityInput = row.querySelector(".quantity-input")
    const totalAmountInput = row.querySelector(".total-amount-input")

    // Populate the fields with item data
    if (itemCodeInput) {
      itemCodeInput.value = item.code
      itemCodeInput.setAttribute("data-original-value", item.code)
    }

    if (itemNameInput) {
      itemNameInput.value = item.name
      itemNameInput.setAttribute("data-original-value", item.name)
    }

    if (stockInput) stockInput.value = item.stock || "0.00"
    if (uomInput) uomInput.value = item.uom || ""

    // Only set unit price if it's empty or zero
    if (unitPriceInput && (!unitPriceInput.value || Number.parseFloat(unitPriceInput.value) === 0)) {
      unitPriceInput.value = item.unit_price || "0.00" // Use unit_price instead of unit_cost
    }

    // Set the warehouse if available
    const warehouseSelect = row.querySelector('select[name*="warehouse"]')
    if (warehouseSelect && item.default_warehouse_id) {
      warehouseSelect.value = item.default_warehouse_id
    }

    // Set focus to quantity input if it exists and is empty
    if (quantityInput && (!quantityInput.value || Number.parseFloat(quantityInput.value) === 0)) {
      quantityInput.value = "1.00"
      quantityInput.focus()
      quantityInput.select()
    }

    // Trigger change events to update calculations
    if (unitPriceInput) {
      const event = new Event("input", { bubbles: true })
      unitPriceInput.dispatchEvent(event)
    }
    
    // If this is a mobile row, also update the corresponding desktop row and vice versa
    if (row.classList.contains('mobile-formset-row') && formsetBody) {
      const index = row.dataset.index;
      const desktopRow = formsetBody.querySelector(`.formset-row[data-index="${index}"]`);
      if (desktopRow) {
        syncRowData(row, desktopRow);
      }
    } else if (row.classList.contains('formset-row') && mobileFormsetContainer) {
      const index = row.dataset.index;
      const mobileRow = mobileFormsetContainer.querySelector(`.mobile-formset-row[data-index="${index}"]`);
      if (mobileRow) {
        syncRowData(row, mobileRow);
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

  // Initialize autocomplete for existing rows
  function initializeAllRows() {
    // Initialize desktop rows
    const desktopRows = document.querySelectorAll("#formsetBody tr.formset-row")
    console.log("Found", desktopRows.length, "desktop rows to initialize")

    // Initialize data-original-value for existing desktop rows
    desktopRows.forEach((row) => {
      const itemCodeInput = row.querySelector(".item-code-input")
      const itemNameInput = row.querySelector(".item-name-input")

      if (itemCodeInput && itemCodeInput.value) {
        itemCodeInput.setAttribute("data-original-value", itemCodeInput.value)
      }

      if (itemNameInput && itemNameInput.value) {
        itemNameInput.setAttribute("data-original-value", itemNameInput.value)
      }
    })
    
    // Initialize mobile rows
    const mobileRows = document.querySelectorAll("#mobileFormsetContainer .mobile-formset-row")
    console.log("Found", mobileRows.length, "mobile rows to initialize")

    // Initialize data-original-value for existing mobile rows
    mobileRows.forEach((row) => {
      const itemCodeInput = row.querySelector(".item-code-input")
      const itemNameInput = row.querySelector(".item-name-input")

      if (itemCodeInput && itemCodeInput.value) {
        itemCodeInput.setAttribute("data-original-value", itemCodeInput.value)
      }

      if (itemNameInput && itemNameInput.value) {
        itemNameInput.setAttribute("data-original-value", itemNameInput.value)
      }
    })
  }

  // Set up a mutation observer to detect when new rows are added
  function setupMutationObserver() {
    // Setup observer for desktop view
    const formsetBody = document.getElementById("formsetBody")
    if (formsetBody) {
      console.log("Setting up mutation observer for desktop formset body")
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === "childList" && mutation.addedNodes.length > 0) {
            console.log("New rows added to desktop formset")
          }
        })
      })
      observer.observe(formsetBody, { childList: true })
    }
    
    // Setup observer for mobile view
    const mobileFormsetContainer = document.getElementById("mobileFormsetContainer")
    if (mobileFormsetContainer) {
      console.log("Setting up mutation observer for mobile formset container")
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === "childList" && mutation.addedNodes.length > 0) {
            console.log("New rows added to mobile formset")
          }
        })
      })
      observer.observe(mobileFormsetContainer, { childList: true })
    }
  }

  // Initialize
  initializeAllRows()
  setupMutationObserver()

  // Handle scroll events to reposition dropdowns
  document.addEventListener(
    "scroll",
    () => {
      const activeDropdown = document.querySelector(".item-search-dropdown")
      if (activeDropdown) {
        const relatedInput = document.activeElement
        if (
          relatedInput &&
          (relatedInput.classList.contains("item-code-input") || relatedInput.classList.contains("item-name-input"))
        ) {
          const rect = relatedInput.getBoundingClientRect()
          activeDropdown.style.top = `${rect.bottom + window.scrollY}px`
        } else {
          hideSearchDropdowns()
        }
      }
    },
    { passive: true },
  )
})