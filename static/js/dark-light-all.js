/**
 * Advanced Theme Management System
 * Handles both color modes (light/dark) and theme variations (default, blue, rose, etc.)
 */

// Available themes configuration
const THEMES = [
    { id: 'default', name: 'Default', color: 'hsl(240 5.9% 10%)' },
    { id: 'blue', name: 'Blue', color: 'hsl(221.2 83.2% 53.3%)' },
    { id: 'rose', name: 'Rose', color: 'hsl(346.8 77.2% 49.8%)' },
    { id: 'indigo', name: 'Indigo', color: 'hsl(240 82% 50%)' },
    { id: 'amber', name: 'Amber', color: 'hsl(35.5 91.7% 32.9%)' },
    { id: 'purple', name: 'Purple', color: 'hsl(262.1 83.3% 57.8%)' },
    { id: 'teal', name: 'Teal', color: 'hsl(173 80% 40%)' },
    { id: 'green', name: 'Green', color: 'hsl(142.1 76.2% 36.3%)' }
];

// Initialize theme system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeThemeSystem();
    setupThemeDropdown();
    setupEventListeners();
});

/**
 * Initialize the theme system based on saved preferences
 */
function initializeThemeSystem() {
    const savedColorMode = localStorage.getItem('colorMode') || 'light'; // light, dark, system
    const savedTheme = localStorage.getItem('cssTheme') || 'default'; // default, blue, rose, etc.
    
    // Apply the saved theme and color mode
    applyTheme(savedTheme);
    applyColorMode(savedColorMode);
    
    // Update UI to reflect current settings
    updateThemeToggleUI(savedColorMode);
}

/**
 * Set up the theme dropdown with all available themes in light/dark variants
 */
function setupThemeDropdown() {
    const themeDropdown = document.getElementById('themeDropdown');
    if (!themeDropdown) return;
    
    // Clear existing content
    themeDropdown.innerHTML = '';
    
    // Add system preference option at the top
    const systemOption = document.createElement('button');
    systemOption.className = 'flex items-center w-full px-4 py-2 text-sm hover:bg-[hsl(var(--accent))] transition-colors';
    systemOption.onclick = () => setTheme('system');
    
    const systemIcon = document.createElement('div');
    systemIcon.innerHTML = `<svg class="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/>
        <path d="M7 8H17M7 12H17M7 16H13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    </svg>`;
    
    systemOption.appendChild(systemIcon.firstChild);
    systemOption.appendChild(document.createTextNode('System Preference'));
    
    // Add checkmark if system is active
    if (localStorage.getItem('colorMode') === 'system') {
        const checkmark = document.createElement('span');
        checkmark.className = 'ml-auto';
        checkmark.innerHTML = '✓';
        systemOption.appendChild(checkmark);
    }
    
    themeDropdown.appendChild(systemOption);
    
    // Add divider
    const divider = document.createElement('div');
    divider.className = 'border-t border-[hsl(var(--border))] my-1';
    themeDropdown.appendChild(divider);
    
    // Get current settings
    const currentTheme = localStorage.getItem('cssTheme') || 'default';
    const currentMode = localStorage.getItem('colorMode') || 'light';
    
    // Add each theme with light/dark options
    THEMES.forEach(theme => {
        // Theme header
        const themeHeader = document.createElement('h3');
        themeHeader.className = 'px-4 py-1 text-xs font-semibold text-[hsl(var(--muted-foreground))]';
        themeHeader.textContent = theme.name;
        themeDropdown.appendChild(themeHeader);
        
        // Light option
        const lightOption = createThemeOption(theme, 'light', currentTheme, currentMode);
        themeDropdown.appendChild(lightOption);
        
        // Dark option
        const darkOption = createThemeOption(theme, 'dark', currentTheme, currentMode);
        themeDropdown.appendChild(darkOption);
        
        // Add small divider except after the last theme
        if (theme.id !== THEMES[THEMES.length - 1].id) {
            const smallDivider = document.createElement('div');
            smallDivider.className = 'border-t border-[hsl(var(--border))/30] mx-4 my-1';
            themeDropdown.appendChild(smallDivider);
        }
    });
}

/**
 * Create a theme option button for the dropdown
 */
