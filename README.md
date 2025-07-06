# 🚀 FastAPI Documentation Assistant

A comprehensive tool for analyzing, editing, and improving FastAPI project documentation with AI assistance.

## ✨ Features

- **📊 Comprehensive Analysis**: Scans FastAPI projects for documentation coverage
- **🤖 AI-Powered Generation**: Uses OpenAI GPT-4 to generate professional docstrings
- **✏️ Interactive Editing**: Streamlit dashboard for easy docstring management
- **💾 Safe Patching**: Automatic backups and validation before applying changes
- **🔍 Deep Insights**: Coverage scores, quality metrics, and detailed analysis

## 🏗️ Architecture

```
fastdoc/
├── scanner.py      # AST-based FastAPI code analysis
├── models.py       # Data models for documentation items
└── cli.py         # Command-line interface

scripts/
├── patcher.py      # Safe docstring patching with backups
└── streamlit_app.py # Interactive documentation dashboard

project/           # Example FastAPI project
reports/          # Generated analysis reports
backups/          # Automatic file backups
```

## 🚀 Quick Start

### Option 1: Using Make (Recommended)

```bash
# Install dependencies
make install

# Scan your FastAPI project
make scan PROJECT_DIR=your_project_path

# Launch the interactive dashboard
make dashboard
```

### Option 2: Docker Deployment

```bash
# Build and run with docker-compose
make docker-compose-up

# Or manually
docker build -t fastapi-docs-assistant .
docker run -p 8501:8501 -v ./your_project:/app/project fastapi-docs-assistant
```

### Option 3: Direct Python

```bash
# Complete workflow
python run_docs_assistant.py

# Or step by step
python -m fastdoc.scanner scan your_project --out report.json
streamlit run scripts/streamlit_app.py
```

## 📋 Available Commands

Run `make help` to see all available commands:

| Command | Description |
|---------|-------------|
| `make scan` | Scan FastAPI project for documentation analysis |
| `make dashboard` | Launch interactive documentation dashboard |
| `make run-assistant` | Complete documentation workflow |
| `make docker-build` | Build Docker image |
| `make clean` | Clean generated files |
| `make check-env` | Verify environment setup |

## 🔧 Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# OpenAI API (optional - for AI features)
OPENAI_API_KEY=your_openai_api_key_here

# Project paths
PROJECT_BASE_PATH=./your_project
REPORTS_DIR=./reports
BACKUPS_DIR=./backups
```

### Project Structure Support

The scanner detects and analyzes:

- ✅ **FastAPI Applications**: `app = FastAPI(...)`
- ✅ **API Routers**: `router = APIRouter(...)`
- ✅ **HTTP Endpoints**: `@app.get`, `@router.post`, etc.
- ✅ **WebSocket Endpoints**: `@app.websocket`
- ✅ **Middleware**: `app.add_middleware(...)`
- ✅ **Dependencies**: Function parameters with `Depends()`
- ✅ **Pydantic Models**: Including `Config` classes
- ✅ **Regular Classes & Functions**: Complete code coverage

## 📊 Dashboard Features

### 1. Documentation Overview
- Real-time coverage metrics
- Filter by item type (endpoints, classes, functions)
- Visual progress indicators

### 2. Interactive Editor
- **Manual Editing**: Direct docstring editing with syntax validation
- **AI Assistant**: GPT-4 powered docstring generation
- **Preview Mode**: See how docstrings will look in code
- **Accept/Reject Workflow**: Review AI suggestions before applying

### 3. Quality Analysis
- Coverage scores for each item
- Documentation style detection (Google, NumPy, Sphinx)
- Parameter validation and missing docs detection
- Exception handling analysis

## 🤖 AI-Powered Features

When `OPENAI_API_KEY` is configured:

1. **Smart Generation**: Context-aware docstring generation
2. **FastAPI Specific**: Understands endpoints, dependencies, models
3. **Style Consistent**: Follows PEP-257 and your project's style
4. **Review Workflow**: Suggestions are reviewable before applying

## 🔒 Safety Features

- **Automatic Backups**: Every change creates timestamped backups
- **Syntax Validation**: Docstrings are validated before patching
- **Error Handling**: Comprehensive error reporting and recovery
- **File Integrity**: Line number validation and proper indentation

## 📈 Example Output

```json
{
  "module": "users",
  "qualname": "create_user",
  "method": "POST",
  "path": "/users/",
  "coverage_score": 85.0,
  "quality_score": 78.0,
  "completeness_issues": ["Missing parameter docs: ['password']"],
  "docstring_style": "google",
  "has_type_hints": true,
  "dependencies": ["get_current_user"],
  "tags": ["users"]
}
```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: '3.8'
services:
  docs-assistant:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./your_project:/app/project:ro
      - ./reports:/app/reports
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

```bash
# Start the service
docker-compose up --build

# Access at http://localhost:8501
```

### Standalone Scanner Service

```bash
# Run only the scanner (batch mode)
docker-compose --profile scanner run docs-scanner
```

## 🛠️ Development

```bash
# Setup development environment
make dev-setup

# Code formatting
make format

# Linting
make lint

# Type checking
make type-check

# Run tests
make test
```

## 📁 Project Structure

```
fastapi-docs-assistant/
├── fastdoc/                  # Core scanning engine
│   ├── __init__.py
│   ├── scanner.py           # AST-based code analysis
│   ├── models.py            # Data models
│   └── cli.py               # CLI interface
├── scripts/                 # User interfaces
│   ├── patcher.py           # Safe code patching
│   └── streamlit_app.py     # Web dashboard
├── project/                 # Example FastAPI app
├── Dockerfile               # Container setup
├── docker-compose.yml       # Service orchestration
├── Makefile                 # Development commands
├── pyproject.toml           # Dependencies
└── README.md                # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run `make dev-setup` and ensure all checks pass
6. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**Poetry/Python Version Issues**
```bash
# Use direct Python instead of Poetry
export USE_POETRY=false
make scan
```

**Docker Permission Issues**
```bash
# Fix volume permissions
sudo chown -R $USER:$USER ./reports ./backups
```

**OpenAI API Issues**
```bash
# Verify API key
echo $OPENAI_API_KEY
# Test API connection
python -c "from openai import OpenAI; client = OpenAI(); print('✅ API key valid')"
```

**Streamlit Not Starting**
```bash
# Check port availability
lsof -i :8501
# Use different port
streamlit run scripts/streamlit_app.py --server.port 8502
```

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/fastapi-docs-assistant/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/yourusername/fastapi-docs-assistant/discussions)
- 📖 **Documentation**: See `/docs` directory
- 💬 **Community**: [Discord Server](https://discord.gg/your-server)

---

**Made with ❤️ for the FastAPI community**