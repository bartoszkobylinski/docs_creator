from setuptools import setup, find_packages

# Read requirements from pyproject.toml or define them here
install_requires = [
    "typer>=0.16.0",
    "pandas>=2.3",
    "openai>=1.0",
    "fastapi>=0.100.0",
    "uvicorn>=0.20.0",
    "python-multipart>=0.0.6",
]

dev_requires = [
    "black>=23.0",
    "flake8>=6.0", 
    "mypy>=1.0",
    "pytest>=7.0",
]

setup(
    name="fastdoc",
    version="0.1.0",
    description="FastAPI doc-coverage scanner + dashboard",
    author="Bartosz Kobylinski",
    packages=find_packages(),
    install_requires=install_requires,
    extras_require={
        "dev": dev_requires,
    },
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "fastdoc=fastdoc.cli:app",
        ],
    },
)