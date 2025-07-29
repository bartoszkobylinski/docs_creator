# Frequently Asked Questions

## General Questions

### What is API Documentation?

API Documentation is an automated documentation generation system that analyzes Python code and produces comprehensive documentation in multiple formats.

### What formats are supported?

- **PDF**: Technical documentation via LaTeX
- **HTML**: Readable documentation via Sphinx
- **Confluence**: Team collaboration pages
- **JSON/YAML**: Raw data for integrations

### How often should I regenerate documentation?

We recommend regenerating documentation:
- After each major feature release
- When documentation coverage drops below 80%
- Before onboarding new team members
- As part of your CI/CD pipeline

## Technical Questions

### How does the code scanner work?

The scanner uses Python's AST (Abstract Syntax Tree) to parse code and extract:
- Functions and their signatures
- Classes and their methods
- Module-level documentation
- Docstrings and their content

### Can I customize the generated documentation?

Yes! You can:
- Edit docstrings directly in the dashboard
- Modify Markdown templates
- Configure Sphinx themes
- Customize LaTeX templates

### What Python versions are supported?

The tool supports Python 3.8 and higher. It can analyze code written for any Python version.

## Integration Questions

### How do I set up Confluence integration?

1. Get an API token from Atlassian
2. Set environment variables (see [Getting Started](getting_started.md))
3. Configure space and parent page in settings

### Can I use this in CI/CD?

Yes! You can:
- Use the CLI mode for automation
- Call API endpoints directly
- Generate documentation as part of your build process

### Is there an API for external integrations?

Yes, all functionality is exposed via REST API. See the [API Reference](api_reference.md) for details.

## Troubleshooting

### Documentation generation fails

Common causes:
- Missing dependencies (LaTeX, PlantUML)
- Invalid Python syntax in scanned code
- Insufficient permissions on output directory

### UML diagrams are not showing

Ensure:
- PlantUML is installed and in PATH
- Java runtime is available
- Network access for PlantUML server (if using remote)

### Confluence publishing fails

Check:
- API credentials are correct
- You have write permissions to the space
- The parent page exists
