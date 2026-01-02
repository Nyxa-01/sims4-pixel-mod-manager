# Test Suite Quick Reference

## Installation

```bash
pip install -e ".[dev]"
```

## Running Tests

### All Tests
```bash
pytest                           # With config from pytest.ini
python run_tests.py              # Using custom runner
```

### By Category
```bash
pytest -m unit                   # Fast unit tests
pytest -m integration            # Integration tests  
pytest -m security               # Security tests
pytest -m slow                   # Slow tests (>1s)
```

### By Module
```bash
pytest tests/core/               # Core module tests
pytest tests/utils/              # Utils module tests
pytest tests/ui/                 # UI module tests
python run_tests.py --module core
```

### By Platform
```bash
pytest -m windows                # Windows-specific
pytest -m macos                  # macOS-specific
pytest -m linux                  # Linux-specific
```

## Coverage

### Generate Reports
```bash
pytest --cov=src --cov-report=html    # HTML report
pytest --cov=src --cov-report=term    # Terminal report
pytest --cov=src --cov-report=xml     # XML (for CI)
```

### View HTML Report
```bash
# Windows
start htmlcov/index.html

# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

## Test Structure

```
tests/
├── conftest.py              # 20+ fixtures
├── pytest.ini               # Configuration
├── test_integration.py      # 50+ integration tests
│
├── core/                    # Core module tests
│   ├── test_mod_scanner.py
│   ├── test_load_order_engine.py
│   └── test_deploy_engine.py
│
├── utils/                   # Utils module tests
│   ├── test_config_manager.py
│   ├── test_backup.py
│   ├── test_game_detector.py
│   └── test_process_manager.py
│
└── ui/                      # UI module tests
    ├── test_pixel_theme.py
    └── test_main_window.py
```

## Key Fixtures

```python
# File fixtures
temp_mod_files(tmp_path)         # Multiple mock mods
sample_package_mod(tmp_path)     # Valid .package
malicious_mod(tmp_path)          # High-entropy file

# Game fixtures
mock_game_install(tmp_path)      # Fake Sims 4 install
mock_game_process()              # Mock psutil.Process

# Config fixtures
mock_config(tmp_path)            # Config dictionary
mock_encryption_key(tmp_path)    # Fernet key

# Backup fixtures
sample_backup_zip(tmp_path)      # Backup with manifest
load_order_structure(tmp_path)   # Load order tree
```

## Common Commands

```bash
# Quick unit test run
pytest -m unit -v

# Full coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing

# Test specific file
pytest tests/core/test_mod_scanner.py -v

# Run with print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Show slowest tests
pytest --durations=10
```

## Test Markers

- `@pytest.mark.unit` - Fast isolated tests
- `@pytest.mark.integration` - Multi-module tests
- `@pytest.mark.security` - Security testing
- `@pytest.mark.slow` - Tests >1 second
- `@pytest.mark.windows` - Windows-only
- `@pytest.mark.macos` - macOS-only
- `@pytest.mark.linux` - Linux-only
- `@pytest.mark.skip_ci` - Skip in CI

## Coverage Targets

| Module | Target |
|--------|--------|
| Core   | 95%    |
| Utils  | 90%    |
| UI     | 60%    |
| Total  | 90%    |

## Troubleshooting

### Import Errors
```bash
# Add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"  # Unix
$env:PYTHONPATH += ";$(pwd)\src"              # Windows
```

### Slow Tests
```bash
pytest -m "not slow"              # Skip slow tests
pytest -m unit                    # Fast tests only
```

### Platform Issues
```bash
pytest -m "not windows"           # Skip Windows tests
pytest -m "windows or linux"      # Run multiple platforms
```

## CI/CD Integration

```yaml
# GitHub Actions
- name: Run tests
  run: pytest --cov=src --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Documentation

- **tests/README.md** - Full test guide (350+ lines)
- **TEST_SUITE_SUMMARY.md** - Implementation summary
- **This file** - Quick reference
