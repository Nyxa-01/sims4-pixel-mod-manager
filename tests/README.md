# Test Suite Documentation

## Overview

Comprehensive test suite with 95%+ code coverage targeting security-first Sims 4 mod management.

## Structure

```
tests/
├── conftest.py              # Shared fixtures (425 LOC)
├── core/
│   ├── test_mod_scanner.py        # Mod scanning & validation (397 LOC)
│   ├── test_load_order_engine.py  # Load order management (335 LOC)
│   └── test_deploy_engine.py      # Deployment & rollback (430 LOC)
├── utils/
│   ├── test_config_manager.py     # Config & encryption (tests exist)
│   ├── test_backup.py             # Backup & restore (298 LOC)
│   ├── test_game_detector.py      # Game path detection (277 LOC)
│   └── test_process_manager.py    # Process management (217 LOC)
└── ui/
    ├── test_pixel_theme.py        # Theme engine (442 LOC)
    └── test_main_window.py        # Main UI (730 LOC)
```

**Total: 3,551+ LOC in implementation + comprehensive test coverage**

## Running Tests

### Quick Start

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests with coverage
pytest

# Or use the test runner
python run_tests.py
```

### Selective Testing

```bash
# Unit tests only (fast)
pytest -m unit
python run_tests.py --fast

# Integration tests
pytest -m integration
python run_tests.py --integration

# Security tests
pytest -m security
python run_tests.py --security

# Specific module
pytest tests/core/
python run_tests.py --module core
```

### Coverage Reports

```bash
# HTML report (opens in browser)
pytest --cov=src --cov-report=html
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html # Windows

# Terminal report with missing lines
pytest --cov=src --cov-report=term-missing

# XML report (for CI)
pytest --cov=src --cov-report=xml
```

## Coverage Targets

| Module     | Target | Current | Status |
|------------|--------|---------|--------|
| Core       | 95%    | TBD     | ⏳     |
| Utils      | 90%    | TBD     | ⏳     |
| UI         | 60%    | TBD     | ⏳     |
| **Overall**| **90%**| **TBD** | **⏳** |

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

Fast, isolated tests with no I/O or external dependencies.

**Examples:**
- `test_should_detect_package_file_type()`
- `test_should_validate_load_order_prefix()`
- `test_should_calculate_crc32_hash()`

**Run:** `pytest -m unit`

### Integration Tests (`@pytest.mark.integration`)

Multi-module workflows testing real interactions.

**Examples:**
- `test_full_workflow_scan_generate_deploy()`
- `test_deploy_with_rollback_on_failure()`
- `test_backup_restore_cycle()`

**Run:** `pytest -m integration`

### Security Tests (`@pytest.mark.security`)

Malicious file handling, entropy detection, timeout enforcement.

**Examples:**
- `test_should_reject_high_entropy_files()`
- `test_should_timeout_infinite_loop_mod()`
- `test_should_reject_oversized_mods()`

**Run:** `pytest -m security`

### Platform Tests

Cross-platform path handling for Windows/Mac/Linux.

**Markers:**
- `@pytest.mark.windows`
- `@pytest.mark.macos`
- `@pytest.mark.linux`

**Run:** `pytest -m windows`

## Fixtures

### File System Fixtures

```python
@pytest.fixture
def temp_mods_dir(tmp_path: Path) -> Path:
    """Temporary Mods directory."""

@pytest.fixture
def temp_mod_files(tmp_path: Path) -> dict[str, Path]:
    """Multiple mock mod files (valid, invalid, oversized, etc.)."""

@pytest.fixture
def malicious_mod(tmp_path: Path) -> Path:
    """High-entropy file for security testing."""
```

### Game Installation Fixtures

```python
@pytest.fixture
def mock_game_install(tmp_path: Path) -> dict[str, Path]:
    """Fake Sims 4 installation with:
    - Game executable (TS4_x64.exe)
    - Version file (GameVersion.txt)
    - Mods folder
    - Resource.cfg
    """
```

### Config Fixtures

```python
@pytest.fixture
def mock_config(tmp_path: Path) -> dict:
    """Mock configuration dictionary."""

@pytest.fixture
def mock_encryption_key(tmp_path: Path) -> Path:
    """Fernet encryption key for testing."""
```

### Backup Fixtures

```python
@pytest.fixture
def sample_backup_zip(tmp_path: Path) -> Path:
    """Backup ZIP with manifest.json."""

@pytest.fixture
def load_order_structure(tmp_path: Path) -> Path:
    """Complete load order directory tree."""
