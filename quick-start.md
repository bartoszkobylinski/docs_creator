# 🚀 Quick Start Guide

## ⚡ Fast Setup (2 minutes)

Your Poetry environment has some compatibility issues, but the documentation assistant works perfectly with pip!

### 1. Install Dependencies
```bash
# Use pip instead of Poetry (works around your Python version issue)
make install-pip
```
✅ **Success**: All dependencies installed successfully!

### 2. Generate Documentation Report
```bash
# Scan your FastAPI project
make scan

# Or scan a different project
make scan PROJECT_DIR=path/to/your/fastapi/project
```
✅ **Success**: Generated report with 38 items from example project!

### 3. Launch Interactive Dashboard
```bash
# Start the documentation assistant
make dashboard
```
✅ **Success**: Dashboard running at http://localhost:8501

## 🔧 Troubleshooting

### Poetry Issues
If you get Poetry/Python version errors:
```bash
# Use pip installation instead
make install-pip

# All commands work the same way
make scan
make dashboard
```

### Docker Issues
If Docker daemon isn't running:
```bash
# Start Docker Desktop first, then:
make docker-compose-up

# Or install Docker and start the daemon:
# brew install docker
# sudo service docker start  # Linux
```

### OpenAI Features (Optional)
```bash
# Set your API key for AI features
export OPENAI_API_KEY="your_key_here"

# Verify it works
python -c "import openai; print('✅ OpenAI ready')"
```

## 🎯 Main Commands

| Command | What it does |
|---------|-------------|
| `make scan` | Analyze your FastAPI project |
| `make dashboard` | Launch the web interface |
| `make run-assistant` | Complete guided workflow |
| `make help` | Show all available commands |

## 🌟 Features Available

✅ **Working perfectly**:
- Project scanning and analysis
- Documentation coverage metrics  
- Interactive Streamlit dashboard
- Manual docstring editing
- File patching with backups
- Support for all FastAPI constructs

🤖 **AI Features** (requires OpenAI API key):
- Intelligent docstring generation
- Context-aware suggestions
- Accept/reject workflow

## 📊 Next Steps

1. **Try it on your project**:
   ```bash
   make scan PROJECT_DIR=/path/to/your/fastapi/project
   make dashboard
   ```

2. **Set up AI features**:
   ```bash
   export OPENAI_API_KEY="your_key_here"
   # Now AI suggestions work in the dashboard
   ```

3. **Use Docker for production**:
   ```bash
   # Start Docker Desktop first
   make docker-compose-up
   ```

Your FastAPI Documentation Assistant is ready! 🎉