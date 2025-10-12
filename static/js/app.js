// JavaScript for the Garage App

// Theme management
function initTheme() {
    const storedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Default to 'auto' if no preference is stored
    const currentTheme = storedTheme || 'auto';
    
    // Apply theme based on current setting
    if (currentTheme === 'auto') {
        document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    } else {
        document.documentElement.setAttribute('data-theme', currentTheme);
    }
    
    // Update button icon
    updateThemeIcon(currentTheme);
    
    // Listen for OS theme changes when in auto mode
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (localStorage.getItem('theme') === 'auto' || !localStorage.getItem('theme')) {
            document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
        }
    });
}

function updateThemeIcon(theme) {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;
    
    // Icons for each mode: auto (circle-half), light (sun), dark (moon)
    const icons = {
        'auto': '◐',  // Half circle for auto mode
        'light': '☀',  // Sun for light mode
        'dark': '☾'    // Moon for dark mode
    };
    
    themeToggle.innerHTML = icons[theme] || icons['auto'];
    themeToggle.setAttribute('aria-label', `Current theme: ${theme}. Click to cycle.`);
}

function toggleTheme() {
    const currentTheme = localStorage.getItem('theme') || 'auto';
    const themes = ['auto', 'light', 'dark'];
    const currentIndex = themes.indexOf(currentTheme);
    const nextTheme = themes[(currentIndex + 1) % themes.length];
    
    localStorage.setItem('theme', nextTheme);
    
    // Apply the new theme
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (nextTheme === 'auto') {
        document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    } else {
        document.documentElement.setAttribute('data-theme', nextTheme);
    }
    
    updateThemeIcon(nextTheme);
}

// Initialize theme before DOMContentLoaded to prevent flash
initTheme();

// Function to update door status display
function updateDoorStatus() {
    fetch('/door_status', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const statusIndicator = document.querySelector('.status-indicator');
            const statusIcon = document.querySelector('.status-icon');
            const statusText = document.querySelector('.status-text');
            
            if (statusIndicator && statusIcon && statusText) {
                // Remove existing status classes
                statusIndicator.classList.remove('closed', 'open');
                
                // Update based on door status
                if (data.status === 'closed') {
                    statusIndicator.classList.add('closed');
                    statusIcon.textContent = '🏠';
                    statusText.textContent = 'CLOSED';
                } else if (data.status === 'open') {
                    statusIndicator.classList.add('open');
                    statusIcon.textContent = '🚪';
                    statusText.textContent = 'OPEN';
                } else {
                    // Unknown status
                    statusIndicator.classList.add('closed');
                    statusIcon.textContent = '❓';
                    statusText.textContent = 'UNKNOWN';
                }
            }
        }
    })
    .catch(error => {
        console.error('Error fetching door status:', error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Setup theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Update door status on page load
    updateDoorStatus();
    
    const runScriptBtn = document.getElementById('runScriptBtn');
    const btnText = document.getElementById('btnText');
    const initialBtnText = btnText.textContent;
    const btnSpinner = document.getElementById('btnSpinner');
    const outputContainer = document.getElementById('outputContainer');
    const scriptOutput = document.getElementById('scriptOutput');
    const errorContainer = document.getElementById('errorContainer');
    const scriptError = document.getElementById('scriptError');

    if (runScriptBtn) {
        runScriptBtn.addEventListener('click', function() {
            // Show loading state
            btnText.textContent = 'Running...';
            btnSpinner.classList.remove('d-none');
            runScriptBtn.disabled = true;
            
            // Hide previous results
            outputContainer.classList.add('d-none');
            errorContainer.classList.add('d-none');

            // Make AJAX request to run the script
            fetch('/run_script', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                // Reset button state
                btnText.textContent = initialBtnText;
                btnSpinner.classList.add('d-none');
                runScriptBtn.disabled = false;

                if (data.success) {
                    // Show output
                    scriptOutput.textContent = data.output || 'Script executed successfully (no output)';
                    outputContainer.classList.remove('d-none');
                    
                    // Update door status after running the script
                    setTimeout(updateDoorStatus, 1000);
                    
                    // Also show errors if any (non-fatal)
                    if (data.error && data.error.trim()) {
                        scriptError.textContent = 'Warnings/Info:\n' + data.error;
                        errorContainer.classList.remove('d-none');
                    }
                } else {
                    // Show error
                    scriptError.textContent = 'Error: ' + (data.error || 'Unknown error occurred');
                    errorContainer.classList.remove('d-none');
                }
            })
            .catch(error => {
                // Reset button state
                btnText.textContent = initialBtnText;
                btnSpinner.classList.add('d-none');
                runScriptBtn.disabled = false;

                // Show error
                scriptError.textContent = 'Network error: ' + error.message;
                errorContainer.classList.remove('d-none');
            });
        });
    }

    // Add some mobile-friendly enhancements
    if (window.innerWidth <= 576) {
        // Add touch feedback for mobile devices
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            button.addEventListener('touchstart', function() {
                this.style.transform = 'scale(0.98)';
            });
            
            button.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.style.transform = '';
                }, 100);
            });
        });
    }
});