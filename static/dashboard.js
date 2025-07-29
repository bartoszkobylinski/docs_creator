// Modern Documentation Dashboard - Complete with all features
const apiBaseUrl = 'http://0.0.0.0:8200';
let globalData = [];

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    checkExistingReport();
    setupEventListeners();
});

// Check for existing report data and show appropriate state
async function checkExistingReport() {
    try {
        const response = await fetch(`${apiBaseUrl}/api/current-data`);
        if (response.ok) {
            const data = await response.json();
            if (data && data.length > 0) {
                globalData = data;
                showDashboard();
                updateStats();
                populateTable();
            } else {
                showEmptyState();
            }
        } else {
            showEmptyState();
        }
    } catch (error) {
        console.log('No existing data found');
        showEmptyState();
    }
}

// State management functions
function showDashboard() {
    document.getElementById('empty-state').style.display = 'none';
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('main-dashboard').style.display = 'grid';
    updateDataStatus('active', 'Data Loaded');
}

function showEmptyState() {
    document.getElementById('empty-state').style.display = 'flex';
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('main-dashboard').style.display = 'none';
    updateDataStatus('inactive', 'No Data');
}

function showLoadingState(message = 'Processing...') {
    document.getElementById('empty-state').style.display = 'none';
    document.getElementById('loading-state').style.display = 'flex';
    document.getElementById('main-dashboard').style.display = 'none';
    document.getElementById('loading-message').textContent = message;
}

function updateDataStatus(status, text) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    if (status === 'active') {
        statusDot.classList.add('active');
    } else {
        statusDot.classList.remove('active');
    }
    statusText.textContent = text;
}

// Setup event listeners
function setupEventListeners() {
    // File drop functionality
    setupFileHandling();
    
    // Modal close handlers
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modalId = e.target.closest('.modal').id;
            closeModal(modalId);
        });
    });
    
    // Modal background click to close
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(modal.id);
            }
        });
    });
    
    // Table filters
    const typeFilter = document.getElementById('type-filter');
    const docFilter = document.getElementById('doc-filter');
    
    if (typeFilter) typeFilter.addEventListener('change', filterTable);
    if (docFilter) docFilter.addEventListener('change', filterTable);
}

// Scan local project from dashboard
async function scanLocalProject() {
    const projectPath = document.getElementById('project-path-input').value.trim();
    
    if (!projectPath) {
        showNotification('Please enter a project path', 'error');
        return;
    }
    
    try {
        showLoadingState('Scanning project files...');
        
        const response = await fetch(`${apiBaseUrl}/api/scan-local`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_path: projectPath })
        });
        
        if (response.ok) {
            const result = await response.json();
            globalData = result.items || result;
            showDashboard();
            updateStats();
            populateTable();
            showNotification('Project scanned successfully!', 'success');
        } else {
            throw new Error('Scan failed');
        }
    } catch (error) {
        showEmptyState();
        showNotification(`Scan failed: ${error.message}`, 'error');
    }
}

// File handling functions
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

async function loadJSONReport(file) {
    try {
        showLoadingState('Loading report...');
        
        const text = await file.text();
        const data = JSON.parse(text);
        
        if (!Array.isArray(data)) {
            throw new Error('Invalid report format: expected an array of items');
        }
        
        globalData = data;
        showDashboard();
        updateStats();
        populateTable();
        showNotification('Report loaded successfully!', 'success');
        
    } catch (error) {
        showEmptyState();
        showNotification(`Error loading report: ${error.message}`, 'error');
    }
}

// Statistics and table functions
function updateStats() {
    const totalItems = globalData.length;
    const documentedItems = globalData.filter(item => item.has_docstring).length;
    const coverage = totalItems > 0 ? Math.round((documentedItems / totalItems) * 100) : 0;
    const missingDocs = totalItems - documentedItems;
    
    document.getElementById('total-items').textContent = totalItems;
    document.getElementById('documented-items').textContent = documentedItems;
    document.getElementById('coverage-percent').textContent = `${coverage}%`;
    document.getElementById('missing-docs').textContent = missingDocs;
    
    // Update coverage bar
    const coverageBar = document.getElementById('coverage-bar');
    if (coverageBar) {
        coverageBar.style.width = `${coverage}%`;
    }
}

