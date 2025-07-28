// Global state
let currentProject = null;
let currentData = null;
let currentEditingItem = null;
let apiBaseUrl = 'http://0.0.0.0:8200';

// Test function to check if script is loaded
window.testFunction = function() {
    console.log('Test function works!');
    alert('Script is loaded and working!');
};

// Scan local project - defined early to ensure availability
window.scanLocalProject = async function() {
    console.log('scanLocalProject function called');
    
    const projectPathInput = document.getElementById('project-path-input');
    if (!projectPathInput) {
        alert('Project path input not found');
        return;
    }
    
    const projectPath = projectPathInput.value.trim();
    console.log('Project path:', projectPath);
    
    if (!projectPath) {
        alert('Please enter a project path');
        return;
    }
    
    console.log('Starting scan for:', projectPath);
    
    // Show scanning section
    const scanningSection = document.getElementById('scanning-section');
    if (scanningSection) {
        scanningSection.style.display = 'block';
    }
    
    try {
        console.log('Making API request to:', `${apiBaseUrl}/api/scan-local`);
        
        const response = await fetch(`${apiBaseUrl}/api/scan-local`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                project_path: projectPath
            })
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Response error:', errorText);
            throw new Error(`Scan failed: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Scan result:', data);
        
        // Store data globally
        window.currentData = data;
        
        // Hide project section and show results
        const projectSection = document.getElementById('project-section');
        if (projectSection) {
            projectSection.style.display = 'none';
        }
        
        // Try to show results
        if (window.showResults) {
            window.showResults();
        } else {
            console.log('showResults function not available yet');
            alert('Scan completed! Check console for results.');
        }
        
    } catch (error) {
        console.error('Local scan error:', error);
        alert(`Scan failed: ${error.message}`);
        
        const scanningSection = document.getElementById('scanning-section');
        if (scanningSection) {
            scanningSection.style.display = 'none';
        }
    }
};

// DOM elements - will be accessed when needed, not during script load
let uploadArea, fileInput, projectInfo, scanningSection, resultsSection, editorSection;

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing...');
    
    // Initialize DOM elements
    uploadArea = document.getElementById('upload-area');
    fileInput = document.getElementById('file-input');
    projectInfo = document.getElementById('project-info');
    scanningSection = document.getElementById('scanning-section');
    resultsSection = document.getElementById('results-section');
    editorSection = document.getElementById('editor-section');
    
    setupEventListeners();
    checkExistingReport();
});

// Setup event listeners
function setupEventListeners() {
    console.log('Setting up event listeners...');
    
    try {
        // JSON file upload
        const jsonFileInput = document.getElementById('json-file-input');
        if (jsonFileInput) {
            jsonFileInput.addEventListener('change', handleJSONFileSelection);
            console.log('✓ json-file-input event listener added');
        } else {
            console.log('✗ json-file-input not found');
        }
        
        // Python files upload
        const pythonFilesInput = document.getElementById('python-files-input');
        if (pythonFilesInput) {
            pythonFilesInput.addEventListener('change', handlePythonFilesSelection);
            console.log('✓ python-files-input event listener added');
        } else {
            console.log('✗ python-files-input not found');
        }
        
        // Drag and drop for JSON reports
        const jsonUploadArea = document.getElementById('json-upload-area');
        if (jsonUploadArea) {
            jsonUploadArea.addEventListener('dragover', handleDragOver);
            jsonUploadArea.addEventListener('dragleave', handleDragLeave);
            jsonUploadArea.addEventListener('drop', handleJSONDrop);
            console.log('✓ json-upload-area event listeners added');
        } else {
            console.log('✗ json-upload-area not found');
        }
        
        // Drag and drop for Python files
        const filesUploadArea = document.getElementById('files-upload-area');
        if (filesUploadArea) {
            filesUploadArea.addEventListener('dragover', handleDragOver);
            filesUploadArea.addEventListener('dragleave', handleDragLeave);
            filesUploadArea.addEventListener('drop', handlePythonFilesDrop);
            console.log('✓ files-upload-area event listeners added');
        } else {
            console.log('✗ files-upload-area not found');
        }
        
        // Filters (these might not exist initially)
        const typeFilter = document.getElementById('type-filter');
        const docFilter = document.getElementById('doc-filter');
        const docstringTextarea = document.getElementById('docstring-textarea');
        
        if (typeFilter) {
            typeFilter.addEventListener('change', applyFilters);
            console.log('✓ type-filter event listener added');
        } else {
            console.log('✗ type-filter not found (this is normal initially)');
        }
        
        if (docFilter) {
            docFilter.addEventListener('change', applyFilters);
            console.log('✓ doc-filter event listener added');
        } else {
            console.log('✗ doc-filter not found (this is normal initially)');
        }
        
        if (docstringTextarea) {
            docstringTextarea.addEventListener('input', updatePreview);
            console.log('✓ docstring-textarea event listener added');
        } else {
            console.log('✗ docstring-textarea not found (this is normal initially)');
        }
        
        console.log('Event listeners setup completed');
        
    } catch (error) {
        console.error('Error setting up event listeners:', error);
    }
}

// Check for existing report
async function checkExistingReport() {
    try {
        const response = await fetch(`${apiBaseUrl}/api/report/status`);
        if (response.ok) {
            const data = await response.json();
            if (data.exists) {
                loadExistingReport();
            }
        }
    } catch (error) {
        console.log('No existing report found');
    }
}

// Load existing report
async function loadExistingReport() {
    try {
        const response = await fetch(`${apiBaseUrl}/api/report/data`);
        if (response.ok) {
            const data = await response.json();
            currentData = data;
            showResults();
        }
    } catch (error) {
        console.error('Error loading existing report:', error);
    }
}

// Handle JSON file selection
function handleJSONFileSelection(event) {
    const file = event.target.files[0];
    if (file && file.type === 'application/json') {
        loadJSONReport(file);
    } else {
        alert('Please select a valid JSON file.');
    }
}

// Handle Python files selection
function handlePythonFilesSelection(event) {
    const files = Array.from(event.target.files);
    processPythonFiles(files);
}

// Handle JSON drag and drop
function handleJSONDrop(event) {
    event.preventDefault();
    document.getElementById('json-upload-area').classList.remove('drag-over');
    
    const files = Array.from(event.dataTransfer.files);
    const jsonFile = files.find(file => file.type === 'application/json' || file.name.endsWith('.json'));
    
    if (jsonFile) {
        loadJSONReport(jsonFile);
    } else {
        alert('Please drop a JSON report file.');
    }
}

// Handle Python files drag and drop
function handlePythonFilesDrop(event) {
    event.preventDefault();
    document.getElementById('files-upload-area').classList.remove('drag-over');
    
    const files = Array.from(event.dataTransfer.files);
    const pythonFiles = files.filter(file => file.name.endsWith('.py'));
    
    if (pythonFiles.length > 0) {
        processPythonFiles(pythonFiles);
    } else {
        alert('Please drop Python (.py) files.');
    }
}

// Handle drag over
function handleDragOver(event) {
    event.preventDefault();
    uploadArea.classList.add('drag-over');
}

// Handle drag leave
function handleDragLeave(event) {
    event.preventDefault();
    uploadArea.classList.remove('drag-over');
}

// Handle drop
function handleDrop(event) {
    event.preventDefault();
    uploadArea.classList.remove('drag-over');
    
    const files = Array.from(event.dataTransfer.files);
    processFiles(files);
}

// Load JSON report
async function loadJSONReport(file) {
    try {
        const text = await file.text();
        const data = JSON.parse(text);
        
        // Validate the data structure
        if (!Array.isArray(data)) {
            throw new Error('Invalid report format: expected an array of items');
        }
        
        // Transform data to expected format
        currentData = {
            items: data,
            total_files: new Set(data.map(item => item.file_path || item.module)).size,
            scan_time: 0
        };
        
        // Hide project section and show results
        document.getElementById('project-section').style.display = 'none';
        showResults();
        
    } catch (error) {
        console.error('Error loading JSON report:', error);
        alert(`Error loading report: ${error.message}`);
    }
}

// Scan local project
window.scanLocalProject = async function scanLocalProject() {
    console.log('scanLocalProject function called');
    
    const projectPath = document.getElementById('project-path-input').value.trim();
    console.log('Project path:', projectPath);
    
    if (!projectPath) {
        alert('Please enter a project path');
        return;
    }
    
    console.log('Starting scan for:', projectPath);
    
    // Show scanning section
    scanningSection.style.display = 'block';
    updateProgress(10, 'Starting scan...');
    
    try {
        console.log('Making API request to:', `${apiBaseUrl}/api/scan-local`);
        
        const response = await fetch(`${apiBaseUrl}/api/scan-local`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                project_path: projectPath
            })
        });
        
        console.log('Response status:', response.status);
        updateProgress(50, 'Processing files...');
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Response error:', errorText);
            throw new Error(`Scan failed: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Scan result:', data);
        currentData = data;
        
        updateProgress(100, 'Scan completed successfully');
        
        setTimeout(() => {
            document.getElementById('project-section').style.display = 'none';
            showResults();
        }, 1000);
        
    } catch (error) {
        console.error('Local scan error:', error);
        alert(`Scan failed: ${error.message}`);
        scanningSection.style.display = 'none';
    }
}

