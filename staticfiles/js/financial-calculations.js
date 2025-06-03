/**
 * Financial Calculations - Handles all financial calculations in the form
 *
 * This script:
 * 1. Calculates total amount by summing all line totals
 * 2. Calculates payable amount based on total and discount
 * 3. Calculates due amount based on payable and paid amounts
 * 4. Sets up automatic payment date when paid amount is entered
 * 5. Handles all financial field dependencies
 */
document.addEventListener("DOMContentLoaded", () => {
  // Get all financial fields
  const totalAmountInput = document.getElementById("id_total_amount")
  const discountAmountInput = document.getElementById("id_discount_amount")
  const payableAmountInput = document.getElementById("id_payable_amount")
  const paidAmountInput = document.getElementById("id_paid_amount")
  const dueAmountInput = document.getElementById("id_due_amount")
  const paymentMethodSelect = document.getElementById("id_payment_method")
  const paymentDateInput = document.getElementById("id_payment_date")

  // Check if financial fields exist before proceeding
  const hasFinancialFields =
    totalAmountInput || discountAmountInput || payableAmountInput || paidAmountInput || dueAmountInput

  // Only initialize financial calculations if at least one financial field exists
  if (hasFinancialFields) {
    // Set default values for financial fields
    //initializeDefaultValues()

    // Set up event listeners for financial fields
    //setupFinancialEventListeners()

    // Listen for line item updates from the line-calculations.js script
    document.addEventListener("lineItemsUpdated", calculateTotalFromLines)

    // Initial calculation
    calculateTotalFromLines()
  }

  /**
   * Calculate total amount by summing all line totals
   */
  function calculateTotalFromLines() {
    if (!totalAmountInput) return

    let total = 0

    // Get all visible (not deleted) formset rows
    const rows = document.querySelectorAll('#formsetBody tr.formset-row:not([style*="display: none"])')

    // Sum up the total amount from each row
    rows.forEach((row) => {
      const totalAmountField = row.querySelector(".total-amount-input")
      if (totalAmountField) {
        total += Number.parseFloat(totalAmountField.value) || 0
      }
    })

    // Update the total amount field
    totalAmountInput.value = total.toFixed(2)

    // Recalculate dependent values
    calculatePayableAmount()
  }

  /**
   * Calculate payable amount based on total amount and discount
   */
  function calculatePayableAmount() {
    if (!payableAmountInput) return

    const totalAmount = totalAmountInput ? Number.parseFloat(totalAmountInput.value) || 0 : 0
    const discountAmount = discountAmountInput ? Number.parseFloat(discountAmountInput.value) || 0 : 0

    // Calculate payable amount (total - discount)
    const payableAmount = totalAmount - discountAmount

    // Update the payable amount field
    payableAmountInput.value = payableAmount.toFixed(2)

    // Recalculate due amount since payable has changed
    calculateDueAmount()
  }

  /**
   * Calculate due amount based on payable amount and paid amount
   */
  function calculateDueAmount() {
    if (!dueAmountInput) return

    const payableAmount = payableAmountInput ? Number.parseFloat(payableAmountInput.value) || 0 : 0
    const paidAmount = paidAmountInput ? Number.parseFloat(paidAmountInput.value) || 0 : 0

    // Calculate due amount (payable - paid)
    const dueAmount = payableAmount - paidAmount

    // Update the due amount field
    dueAmountInput.value = dueAmount.toFixed(2)
  }

  // Set up event listeners for financial fields
  if (discountAmountInput) {
    discountAmountInput.addEventListener("input", calculatePayableAmount)
  }

  if (paidAmountInput) {
    paidAmountInput.addEventListener("input", calculateDueAmount)
  }
})