function populateTable() {
    const tbody = document.getElementById('docs-table-body');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    globalData.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.module || 'N/A'}</td>
            <td><code>${item.name}</code></td>
            <td><span class="badge">${item.type}</span></td>
            <td>
                <span class="status-badge ${item.has_docstring ? 'success' : 'error'}">
                    ${item.has_docstring ? '✓' : '✗'}
                </span>
            </td>
            <td>
                <div class="mini-progress">
                    <div class="mini-progress-fill" style="width: ${item.has_docstring ? 100 : 0}%"></div>
                </div>
                ${item.has_docstring ? '100%' : '0%'}
            </td>
            <td>
                <span class="badge">${item.has_docstring ? 'Good' : 'Missing'}</span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline" onclick="editDocumentation('${item.name}', '${item.type}')">
                    Edit
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function filterTable() {
    const typeFilter = document.getElementById('type-filter').value;
    const docFilter = document.getElementById('doc-filter').value;
    const rows = document.querySelectorAll('#docs-table-body tr');
    
    rows.forEach(row => {
        const type = row.querySelector('.badge').textContent.trim();
        const isDocumented = row.querySelector('.status-badge').classList.contains('success');
        
        let showRow = true;
        
        if (typeFilter && type !== typeFilter) {
            showRow = false;
        }
        
        if (docFilter === 'missing' && isDocumented) {
            showRow = false;
        } else if (docFilter === 'documented' && !isDocumented) {
            showRow = false;
        }
        
        row.style.display = showRow ? '' : 'none';
    });
}

// Documentation generation functions
function generateUMLDashboard() {
    openModal('uml-modal');
}

function generateLatexDashboard() {
    openModal('latex-modal');
}

function generateMarkdownDashboard() {
    openModal('markdown-modal');
}

function openConfluenceDashboard() {
    openModal('confluence-modal');
}

async function generateUMLType(type) {
    try {
        const response = await fetch(`${apiBaseUrl}/api/docs/uml/generate?diagram_type=${type}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `uml_${type}_diagram.png`;
            a.click();
            window.URL.revokeObjectURL(url);
            
            closeModal('uml-modal');
            showNotification('UML diagram generated successfully!', 'success');
        } else {
            throw new Error('Failed to generate UML');
        }
    } catch (error) {
        showNotification(`UML generation failed: ${error.message}`, 'error');
    }
}

async function generatePDF() {
    const projectName = document.getElementById('pdf-project-name').value.trim() || 'API_Documentation';
    const includeUML = document.getElementById('include-uml-pdf').checked;
    const statusDiv = document.getElementById('pdf-status');
    
    try {
        statusDiv.innerHTML = '<div class="loading-spinner"></div>';
        
        const response = await fetch(`${apiBaseUrl}/api/docs/latex/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_name: projectName,
                include_uml: includeUML
            })
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${projectName.replace(/[^a-zA-Z0-9]/g, '_')}_documentation.pdf`;
            a.click();
            window.URL.revokeObjectURL(url);
            
            statusDiv.innerHTML = '<div class="status-message success">✅ PDF generated successfully!</div>';
            setTimeout(() => closeModal('latex-modal'), 2000);
        } else {
            throw new Error('Failed to generate PDF');
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="status-message error">❌ ${error.message}</div>`;
    }
}

