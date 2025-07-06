// Global state
let currentProject = null;
let currentData = null;
let currentEditingItem = null;
let apiBaseUrl = 'http://localhost:8200';

// DOM elements
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const projectInfo = document.getElementById('project-info');
const scanningSection = document.getElementById('scanning-section');
const resultsSection = document.getElementById('results-section');
const editorSection = document.getElementById('editor-section');

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    checkExistingReport();
});

// Setup event listeners
function setupEventListeners() {
    // File input change
    fileInput.addEventListener('change', handleFileSelection);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    // Filters
    document.getElementById('type-filter').addEventListener('change', applyFilters);
    document.getElementById('doc-filter').addEventListener('change', applyFilters);
    
    // Docstring textarea
    document.getElementById('docstring-textarea').addEventListener('input', updatePreview);
}

// Check for existing report
async function checkExistingReport() {
    try {
        const response = await fetch(`${apiBaseUrl}/report/status`);
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
        const response = await fetch(`${apiBaseUrl}/report/data`);
        if (response.ok) {
            const data = await response.json();
            currentData = data;
            showResults();
        }
    } catch (error) {
        console.error('Error loading existing report:', error);
    }
}

// Handle file selection
function handleFileSelection(event) {
    const files = Array.from(event.target.files);
    processFiles(files);
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

// Process selected files
function processFiles(files) {
    // Filter Python files
    const pythonFiles = files.filter(file => file.name.endsWith('.py'));
    
    if (pythonFiles.length === 0) {
        alert('No Python files found. Please select a folder containing Python files.');
        return;
    }
    
    // Extract project path from first file
    const firstFile = pythonFiles[0];
    const projectPath = firstFile.webkitRelativePath ? 
        firstFile.webkitRelativePath.split('/')[0] : 
        'Selected Files';
    
    // Check for FastAPI indicators
    const fastApiDetected = checkForFastAPI(pythonFiles);
    
    // Update UI
    document.getElementById('project-path').textContent = projectPath;
    document.getElementById('file-count').textContent = pythonFiles.length;
    document.getElementById('fastapi-status').textContent = fastApiDetected ? 'Yes' : 'No';
    
    // Store files
    currentProject = {
        path: projectPath,
        files: pythonFiles,
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
async function scanProject() {
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
        const response = await fetch(`${apiBaseUrl}/scan`, {
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
                <button class="btn btn-primary" onclick="editItem(${index})">Edit</button>
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
function editItem(index) {
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
async function saveDocstring() {
    if (!currentEditingItem) {
        alert('No item selected for editing');
        return;
    }
    
    const docstring = document.getElementById('docstring-textarea').value;
    
    try {
        const response = await fetch(`${apiBaseUrl}/docstring/save`, {
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
async function generateAI() {
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
        const response = await fetch(`${apiBaseUrl}/docstring/generate`, {
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
function resetDocstring() {
    if (currentEditingItem) {
        document.getElementById('docstring-textarea').value = currentEditingItem.docstring || '';
        updatePreview();
    }
}

// Close editor
function closeEditor() {
    editorSection.style.display = 'none';
    currentEditingItem = null;
}

// Show OpenAI modal
function showOpenAIModal() {
    document.getElementById('openai-modal').style.display = 'flex';
}

// Close modal
function closeModal() {
    document.getElementById('openai-modal').style.display = 'none';
}

// Save OpenAI key
function saveOpenAIKey() {
    const key = document.getElementById('openai-key').value;
    if (key.trim()) {
        localStorage.setItem('openai_key', key.trim());
        closeModal();
        alert('OpenAI API key saved successfully!');
    } else {
        alert('Please enter a valid API key');
    }
}