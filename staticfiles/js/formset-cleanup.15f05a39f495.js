/**
 * Formset Cleanup - Automatically removes empty rows before form submission
 */
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("goodsReceiptForm");

    if (form) {
        form.addEventListener("submit", function (event) {
            event.preventDefault(); // Prevent default form submission

            const formsetBody = document.getElementById("formsetBody");
            const rows = formsetBody.querySelectorAll("tr.formset-row");

            rows.forEach((row) => {
                // Identify key input fields in each row
                const itemCode = row.querySelector(".item-code-input");
                const quantity = row.querySelector(".quantity-input");
                const unitPrice = row.querySelector(".unit-price-input");

                // Check if the row is empty
                if (
                    itemCode && itemCode.value.trim() === "" &&
                    quantity && (quantity.value.trim() === "" || parseFloat(quantity.value) === 0) &&
                    unitPrice && (unitPrice.value.trim() === "" || parseFloat(unitPrice.value) === 0)
                ) {
                    // Mark row for deletion
                    const deleteCheckbox = row.querySelector(".delete-checkbox");
                    if (deleteCheckbox) {
                        deleteCheckbox.checked = true;
                        row.style.display = "none"; // Hide row visually
                    } else {
                        row.remove(); // Remove row if no delete checkbox exists
                    }
                }
            });

            // Submit form after cleanup
            form.submit();
        });
    }
});
