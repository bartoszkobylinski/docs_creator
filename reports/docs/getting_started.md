# Getting Started

## Prerequisites

- Python 3.8 or higher
- Poetry (for dependency management)
- LaTeX distribution (for PDF generation)
- PlantUML (for diagram generation)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd docs_creator
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Quick Start

1. Start the server:
   ```bash
   poetry run python main.py
   ```

2. Open the dashboard:
   ```
   http://localhost:8200
   ```

3. Scan a project:
   - Enter the project path in the dashboard
   - Click "Scan Project"
   - Wait for analysis to complete

4. Generate documentation:
   - Choose your output format (PDF, HTML, Confluence)
   - Click the appropriate generation button
   - Download or view the results

## Configuration

### Confluence Integration

To enable Confluence publishing:

1. Set environment variables:
   ```bash
   CONFLUENCE_URL=https://your-domain.atlassian.net
   CONFLUENCE_USERNAME=your-email@example.com
   CONFLUENCE_API_TOKEN=your-api-token
   CONFLUENCE_SPACE_KEY=YOUR_SPACE
   ```

2. Test the connection in the dashboard

### OpenAI Integration

For AI-powered docstring generation:

1. Get an OpenAI API key
2. Add it in the dashboard settings
3. Use the "AI Generate" button when editing docstrings

## Next Steps

- [Explore the API Reference](api_reference.md)
- [View Code Structure](code_structure.md)
- [Check Documentation Coverage](docstring_report.md)
