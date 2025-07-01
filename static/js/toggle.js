document.addEventListener("DOMContentLoaded", () => {
    setupSidebarDropdowns();
});

function setupSidebarDropdowns() {
    const dropdownButtons = document.querySelectorAll("[data-dropdown-toggle]");

    dropdownButtons.forEach(button => {
        const dropdownId = button.getAttribute("data-dropdown-toggle");
        const dropdownMenu = document.getElementById(dropdownId);
        const arrow = button.querySelector("svg");

        if (!dropdownMenu) return;

        // Toggle dropdown on click
        button.addEventListener("click", (event) => {
            event.stopPropagation();
            closeAllDropdowns();
            dropdownMenu.classList.remove("hidden");
            dropdownMenu.classList.add("dropdown-menu", "animate-fade-in");
            if (arrow) arrow.style.transform = "rotate(180deg)";
        });

        // Close dropdown when clicking outside
        // document.addEventListener("click", (event) => {
        //     if (!dropdownMenu.contains(event.target) && !button.contains(event.target)) {
        //         closeDropdown(dropdownMenu, arrow);
        //     }
        // });

        // Close dropdown on mouse leave
        // dropdownMenu.addEventListener("mouseleave", () => {
        //     closeDropdown(dropdownMenu, arrow);
        // });

        // Close dropdown when pressing Escape key
        // document.addEventListener("keydown", (event) => {
        //     if (event.key === "Escape") {
        //         closeAllDropdowns();
        //     }
        // });
    });
}

// Function to close a specific dropdown with animation
function closeDropdown(menu, arrow) {
    if (menu) {
        menu.classList.add("closing");
        setTimeout(() => {
            menu.classList.add("hidden");
            menu.classList.remove("dropdown-menu", "closing", "animate-fade-in");
        }, 300);
    }
    if (arrow) {
        arrow.style.transform = "rotate(0deg)";
    }
}

// Function to close all dropdowns
function closeAllDropdowns() {
    document.querySelectorAll(".dropdown-menu").forEach(menu => {
        closeDropdown(menu, menu.previousElementSibling?.querySelector("svg"));
    });
}