function createThemeOption(theme, mode, currentTheme, currentMode) {
    const option = document.createElement('button');
    option.className = 'flex items-center w-full px-4 py-2 text-sm hover:bg-[hsl(var(--accent))] transition-colors';
    
    // When clicked, set both theme and mode
    option.onclick = () => {
        setCssTheme(theme.id);
        setTheme(mode);
    };
    
    // Create color swatch with appropriate color
    const swatch = document.createElement('div');
    swatch.className = 'w-4 h-4 mr-2 rounded-full border border-[hsl(var(--border))]';
    swatch.style.backgroundColor = theme.color;
    
    // For dark mode, make the swatch darker
    if (mode === 'dark') {
        swatch.style.filter = 'brightness(0.7)';
    }
    
    // Add mode icon
    const modeIcon = document.createElement('div');
    if (mode === 'light') {
        modeIcon.innerHTML = `<svg class="w-3 h-3 mr-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="4" stroke="currentColor" stroke-width="2"/>
            <path d="M12 5V3M12 21V19M5 12H3M21 12H19M17.6569 17.6569L19.0711 19.0711M4.92893 4.92893L6.34315 6.34315M6.34315 17.6569L4.92893 19.0711M19.0711 4.92893L17.6569 6.34315" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>`;
    } else {
        modeIcon.innerHTML = `<svg class="w-3 h-3 mr-2" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21.9548 12.9564C20.5779 15.3717 17.9791 17.0001 15 17.0001C10.5817 17.0001 7 13.4184 7 9.00006C7 6.02097 8.62837 3.42216 11.0437 2.04529C5.96874 2.52861 2 6.79962 2 12.0001C2 17.5229 6.47715 22.0001 12 22.0001C17.2004 22.0001 21.4714 18.0313 21.9548 12.9564Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>`;
    }
    
    option.appendChild(swatch);
    option.appendChild(modeIcon.firstChild);
    option.appendChild(document.createTextNode(`${theme.name} ${mode.charAt(0).toUpperCase() + mode.slice(1)}`));
    
    // Add checkmark if this is the active theme and mode
    if (currentTheme === theme.id && currentMode === mode) {
        const checkmark = document.createElement('span');
        checkmark.className = 'ml-auto';
        checkmark.innerHTML = '✓';
        option.appendChild(checkmark);
    }
    
    return option;
}

/**
 * Set up event listeners for theme controls
 */
function setupEventListeners() {
    // Theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const dropdown = document.getElementById('themeDropdown');
            dropdown.classList.toggle('hidden');
        });
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        const dropdown = document.getElementById('themeDropdown');
        const toggle = document.getElementById('themeToggle');
        
        if (dropdown && !dropdown.classList.contains('hidden') && 
            !dropdown.contains(event.target) && 
            !toggle.contains(event.target)) {
            dropdown.classList.add('hidden');
        }
    });
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        if (localStorage.getItem('colorMode') === 'system') {
            applySystemColorMode();
        }
    });
}

/**
 * Set the CSS theme (default, blue, rose, etc.)
 */
function setCssTheme(themeId) {
    localStorage.setItem('cssTheme', themeId);
    applyTheme(themeId);
    
    // Reapply color mode to ensure proper combination
    const currentColorMode = localStorage.getItem('colorMode') || 'light';
    applyColorMode(currentColorMode);
}

/**
 * Apply the specified theme
 */
function applyTheme(themeId) {
    // Remove all theme classes
    THEMES.forEach(theme => {
        if (theme.id !== 'default') {
            document.documentElement.classList.remove(`${theme.id}-theme`);
        }
    });
    
    // Add the new theme class if it's not default
    if (themeId !== 'default') {
        document.documentElement.classList.add(`${themeId}-theme`);
    }
    
    // Update theme CSS link if using separate CSS files
    updateThemeCssLink(themeId);
}

/**
 * Set the color mode (light, dark, system)
 */
function setTheme(mode) {
    localStorage.setItem('colorMode', mode);
    applyColorMode(mode);
    updateThemeToggleUI(mode);
    
    // Refresh the dropdown to show the active theme
    setupThemeDropdown();
    
    // Hide dropdown after selection
    const dropdown = document.getElementById('themeDropdown');
    if (dropdown) {
        dropdown.classList.add('hidden');
    }
}

/**
 * Apply the specified color mode
 */
function applyColorMode(mode) {
    if (mode === 'system') {
        applySystemColorMode();
    } else {
        document.documentElement.classList.toggle('dark', mode === 'dark');
    }
}

/**
 * Apply system color mode preference
 */
function applySystemColorMode() {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.classList.toggle('dark', prefersDark);
}

/**
 * Update the theme toggle UI to show the active color mode
 */
function updateThemeToggleUI(mode) {
    // Hide all theme icons
    document.querySelectorAll('.theme-light, .theme-dark, .theme-system').forEach(icon => {
        icon.style.display = 'none';
    });
    
    // Show active icon
    const activeIcon = document.querySelector(`.theme-${mode}`);
    if (activeIcon) {
        activeIcon.style.display = 'block';
    }
}

/**
 * Update the theme CSS link if using separate CSS files
 * This is optional - only needed if you're loading theme CSS files dynamically
 */
function updateThemeCssLink(themeId) {
    const themeLinkElement = document.getElementById('theme-css');
    if (!themeLinkElement) return;
    
    if (themeId === 'default') {
        themeLinkElement.setAttribute('href', '');
    } else {
        // Adjust the path to match your CSS file structure
        const cssPath = `/static/css/${themeId}-theme.css`;
        themeLinkElement.setAttribute('href', cssPath);
    }
}