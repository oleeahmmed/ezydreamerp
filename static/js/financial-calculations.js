/**
 * Desktop Financial Calculations - Handles overall financial calculations for the desktop view
 *
 * This script:
 * 1. Calculates subtotals from all desktop line items
 * 2. Applies discounts
 * 3. Calculates final totals, payable and due amounts
 * 4. Updates summary fields in the desktop view
 * 5. Listens for changes in line items directly and via events
 */
document.addEventListener("DOMContentLoaded", () => {
  console.log("Desktop Financial Calculations loaded")

  // Initialize financial calculations
  calculateDesktopFinancials()

  // Listen for line item updates from line-calculations.js
  document.addEventListener("lineItemsUpdated", () => {
    console.log("lineItemsUpdated event received in desktop calculations")
    calculateDesktopFinancials()
  })

  // Direct listeners for quantity and price changes as a backup
  const formsetBody = document.getElementById("formsetBody")
  if (formsetBody) {
    formsetBody.addEventListener("input", (e) => {
      if (e.target.classList.contains("quantity-input") || e.target.classList.contains("unit-price-input")) {
        console.log("Direct input detected in desktop formset")
        // Use setTimeout to ensure the line calculations complete first
        setTimeout(calculateDesktopFinancials, 10)
      }
    })
  }

  /**
   * Calculate all financial values for the desktop view
   */
  function calculateDesktopFinancials() {
    console.log("Calculating desktop financials")
    const subtotal = calculateDesktopSubtotal()
    const discountAmount = getDesktopDiscountAmount()
    const payableAmount = subtotal - discountAmount
    const paidAmount = getDesktopPaidAmount()
    const dueAmount = payableAmount - paidAmount

    console.log({
      subtotal,
      discountAmount,
      payableAmount,
      paidAmount,
      dueAmount,
    })

    // Update the financial summary fields in the desktop view
    updateDesktopFinancialSummary(subtotal, discountAmount, payableAmount, paidAmount, dueAmount)
  }

  /**
   * Calculate the subtotal from all visible desktop line items
   */
  function calculateDesktopSubtotal() {
    let subtotal = 0

    // Get all visible (not deleted) formset rows from desktop view
    const desktopRows = document.querySelectorAll('#formsetBody tr.formset-row:not([style*="display: none"])')

    // Sum up the total amount from each desktop row
    desktopRows.forEach((row) => {
      const totalAmountField = row.querySelector(".total-amount-input")
      if (totalAmountField) {
        const rowTotal = Number.parseFloat(totalAmountField.value) || 0
        subtotal += rowTotal
        console.log(`Desktop row total: ${rowTotal}, Running subtotal: ${subtotal}`)
      }
    })

    console.log(`Final calculated subtotal: ${subtotal}`)
    return subtotal
  }

  /**
   * Get the discount amount from the desktop discount input
   */
  function getDesktopDiscountAmount() {
    const discountInput = document.getElementById("id_discount_amount")
    const discount = discountInput ? Number.parseFloat(discountInput.value) || 0 : 0

    console.log(`Desktop discount amount: ${discount}`)
    return discount
  }

  /**
   * Get the paid amount from the desktop paid input
   */
  function getDesktopPaidAmount() {
    const paidInput = document.getElementById("id_paid_amount")

    // Remove readonly attribute if it exists
    if (paidInput && paidInput.hasAttribute("readonly")) {
      paidInput.removeAttribute("readonly")
      console.log("Removed readonly attribute from paid_amount field")
    }

    const paidAmount = paidInput ? Number.parseFloat(paidInput.value) || 0 : 0

    console.log(`Desktop paid amount: ${paidAmount}`)
    return paidAmount
  }

  /**
   * Update all financial summary fields in the desktop view
   */
  function updateDesktopFinancialSummary(subtotal, discountAmount, payableAmount, paidAmount, dueAmount) {
    // Update total amount input
    const totalAmountInput = document.getElementById("id_total_amount")
    if (totalAmountInput) {
      totalAmountInput.value = subtotal.toFixed(2)
      console.log(`Updated total amount: ${subtotal.toFixed(2)}`)
    }

    // Update discount amount input (if not already set by user)
    const discountAmountInput = document.getElementById("id_discount_amount")
    if (discountAmountInput && !discountAmountInput._userModified) {
      discountAmountInput.value = discountAmount.toFixed(2)
      console.log(`Updated discount amount: ${discountAmount.toFixed(2)}`)
    }

    // Update payable amount input
    const payableAmountInput = document.getElementById("id_payable_amount")
    if (payableAmountInput) {
      payableAmountInput.value = payableAmount.toFixed(2)
      console.log(`Updated payable amount: ${payableAmount.toFixed(2)}`)
    }

    // Update due amount input
    const dueAmountInput = document.getElementById("id_due_amount")
    if (dueAmountInput) {
      dueAmountInput.value = dueAmount.toFixed(2)
      console.log(`Updated due amount: ${dueAmount.toFixed(2)}`)
    }

    // Update payment date if paid amount > 0 and payment date is not set
    if (paidAmount > 0) {
      const paymentDateInput = document.getElementById("id_payment_date")
      if (paymentDateInput && !paymentDateInput.value) {
        const today = new Date()
        const formattedDate = today.toISOString().split("T")[0] // Format as YYYY-MM-DD
        paymentDateInput.value = formattedDate
        console.log(`Set payment date to today: ${formattedDate}`)
      }
    }

    console.log("Desktop financial summary updated")
  }

  // Listen for changes on discount input
  const discountAmountInput = document.getElementById("id_discount_amount")
  if (discountAmountInput) {
    discountAmountInput.addEventListener("input", () => {
      discountAmountInput._userModified = true
      console.log("Discount amount changed by user:", discountAmountInput.value)
      calculateDesktopFinancials()
    })
  }

  // Listen for changes on paid amount input
  const paidAmountInput = document.getElementById("id_paid_amount")
  if (paidAmountInput) {
    paidAmountInput.addEventListener("input", () => {
      console.log("Paid amount changed:", paidAmountInput.value)
      calculateDesktopFinancials()
    })
  }

  // Make the calculation function available globally for debugging
  window.calculateDesktopFinancials = calculateDesktopFinancials
})
