/**
 * Mobile Financial Calculations - Handles overall financial calculations for the mobile view
 *
 * This script:
 * 1. Calculates subtotals from all mobile line items
 * 2. Applies taxes and discounts
 * 3. Calculates final totals, payable and due amounts
 * 4. Updates summary fields in the mobile view
 * 5. Listens for changes in line items directly and via events
 */
document.addEventListener("DOMContentLoaded", () => {
  console.log("Mobile Financial Calculations loaded")

  // Initialize financial calculations
  calculateMobileFinancials()

  // Listen for line item updates from mobile-line-calculations.js
  document.addEventListener("lineItemsUpdated", () => {
    console.log("lineItemsUpdated event received")
    calculateMobileFinancials()
  })

  // Direct listeners for quantity and price changes as a backup
  const mobileFormsetContainer = document.getElementById("mobileFormsetContainer")
  if (mobileFormsetContainer) {
    mobileFormsetContainer.addEventListener("input", (e) => {
      if (e.target.classList.contains("quantity-input") || e.target.classList.contains("unit-price-input")) {
        console.log("Direct input detected in mobile formset")
        // Use setTimeout to ensure the line calculations complete first
        setTimeout(calculateMobileFinancials, 10)
      }
    })
  }

  /**
   * Calculate all financial values for the mobile view
   */
  function calculateMobileFinancials() {
    console.log("Calculating mobile financials")
    const subtotal = calculateMobileSubtotal()
    const taxRate = getMobileTaxRate()
    const taxAmount = calculateMobileTaxAmount(subtotal, taxRate)
    const discountAmount = getMobileDiscountAmount()
    const total = calculateMobileTotal(subtotal, taxAmount, discountAmount)

    // Calculate payable and due amounts
    const payableAmount = total // Payable is typically the same as total
    const paidAmount = getMobilePaidAmount()
    const dueAmount = payableAmount - paidAmount

    console.log({
      subtotal,
      taxRate,
      taxAmount,
      discountAmount,
      total,
      payableAmount,
      paidAmount,
      dueAmount,
    })

    // Update the financial summary fields in the mobile view
    updateMobileFinancialSummary(subtotal, taxAmount, discountAmount, total, payableAmount, dueAmount)
  }

  /**
   * Calculate the subtotal from all visible mobile line items
   */
  function calculateMobileSubtotal() {
    let subtotal = 0

    // Try multiple selectors to find the mobile rows
    const selectors = [
      "#mobileFormsetContainer .mobile-formset-row:not(.d-none)",
      ".mobile-formset-row:not(.d-none)",
      ".mobile-row:not(.d-none)",
      "[data-mobile-row]:not(.d-none)",
    ]

    let mobileRows = []
    for (const selector of selectors) {
      mobileRows = document.querySelectorAll(selector)
      if (mobileRows.length > 0) {
        console.log(`Found ${mobileRows.length} mobile rows with selector: ${selector}`)
        break
      }
    }

    mobileRows.forEach((row) => {
      // Try multiple selectors for total amount
      const totalSelectors = [".total-amount-input", ".line-total", "[data-total]", "input[name*='total']"]

      let totalAmountInput = null
      for (const selector of totalSelectors) {
        totalAmountInput = row.querySelector(selector)
        if (totalAmountInput) break
      }

      if (totalAmountInput) {
        const value = totalAmountInput.value || totalAmountInput.textContent || "0"
        const amount = Number.parseFloat(value.replace(/[^0-9.-]+/g, "")) || 0
        subtotal += amount
      }
    })

    console.log(`Calculated subtotal: ${subtotal}`)
    return subtotal
  }

  /**
   * Get the tax rate from the mobile tax rate input
   */
  function getMobileTaxRate() {
    // Try multiple selectors for tax rate
    const selectors = ["#mobileTaxRate", ".tax-rate", "[data-tax-rate]", "input[name*='tax_rate']"]

    let taxRateInput = null
    for (const selector of selectors) {
      taxRateInput = document.querySelector(selector)
      if (taxRateInput) break
    }

    const taxRate = taxRateInput ? (Number.parseFloat(taxRateInput.value) || 0) / 100 : 0

    console.log(`Tax rate: ${taxRate}`)
    return taxRate
  }

  /**
   * Calculate the tax amount based on subtotal and tax rate
   */
  function calculateMobileTaxAmount(subtotal, taxRate) {
    return subtotal * taxRate
  }

  /**
   * Get the discount amount from the mobile discount input
   */
  function getMobileDiscountAmount() {
    // Try multiple selectors for discount
    const selectors = ["#mobileDiscountAmount", ".discount-amount", "[data-discount]", "input[name*='discount']"]

    let discountInput = null
    for (const selector of selectors) {
      discountInput = document.querySelector(selector)
      if (discountInput) break
    }

    const discount = discountInput ? Number.parseFloat(discountInput.value) || 0 : 0

    console.log(`Discount amount: ${discount}`)
    return discount
  }

  /**
   * Get the paid amount from the mobile paid input
   */
  function getMobilePaidAmount() {
    // Try multiple selectors for paid amount
    const selectors = ["#mobilePaidAmount", ".paid-amount", "[data-paid]", "input[name*='paid']"]

    let paidInput = null
    for (const selector of selectors) {
      paidInput = document.querySelector(selector)
      if (paidInput) break
    }

    const paidAmount = paidInput ? Number.parseFloat(paidInput.value) || 0 : 0

    console.log(`Paid amount: ${paidAmount}`)
    return paidAmount
  }

  /**
   * Calculate the final total
   */
  function calculateMobileTotal(subtotal, taxAmount, discountAmount) {
    return subtotal + taxAmount - discountAmount
  }

  /**
   * Update all financial summary fields in the mobile view
   */
  function updateMobileFinancialSummary(subtotal, taxAmount, discountAmount, total, payableAmount, dueAmount) {
    // Update subtotal display - try multiple selectors
    updateDisplayElement(
      ["#mobileSubtotalDisplay", ".subtotal-display", "[data-subtotal-display]"],
      formatCurrency(subtotal),
    )

    // Update tax amount display
    updateDisplayElement(["#mobileTaxDisplay", ".tax-display", "[data-tax-display]"], formatCurrency(taxAmount))

    // Update discount display
    updateDisplayElement(
      ["#mobileDiscountDisplay", ".discount-display", "[data-discount-display]"],
      formatCurrency(discountAmount),
    )

    // Update total display
    updateDisplayElement(["#mobileTotalDisplay", ".total-display", "[data-total-display]"], formatCurrency(total))

    // Update payable amount display
    updateDisplayElement(
      ["#mobilePayableDisplay", ".payable-display", "[data-payable-display]"],
      formatCurrency(payableAmount),
    )

    // Update due amount display
    updateDisplayElement(["#mobileDueDisplay", ".due-display", "[data-due-display]"], formatCurrency(dueAmount))

    // Update hidden input fields for form submission
    updateInputValue(["#mobileTotalInput", "input[name*='total']", "[data-total-input]"], total.toFixed(2))

    updateInputValue(
      ["#mobilePayableInput", "input[name*='payable']", "[data-payable-input]"],
      payableAmount.toFixed(2),
    )

    updateInputValue(["#mobileDueInput", "input[name*='due']", "[data-due-input]"], dueAmount.toFixed(2))

    console.log("Financial summary updated")
  }

  /**
   * Helper function to update display elements with multiple selector attempts
   */
  function updateDisplayElement(selectors, value) {
    for (const selector of selectors) {
      const element = document.querySelector(selector)
      if (element) {
        element.textContent = value
        console.log(`Updated ${selector} with ${value}`)
        break
      }
    }
  }

  /**
   * Helper function to update input values with multiple selector attempts
   */
  function updateInputValue(selectors, value) {
    for (const selector of selectors) {
      const element = document.querySelector(selector)
      if (element) {
        element.value = value
        console.log(`Updated input ${selector} with ${value}`)
        break
      }
    }
  }

  /**
   * Format a number as currency
   */
  function formatCurrency(amount) {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
    }).format(amount)
  }

  // Listen for changes on tax rate input with multiple selector attempts
  const taxRateSelectors = ["#mobileTaxRate", ".tax-rate", "[data-tax-rate]"]
  for (const selector of taxRateSelectors) {
    const taxRateInput = document.querySelector(selector)
    if (taxRateInput) {
      taxRateInput.addEventListener("input", calculateMobileFinancials)
      console.log(`Added listener to tax rate input: ${selector}`)
      break
    }
  }

  // Listen for changes on discount input with multiple selector attempts
  const discountSelectors = ["#mobileDiscountAmount", ".discount-amount", "[data-discount]"]
  for (const selector of discountSelectors) {
    const discountInput = document.querySelector(selector)
    if (discountInput) {
      discountInput.addEventListener("input", calculateMobileFinancials)
      console.log(`Added listener to discount input: ${selector}`)
      break
    }
  }

  // Listen for changes on paid amount input
  const paidSelectors = ["#mobilePaidAmount", ".paid-amount", "[data-paid]"]
  for (const selector of paidSelectors) {
    const paidInput = document.querySelector(selector)
    if (paidInput) {
      paidInput.addEventListener("input", calculateMobileFinancials)
      console.log(`Added listener to paid amount input: ${selector}`)
      break
    }
  }

  // Make the calculation function available globally for debugging
  window.calculateMobileFinancials = calculateMobileFinancials
})

