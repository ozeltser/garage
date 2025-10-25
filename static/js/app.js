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

// Global variable to track the current door status and polling
let currentDoorStatus = null;
let doorStatusInterval = null;

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
                const newStatus = data.status;
                const previousStatus = currentDoorStatus;
                
                // Remove existing status classes
                statusIndicator.classList.remove('closed', 'open');
                
                // Update based on door status
                if (newStatus === 'closed') {
                    statusIndicator.classList.add('closed');
                    statusIcon.textContent = '🏠';
                    statusText.textContent = 'CLOSED';
                } else if (newStatus === 'open') {
                    statusIndicator.classList.add('open');
                    statusIcon.textContent = '🚪';
                    statusText.textContent = 'OPEN';
                } else {
                    // Unknown status
                    statusIndicator.classList.add('closed');
                    statusIcon.textContent = '❓';
                    statusText.textContent = 'UNKNOWN';
                }
                
                // Check if status changed and trigger event
                if (previousStatus !== null && previousStatus !== newStatus) {
                    onDoorStatusChanged(previousStatus, newStatus);
                }
                
                // Update current status
                currentDoorStatus = newStatus;
            }
        }
    })
    .catch(error => {
        console.error('Error fetching door status:', error);
    });
}

// Function to handle door status changes
// This provides extensibility for future actions when door status changes
function onDoorStatusChanged(oldStatus, newStatus) {
    console.log(`Door status changed from ${oldStatus} to ${newStatus}`);
    
    // Future actions can be added here, such as:
    // - Sending notifications
    // - Logging to a server
    // - Triggering other UI updates
    // - Playing sounds
    // etc.
    
    // Dispatch custom event for other parts of the application
    const event = new CustomEvent('doorStatusChanged', {
        detail: {
            oldStatus: oldStatus,
            newStatus: newStatus,
            timestamp: new Date()
        }
    });
    document.dispatchEvent(event);
}

// Function to start automatic door status polling
function startDoorStatusPolling(intervalSeconds) {
    // Clear any existing interval
    if (doorStatusInterval) {
        clearInterval(doorStatusInterval);
    }
    
    // Convert seconds to milliseconds
    const intervalMs = intervalSeconds * 1000;
    
    // Set up periodic polling
    doorStatusInterval = setInterval(updateDoorStatus, intervalMs);
    
    console.log(`Door status polling started with ${intervalSeconds} second interval`);
}

// Function to stop automatic door status polling
function stopDoorStatusPolling() {
    if (doorStatusInterval) {
        clearInterval(doorStatusInterval);
        doorStatusInterval = null;
        console.log('Door status polling stopped');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Setup theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Update door status on page load
    updateDoorStatus();
    
    // Start automatic door status polling if refresh interval is set
    const refreshInterval = document.getElementById('doorRefreshInterval');
    if (refreshInterval && refreshInterval.value) {
        const intervalSeconds = parseInt(refreshInterval.value, 10);
        if (!isNaN(intervalSeconds) && intervalSeconds > 0) {
            startDoorStatusPolling(intervalSeconds);
        }
    }
    
    // Add click handler to garage status box for manual refresh
    const garageStatus = document.getElementById('garageStatus');
    if (garageStatus) {
        garageStatus.addEventListener('click', function() {
            updateDoorStatus();
        });
    }
    
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