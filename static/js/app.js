// JavaScript for the Garage App

document.addEventListener('DOMContentLoaded', function() {
    const runScriptBtn = document.getElementById('runScriptBtn');
    const btnText = document.getElementById('btnText');
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
                btnText.textContent = 'Run Python Script';
                btnSpinner.classList.add('d-none');
                runScriptBtn.disabled = false;

                if (data.success) {
                    // Show output
                    scriptOutput.textContent = data.output || 'Script executed successfully (no output)';
                    outputContainer.classList.remove('d-none');
                    
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
                btnText.textContent = 'Run Python Script';
                btnSpinner.classList.add('d-none');
                runScriptBtn.disabled = false;

                // Show error
                scriptError.textContent = 'Network error: ' + error.message;
                errorContainer.classList.remove('d-none');
            });
        });
    }

    // Database status functionality (admin only)
    const refreshDbStatusBtn = document.getElementById('refreshDbStatus');
    const dbStatusInfo = document.getElementById('dbStatusInfo');
    
    if (refreshDbStatusBtn) {
        refreshDbStatusBtn.addEventListener('click', function() {
            refreshDbStatusBtn.disabled = true;
            refreshDbStatusBtn.textContent = 'Loading...';
            
            fetch('/db_status')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    dbStatusInfo.innerHTML = `<span class="text-danger">Error: ${data.error}</span>`;
                } else {
                    dbStatusInfo.innerHTML = `
                        <div class="row">
                            <div class="col-sm-6"><strong>Pool Name:</strong> ${data.pool_name || 'N/A'}</div>
                            <div class="col-sm-6"><strong>Pool Size:</strong> ${data.pool_size || 'N/A'}</div>
                            <div class="col-sm-6"><strong>Connections in Use:</strong> ${data.connections_in_use || 'N/A'}</div>
                            <div class="col-sm-6"><strong>Total Connections:</strong> ${data.total_connections || 'N/A'}</div>
                        </div>
                    `;
                }
            })
            .catch(error => {
                dbStatusInfo.innerHTML = `<span class="text-danger">Network error: ${error.message}</span>`;
            })
            .finally(() => {
                refreshDbStatusBtn.disabled = false;
                refreshDbStatusBtn.textContent = 'Refresh DB Status';
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