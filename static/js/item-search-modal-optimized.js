/**
 * Optimized Item Search Modal - With client-side caching
 *
 * Features:
 * 1. Caches item data in localStorage to avoid repeated server requests
 * 2. Only fetches fresh data when needed (configurable cache expiry)
 * 3. Provides instant search results from cached data
 * 4. Works with both desktop and mobile views
 */
document.addEventListener("DOMContentLoaded", () => {
  // Cache configuration
  const CACHE_KEY = "inventory_items_cache"
  const CACHE_EXPIRY = 30 * 60 * 1000 // 30 minutes in milliseconds

  // Item data cache
  let itemsCache = null
  let lastFetchTime = 0

  // Create modal HTML structure once and append to body
  const modalHTML = `
    <div id="itemSearchModal" class="fixed inset-0 z-[9999] hidden">
        <div class="absolute inset-0 bg-black bg-opacity-50" id="itemSearchModalBackdrop"></div>
        <div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-11/12 max-w-2xl max-h-[80vh] bg-[hsl(var(--background))] rounded-xl shadow-2xl flex flex-col overflow-hidden border border-[hsl(var(--border))]">
            <div class="p-4 border-b border-[hsl(var(--border))] flex items-center justify-between">
                <h3 class="text-lg font-semibold text-[hsl(var(--foreground))]">Search Items</h3>
                <div class="flex items-center gap-2">
                    <button type="button" id="refreshItemsBtn" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-[hsl(var(--accent))]" title="Refresh Items">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-5 h-5">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                    </button>
                    <button type="button" id="itemSearchModalClose" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-[hsl(var(--accent))]">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-5 h-5">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="p-4 border-b border-[hsl(var(--border))]">
                <div class="relative">
                    <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-5 h-5 text-[hsl(var(--muted-foreground))]">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                        </svg>
                    </div>
                    <input type="text" id="itemSearchInput" class="w-full pl-10 pr-4 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]" placeholder="Search by item code or name...">
                </div>
            </div>
            <div class="flex-1 overflow-y-auto p-1" id="itemSearchResults">
                <div class="flex items-center justify-center h-full text-[hsl(var(--muted-foreground))]">
                    Loading items...
                </div>
            </div>
            <div class="p-3 border-t border-[hsl(var(--border))] flex justify-between items-center text-xs">
                <div class="text-[hsl(var(--muted-foreground))]">
                    <span id="itemCount">0</span> items found
                </div>
                <div id="cacheStatus" class="text-[hsl(var(--muted-foreground))]">
                    Using cached data
                </div>
            </div>
        </div>
    </div>
    `

  // Append modal to body
  const modalContainer = document.createElement("div")
  modalContainer.innerHTML = modalHTML
  document.body.appendChild(modalContainer.firstElementChild)

  // Get modal elements
  const modal = document.getElementById("itemSearchModal")
  const modalBackdrop = document.getElementById("itemSearchModalBackdrop")
  const modalClose = document.getElementById("itemSearchModalClose")
  const refreshItemsBtn = document.getElementById("refreshItemsBtn")
  const searchInput = document.getElementById("itemSearchInput")
  const searchResults = document.getElementById("itemSearchResults")
  const itemCount = document.getElementById("itemCount")
  const cacheStatus = document.getElementById("cacheStatus")

  // Current active input field that triggered the modal
  let currentInputField = null
  // Track if the input is from mobile view
  let isMobileInput = false

  // Load cache from localStorage on startup
  function loadCacheFromStorage() {
    try {
      const cachedData = localStorage.getItem(CACHE_KEY)
      if (cachedData) {
        const parsed = JSON.parse(cachedData)
        itemsCache = parsed.items
        lastFetchTime = parsed.timestamp

        // Check if cache is expired
        const now = Date.now()
        if (now - lastFetchTime > CACHE_EXPIRY) {
          console.log("Cache expired, will fetch fresh data")
          itemsCache = null
          lastFetchTime = 0
        } else {
          console.log(`Using cached data (${itemsCache.length} items)`)
        }
      }
    } catch (error) {
      console.error("Error loading cache:", error)
      itemsCache = null
      lastFetchTime = 0
    }
  }

  // Save cache to localStorage
  function saveCacheToStorage() {
    try {
      if (itemsCache) {
        const cacheData = {
          items: itemsCache,
          timestamp: lastFetchTime,
        }
        localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData))
        console.log(`Saved ${itemsCache.length} items to cache`)
      }
    } catch (error) {
      console.error("Error saving cache:", error)
    }
  }

  // Add search icon to all item code inputs (both desktop and mobile)
  function addSearchIconToInputs() {
    // Get all item code inputs from both desktop and mobile views
    const itemCodeInputs = document.querySelectorAll(".item-code-input")

    itemCodeInputs.forEach((input) => {
      // Skip if already has search icon
      if (input.parentElement.querySelector(".item-search-icon")) return

      // Create wrapper if input is not already wrapped
      let wrapper = input.parentElement
      if (!wrapper.classList.contains("item-input-wrapper")) {
        wrapper = document.createElement("div")
        wrapper.className = "item-input-wrapper relative"
        input.parentNode.insertBefore(wrapper, input)
        wrapper.appendChild(input)
      }

      // Add search icon
      const searchIcon = document.createElement("button")
      searchIcon.type = "button"
      searchIcon.className =
        "item-search-icon absolute right-2 top-1/2 transform -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-full hover:bg-[hsl(var(--accent))] transition-colors"
      searchIcon.setAttribute("data-input-id", input.id)
      searchIcon.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-4 h-4 text-[hsl(var(--muted-foreground))]">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
            `

      wrapper.appendChild(searchIcon)

      // Adjust input padding to make room for icon
      input.style.paddingRight = "2.5rem"
    })
  }

  // Open modal and load items
  function openModal() {
    modal.classList.remove("hidden")
    searchInput.value = ""
    searchInput.focus()

    // Check if we need to fetch items or can use cache
    if (!itemsCache) {
      fetchItems()
    } else {
      // Use cached items
      updateCacheStatus()
      filterAndRenderItems("")
    }
  }

  // Close modal
  function closeModal() {
    modal.classList.add("hidden")
    searchResults.innerHTML = ""
    currentInputField = null
    isMobileInput = false
  }

  // Update cache status display
  function updateCacheStatus() {
    if (!itemsCache) {
      cacheStatus.textContent = "Fetching data..."
      return
    }

    const now = Date.now()
    const ageInMinutes = Math.round((now - lastFetchTime) / 60000)

    if (ageInMinutes < 1) {
      cacheStatus.textContent = "Using fresh data"
    } else if (ageInMinutes === 1) {
      cacheStatus.textContent = "Cache: 1 minute old"
    } else {
      cacheStatus.textContent = `Cache: ${ageInMinutes} minutes old`
    }
  }

  // Fetch items from API
  function fetchItems(forceRefresh = false) {
    // Show loading state
    searchResults.innerHTML =
      '<div class="flex items-center justify-center h-32 text-[hsl(var(--muted-foreground))]">Loading items...</div>'
    cacheStatus.textContent = "Fetching data..."

    // Construct the URL
    const url = "/inventory/api/items/search/"

    // Make the AJAX request
    fetch(url)
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok")
        }
        return response.json()
      })
      .then((data) => {
        // Update cache
        itemsCache = data.items
        lastFetchTime = Date.now()
        saveCacheToStorage()

        // Update UI
        updateCacheStatus()
        filterAndRenderItems(searchInput.value.trim())
      })
      .catch((error) => {
        console.error("Error loading items:", error)
        searchResults.innerHTML = `
                    <div class="flex items-center justify-center h-32 text-[hsl(var(--destructive))]">
                        Error loading items. Please try again.
                    </div>
                `

        // If we have cached data, use it despite the error
        if (itemsCache && !forceRefresh) {
          cacheStatus.textContent = "Error fetching data, using cache"
          filterAndRenderItems(searchInput.value.trim())
        } else {
          cacheStatus.textContent = "Error fetching data"
          itemCount.textContent = "0"
        }
      })
  }

  // Filter and render items based on search query
  function filterAndRenderItems(query) {
    if (!itemsCache) {
      return
    }

    // Filter items based on query
    let filteredItems = itemsCache

    if (query) {
      query = query.toLowerCase()
      filteredItems = itemsCache.filter(
        (item) => item.code.toLowerCase().includes(query) || item.name.toLowerCase().includes(query),
      )
    }

    // Update item count
    itemCount.textContent = filteredItems.length

    // Render filtered items
    renderItems(filteredItems)
  }

  // Render items in the modal
  function renderItems(items) {
    if (items.length === 0) {
      searchResults.innerHTML = `
                <div class="flex items-center justify-center h-32 text-[hsl(var(--muted-foreground))]">
                    No items found. Try a different search term.
                </div>
            `
      return
    }

    let html = '<div class="grid grid-cols-1 gap-1 p-2">'

    items.forEach((item) => {
      html += `
                <div class="item-result flex items-center p-3 rounded-md hover:bg-[hsl(var(--accent))] cursor-pointer transition-colors" 
                     data-item-code="${item.code}" 
                     data-item-name="${item.name}"
                     data-item-uom="${item.uom || ""}"
                     data-item-stock="${item.stock || "0.00"}"
                     data-item-price="${item.unit_price || "0.00"}">
                    <div class="flex-1">
                        <div class="font-medium text-[hsl(var(--foreground))]">${item.code}</div>
                        <div class="text-sm text-[hsl(var(--muted-foreground))]">${item.name}</div>
                    </div>
                    <div class="text-right">
                        <div class="text-sm font-medium text-[hsl(var(--foreground))]">Stock: ${item.stock || "0.00"}</div>
                        <div class="text-xs text-[hsl(var(--muted-foreground))]">${item.uom || "N/A"}</div>
                    </div>
                </div>
            `
    })

    html += "</div>"
    searchResults.innerHTML = html

    // Add click event to item results
    const itemResults = searchResults.querySelectorAll(".item-result")
    itemResults.forEach((result) => {
      result.addEventListener("click", function () {
        selectItem(this)
      })
    })
  }

  // Select an item from the modal
  function selectItem(itemElement) {
    if (!currentInputField) return

    const itemCode = itemElement.getAttribute("data-item-code")
    const itemName = itemElement.getAttribute("data-item-name")
    const itemUom = itemElement.getAttribute("data-item-uom")
    const itemStock = itemElement.getAttribute("data-item-stock")
    const itemPrice = itemElement.getAttribute("data-item-price")

    // Set the item code in the input field
    currentInputField.value = itemCode

    // Find the row containing the input - could be in desktop or mobile view
    const row = currentInputField.closest(".formset-row, .mobile-formset-row")
    if (row) {
      // Update other fields in the row
      const itemNameInput = row.querySelector(".item-name-input")
      const stockInput = row.querySelector(".stock-input")
      const uomInput = row.querySelector(".uom-input")
      const unitPriceInput = row.querySelector(".unit-price-input")
      const quantityInput = row.querySelector(".quantity-input")

      if (itemNameInput) {
        itemNameInput.value = itemName
        itemNameInput.setAttribute("data-original-value", itemName)
      }

      if (stockInput) stockInput.value = itemStock
      if (uomInput) uomInput.value = itemUom

      // Only set unit price if it's empty or zero
      if (unitPriceInput && (!unitPriceInput.value || Number.parseFloat(unitPriceInput.value) === 0)) {
        unitPriceInput.value = itemPrice
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

      // Store original value for validation
      currentInputField.setAttribute("data-original-value", itemCode)

      // If this is a mobile row, also update the corresponding desktop row and vice versa
      const formsetBody = document.getElementById("formsetBody")
      const mobileFormsetContainer = document.getElementById("mobileFormsetContainer")

      if (isMobileInput && formsetBody) {
        const index = row.dataset.index
        const desktopRow = formsetBody.querySelector(`.formset-row[data-index="${index}"]`)
        if (desktopRow) {
          syncRowData(row, desktopRow)
        }
      } else if (!isMobileInput && mobileFormsetContainer) {
        const index = row.dataset.index
        const mobileRow = mobileFormsetContainer.querySelector(`.mobile-formset-row[data-index="${index}"]`)
        if (mobileRow) {
          syncRowData(row, mobileRow)
        }
      }
    }

    closeModal()
  }

  // Sync data between mobile and desktop rows
  function syncRowData(sourceRow, targetRow) {
    const fields = [
      "item-code-input",
      "item-name-input",
      "quantity-input",
      "unit-price-input",
      "uom-input",
      "stock-input",
      "total-amount-input",
    ]

    fields.forEach((fieldClass) => {
      const sourceInput = sourceRow.querySelector(`.${fieldClass}`)
      const targetInput = targetRow.querySelector(`.${fieldClass}`)

      if (sourceInput && targetInput) {
        targetInput.value = sourceInput.value

        // Also sync data attributes
        if (sourceInput.hasAttribute("data-original-value")) {
          targetInput.setAttribute("data-original-value", sourceInput.getAttribute("data-original-value"))
        }
      }
    })
  }

  // Event listeners for modal
  modalClose.addEventListener("click", closeModal)
  modalBackdrop.addEventListener("click", closeModal)
  refreshItemsBtn.addEventListener("click", () => {
    fetchItems(true) // Force refresh
  })

  // Search input event - filter from cache
  searchInput.addEventListener("input", function () {
    const query = this.value.trim()
    filterAndRenderItems(query)
  })

  // Close modal on escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !modal.classList.contains("hidden")) {
      closeModal()
    }
  })

  // Use event delegation for search icon clicks
  document.addEventListener("click", (e) => {
    // Check if the click was on a search icon or its child (the SVG)
    const searchIcon = e.target.closest(".item-search-icon")
    if (searchIcon) {
      // Find the associated input field
      const wrapper = searchIcon.closest(".item-input-wrapper")
      if (wrapper) {
        const input = wrapper.querySelector(".item-code-input")
        if (input) {
          currentInputField = input
          // Check if this is a mobile input
          isMobileInput = !!input.closest(".mobile-formset-row")
          openModal()
          e.preventDefault()
          e.stopPropagation()
        }
      }
    }
  })

  // Initialize search icons for existing rows
  addSearchIconToInputs()

  // Load cache on startup
  loadCacheFromStorage()

  // Run addSearchIconToInputs periodically to catch any new rows
  setInterval(addSearchIconToInputs, 500)

  // Set up a mutation observer to detect when new rows are added
  const formsetBody = document.getElementById("formsetBody")
  const mobileFormsetContainer = document.getElementById("mobileFormsetContainer")

  // Setup observer for desktop view
  if (formsetBody) {
    const observer = new MutationObserver((mutations) => {
      let needsUpdate = false

      mutations.forEach((mutation) => {
        if (mutation.type === "childList" && mutation.addedNodes.length > 0) {
          needsUpdate = true
        }
      })

      if (needsUpdate) {
        // Add a small delay to ensure DOM is fully updated
        setTimeout(addSearchIconToInputs, 10)
      }
    })

    observer.observe(formsetBody, {
      childList: true,
      subtree: true,
    })
  }

  // Setup observer for mobile view
  if (mobileFormsetContainer) {
    const observer = new MutationObserver((mutations) => {
      let needsUpdate = false

      mutations.forEach((mutation) => {
        if (mutation.type === "childList" && mutation.addedNodes.length > 0) {
          needsUpdate = true
        }
      })

      if (needsUpdate) {
        // Add a small delay to ensure DOM is fully updated
        setTimeout(addSearchIconToInputs, 10)
      }
    })

    observer.observe(mobileFormsetContainer, {
      childList: true,
      subtree: true,
    })
  }
})