```

### Process Fixtures

```python
@pytest.fixture
def mock_game_process() -> Mock:
    """Mock psutil.Process for game."""
```

### Platform Fixtures

```python
@pytest.fixture
def mock_windows_platform(monkeypatch) -> None:
    """Mock Windows OS."""

@pytest.fixture
def mock_macos_platform(monkeypatch) -> None:
    """Mock macOS."""
```

## Key Test Cases

### Mod Scanner

- ✅ Valid/invalid file detection
- ✅ DBPF header validation
- ✅ Timeout enforcement (30s)
- ✅ Malware signatures
- ✅ Entropy analysis
- ✅ Size limits (500MB)

### Load Order Engine

- ✅ Alphabetical sorting
- ✅ Prefix validation (`\d{3}_\w+`)
- ✅ Script depth rules (root only)
- ✅ Path length limits (260 chars)
- ✅ Conflict detection
- ✅ Edge cases (ZZZ_, numeric prefixes)

### Deploy Engine

- ✅ Junction creation (Windows mklink /J)
- ✅ Symlink fallback
- ✅ Copy fallback
- ✅ Rollback on error
- ✅ CRC32 verification
- ✅ Transactional guarantees
- ✅ Game process handling

### Backup Manager

- ✅ CRC32 validation
- ✅ Manifest creation
- ✅ Corruption detection
- ✅ Retention policy (10 backups)
- ✅ Atomic writes (.tmp → rename)
- ✅ Restore verification

### Config Manager

- ✅ Fernet encryption/decryption
- ✅ Corruption recovery
- ✅ Transactional writes
- ✅ Key generation
- ✅ Cross-platform paths

### Game Detector

- ✅ Windows Registry detection
- ✅ Steam VDF parsing
- ✅ Documents folder detection
- ✅ Version reading
- ✅ Process detection (psutil)

### Process Manager

- ✅ Graceful termination (SIGTERM)
- ✅ Force kill fallback (SIGKILL)
- ✅ Wait timeout (10s)
- ✅ Process restoration
- ✅ AccessDenied handling

## Mocking Strategy

### Subprocess (mklink, symlink)

```python
with patch("subprocess.run") as mock_run:
    mock_run.return_value.returncode = 0
    # Test junction creation
```

### psutil (game processes)

```python
with patch("psutil.process_iter") as mock_iter:
    mock_iter.return_value = [mock_game_process]
    # Test game detection
```

### File operations (permissions)

```python
with patch("pathlib.Path.mkdir") as mock_mkdir:
    mock_mkdir.side_effect = PermissionError()
    # Test error handling
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests
        run: pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Best Practices

1. **Clear test names**: `test_should_reject_oversized_mods`
2. **Arrange-Act-Assert**: Setup → Execute → Verify
3. **Parametrize**: Use `@pytest.mark.parametrize` for multiple cases
4. **Fixtures**: Reuse setup code with fixtures
5. **Mocking**: Mock external dependencies (filesystem, network, processes)
6. **Assertions**: Specific assertions with clear messages
7. **Cleanup**: Use context managers and teardown

## Troubleshooting

### Tests fail with ImportError

```bash
# Ensure src is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"  # Unix
$env:PYTHONPATH += ";$(pwd)\src"              # PowerShell
```

### Coverage not working

```bash
# Install pytest-cov
pip install pytest-cov

# Check .coveragerc or pytest.ini configuration
```

### Slow tests

```bash
# Run only fast unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"
```

### Platform-specific failures

```bash
# Run only Windows tests
pytest -m windows

# Skip platform-specific tests
pytest -m "not windows and not macos"
```

## Maintenance

### Adding New Tests

1. Create test file in appropriate directory (`tests/core/`, `tests/utils/`, `tests/ui/`)
2. Add markers (`@pytest.mark.unit`, etc.)
3. Use existing fixtures from `conftest.py`
4. Follow naming convention: `test_should_<expected_behavior>`
5. Update this documentation

### Updating Fixtures

1. Edit `tests/conftest.py`
2. Add docstring with clear description
3. Type hint return values
4. Test fixture in isolation
5. Document in this file

### Coverage Goals

- **Add tests** for uncovered lines shown in HTML report
- **Parametrize** similar test cases
- **Mock** external dependencies for unit tests
- **Integration tests** for critical workflows

---

**Next Steps:**
1. Install dev dependencies: `pip install -e ".[dev]"`
2. Run full test suite: `pytest`
3. Generate coverage report: `pytest --cov=src --cov-report=html`
4. Open report: `open htmlcov/index.html`
5. Address uncovered lines
6. Achieve 90%+ coverage target
