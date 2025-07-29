// Modern Documentation Dashboard - 2025
// Clean, organized JavaScript with proper state management

class DocumentationDashboard {
    constructor() {
        this.apiBaseUrl = 'http://0.0.0.0:8200';
        this.currentData = null;
        this.currentEditingItem = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.checkExistingReport();
        this.updateUIState();
    }
    
    // ===== STATE MANAGEMENT =====
    
    updateUIState() {
        const hasData = this.currentData && this.currentData.items && this.currentData.items.length > 0;
        
        // Update status indicator
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-text');
        
        if (hasData) {
            statusDot.classList.add('active');
            statusText.textContent = `${this.currentData.items.length} items loaded`;
        } else {
            statusDot.classList.remove('active');
            statusText.textContent = 'No data';
        }
        
        // Show appropriate view
        if (hasData) {
            this.showDashboard();
        } else {
            this.showEmptyState();
        }
    }
    
    showEmptyState() {
        document.getElementById('empty-state').style.display = 'flex';
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('main-dashboard').style.display = 'none';
    }
    
    showLoadingState(message = 'Processing...') {
        document.getElementById('empty-state').style.display = 'none';
        document.getElementById('loading-state').style.display = 'flex';
        document.getElementById('main-dashboard').style.display = 'none';
        document.getElementById('loading-message').textContent = message;
    }
    
    showDashboard() {
        document.getElementById('empty-state').style.display = 'none';
        document.getElementById('loading-state').style.display = 'none';
        document.getElementById('main-dashboard').style.display = 'grid';
        
        this.updateDashboardData();
    }
    
    updateProgress(percentage, message = '') {
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        const loadingMessage = document.getElementById('loading-message');
        
        progressFill.style.width = `${percentage}%`;
        progressText.textContent = `${percentage}%`;
        if (message) loadingMessage.textContent = message;
    }
    
    // ===== EVENT LISTENERS =====
    
