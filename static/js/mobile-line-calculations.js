/**
 * Mobile Line Calculations - Handles calculations for each line item in the mobile formset
 *
 * This script:
 * 1. Initializes calculations for existing mobile rows
 * 2. Sets up event listeners for quantity and unit price changes
 * 3. Calculates line totals (quantity * unit price)
 * 4. Triggers financial calculations when line values change
 * 5. Observes when new rows are added to the mobile formset
 */
document.addEventListener("DOMContentLoaded", () => {
  // Initialize calculations for existing mobile rows
  initializeAllMobileRows()

  // Set up a mutation observer to detect when new rows are added
  setupMobileMutationObserver()

  /**
   * Initialize calculations for all existing mobile formset rows
   */
  function initializeAllMobileRows() {
    const mobileRows = document.querySelectorAll("#mobileFormsetContainer .mobile-formset-row")
    mobileRows.forEach((row) => {
      setupMobileRowCalculations(row)
    })
  }

  /**
   * Set up calculations for a single mobile formset row
   */
  function setupMobileRowCalculations(row) {
    const quantityInput = row.querySelector(".quantity-input")
    const unitPriceInput = row.querySelector(".unit-price-input")
    const totalAmountInput = row.querySelector(".total-amount-input")

    if (quantityInput && unitPriceInput && totalAmountInput) {
      // Calculate total when quantity changes
      quantityInput.addEventListener("input", () => {
        calculateMobileLineTotal(quantityInput, unitPriceInput, totalAmountInput)
        triggerFinancialCalculations()
      })

      // Calculate total when unit price changes
      unitPriceInput.addEventListener("input", () => {
        calculateMobileLineTotal(quantityInput, unitPriceInput, totalAmountInput)
        triggerFinancialCalculations()
      })

      // Initial calculation
      calculateMobileLineTotal(quantityInput, unitPriceInput, totalAmountInput)
    }
  }

  /**
   * Calculate the total amount for a mobile line item
   */
  function calculateMobileLineTotal(quantityInput, unitPriceInput, totalAmountInput) {
    const quantity = Number.parseFloat(quantityInput.value) || 0
    const unitPrice = Number.parseFloat(unitPriceInput.value) || 0
    const total = quantity * unitPrice

    // Format to 2 decimal places and update the total amount field
    totalAmountInput.value = total.toFixed(2)
  }

  /**
   * Trigger the financial calculations by dispatching a custom event
   */
  function triggerFinancialCalculations() {
    // Create and dispatch a custom event that the financial calculations script will listen for
    console.log("Triggering lineItemsUpdated event")
    const event = new CustomEvent("lineItemsUpdated")
    document.dispatchEvent(event)

    // As a backup, try to call the financial calculations directly if available
    if (window.calculateMobileFinancials) {
      console.log("Calling calculateMobileFinancials directly")
      window.calculateMobileFinancials()
    }
  }

  /**
   * Set up a mutation observer to detect when new rows are added to the mobile formset
   */
  function setupMobileMutationObserver() {
    const mobileFormsetContainer = document.getElementById("mobileFormsetContainer")
    if (!mobileFormsetContainer) return

    // Create a new observer
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === "childList" && mutation.addedNodes.length > 0) {
          // Check each added node
          mutation.addedNodes.forEach((node) => {
            // If it's a mobile formset row, set up calculations
            if (node.nodeType === 1 && node.classList.contains("mobile-formset-row")) {
              setupMobileRowCalculations(node)
            }
          })
          // Trigger financial calculations after rows are added
          triggerFinancialCalculations()
        }
      })
    })

    // Start observing the mobile formset container for added nodes
    observer.observe(mobileFormsetContainer, { childList: true })
  }

  // Listen for delete row events in mobile view
  document.addEventListener("click", (e) => {
    if (e.target.closest(".mobile-delete-row")) {
      // Use setTimeout to ensure the row is hidden before recalculating
      setTimeout(triggerFinancialCalculations, 0)
    }
  })
})

