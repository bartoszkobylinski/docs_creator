# Testing Strategy and Implementation

This document outlines the comprehensive testing strategy implemented for the FastAPI Documentation Assistant.

## 🎯 Testing Philosophy

Our testing approach focuses on **real functionality validation** rather than just achieving coverage numbers. Each test is designed to:

- Test actual business logic and user workflows
- Catch real bugs and regressions
- Validate integration between components
- Ensure performance doesn't degrade over time

## 📋 Test Types Implemented

### 1. Unit Tests (`tests/unit/`)
**Purpose**: Test individual components in isolation with mocked dependencies.

#### Services Tests:
- **Scanner Service** (`test_scanner_service.py`)
  - File upload processing
  - Local project scanning  
  - Error handling and edge cases
  - Integration with core scanner module

- **Confluence Service** (`test_confluence_service.py`)
  - API authentication and connection
  - Document publishing workflows
  - HTML generation and formatting
  - Error handling for API failures

- **Coverage Tracker** (`test_coverage_tracker.py`)
  - Statistics calculation accuracy
  - Historical data persistence  
  - Trend analysis algorithms
  - Progress report generation

#### Core Module Tests:
- **Scanner Module** (`test_scanner.py`)
  - AST parsing and analysis
  - FastAPI endpoint detection
  - Pydantic model scanning
  - Complex inheritance scenarios
  - Unicode and encoding handling

### 2. Integration Tests (`tests/integration/`)
**Purpose**: Test component interactions with realistic data flows.

#### API Endpoint Tests:
- **Report Endpoints**: Status checking, data retrieval
- **Scan Endpoints**: File upload, local scanning workflows
- **Docstring Endpoints**: Save/generate functionality
- **Confluence Endpoints**: Publishing workflows
- **Coverage Endpoints**: History and trend analysis

#### End-to-End Workflows:
- Complete scan → edit → publish workflow
- Scan → Confluence integration workflow
- Error handling across service boundaries

### 3. Regression Tests (`tests/regression/`)
**Purpose**: Ensure existing behavior doesn't change across versions.

#### Scanner Regression Tests:
- **FastAPI Example**: Consistent parsing of complex FastAPI applications
- **Pydantic Models**: Stable detection of model structures
- **Inheritance**: Complex class hierarchy handling
- **Coverage Calculation**: Mathematical accuracy over time
- **Performance**: Ensure scanning speed doesn't degrade

#### Service Integration Regression:
- Output format consistency
- API response structure stability
- Statistics calculation accuracy

### 4. Mutation Testing (mutmut)
**Purpose**: Validate that tests actually catch bugs by introducing code mutations.

#### Configuration:
- Targets: `fastdoc/`, `services/`, `api/`, `core/`
- Excludes: `tests/`, `__pycache__`, virtual environments
- Runner: `poetry run pytest` with fast execution options
- Coverage-based mutation selection

## 🔧 Test Infrastructure

### Test Configuration (`pyproject.toml`)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--strict-markers",
    "--cov=fastdoc", "--cov=services", "--cov=api", "--cov=core",
    "--cov-report=html:htmlcov",
    "--cov-fail-under=30"
]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests", 
    "unit: marks tests as unit tests",
    "regression: marks tests as regression tests"
]
asyncio_mode = "auto"
```

### Fixtures (`tests/conftest.py`)
- **Test Client**: FastAPI test client for API testing
- **Sample Projects**: Realistic Python code samples
- **Documentation Items**: Consistent test data
- **Mock Services**: Confluence, OpenAI API mocks
- **Temporary Environment**: Isolated test filesystem

### Dependencies
- `pytest`: Core testing framework
- `pytest-asyncio`: Async test support
- `pytest-cov`: Coverage reporting
- `pytest-mock`: Enhanced mocking capabilities
- `httpx`: HTTP client for API testing
- `freezegun`: Time manipulation for testing
- `mutmut`: Mutation testing

## 🏃‍♂️ Running Tests

### Basic Commands
```bash
# Run all tests
make test

# Run specific test types  
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-regression    # Regression tests only
make test-fast          # Exclude slow tests