    setupEventListeners() {
        // File drop zone
        const jsonDropZone = document.getElementById('json-drop-zone');
        const jsonFileInput = document.getElementById('json-file-input');
        
        jsonDropZone.addEventListener('click', () => jsonFileInput.click());
        jsonDropZone.addEventListener('dragover', this.handleDragOver.bind(this));
        jsonDropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        jsonDropZone.addEventListener('drop', this.handleFileDrop.bind(this));
        
        jsonFileInput.addEventListener('change', (e) => {
            if (e.target.files[0]) {
                this.loadJSONReport(e.target.files[0]);
            }
        });
        
        // Filters
        const typeFilter = document.getElementById('type-filter');
        const docFilter = document.getElementById('doc-filter');
        
        if (typeFilter) typeFilter.addEventListener('change', () => this.applyFilters());
        if (docFilter) docFilter.addEventListener('change', () => this.applyFilters());
        
        // Modal close on background click
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModal(modal.id);
                }
            });
        });
    }
    
    // ===== FILE HANDLING =====
    
    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.style.borderColor = 'var(--color-primary)';
        e.currentTarget.style.background = 'var(--color-gray-50)';
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.style.borderColor = 'var(--color-gray-300)';
        e.currentTarget.style.background = 'transparent';
    }
    
    handleFileDrop(e) {
        e.preventDefault();
        this.handleDragLeave(e);
        
        const files = Array.from(e.dataTransfer.files);
        const jsonFile = files.find(file => file.type === 'application/json' || file.name.endsWith('.json'));
        
        if (jsonFile) {
            this.loadJSONReport(jsonFile);
        } else {
            this.showNotification('Please drop a JSON report file.', 'error');
        }
    }
    
    async loadJSONReport(file) {
        try {
            this.showLoadingState('Loading report...');
            
            const text = await file.text();
            const data = JSON.parse(text);
            
            if (!Array.isArray(data)) {
                throw new Error('Invalid report format: expected an array of items');
            }
            
            this.currentData = {
                items: data,
                total_files: new Set(data.map(item => item.file_path || item.module)).size,
                scan_time: 0
            };
            
            this.updateUIState();
            this.showNotification('Report loaded successfully!', 'success');
            
        } catch (error) {
            console.error('Error loading JSON report:', error);
            this.showNotification(`Error loading report: ${error.message}`, 'error');
            this.showEmptyState();
        }
    }
    
    // ===== API CALLS =====
    
    async checkExistingReport() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/report/status`);
            if (response.ok) {
                const data = await response.json();
                if (data.exists) {
                    await this.loadExistingReport();
                }
            }
        } catch (error) {
            console.log('No existing report found');
        }
    }
    
    async loadExistingReport() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/report/data`);
            if (response.ok) {
                this.currentData = await response.json();
                this.updateUIState();
            }
        } catch (error) {
            console.error('Error loading existing report:', error);
        }
    }
    
    async scanLocalProject() {
        const projectPath = document.getElementById('project-path-input').value.trim();
        
        if (!projectPath) {
            this.showNotification('Please enter a project path', 'error');
            return;
        }
        
        try {
            this.showLoadingState('Starting scan...');
            this.updateProgress(10, 'Initializing...');
            
            const response = await fetch(`${this.apiBaseUrl}/api/scan-local`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_path: projectPath })
            });
            
            this.updateProgress(50, 'Processing files...');
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Scan failed: ${errorText}`);
            }
            
            this.currentData = await response.json();
            this.updateProgress(100, 'Scan completed!');
            
            setTimeout(() => {
                this.updateUIState();
                this.showNotification('Project scanned successfully!', 'success');
            }, 500);
            
        } catch (error) {
            console.error('Scan error:', error);
            this.showNotification(`Scan failed: ${error.message}`, 'error');
            this.showEmptyState();
        }
    }
    
    // ===== DASHBOARD DATA =====
    
    updateDashboardData() {
        if (!this.currentData || !this.currentData.items) return;
        
        const items = this.currentData.items;
        const totalItems = items.length;
        const documentedItems = items.filter(item => item.docstring && item.docstring.trim() !== '').length;
        const coveragePercent = totalItems > 0 ? Math.round((documentedItems / totalItems) * 100) : 0;
        const missingDocs = totalItems - documentedItems;
        
        // Update stats
        document.getElementById('total-items').textContent = totalItems;
        document.getElementById('documented-items').textContent = documentedItems;
        document.getElementById('coverage-percent').textContent = `${coveragePercent}%`;
        document.getElementById('missing-docs').textContent = missingDocs;
        
        // Update coverage bar
        const coverageBar = document.getElementById('coverage-bar');
        coverageBar.style.width = `${coveragePercent}%`;
        
        // Update table
        this.populateTable(items);
        
        // Check integrations
        this.checkIntegrations();
    }
    
    populateTable(items) {
        const tbody = document.getElementById('docs-table-body');
        tbody.innerHTML = '';
        
        items.forEach((item, index) => {
            const hasDoc = item.docstring && item.docstring.trim() !== '';
            const coverage = item.coverage_score || 0;
            const quality = item.quality_score || 0;
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><code>${item.module || 'N/A'}</code></td>
                <td><code>${item.qualname || 'N/A'}</code></td>
                <td><span class="badge">${item.method || 'N/A'}</span></td>
                <td><span class="status-badge ${hasDoc ? 'success' : 'error'}">${hasDoc ? '✓' : '✗'}</span></td>
                <td>
                    <div class="mini-progress">
                        <div class="mini-progress-fill" style="width: ${coverage}%"></div>
                    </div>
                    ${coverage}%
                </td>
                <td>
                    <div class="mini-progress">
                        <div class="mini-progress-fill" style="width: ${quality}%"></div>
                    </div>
                    ${quality}%
                </td>
                <td>
                    <button onclick="dashboard.editItem(${index})" class="btn btn-outline btn-sm">Edit</button>
                </td>
            `;
            
            tbody.appendChild(row);
        });
    }
    
    applyFilters() {
        if (!this.currentData) return;
        
        const typeFilter = document.getElementById('type-filter').value;
        const docFilter = document.getElementById('doc-filter').value;
        
        let filteredItems = this.currentData.items;
        
        if (typeFilter) {
            filteredItems = filteredItems.filter(item => item.method === typeFilter);
        }
        
        if (docFilter === 'missing') {
            filteredItems = filteredItems.filter(item => !item.docstring || item.docstring.trim() === '');
        } else if (docFilter === 'documented') {
            filteredItems = filteredItems.filter(item => item.docstring && item.docstring.trim() !== '');
        }
        
        this.populateTable(filteredItems);
    }
    
    // ===== INTEGRATIONS =====
    
    async checkIntegrations() {
        // Check Confluence
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/confluence/status`);
            if (response.ok) {
                const data = await response.json();
                const confluenceBtn = document.getElementById('confluence-action');
                if (data.enabled) {
                    confluenceBtn.classList.remove('disabled');
                    confluenceBtn.querySelector('.btn-subtitle').textContent = 'Ready to publish';
                } else {
                    confluenceBtn.classList.add('disabled');
                    confluenceBtn.querySelector('.btn-subtitle').textContent = 'Not configured';
                }
            }
        } catch (error) {
            console.log('Confluence check failed:', error);
        }
    }
    
    // ===== MODAL MANAGEMENT =====
    
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.style.display = 'flex';
        modal.classList.add('show');
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 200);
    }
    
    // ===== ACTION HANDLERS =====
    
    generateUMLDashboard() {
        if (!this.currentData || !this.currentData.items) {
            this.showNotification('No data available for UML generation', 'error');
            return;
        }
        this.showModal('uml-modal');
    }
    
    generateLatexDashboard() {
        if (!this.currentData || !this.currentData.items) {
            this.showNotification('No data available for PDF generation', 'error');
            return;
        }
        this.showModal('latex-modal');
    }
    
    generateMarkdownDashboard() {
        if (!this.currentData || !this.currentData.items) {
            this.showNotification('No data available for Markdown generation', 'error');
            return;
        }
        this.showModal('markdown-modal');
    }
    
    openConfluenceDashboard() {
        if (!this.currentData || !this.currentData.items) {
            this.showNotification('No data available for Confluence publishing', 'error');
            return;
        }
        // For now, just show notification - could expand to full Confluence modal
        this.showNotification('Confluence integration coming soon!', 'info');
    }
    
    async generateUMLType(type) {
        this.closeModal('uml-modal');
        
        try {
            // Open UML page with the selected type
            const url = `/uml`;
            window.open(url, '_blank');
            
        } catch (error) {
            this.showNotification(`UML generation failed: ${error.message}`, 'error');
        }
    }
    
    async generatePDF() {
        const projectName = document.getElementById('pdf-project-name').value || 'API Documentation';
        const includeUML = document.getElementById('include-uml-pdf').checked;
        const statusDiv = document.getElementById('pdf-status');
        
        try {
            statusDiv.innerHTML = '<div class="loading-spinner" style="width: 20px; height: 20px; margin: 0 auto;"></div>';
            
            const response = await fetch(`${this.apiBaseUrl}/api/docs/latex`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_name: projectName,
                    include_uml: includeUML
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                
                if (result.success) {
                    const latexFile = result.latex_file.split('/').pop();
                    const pdfFile = result.pdf_file ? result.pdf_file.split('/').pop() : null;
                    
                    let statusHTML = '<div class="status-message success">✅ PDF generated successfully!</div>';
                    statusHTML += '<div style="margin-top: 10px; display: flex; gap: 10px;">';
                    statusHTML += `<a href="${this.apiBaseUrl}/api/docs/latex/download/${latexFile}" target="_blank" class="btn btn-outline btn-sm">LaTeX Source</a>`;
                    if (pdfFile) {
                        statusHTML += `<a href="${this.apiBaseUrl}/api/docs/latex/download/${pdfFile}" target="_blank" class="btn btn-primary btn-sm">📄 Download PDF</a>`;
                    }
                    statusHTML += '</div>';
                    
                    statusDiv.innerHTML = statusHTML;
                } else {
                    throw new Error(result.error || 'Unknown error');
                }
            } else {
                const error = await response.text();
                throw new Error(error);
            }
        } catch (error) {
            statusDiv.innerHTML = `<div class="status-message error">❌ ${error.message}</div>`;
        }
    }
    
    async generateMarkdown() {
        const projectName = document.getElementById('markdown-project-name').value || 'API Documentation';
        const includeUML = document.getElementById('include-uml-markdown').checked;
        const publishConfluence = document.getElementById('publish-confluence').checked;
        const statusDiv = document.getElementById('markdown-status');
        
        try {
            statusDiv.innerHTML = '<div class="loading-spinner" style="width: 20px; height: 20px; margin: 0 auto;"></div>';
            
            // First generate Markdown
            const response = await fetch(`${this.apiBaseUrl}/api/docs/markdown`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_name: projectName,
                    include_uml: includeUML
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                
                if (result.success) {
                    let statusHTML = '<div class="status-message success">✅ Markdown generated successfully!</div>';
                    statusHTML += '<div style="margin-top: 10px;">';
                    statusHTML += `<p><strong>Generated files:</strong></p>`;
                    statusHTML += '<ul style="margin: 10px 0; text-align: left;">';
                    
                    Object.entries(result.files).forEach(([key, path]) => {
                        const filename = path.split('/').pop();
                        statusHTML += `<li>${filename}</li>`;
                    });
                    
                    statusHTML += '</ul>';
                    
                    // If publish to Confluence is checked
                    if (publishConfluence && await this.checkConfluenceEnabled()) {
                        statusHTML += '<p>Publishing to Confluence...</p>';
                        statusDiv.innerHTML = statusHTML;
                        
                        // Publish to Confluence
                        const confluenceResponse = await fetch(`${this.apiBaseUrl}/api/confluence/publish-markdown`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                project_name: projectName,
                                include_uml: includeUML
                            })
                        });
                        
                        if (confluenceResponse.ok) {
                            const confluenceResult = await confluenceResponse.json();
                            statusHTML += `<div class="status-message success" style="margin-top: 10px;">`;
                            statusHTML += `✅ Published to Confluence!<br>`;
                            statusHTML += `<a href="${confluenceResult.page_url}" target="_blank" class="btn btn-primary btn-sm" style="margin-top: 5px;">View in Confluence</a>`;
                            statusHTML += `</div>`;
                        } else {
                            statusHTML += `<div class="status-message error" style="margin-top: 10px;">❌ Failed to publish to Confluence</div>`;
                        }
                    }
                    
                    statusHTML += '</div>';
                    statusDiv.innerHTML = statusHTML;
                } else {
                    throw new Error(result.error || 'Unknown error');
                }
            } else {
                const error = await response.text();
                throw new Error(error);
            }
        } catch (error) {
            statusDiv.innerHTML = `<div class="status-message error">❌ ${error.message}</div>`;
        }
    }
    
    async checkConfluenceEnabled() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/confluence/status`);
            if (response.ok) {
                const data = await response.json();
                return data.enabled;
            }
        } catch (error) {
            console.log('Confluence check failed:', error);
        }
        return false;
    }
    
    // ===== EDITOR =====
    
    editItem(index) {
        if (!this.currentData || !this.currentData.items[index]) {
            this.showNotification('Item not found', 'error');
            return;
        }
        
        const item = this.currentData.items[index];
        this.currentEditingItem = { ...item, index };
        
        // Populate editor
        document.getElementById('editor-title').textContent = `Edit: ${item.qualname || 'Unknown'}`;
        document.getElementById('edit-module').textContent = item.module || 'N/A';
        document.getElementById('edit-name').textContent = item.qualname || 'N/A';
        document.getElementById('edit-type').textContent = item.method || 'N/A';
        document.getElementById('edit-file').textContent = item.file_path || 'N/A';
        
        document.getElementById('source-code').textContent = item.full_source || item.first_lines || 'Source not available';
        document.getElementById('docstring-textarea').value = item.docstring || '';
        
        this.updatePreview();
        this.showEditor();
    }
    
    showEditor() {
        document.getElementById('editor-panel').classList.add('show');
    }
    
    closeEditor() {
        document.getElementById('editor-panel').classList.remove('show');
        this.currentEditingItem = null;
    }
    
    updatePreview() {
        const docstring = document.getElementById('docstring-textarea').value;
        const preview = document.getElementById('docstring-preview');
        
        if (docstring.trim()) {
            const lines = docstring.split('\\n');
            const indentedLines = lines.map(line => line.trim() ? `    ${line}` : '');
            preview.textContent = `    \"\"\"\\n${indentedLines.join('\\n')}\\n    \"\"\"`;
        } else {
            preview.textContent = '# No docstring';
        }
    }
    
    async saveDocstring() {
        if (!this.currentEditingItem) {
            this.showNotification('No item selected for editing', 'error');
            return;
        }
        
        const docstring = document.getElementById('docstring-textarea').value;
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/docstring/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    item: this.currentEditingItem,
                    docstring: docstring
                })
            });
            
            if (response.ok) {
                this.currentData.items[this.currentEditingItem.index].docstring = docstring;
                this.updateDashboardData();
                this.showNotification('Documentation saved successfully!', 'success');
            } else {
                throw new Error('Failed to save documentation');
            }
        } catch (error) {
            this.showNotification('Failed to save documentation', 'error');
        }
    }
    
    async generateAI() {
        if (!this.currentEditingItem) {
            this.showNotification('No item selected for editing', 'error');
            return;
        }
        
        const openaiKey = localStorage.getItem('openai_key');
        if (!openaiKey) {
            this.showModal('openai-modal');
            return;
        }
        
        const aiBtn = document.getElementById('ai-btn');
        const originalText = aiBtn.textContent;
        aiBtn.textContent = 'Generating...';
        aiBtn.disabled = true;
        
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/docstring/generate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${openaiKey}`
                },
                body: JSON.stringify({ item: this.currentEditingItem })
            });
            
            if (response.ok) {
                const result = await response.json();
                document.getElementById('docstring-textarea').value = result.docstring;
                this.updatePreview();
                this.showNotification('AI documentation generated!', 'success');
            } else {
                throw new Error('Failed to generate documentation');
            }
        } catch (error) {
            this.showNotification('Failed to generate AI documentation', 'error');
        } finally {
            aiBtn.textContent = originalText;
            aiBtn.disabled = false;
        }
    }
    
    resetDocstring() {
        if (this.currentEditingItem) {
            document.getElementById('docstring-textarea').value = this.currentEditingItem.docstring || '';
            this.updatePreview();
        }
    }
    
    saveOpenAIKey() {
        const key = document.getElementById('openai-key').value;
        if (key.trim()) {
            localStorage.setItem('openai_key', key.trim());
            this.closeModal('openai-modal');
            this.showNotification('OpenAI API key saved!', 'success');
        } else {
            this.showNotification('Please enter a valid API key', 'error');
        }
    }
    
    // ===== UTILITIES =====
    
    showNotification(message, type = 'info') {
        // Create notification element
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
    
    refreshData() {
        this.checkExistingReport();
    }
}

// Initialize dashboard
const dashboard = new DocumentationDashboard();

// Global functions for onclick handlers
window.scanLocalProject = () => dashboard.scanLocalProject();
window.generateUMLDashboard = () => dashboard.generateUMLDashboard();
window.generateLatexDashboard = () => dashboard.generateLatexDashboard();
window.generateMarkdownDashboard = () => dashboard.generateMarkdownDashboard();
window.openConfluenceDashboard = () => dashboard.openConfluenceDashboard();
window.generateUMLType = (type) => dashboard.generateUMLType(type);
window.generatePDF = () => dashboard.generatePDF();
window.generateMarkdown = () => dashboard.generateMarkdown();
window.closeModal = (id) => dashboard.closeModal(id);
window.editItem = (index) => dashboard.editItem(index);
window.closeEditor = () => dashboard.closeEditor();
window.saveDocstring = () => dashboard.saveDocstring();
window.generateAI = () => dashboard.generateAI();
window.resetDocstring = () => dashboard.resetDocstring();
window.saveOpenAIKey = () => dashboard.saveOpenAIKey();
window.refreshData = () => dashboard.refreshData();

// Add docstring textarea event listener
document.addEventListener('DOMContentLoaded', () => {
    const textarea = document.getElementById('docstring-textarea');
    if (textarea) {
        textarea.addEventListener('input', () => dashboard.updatePreview());
    }
});