// Process Python files (for individual file upload)
function processPythonFiles(files) {
    if (files.length === 0) {
        alert('No Python files found.');
        return;
    }
    
    // Check for FastAPI indicators
    const fastApiDetected = checkForFastAPI(files);
    
    // Update UI
    document.getElementById('project-path').textContent = 'Uploaded Files';
    document.getElementById('file-count').textContent = files.length;
    document.getElementById('fastapi-status').textContent = fastApiDetected ? 'Yes' : 'No';
    
    // Store files
    currentProject = {
        path: 'uploaded_files',
        files: files,
        fastApiDetected: fastApiDetected
    };
    
    // Show project info
    projectInfo.style.display = 'block';
}

// Check for FastAPI indicators
function checkForFastAPI(files) {
    // This is a simplified check - in a real implementation,
    // you might want to read file contents
    return files.some(file => 
        file.name.includes('main') || 
        file.name.includes('app') || 
        file.name.includes('api')
    );
}

// Scan project
window.scanProject = async function scanProject() {
    if (!currentProject) {
        alert('Please select a project first.');
        return;
    }
    
    // Show scanning section
    scanningSection.style.display = 'block';
    document.getElementById('scan-btn').disabled = true;
    
    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('project_path', currentProject.path);
        
        // Add files with proper relative paths
        for (const file of currentProject.files) {
            // Use webkitRelativePath if available (for directory uploads)
            const fileName = file.webkitRelativePath || file.name;
            formData.append('files', file, fileName);
        }
        
        // Update progress during upload
        updateProgress(10, 'Uploading files...');
        
        // Start scanning
        const response = await fetch(`${apiBaseUrl}/api/scan`, {
            method: 'POST',
            body: formData
        });
        
        updateProgress(50, 'Processing files...');
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Scanning failed: ${errorText}`);
        }
        
        // Get scan results
        const data = await response.json();
        currentData = data;
        
        // Update progress to 100%
        updateProgress(100, 'Scan completed successfully');
        
        // Show results after a short delay
        setTimeout(() => {
            showResults();
        }, 1000);
        
    } catch (error) {
        console.error('Scanning error:', error);
        alert(`Scanning failed: ${error.message}. Please try again or check the console for details.`);
        scanningSection.style.display = 'none';
        document.getElementById('scan-btn').disabled = false;
    }
}

// Update progress
function updateProgress(percentage, currentFile = '') {
    document.getElementById('progress-fill').style.width = percentage + '%';
    document.getElementById('progress-percentage').textContent = percentage + '%';
    document.getElementById('current-file').textContent = currentFile;
}

// Show results
function showResults() {
    if (!currentData || !currentData.items) {
        console.error('No data to display');
        return;
    }
    
    // Hide other sections
    scanningSection.style.display = 'none';
    
    // Calculate stats
    const totalItems = currentData.items.length;
    const documentedItems = currentData.items.filter(item => 
        item.docstring && item.docstring.trim() !== ''
    ).length;
    const missingDocs = totalItems - documentedItems;
    const coveragePercent = totalItems > 0 ? Math.round((documentedItems / totalItems) * 100) : 0;
    
    // Update stats
    document.getElementById('total-items').textContent = totalItems;
    document.getElementById('documented-items').textContent = documentedItems;
    document.getElementById('missing-docs').textContent = missingDocs;
    document.getElementById('coverage-percent').textContent = coveragePercent + '%';
    
    // Populate table
    populateTable(currentData.items);
    
    // Show results section
    resultsSection.style.display = 'block';
    
    // Check Confluence status and show panel if enabled
    checkConfluenceStatus();
    
    // Show UML panel if data is available
    const umlPanel = document.getElementById('uml-panel');
    if (currentData && currentData.items && currentData.items.length > 0) {
        umlPanel.style.display = 'block';
    }
}

// Populate table
function populateTable(items) {
    const tbody = document.getElementById('docs-table-body');
    tbody.innerHTML = '';
    
    items.forEach((item, index) => {
        const row = document.createElement('tr');
        
        const hasDoc = item.docstring && item.docstring.trim() !== '';
        const coverage = item.coverage_score || 0;
        const quality = item.quality_score || 0;
        
        // Find the original index in currentData.items
        let originalIndex = index;
        if (currentData && currentData.items) {
            originalIndex = currentData.items.findIndex(originalItem => 
                originalItem.qualname === item.qualname && 
                originalItem.module === item.module && 
                originalItem.lineno === item.lineno
            );
        }
        
        row.innerHTML = `
            <td>${item.module || 'N/A'}</td>
            <td>${item.qualname || 'N/A'}</td>
            <td>${item.method || 'N/A'}</td>
            <td><span class="${hasDoc ? 'status-yes' : 'status-no'}">${hasDoc ? 'Yes' : 'No'}</span></td>
            <td>
                <div class="coverage-bar">
                    <div class="coverage-fill" style="width: ${coverage}%"></div>
                </div>
                ${coverage}%
            </td>
            <td>
                <div class="coverage-bar">
                    <div class="coverage-fill" style="width: ${quality}%"></div>
                </div>
                ${quality}%
            </td>
            <td>
                <button class="btn btn-primary" onclick="editItem(${originalIndex})">Edit</button>
                <button class="btn btn-secondary confluence-publish-btn" onclick="publishSingleItem(${originalIndex})" style="display: none; margin-left: 5px;" title="Publish to Confluence">
                    📄
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

// Apply filters
function applyFilters() {
    if (!currentData) return;
    
    const typeFilter = document.getElementById('type-filter').value;
    const docFilter = document.getElementById('doc-filter').value;
    
    let filteredItems = currentData.items;
    
    // Apply type filter
    if (typeFilter) {
        filteredItems = filteredItems.filter(item => item.method === typeFilter);
    }
    
    // Apply documentation filter
    if (docFilter === 'missing') {
        filteredItems = filteredItems.filter(item => !item.docstring || item.docstring.trim() === '');
    } else if (docFilter === 'documented') {
        filteredItems = filteredItems.filter(item => item.docstring && item.docstring.trim() !== '');
    }
    
    // Repopulate table
    populateTable(filteredItems);
}

// Edit item
window.editItem = function editItem(index) {
    if (!currentData || !currentData.items[index]) {
        alert('Item not found');
        return;
    }
    
    const item = currentData.items[index];
    currentEditingItem = { ...item, index };
    
    // Populate editor
    document.getElementById('editor-title').textContent = `Edit: ${item.qualname || 'Unknown'}`;
    document.getElementById('edit-module').textContent = item.module || 'N/A';
    document.getElementById('edit-name').textContent = item.qualname || 'N/A';
    document.getElementById('edit-type').textContent = item.method || 'N/A';
    document.getElementById('edit-file').textContent = item.file_path || 'N/A';
    document.getElementById('edit-line').textContent = item.lineno || 'N/A';
    
    // Show source preview
    document.getElementById('source-code').textContent = item.full_source || item.first_lines || 'Source not available';
    
    // Load current docstring
    document.getElementById('docstring-textarea').value = item.docstring || '';
    updatePreview();
    
    // Show editor
    editorSection.style.display = 'block';
    editorSection.scrollIntoView({ behavior: 'smooth' });
}

// Update preview
function updatePreview() {
    const docstring = document.getElementById('docstring-textarea').value;
    const preview = document.getElementById('docstring-preview');
    
    if (docstring.trim()) {
        // Create preview with proper formatting
        const lines = docstring.split('\n');
        const indentedLines = lines.map(line => line.trim() ? `    ${line}` : '');
        preview.textContent = `    """\n${indentedLines.join('\n')}\n    """`;
    } else {
        preview.textContent = '# No docstring';
    }
}

// Save docstring
window.saveDocstring = async function saveDocstring() {
    if (!currentEditingItem) {
        alert('No item selected for editing');
        return;
    }
    
    const docstring = document.getElementById('docstring-textarea').value;
    
    try {
        const response = await fetch(`${apiBaseUrl}/api/docstring/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                item: currentEditingItem,
                docstring: docstring
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            alert('Docstring saved successfully!');
            
            // Update current data
            currentData.items[currentEditingItem.index].docstring = docstring;
            
            // Refresh table
            populateTable(currentData.items);
            
            // Update stats
            showResults();
            
        } else {
            throw new Error('Failed to save docstring');
        }
    } catch (error) {
        console.error('Save error:', error);
        alert('Failed to save docstring. Please try again.');
    }
}

// Generate AI docstring
window.generateAI = async function generateAI() {
    if (!currentEditingItem) {
        alert('No item selected for editing');
        return;
    }
    
    // Check if OpenAI key is configured
    const openaiKey = localStorage.getItem('openai_key');
    if (!openaiKey) {
        showOpenAIModal();
        return;
    }
    
    const aiBtn = document.getElementById('ai-btn');
    const originalText = aiBtn.textContent;
    aiBtn.textContent = 'Generating...';
    aiBtn.disabled = true;
    
    try {
        const response = await fetch(`${apiBaseUrl}/api/docstring/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${openaiKey}`
            },
            body: JSON.stringify({
                item: currentEditingItem
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            document.getElementById('docstring-textarea').value = result.docstring;
            updatePreview();
        } else {
            throw new Error('Failed to generate docstring');
        }
    } catch (error) {
        console.error('AI generation error:', error);
        alert('Failed to generate docstring. Please check your API key and try again.');
    } finally {
        aiBtn.textContent = originalText;
        aiBtn.disabled = false;
    }
}

// Reset docstring
window.resetDocstring = function resetDocstring() {
    if (currentEditingItem) {
        document.getElementById('docstring-textarea').value = currentEditingItem.docstring || '';
        updatePreview();
    }
}

// Close editor  
window.closeEditor = function closeEditor() {
    editorSection.style.display = 'none';
    currentEditingItem = null;
}

// Show OpenAI modal
function showOpenAIModal() {
    document.getElementById('openai-modal').style.display = 'flex';
}

// Close modal
window.closeModal = function closeModal() {
    document.getElementById('openai-modal').style.display = 'none';
}

// Save OpenAI key
window.saveOpenAIKey = function saveOpenAIKey() {
    const key = document.getElementById('openai-key').value;
    if (key.trim()) {
        localStorage.setItem('openai_key', key.trim());
        closeModal();
        alert('OpenAI API key saved successfully!');
    } else {
        alert('Please enter a valid API key');
    }
}

// Confluence Integration Functions

// Check Confluence status
async function checkConfluenceStatus() {
    try {
        const response = await fetch(`${apiBaseUrl}/api/confluence/status`);
        if (response.ok) {
            const data = await response.json();
            updateConfluenceUI(data);
        }
    } catch (error) {
        console.log('Confluence status check failed:', error);
    }
}

// Update Confluence UI based on status
function updateConfluenceUI(status) {
    const panel = document.getElementById('confluence-panel');
    const statusElement = document.getElementById('confluence-status');
    const statusText = document.getElementById('confluence-status-text');
    const coverageBtn = document.getElementById('publish-coverage-btn');
    const endpointsBtn = document.getElementById('publish-endpoints-btn');
    const publishBtns = document.querySelectorAll('.confluence-publish-btn');
    
    if (status.enabled) {
        panel.style.display = 'block';
        statusElement.className = 'confluence-status enabled';
        statusText.textContent = `Connected to ${status.url} (Space: ${status.space_key})`;
        
        // Enable buttons
        coverageBtn.disabled = false;
        endpointsBtn.disabled = false;
        publishBtns.forEach(btn => btn.style.display = 'inline-block');
    } else {
        panel.style.display = 'block';
        statusElement.className = 'confluence-status disabled';
        statusText.textContent = 'Not configured. Set CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN, and CONFLUENCE_SPACE_KEY environment variables.';
        
        // Keep buttons disabled
        coverageBtn.disabled = true;
        endpointsBtn.disabled = true;
        publishBtns.forEach(btn => btn.style.display = 'none');
    }
}

// Publish coverage report to Confluence
window.publishCoverageReport = async function() {
    if (!currentData || !currentData.items) {
        alert('No data to publish');
        return;
    }
    
    const button = document.getElementById('publish-coverage-btn');
    const originalText = button.textContent;
    button.textContent = 'Publishing...';
    button.disabled = true;
    
    try {
        const response = await fetch(`${apiBaseUrl}/api/confluence/publish-coverage`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                items: currentData.items,
                title_suffix: new Date().toLocaleDateString()
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            alert(`Coverage report published successfully!\nPage URL: ${result.page_url}`);
        } else {
            const error = await response.text();
            throw new Error(error);
        }
    } catch (error) {
        console.error('Publish error:', error);
        alert(`Failed to publish coverage report: ${error.message}`);
    } finally {
        button.textContent = originalText;
        button.disabled = false;
    }
};

// Publish all endpoints to Confluence
window.publishAllEndpoints = async function() {
    if (!currentData || !currentData.items) {
        alert('No data to publish');
        return;
    }
    
    // Filter for endpoints only
    const endpoints = currentData.items.filter(item => 
        item.method && ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'].includes(item.method)
    );
    
    if (endpoints.length === 0) {
        alert('No endpoints found to publish');
        return;
    }
    
    const button = document.getElementById('publish-endpoints-btn');
    const originalText = button.textContent;
    button.disabled = true;
    
    let publishedCount = 0;
    let failedCount = 0;
    
    for (let i = 0; i < endpoints.length; i++) {
        const endpoint = endpoints[i];
        button.textContent = `Publishing ${i + 1}/${endpoints.length}...`;
        
        try {
            const response = await fetch(`${apiBaseUrl}/api/confluence/publish-endpoint`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(endpoint)
            });
            
            if (response.ok) {
                publishedCount++;
            } else {
                failedCount++;
                console.error(`Failed to publish ${endpoint.method} ${endpoint.path}`);
            }
        } catch (error) {
            failedCount++;
            console.error(`Error publishing ${endpoint.method} ${endpoint.path}:`, error);
        }
    }
    
    alert(`Endpoint publishing complete!\nPublished: ${publishedCount}\nFailed: ${failedCount}`);
    
    button.textContent = originalText;
    button.disabled = false;
};

// Publish single item to Confluence
window.publishSingleItem = async function(index) {
    if (!currentData || !currentData.items[index]) {
        alert('Item not found');
        return;
    }
    
    const item = currentData.items[index];
    
    // Check if it's an endpoint
    if (!item.method || !['GET', 'POST', 'PUT', 'DELETE', 'PATCH'].includes(item.method)) {
        alert('Only endpoints can be published to Confluence');
        return;
    }
    
    try {
        const response = await fetch(`${apiBaseUrl}/api/confluence/publish-endpoint`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(item)
        });
        
        if (response.ok) {
            const result = await response.json();
            alert(`Endpoint published successfully!\nPage URL: ${result.page_url}`);
        } else {
            const error = await response.text();
            throw new Error(error);
        }
    } catch (error) {
        console.error('Publish error:', error);
        alert(`Failed to publish endpoint: ${error.message}`);
    }
};

