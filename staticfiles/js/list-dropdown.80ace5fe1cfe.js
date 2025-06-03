document.addEventListener("DOMContentLoaded", function () {
    const actionDropdownTriggers = document.querySelectorAll(".dropdown-trigger");

    actionDropdownTriggers.forEach(trigger => {
        trigger.addEventListener("click", function (event) {
            event.stopPropagation(); // Prevent closing other elements

            const dropdownMenu = this.nextElementSibling;

            // Close only other action dropdowns (ignore Settings/Profile dropdowns)
            document.querySelectorAll(".dropdown-menu").forEach(menu => {
                if (menu !== dropdownMenu && menu.closest(".dropdown-container")) {
                    menu.classList.add("hidden");
                }
            });

            // Toggle current action dropdown
            dropdownMenu.classList.toggle("hidden");
        });
    });

    // Close only action dropdowns when clicking outside
    document.addEventListener("click", function (event) {
        if (!event.target.closest(".dropdown-container")) {
            document.querySelectorAll(".dropdown-menu").forEach(menu => {
                if (menu.closest(".dropdown-container")) {
                    menu.classList.add("hidden");
                }
            });
        }
    });

    // Close only action dropdowns when pressing Escape key
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            document.querySelectorAll(".dropdown-menu").forEach(menu => {
                if (menu.closest(".dropdown-container")) {
                    menu.classList.add("hidden");
                }
            });
        }
    });
});
