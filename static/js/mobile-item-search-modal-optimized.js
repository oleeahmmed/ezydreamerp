/**
 * Mobile Item Search Modal - Optimized with client-side caching
 *
 * Features:
 * 1. Uses the same cache as the desktop version
 * 2. Provides a mobile-optimized interface
 * 3. Instant search results from cached data
 */
document.addEventListener("DOMContentLoaded", () => {
  // Cache configuration
  const CACHE_KEY = "inventory_items_cache"
  const CACHE_EXPIRY = 30 * 60 * 1000 // 30 minutes in milliseconds

  // Item data cache
  let itemsCache = null
  let lastFetchTime = 0

  // Create mobile modal HTML structure once and append to body
  const mobileModalHTML = `
    <div id="mobileItemSearchModal" class="fixed inset-0 z-[9999] hidden bg-[hsl(var(--background))] flex flex-col">
        <div class="p-3 border-b border-[hsl(var(--border))] flex items-center justify-between">
            <h3 class="text-lg font-semibold text-[hsl(var(--foreground))]">Search Items</h3>
            <div class="flex items-center gap-2">
                <button type="button" id="mobileRefreshItemsBtn" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-[hsl(var(--accent))]" title="Refresh Items">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-5 h-5">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                </button>
                <button type="button" id="mobileItemSearchModalClose" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-[hsl(var(--accent))]">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-5 h-5">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        </div>
        <div class="p-3 border-b border-[hsl(var(--border))]">
            <div class="relative">
                <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" class="w-5 h-5 text-[hsl(var(--muted-foreground))]">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                </div>
                <input type="text" id="mobileItemSearchInput" class="w-full pl-10 pr-4 py-2 rounded-md border-2 border-[hsl(var(--border))] bg-transparent text-[hsl(var(--foreground))] transition-all duration-200 focus:outline-none focus:border-[hsl(var(--primary))] focus:ring-1 focus:ring-[hsl(var(--primary))]" placeholder="Search by item code or name...">
            </div>
        </div>
        <div class="flex-1 overflow-y-auto p-1" id="mobileItemSearchResults">
            <div class="flex items-center justify-center h-full text-[hsl(var(--muted-foreground))]">
                Loading items...
            </div>
        </div>
        <div class="p-3 border-t border-[hsl(var(--border))] flex justify-between items-center text-xs">
            <div class="text-[hsl(var(--muted-foreground))]">
                <span id="mobileItemCount">0</span> items found
            </div>
            <div id="mobileCacheStatus" class="text-[hsl(var(--muted-foreground))]">
                Using cached data
            </div>
        </div>
    </div>
    `

  // Append modal to body
  const mobileModalContainer = document.createElement("div")
  mobileModalContainer.innerHTML = mobileModalHTML
  document.body.appendChild(mobileModalContainer.firstElementChild)

  // Get modal elements
  const mobileModal = document.getElementById("mobileItemSearchModal")
  const mobileModalClose = document.getElementById("mobileItemSearchModalClose")
  const mobileRefreshItemsBtn = document.getElementById("mobileRefreshItemsBtn")
  const mobileSearchInput = document.getElementById("mobileItemSearchInput")
  const mobileSearchResults = document.getElementById("mobileItemSearchResults")
  const mobileItemCount = document.getElementById("mobileItemCount")
  const mobileCacheStatus = document.getElementById("mobileCacheStatus")

  // Current active input field that triggered the modal
  let currentMobileInputField = null

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

  // Add search icon to all mobile item code inputs
  function addSearchIconToMobileInputs() {
    const mobileFormsetContainer = document.getElementById("mobileFormsetContainer")
    if (!mobileFormsetContainer) return

    const itemCodeInputs = mobileFormsetContainer.querySelectorAll(".item-code-input")

    itemCodeInputs.forEach((input) => {
      // Skip if already has search icon
      if (input.parentElement.querySelector(".mobile-item-search-icon")) return

      // Create wrapper if input is not already wrapped
      let wrapper = input.parentElement
      if (!wrapper.classList.contains("mobile-item-input-wrapper")) {
        wrapper = document.createElement("div")
        wrapper.className = "mobile-item-input-wrapper relative"
        input.parentNode.insertBefore(wrapper, input)
        wrapper.appendChild(input)
      }

      // Add search icon
      const searchIcon = document.createElement("button")
      searchIcon.type = "button"
      searchIcon.className =
        "mobile-item-search-icon absolute right-2 top-1/2 transform -translate-y-1/2 w-8 h-8 flex items-center justify-center rounded-full hover:bg-[hsl(var(--accent))] transition-colors"
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
  function openMobileModal() {
    mobileModal.classList.remove("hidden")
    mobileSearchInput.value = ""
    mobileSearchInput.focus()

    // Check if we need to fetch items or can use cache
    if (!itemsCache) {
      fetchMobileItems()
    } else {
      // Use cached items
      updateMobileCacheStatus()
      filterAndRenderMobileItems("")
    }
  }

  // Close modal
  function closeMobileModal() {
    mobileModal.classList.add("hidden")
    mobileSearchResults.innerHTML = ""
    currentMobileInputField = null
  }

  // Update cache status display
  function updateMobileCacheStatus() {
    if (!itemsCache) {
      mobileCacheStatus.textContent = "Fetching data..."
      return
    }

    const now = Date.now()
    const ageInMinutes = Math.round((now - lastFetchTime) / 60000)

    if (ageInMinutes < 1) {
      mobileCacheStatus.textContent = "Using fresh data"
    } else if (ageInMinutes === 1) {
      mobileCacheStatus.textContent = "Cache: 1 minute old"
    } else {
      mobileCacheStatus.textContent = `Cache: ${ageInMinutes} minutes old`
    }
  }

  // Fetch items from API
  function fetchMobileItems(forceRefresh = false) {
    // Show loading state
    mobileSearchResults.innerHTML =
      '<div class="flex items-center justify-center h-32 text-[hsl(var(--muted-foreground))]">Loading items...</div>'
    mobileCacheStatus.textContent = "Fetching data..."

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
        updateMobileCacheStatus()
        filterAndRenderMobileItems(mobileSearchInput.value.trim())
      })
      .catch((error) => {
        console.error("Error loading items:", error)
        mobileSearchResults.innerHTML = `
                    <div class="flex items-center justify-center h-32 text-[hsl(var(--destructive))]">
                        Error loading items. Please try again.
                    </div>
                `

        // If we have cached data, use it despite the error
        if (itemsCache && !forceRefresh) {
          mobileCacheStatus.textContent = "Error fetching data, using cache"
          filterAndRenderMobileItems(mobileSearchInput.value.trim())
        } else {
          mobileCacheStatus.textContent = "Error fetching data"
          mobileItemCount.textContent = "0"
        }
      })
  }

  // Filter and render items based on search query
  function filterAndRenderMobileItems(query) {
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
    mobileItemCount.textContent = filteredItems.length

    // Render filtered items
    renderMobileItems(filteredItems)
  }

  // Render items in the modal
  function renderMobileItems(items) {
    if (items.length === 0) {
      mobileSearchResults.innerHTML = `
                <div class="flex items-center justify-center h-32 text-[hsl(var(--muted-foreground))]">
                    No items found. Try a different search term.
                </div>
            `
      return
    }

    let html = '<div class="grid grid-cols-1 gap-1 p-2">'

    items.forEach((item) => {
      html += `
                <div class="mobile-item-result flex items-center p-3 rounded-md hover:bg-[hsl(var(--accent))] active:bg-[hsl(var(--accent))] cursor-pointer transition-colors" 
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
    mobileSearchResults.innerHTML = html

    // Add click event to item results
    const itemResults = mobileSearchResults.querySelectorAll(".mobile-item-result")
    itemResults.forEach((result) => {
      result.addEventListener("click", function () {
        selectMobileItem(this)
      })
    })
  }

  // Select an item from the modal
  function selectMobileItem(itemElement) {
    if (!currentMobileInputField) return

    const itemCode = itemElement.getAttribute("data-item-code")
    const itemName = itemElement.getAttribute("data-item-name")
    const itemUom = itemElement.getAttribute("data-item-uom")
    const itemStock = itemElement.getAttribute("data-item-stock")
    const itemPrice = itemElement.getAttribute("data-item-price")

    // Set the item code in the input field
    currentMobileInputField.value = itemCode

    // Find the row containing the input
    const row = currentMobileInputField.closest(".mobile-formset-row")
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
      currentMobileInputField.setAttribute("data-original-value", itemCode)

      // Also update the corresponding desktop row if it exists
      const formsetBody = document.getElementById("formsetBody")
      if (formsetBody) {
        const index = row.dataset.index
        const desktopRow = formsetBody.querySelector(`.formset-row[data-index="${index}"]`)
        if (desktopRow) {
          syncMobileToDesktopRow(row, desktopRow)
        }
      }
    }

    closeMobileModal()
  }

  // Sync data from mobile to desktop row
  function syncMobileToDesktopRow(mobileRow, desktopRow) {
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
      const mobileInput = mobileRow.querySelector(`.${fieldClass}`)
      const desktopInput = desktopRow.querySelector(`.${fieldClass}`)

      if (mobileInput && desktopInput) {
        desktopInput.value = mobileInput.value

        // Also sync data attributes
        if (mobileInput.hasAttribute("data-original-value")) {
          desktopInput.setAttribute("data-original-value", mobileInput.getAttribute("data-original-value"))
        }
      }
    })
  }

  // Event listeners for modal
  mobileModalClose.addEventListener("click", closeMobileModal)
  mobileRefreshItemsBtn.addEventListener("click", () => {
    fetchMobileItems(true) // Force refresh
  })

  // Search input event - filter from cache
  mobileSearchInput.addEventListener("input", function () {
    const query = this.value.trim()
    filterAndRenderMobileItems(query)
  })

  // Close modal on escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !mobileModal.classList.contains("hidden")) {
      closeMobileModal()
    }
  })

  // Use event delegation for search icon clicks
  document.addEventListener("click", (e) => {
    // Check if the click was on a search icon or its child (the SVG)
    const searchIcon = e.target.closest(".mobile-item-search-icon")
    if (searchIcon) {
      // Find the associated input field
      const wrapper = searchIcon.closest(".mobile-item-input-wrapper")
      if (wrapper) {
        const input = wrapper.querySelector(".item-code-input")
        if (input) {
          currentMobileInputField = input
          openMobileModal()
          e.preventDefault()
          e.stopPropagation()
        }
      }
    }
  })

  // Initialize search icons for existing rows
  addSearchIconToMobileInputs()

  // Load cache on startup
  loadCacheFromStorage()

  // Run addSearchIconToMobileInputs periodically to catch any new rows
  setInterval(addSearchIconToMobileInputs, 500)

  // Get the mobileFormsetContainer element
  const mobileFormsetContainer = document.getElementById("mobileFormsetContainer")

  // Set up a mutation observer to detect when new rows are added
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
        setTimeout(addSearchIconToMobileInputs, 10)
      }
    })

    observer.observe(mobileFormsetContainer, {
      childList: true,
      subtree: true,
    })
  }
})

