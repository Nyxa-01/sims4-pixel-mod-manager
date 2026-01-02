# Contributing to Sims 4 Pixel Mod Manager

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Bug Reports](#bug-reports)
- [Feature Requests](#feature-requests)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, gender identity, sexual orientation, disability, personal appearance, race, ethnicity, age, religion, or nationality.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Respecting differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what's best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Harassment, trolling, or derogatory comments
- Publishing others' private information
- Spam or off-topic conversations
- Any conduct inappropriate in a professional setting

### Enforcement

Project maintainers will remove, edit, or reject comments, commits, code, issues, and other contributions that violate this Code of Conduct. Report violations to your.email@example.com.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- GitHub account
- Familiarity with Python, tkinter, and pytest

### Fork and Clone

```bash
# 1. Fork repository on GitHub (click Fork button)

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/sims4-pixel-mod-manager.git
cd sims4-pixel-mod-manager

# 3. Add upstream remote
git remote add upstream https://github.com/yourusername/sims4-pixel-mod-manager.git

# 4. Verify remotes
git remote -v
# origin    https://github.com/YOUR_USERNAME/sims4-pixel-mod-manager.git (fetch)
# origin    https://github.com/YOUR_USERNAME/sims4-pixel-mod-manager.git (push)
# upstream  https://github.com/yourusername/sims4-pixel-mod-manager.git (fetch)
# upstream  https://github.com/yourusername/sims4-pixel-mod-manager.git (push)
```

### Development Setup

```bash
# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Verify installation
pytest --version
black --version
ruff --version
mypy --version
```

### Running the Application

```bash
# Run from source
python main.py

# With debugging
python main.py --log-level DEBUG

# Run tests
pytest -v
```

## Development Workflow

### Branch Naming Convention

```bash
# Feature branches
git checkout -b feat/add-cloud-backup

# Bug fix branches
git checkout -b fix/deployment-rollback

# Documentation branches
git checkout -b docs/update-readme

# Refactoring branches
git checkout -b refactor/simplify-scanner
```

### Keeping Your Fork Updated

```bash
# Fetch upstream changes
git fetch upstream

# Merge upstream main into your branch
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

### Making Changes

```bash
# 1. Create feature branch from main
git checkout main
git pull upstream main
git checkout -b feat/amazing-feature

# 2. Make your changes
# Edit files...

# 3. Run tests
pytest

# 4. Check code quality
black src tests
ruff check src tests
mypy src

# 5. Commit with conventional commit message
git add .
git commit -m "feat: Add amazing feature"

# 6. Push to your fork
git push origin feat/amazing-feature

# 7. Open Pull Request on GitHub
```

## Coding Standards

### Python Style Guide

We follow **PEP 8** with these tools:
- **Black** (formatter)
- **Ruff** (linter)
- **Mypy** (type checker)

**Run before committing:**
```bash
# Format code
black src tests

# Lint
ruff check src tests --fix

# Type check
mypy src --ignore-missing-imports
```

### Type Hints

**Required** for all functions:

```python
# ✅ Good
def scan_mods(path: Path) -> dict[str, list[ModFile]]:
    """Scan folder for mod files."""
    pass

# ❌ Bad - no type hints
def scan_mods(path):
    pass
```

### Docstrings

Use **Google-style docstrings**:

```python
def install_mod(source: Path, dest: Path, slot: int) -> bool:
    """Install mod with load order slot.
    
    Args:
        source: Path to source mod file
        dest: Destination directory
        slot: Load order slot number (1-999)
    
    Returns:
        True if installation successful, False otherwise
    
    Raises:
        FileNotFoundError: If source file doesn't exist
        PermissionError: If no write access to dest
    
    Example:
        >>> install_mod(Path("mod.package"), Path("Mods/"), 1)
        True
    """
    pass
```

### File Structure

Follow project conventions:

```
src/
├── core/           # Business logic (no UI dependencies)
├── ui/             # User interface (tkinter)
└── utils/          # Shared utilities

tests/
├── core/           # Core module tests
├── ui/             # UI tests (with mocks)
└── utils/          # Utility tests
```

### Imports

```python
# Standard library first
import json
import logging
from pathlib import Path

# Third-party libraries
import pytest
from cryptography.fernet import Fernet

# Local imports
from src.core.scanner import ModScanner
from src.utils.config_manager import ConfigManager
```

### Error Handling

```python
# ✅ Good - specific exceptions
try:
    file.read_text()
except FileNotFoundError:
    logger.error(f"File not found: {file}")
    raise
except PermissionError:
    logger.error(f"No read access: {file}")
    raise

# ❌ Bad - bare except
try:
    file.read_text()
except:
    pass
```

### Path Handling

**Always use pathlib.Path:**

```python
# ✅ Good
from pathlib import Path

def scan_folder(path: Path) -> list[Path]:
    return list(path.glob("*.package"))

# ❌ Bad - os.path
import os.path

def scan_folder(path):
    return [os.path.join(path, f) for f in os.listdir(path)]
```

## Testing Requirements

### Coverage Requirements

- **Core modules**: 95%+ coverage
- **Utils modules**: 90%+ coverage
- **UI modules**: 60%+ coverage

```bash
# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov\index.html  # Windows
```

### Writing Tests

**Test structure:**

```python
# tests/core/test_scanner.py
import pytest
from pathlib import Path
from src.core.scanner import ModScanner

class TestModScanner:
    """Test suite for ModScanner."""
    
    def test_scan_finds_package_files(self, temp_mods_dir):
        """Test scanning detects .package files."""
        # Arrange
        scanner = ModScanner()
        mod_file = temp_mods_dir / "test.package"
        mod_file.write_bytes(b"DBPF" + b"\x00" * 100)
        
        # Act
        result = scanner.scan_folder(temp_mods_dir)
        
        # Assert
        assert len(result) == 1
        assert result[0].path == mod_file
    
    def test_scan_rejects_oversized_files(self, temp_mods_dir):
        """Test files >500MB are rejected."""
        # Arrange
        scanner = ModScanner(max_size_mb=500)
        large_file = temp_mods_dir / "large.package"
        # Create 501 MB file
        
        # Act & Assert
        with pytest.raises(ValueError, match="exceeds size limit"):
            scanner.scan_folder(temp_mods_dir)
```

**Fixture usage:**

```python
@pytest.fixture
def temp_mods_dir(tmp_path):
    """Create temporary mods directory."""
    mods_dir = tmp_path / "Mods"
    mods_dir.mkdir()
    return mods_dir

def test_with_fixture(temp_mods_dir):
    # Use fixture
    assert temp_mods_dir.exists()
```

### Mocking

```python
from unittest.mock import Mock, patch

def test_game_detector_with_mock():
    """Test game detection with mocked registry access."""
    with patch('winreg.OpenKey') as mock_open:
        mock_open.return_value = Mock()
        # Test code...
```

### Test Markers

```python
# Mark slow tests
@pytest.mark.slow
def test_large_mod_collection():
    pass

# Mark integration tests
@pytest.mark.integration
def test_full_deployment_workflow():
    pass

# Mark platform-specific
@pytest.mark.windows
def test_registry_detection():
    pass

# Run specific markers
# pytest -m "not slow"  # Skip slow tests
# pytest -m integration  # Only integration tests
```

## Pull Request Process

### Before Submitting

**Checklist:**
- [ ] All tests pass: `pytest -v`
- [ ] Coverage meets requirements: `pytest --cov=src`
- [ ] Code formatted: `black src tests`
- [ ] Linting clean: `ruff check src tests`
- [ ] Type checking passes: `mypy src`
- [ ] Documentation updated (if needed)
- [ ] CHANGELOG.md updated (for notable changes)

### PR Description Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Related Issues
Closes #123
Relates to #456

## Changes Made
- Added feature X
- Fixed bug Y
- Refactored module Z

## Testing
- [ ] Tested on Windows 10/11
- [ ] Tested on macOS (Intel/ARM)
- [ ] Tested on Linux (Ubuntu 22.04)
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
(Add screenshots for UI changes)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests added/updated
- [ ] All tests pass
```

### Review Process

1. **Automated Checks:**
   - GitHub Actions runs tests on all platforms
   - Codecov checks coverage thresholds
   - Ruff checks code quality

2. **Code Review:**
   - Maintainer reviews code
   - Requests changes if needed
   - Discussion in PR comments

3. **Approval:**
   - At least 1 approval required
   - All checks must pass
   - Merge conflicts resolved

4. **Merge:**
   - Maintainer merges PR
   - Delete feature branch
   - Close related issues

### Commit Message Format

Use **Conventional Commits**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting (no logic change)
- `refactor`: Code restructuring
- `test`: Add/update tests
- `chore`: Maintenance (dependencies, build, etc.)
- `perf`: Performance improvement

**Examples:**

```bash
# Simple feature
git commit -m "feat: Add cloud backup integration"

# Bug fix with scope
git commit -m "fix(scanner): Handle empty mod files"

# Breaking change
git commit -m "feat!: Change config file format

BREAKING CHANGE: Config files from v0.x are incompatible. Run migration script."

# Multiple changes
git commit -m "feat(ui): Add drag-drop reordering

- Implement drag event handlers
- Add visual feedback during drag
- Update tests"
```

## Bug Reports

Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.yml).

**Include:**
- Clear title: "Deployment fails on Windows with long paths"
- Steps to reproduce (detailed)
- Expected vs actual behavior
- System info (OS, Python version, app version)
- Error messages (full text or screenshots)
- Logs (if available)

**Example:**

```markdown
**Bug Description:**
Deployment fails silently when mod file path exceeds 260 characters on Windows.

**Steps to Reproduce:**
1. Create deeply nested folder structure
2. Add mod with long filename
3. Click DEPLOY
4. No error shown, mod not installed

**Expected:**
Error message: "Path too long for Windows (260 char limit)"

**Actual:**
Silent failure, no feedback

**Environment:**
- OS: Windows 10 21H2
- Python: 3.10.8
- App Version: 1.0.0

**Logs:**
```
[2026-01-01 12:00:00] ERROR: FileNotFoundError: [WinError 3] The system cannot find the path specified
```
```

## Feature Requests

Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.yml).

**Include:**
- Clear problem statement
- Proposed solution
- Alternative solutions considered
- Priority (Low/Medium/High)
- Willingness to implement

**Example:**

```markdown
**Feature Request: Cloud Backup Integration**

**Problem:**
Users want to sync mod setups across multiple computers. Manual backup/restore is tedious.

**Proposed Solution:**
Integrate with cloud storage (Dropbox, Google Drive, OneDrive):
- Automatic backup to cloud on deployment
- Sync between devices
- Restore from any device

**Alternatives:**
1. Manual export/import of config + mods
2. GitHub Gists for load order only
3. Self-hosted server option

**Priority:** Medium

**I can implement this:** Yes, I have experience with cloud APIs.
```

## Questions?

- **GitHub Discussions**: [Ask here](https://github.com/yourusername/sims4-pixel-mod-manager/discussions)
- **Discord**: [Join server](https://discord.gg/your-invite)
- **Email**: your.email@example.com

---

**Thank you for contributing!** 🎉

Your efforts help make mod management better for the entire Sims 4 community.