# Coverage and reporting
make test-coverage      # With HTML coverage report
make test-mutation      # Run mutation tests
make test-all          # Complete test suite
```

### Advanced Usage
```bash
# Run specific test files
poetry run pytest tests/unit/services/test_scanner_service.py -v

# Run tests matching pattern
poetry run pytest -k "test_scan" -v

# Run with specific markers
poetry run pytest -m "not slow" -v

# Debug failing tests
poetry run pytest --pdb -x
```

## 📊 Test Quality Metrics

### Coverage Targets
- **Minimum Coverage**: 30% (current baseline)
- **Target Coverage**: 80%+ for critical paths
- **Mutation Score**: 75%+ for core logic

### Critical Test Areas
1. **Scanner Accuracy**: AST parsing must be 100% accurate
2. **API Reliability**: All endpoints must handle errors gracefully  
3. **Data Integrity**: Coverage statistics must be mathematically correct
4. **Integration Stability**: Service interactions must be robust

### Performance Benchmarks
- **Large File Scanning**: < 5 seconds for 500 functions
- **Multiple File Scanning**: < 10 seconds for 50 files
- **API Response Time**: < 500ms for standard operations

## 🔍 Test Data Strategy

### Sample Projects
Tests use realistic code samples that mirror real-world usage:
- FastAPI applications with complex routing
- Pydantic models with validation
- Class hierarchies with inheritance
- Mixed documented/undocumented code

### Fixtures Design
- **Isolated**: Each test gets fresh data
- **Realistic**: Based on actual project structures  
- **Comprehensive**: Cover edge cases and error conditions
- **Maintainable**: Easy to update when requirements change

## 🐛 Debugging Tests

### Common Issues
1. **Import Errors**: Ensure PYTHONPATH includes project root
2. **Async Tests**: Use `pytest.mark.asyncio` for async functions
3. **Mock Issues**: Verify mock patches target correct modules
4. **File Permissions**: Temporary directories need write access

### Debug Tools
```bash
# Verbose output
poetry run pytest -v -s

# Stop on first failure  
poetry run pytest -x

# Drop into debugger on failure
poetry run pytest --pdb

# Show test coverage gaps
poetry run pytest --cov-report=term-missing
```

## 🔄 Continuous Integration

### Pre-commit Hooks
```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run manually
poetry run pre-commit run --all-files
```

### CI Pipeline (Recommended)
1. **Unit Tests**: Fast feedback on core logic
2. **Integration Tests**: Validate component interactions  
3. **Regression Tests**: Ensure no behavioral changes
4. **Mutation Tests**: Validate test quality (weekly)
5. **Performance Tests**: Catch performance regressions

### Test Artifacts
- **Coverage Reports**: `htmlcov/index.html`
- **Mutation Reports**: `.mutmut-cache/`
- **Test Results**: `pytest-report.html`

## 📈 Test Maintenance

### Regular Tasks
- **Review Coverage**: Identify untested code paths
- **Update Fixtures**: Keep test data current with real usage
- **Performance Monitoring**: Track test execution times
- **Mutation Testing**: Run weekly to validate test quality

### Adding New Tests
1. **Unit Tests**: For new functions/classes
2. **Integration Tests**: For new API endpoints  
3. **Regression Tests**: For bug fixes
4. **Performance Tests**: For optimization changes

### Test Cleanup
```bash
# Clean test artifacts
make test-clean

# Remove coverage data
rm -rf .coverage htmlcov/

# Clear pytest cache
rm -rf .pytest_cache/
```

## ✅ Quality Assurance

### Test Review Checklist
- [ ] Tests cover both success and failure cases
- [ ] Edge cases and error conditions tested
- [ ] Mock usage is appropriate and isolated
- [ ] Test names clearly describe what's being tested
- [ ] Assertions are specific and meaningful
- [ ] Tests are independent and can run in any order

### Validation Criteria
- **Functionality**: Tests validate actual business requirements
- **Reliability**: Tests pass consistently across environments
- **Performance**: Test suite runs in reasonable time
- **Maintainability**: Tests are easy to understand and modify

---

This testing strategy ensures robust, reliable software through comprehensive validation of functionality, integration, and performance. The multi-layered approach catches issues at different levels while maintaining high development velocity.