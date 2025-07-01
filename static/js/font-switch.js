document.addEventListener("DOMContentLoaded", () => {
    setupFontSwitcher();
});

function setupFontSwitcher() {
    const fontToggle = document.getElementById("fontToggle");
    const fontDropdown = document.getElementById("fontDropdown");
    const fontOptions = document.querySelectorAll(".font-option");
    const fontStylesheet = document.getElementById("fontStylesheet");

    // Load saved font from localStorage
    const savedFont = localStorage.getItem("selectedFont") || "Inter";
    document.body.style.fontFamily = `'${savedFont}', sans-serif`;

    // Toggle dropdown visibility
    fontToggle.addEventListener("click", (e) => {
        e.stopPropagation();
        fontDropdown.classList.toggle("hidden");
    });

    // Change font when an option is clicked
    fontOptions.forEach(option => {
        option.addEventListener("click", (e) => {
            const selectedFont = e.target.getAttribute("data-font");
            document.body.style.fontFamily = `'${selectedFont}', sans-serif`;
            fontStylesheet.setAttribute("href", `https://fonts.googleapis.com/css2?family=${selectedFont}:wght@300;400;700&display=swap`);
            localStorage.setItem("selectedFont", selectedFont);
            fontDropdown.classList.add("hidden"); // Close dropdown after selection
        });
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", (event) => {
        if (!fontDropdown.contains(event.target) && !fontToggle.contains(event.target)) {
            fontDropdown.classList.add("hidden");
        }
    });

    // Close dropdown on Escape key
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            fontDropdown.classList.add("hidden");
        }
    });
}