async function generateMarkdown() {
    const projectName = document.getElementById('markdown-project-name').value.trim() || 'API_Documentation';
    const includeUML = document.getElementById('include-uml-markdown').checked;
    const publishConfluence = document.getElementById('publish-confluence').checked;
    const statusDiv = document.getElementById('markdown-status');
    
    try {
        statusDiv.innerHTML = '<div class="loading-spinner"></div>';
        
        const response = await fetch(`${apiBaseUrl}/api/docs/markdown/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_name: projectName,
                include_uml: includeUML,
                publish_to_confluence: publishConfluence
            })
        });
        
        if (response.ok) {
            let successMessage = '✅ Markdown generated successfully!';
            
            // Download link
            const downloadUrl = `${apiBaseUrl}/api/docs/markdown/download?project_name=${encodeURIComponent(projectName)}`;
            successMessage += ` <a href="${downloadUrl}" class="btn btn-sm btn-primary" style="margin-left: 10px;">Download ZIP</a>`;
            
            if (publishConfluence) {
                successMessage += '<br>📄 Published to Confluence successfully!';
            }
            
            statusDiv.innerHTML = `<div class="status-message success">${successMessage}</div>`;
            
            // Auto-scroll to see the download link
            setTimeout(() => {
                statusDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }, 100);
            
        } else {
            throw new Error('Failed to generate Markdown');
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="status-message error">❌ ${error.message}</div>`;
    }
}

async function saveConfluenceSettings() {
    const url = document.getElementById('confluence-url').value.trim();
    const username = document.getElementById('confluence-username').value.trim();
    const token = document.getElementById('confluence-token').value.trim();
    const space = document.getElementById('confluence-space').value.trim();
    const statusDiv = document.getElementById('confluence-settings-status');
    
    if (!url || !username || !token || !space) {
        statusDiv.innerHTML = '<div class="status-message error">❌ Please fill in all fields</div>';
        return;
    }
    
    try {
        statusDiv.innerHTML = '<div class="loading-spinner"></div>';
        
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
            document.getElementById('confluence-token').value = '';
        } else {
            throw new Error('Failed to save settings');
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="status-message error">❌ ${error.message}</div>`;
    }
}

async function publishToConfluence() {
    const projectName = document.getElementById('confluence-project-name').value.trim() || 'API_Documentation';
    const includeUML = document.getElementById('confluence-include-uml').checked;
    const statusDiv = document.getElementById('confluence-publish-status');
    
    try {
        statusDiv.innerHTML = '<div class="loading-spinner"></div>';
        
        const response = await fetch(`${apiBaseUrl}/api/docs/markdown/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_name: projectName,
                include_uml: includeUML,
                publish_to_confluence: true
            })
        });
        
        if (response.ok) {
            statusDiv.innerHTML = '<div class="status-message success">✅ Published to Confluence successfully!</div>';
        } else {
            throw new Error('Failed to publish to Confluence');
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="status-message error">❌ ${error.message}</div>`;
    }
}

// Modal functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
        setTimeout(() => modal.classList.add('show'), 10);
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => modal.style.display = 'none', 200);
    }
}

// Editor functions
function editDocumentation(name, type) {
    const item = globalData.find(i => i.name === name && i.type === type);
    if (item) {
        openEditor(item);
    }
}

function openEditor(item) {
    const panel = document.getElementById('editor-panel');
    if (panel) {
        document.getElementById('edit-module').textContent = item.module || 'N/A';
        document.getElementById('edit-name').textContent = item.name;
        document.getElementById('edit-type').textContent = item.type;
        document.getElementById('edit-file').textContent = item.file_path || 'N/A';
        document.getElementById('source-code').textContent = item.source_code || 'Source code not available';
        document.getElementById('docstring-textarea').value = item.docstring || '';
        
        panel.classList.add('show');
        panel.style.display = 'block';
    }
}

function closeEditor() {
    const panel = document.getElementById('editor-panel');
    if (panel) {
        panel.classList.remove('show');
        setTimeout(() => panel.style.display = 'none', 300);
    }
}

function refreshData() {
    checkExistingReport();
}

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = message; // Use innerHTML to support HTML content like download links
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
        max-width: 400px;
    `;
    
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
    
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 5000);
}