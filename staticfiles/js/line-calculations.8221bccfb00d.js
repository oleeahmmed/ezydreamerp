/**
 * Line Calculations - Handles calculations for each line item in the formset
 */
document.addEventListener("DOMContentLoaded", () => {
  // Initialize calculations for existing rows
  initializeAllRows()

  // Set up a mutation observer to detect when new rows are added
  setupMutationObserver()

  /**
   * Initialize calculations for all existing formset rows
   */
  function initializeAllRows() {
    const rows = document.querySelectorAll("#formsetBody tr.formset-row")
    rows.forEach((row) => {
      setupRowCalculations(row)
    })
  }

  /**
   * Set up calculations for a single formset row
   */
  function setupRowCalculations(row) {
    const quantityInput = row.querySelector(".quantity-input")
    const unitPriceInput = row.querySelector(".unit-price-input")
    const totalAmountInput = row.querySelector(".total-amount-input")

    if (quantityInput && unitPriceInput && totalAmountInput) {
      // Calculate total when quantity changes
      quantityInput.addEventListener("input", () => {
        calculateLineTotal(quantityInput, unitPriceInput, totalAmountInput)
        triggerFinancialCalculations()
      })

      // Calculate total when unit price changes
      unitPriceInput.addEventListener("input", () => {
        calculateLineTotal(quantityInput, unitPriceInput, totalAmountInput)
        triggerFinancialCalculations()
      })

      // Initial calculation
      calculateLineTotal(quantityInput, unitPriceInput, totalAmountInput)
    }
  }

  /**
   * Calculate the total amount for a line item
   */
  function calculateLineTotal(quantityInput, unitPriceInput, totalAmountInput) {
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
    const event = new CustomEvent("lineItemsUpdated")
    document.dispatchEvent(event)
  }

  /**
   * Set up a mutation observer to detect when new rows are added to the formset
   */
  function setupMutationObserver() {
    const formsetBody = document.getElementById("formsetBody")

    // Create a new observer
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === "childList" && mutation.addedNodes.length > 0) {
          // Check each added node
          mutation.addedNodes.forEach((node) => {
            // If it's a formset row, set up calculations
            if (node.nodeType === 1 && node.classList.contains("formset-row")) {
              setupRowCalculations(node)
            }
          })
          // Trigger financial calculations after rows are added
          triggerFinancialCalculations()
        }
      })
    })

    // Start observing the formset body for added nodes
    observer.observe(formsetBody, { childList: true })
  }

  // Listen for delete row events
  document.addEventListener("click", (e) => {
    if (e.target.closest(".delete-row")) {
      // Use setTimeout to ensure the row is hidden before recalculating
      setTimeout(triggerFinancialCalculations, 0)
    }
  })
})

