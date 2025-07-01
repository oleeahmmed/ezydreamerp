

// Available themes configuration
const THEMES = [
    { id: "default", name: "Default", color: "hsl(240 5.9% 10%)" },
    { id: "blue", name: "Blue", color: "hsl(217 91% 60%)" },
    { id: "rose", name: "Rose", color: "hsl(346.8 77.2% 49.8%)" },
    { id: "indigo", name: "Indigo", color: "hsl(240 82% 50%)" },
    { id: "amber", name: "Amber", color: "hsl(35.5 91.7% 32.9%)" },
    { id: "purple", name: "Purple", color: "hsl(262.1 83.3% 57.8%)" },
    { id: "teal", name: "Teal", color: "hsl(173 80% 40%)" },
    { id: "green", name: "Green", color: "hsl(142.1 76.2% 36.3%)" },
    // New modern themes
    { id: "cyan", name: "Cyan", color: "hsl(190 95% 39%)" },
    { id: "violet", name: "Violet", color: "hsl(265 89% 66%)" },
    { id: "crimson", name: "Crimson", color: "hsl(348 86% 61%)" },
    { id: "emerald", name: "Emerald", color: "hsl(152 81% 42%)" },
    { id: "slate", name: "Slate", color: "hsl(215 30% 40%)" },
    { id: "coral", name: "Coral", color: "hsl(16 90% 60%)" },
    { id: "mint", name: "Mint", color: "hsl(160 84% 39%)" },
  ]
  
  // Initialize when DOM is loaded
  document.addEventListener("DOMContentLoaded", () => {
    initThemeSystem()
    setupThemeOptions()
    setupEventListeners()
  })
  
  // Initialize theme system
  function initThemeSystem() {
    const savedColorMode = localStorage.getItem("colorMode") || "light"
    const savedTheme = localStorage.getItem("cssTheme") || "default"
  
    applyTheme(savedTheme)
    applyColorMode(savedColorMode)
    updateThemeIcon(savedColorMode)
  }
  
  // Update the visible theme icon
  function updateThemeIcon(mode) {
    document.querySelectorAll(".theme-light, .theme-dark, .theme-system").forEach((icon) => {
      icon.style.display = "none"
    })
  
    const activeIcon = document.querySelector(`.theme-${mode}`)
    if (activeIcon) {
      activeIcon.style.display = "block"
    }
  }
  
  // Set up theme options in dropdown
  function setupThemeOptions() {
    const themeOptions = document.getElementById("themeOptions")
    if (!themeOptions) return
  
    themeOptions.innerHTML = "" // Clear existing options
  
    const currentTheme = localStorage.getItem("cssTheme") || "default"
  
    THEMES.forEach((theme) => {
      const button = document.createElement("button")
      button.className = "flex items-center w-full px-4 py-2 text-sm hover:bg-[hsl(var(--accent))] transition-colors"
      button.onclick = () => setCssTheme(theme.id)
  
      // Create color swatch
      const swatch = document.createElement("div")
      swatch.className = "w-4 h-4 mr-2 rounded-full border border-[hsl(var(--border))]"
      swatch.style.backgroundColor = theme.color
  
      button.appendChild(swatch)
      button.appendChild(document.createTextNode(theme.name))
  
      // Add checkmark for active theme
      if (currentTheme === theme.id) {
        const checkmark = document.createElement("span")
        checkmark.className = "ml-auto"
        checkmark.innerHTML = "✓"
        button.appendChild(checkmark)
      }
  
      themeOptions.appendChild(button)
    })
  }
  
  // Set up event listeners
  function setupEventListeners() {
    const themeToggle = document.getElementById("themeToggle")
    const themeDropdown = document.getElementById("themeDropdown")
  
    if (themeToggle && themeDropdown) {
      // Toggle dropdown when button is clicked
      themeToggle.addEventListener("click", (e) => {
        e.stopPropagation()
        themeDropdown.classList.toggle("hidden")
      })
  
      // Close dropdown when clicking outside
      document.addEventListener("click", (event) => {
        if (!themeDropdown.contains(event.target) && !themeToggle.contains(event.target)) {
          themeDropdown.classList.add("hidden")
        }
      })
  
      // Close dropdown on Escape key
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
          themeDropdown.classList.add("hidden")
        }
      })
    }
  }
  
  // Set color mode (light, dark, system)
  function setTheme(mode) {
    localStorage.setItem("colorMode", mode)
    applyColorMode(mode)
    updateThemeIcon(mode)
  
    // Hide dropdown after selection
    document.getElementById("themeDropdown").classList.add("hidden")
  }
  
  // Apply color mode
  function applyColorMode(mode) {
    if (mode === "system") {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches
      document.documentElement.classList.toggle("dark", prefersDark)
    } else {
      document.documentElement.classList.toggle("dark", mode === "dark")
    }
  }
  
  // Set CSS theme
  function setCssTheme(themeId) {
    localStorage.setItem("cssTheme", themeId)
    applyTheme(themeId)
  
    // Refresh theme options to show active theme
    setupThemeOptions()
  
    // Hide dropdown after selection
    document.getElementById("themeDropdown").classList.add("hidden")
  }
  
  // Apply theme
  function applyTheme(themeId) {
    // Remove all theme classes
    THEMES.forEach((theme) => {
      if (theme.id !== "default") {
        document.documentElement.classList.remove(`${theme.id}-theme`)
      }
    })
  
    // Add the new theme class if it's not default
    if (themeId !== "default") {
      document.documentElement.classList.add(`${themeId}-theme`)
    }
  
    // Update theme CSS link if using separate CSS files
    const themeLinkElement = document.getElementById("theme-css")
    if (themeLinkElement) {
      if (themeId === "default") {
        themeLinkElement.setAttribute("href", "")
      } else {
        themeLinkElement.setAttribute("href", `/static/css/${themeId}-theme.css`)
      }
    }
  }
  
  

document.addEventListener("DOMContentLoaded", () => {
    setupDropdownToggle()
  })
  
  /**
   * Set up the dropdown toggle functionality
   */
  function setupDropdownToggle() {
    const toggleButton = document.getElementById("themeToggle")
    const dropdown = document.getElementById("themeDropdown")
  
    if (!toggleButton || !dropdown) return
  
    // Toggle dropdown when button is clicked
    toggleButton.addEventListener("click", (e) => {
      e.stopPropagation()
      dropdown.classList.toggle("hidden")
    })
  
    // Close dropdown when clicking outside
    document.addEventListener("click", (event) => {
      if (!dropdown.contains(event.target) && !toggleButton.contains(event.target)) {
        dropdown.classList.add("hidden")
      }
    })
  
    // Close dropdown when pressing Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        dropdown.classList.add("hidden")
      }
    })
  }
  
  