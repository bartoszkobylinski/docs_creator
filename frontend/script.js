// Main page JavaScript - Simple interface before scanning
const apiBaseUrl = 'http://0.0.0.0:8200';

// Scan project function
async function scanProject() {
    const projectPath = document.getElementById('project-path').value.trim();
    const statusDiv = document.getElementById('scan-status');
    
    if (!projectPath) {
        statusDiv.innerHTML = '<div class="status-message error">❌ Please enter a project path</div>';
        return;
    }
    
    try {
        statusDiv.innerHTML = '<div class="loading-spinner" style="width: 20px; height: 20px; margin: 0 auto;"></div>';
        
        const response = await fetch(`${apiBaseUrl}/api/scan-local`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_path: projectPath })
        });
        
        if (response.ok) {
            const result = await response.json();
            statusDiv.innerHTML = '<div class="status-message success">✅ Project scanned successfully! Redirecting to dashboard...</div>';
            
            // Redirect to dashboard after successful scan
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
        } else {
            const error = await response.text();
            throw new Error(error);
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="status-message error">❌ Scan failed: ${error.message}</div>`;
    }
}

// File drop functionality
function setupFileHandling() {
    const jsonDropZone = document.getElementById('json-drop-zone');
    const jsonFileInput = document.getElementById('json-file-input');
    
    if (jsonDropZone && jsonFileInput) {
        jsonDropZone.addEventListener('click', () => jsonFileInput.click());
        
        jsonDropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            jsonDropZone.style.borderColor = 'var(--color-primary)';
            jsonDropZone.style.background = 'var(--color-gray-50)';
        });
        
        jsonDropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            jsonDropZone.style.borderColor = 'var(--color-gray-300)';
            jsonDropZone.style.background = 'transparent';
        });
        
        jsonDropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            jsonDropZone.style.borderColor = 'var(--color-gray-300)';
            jsonDropZone.style.background = 'transparent';
            
            const files = Array.from(e.dataTransfer.files);
            const jsonFile = files.find(file => file.type === 'application/json' || file.name.endsWith('.json'));
            
            if (jsonFile) {
                loadJSONReport(jsonFile);
            } else {
                showNotification('Please drop a JSON report file.', 'error');
            }
        });
        
        jsonFileInput.addEventListener('change', (e) => {
            if (e.target.files[0]) {
                loadJSONReport(e.target.files[0]);
            }
        });
    }
}

// Load JSON report
async function loadJSONReport(file) {
    try {
        const text = await file.text();
        const data = JSON.parse(text);
        
        if (!Array.isArray(data)) {
            throw new Error('Invalid report format: expected an array of items');
        }
        
        showNotification('Report loaded successfully! Redirecting to dashboard...', 'success');
        
        // Redirect to dashboard after loading report
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 1500);
        
    } catch (error) {
        showNotification(`Error loading report: ${error.message}`, 'error');
    }
}

// Confluence settings
async function saveConfluenceSettings() {
    const url = document.getElementById('confluence-url').value.trim();
    const username = document.getElementById('confluence-username').value.trim();
    const token = document.getElementById('confluence-token').value.trim();
    const space = document.getElementById('confluence-space').value.trim();
    const statusDiv = document.getElementById('confluence-status');
    
    if (!url || !username || !token || !space) {
        statusDiv.innerHTML = '<div class="status-message error">❌ Please fill in all fields</div>';
        return;
    }
    
    try {
        statusDiv.innerHTML = '<div class="loading-spinner" style="width: 20px; height: 20px; margin: 0 auto;"></div>';
        
        const response = await fetch(`${apiBaseUrl}/api/confluence/save-settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: url,
                username: username,
                token: token,
                space_key: space
            })
        });
        
        if (response.ok) {
            statusDiv.innerHTML = '<div class="status-message success">✅ Confluence settings saved successfully!</div>';
            // Clear token for security
            document.getElementById('confluence-token').value = '';
        } else {
            throw new Error('Failed to save settings');
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="status-message error">❌ ${error.message}</div>`;
    }
}

// OpenAI settings
function saveOpenAIKey() {
    const key = document.getElementById('openai-key').value.trim();
    const statusDiv = document.getElementById('openai-status');
    
    if (key) {
        localStorage.setItem('openai_key', key);
        statusDiv.innerHTML = '<div class="status-message success">✅ OpenAI API key saved!</div>';
        document.getElementById('openai-key').value = '';
    } else {
        statusDiv.innerHTML = '<div class="status-message error">❌ Please enter a valid API key</div>';
    }
}

// Utility function for notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 500;
        z-index: 1000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    // Style based on type
    switch (type) {
        case 'success':
            notification.style.background = '#dcfce7';
            notification.style.color = '#166534';
            notification.style.border = '1px solid #bbf7d0';
            break;
        case 'error':
            notification.style.background = '#fef2f2';
            notification.style.color = '#991b1b';
            notification.style.border = '1px solid #fecaca';
            break;
        default:
            notification.style.background = '#f0f9ff';
            notification.style.color = '#0c4a6e';
            notification.style.border = '1px solid #bae6fd';
    }
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 4 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 4000);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    setupFileHandling();
});