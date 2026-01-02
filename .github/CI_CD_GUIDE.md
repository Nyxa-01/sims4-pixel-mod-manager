# CI/CD Pipeline Documentation

## Overview

Automated continuous integration and deployment pipeline using GitHub Actions.

## Pipeline Jobs

### 1. Test Job

**Runs on:** All platforms (Windows, macOS, Linux)  
**Python versions:** 3.10, 3.11, 3.12  
**Matrix:** 9 total combinations (3 OS × 3 Python versions)

**Steps:**
1. Checkout code
2. Set up Python with pip caching
3. Install dependencies (`pip install -e ".[dev]"`)
4. Run pytest with coverage (`pytest --cov=src --cov-report=xml`)
5. Upload coverage to Codecov (Python 3.11 on Ubuntu only)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

### 2. Lint Job

**Runs on:** Ubuntu (latest)  
**Python version:** 3.11

**Steps:**
1. Checkout code
2. Set up Python
3. Install dependencies
4. Check formatting with Black (`black --check --diff src tests`)
5. Lint with Ruff (`ruff check src tests`)
6. Type check with Mypy (`mypy src --ignore-missing-imports`)

**Fail conditions:**
- Black formatting violations
- Ruff linting errors
- Mypy errors (informational only, marked `continue-on-error: true`)

### 3. Build Job

**Runs on:** All platforms (Windows, macOS, Linux)  
**Python version:** 3.11  
**Depends on:** Test and Lint jobs must pass

**Steps:**
1. Checkout code
2. Set up Python
3. Install dependencies + PyInstaller
4. Create placeholder icon if missing
5. Build with PyInstaller (platform-specific commands)
6. Upload artifacts to GitHub

**Artifacts:**
- `Sims4ModManager-Windows.exe` (Windows)
- `Sims4ModManager-macOS.app` (macOS)
- `Sims4ModManager-Linux` (Linux)

**Retention:** 30 days

### 4. Release Job

**Runs on:** Ubuntu (latest)  
**Triggers:** Git tags matching `v*.*.*` pattern  
**Depends on:** Build job must pass  
**Permissions:** `contents: write` for creating releases

**Steps:**
1. Checkout code with full history (`fetch-depth: 0`)
2. Download all build artifacts
3. Generate changelog from git commits
4. Create GitHub Release with:
   - Release title: `Release v1.0.0`
   - Changelog body
   - All platform executables attached

**Changelog format:**
```markdown
## What's Changed
- Commit message 1 (abc123)
- Commit message 2 (def456)

**Full Changelog**: https://github.com/user/repo/compare/v0.9.0...v1.0.0
```

### 5. Security Scan Job

**Runs on:** Ubuntu (latest)  
**Python version:** 3.11

**Steps:**
1. Checkout code
2. Install security tools (`safety`, `bandit`)
3. Check dependencies for known vulnerabilities (`safety check`)
4. Run Bandit security linter (`bandit -r src`)
5. Upload security reports as artifacts

**Note:** Marked `continue-on-error: true` for informational purposes

## PyInstaller Build Commands

### Windows
```powershell
pyinstaller --onefile --windowed `
  --icon=assets/icon.ico `
  --add-data "assets;assets" `
  --name Sims4ModManager `
  --clean `
  main.py
```

### macOS / Linux
```bash
pyinstaller --onefile --windowed \
  --icon=assets/icon.ico \
  --add-data "assets:assets" \
  --name Sims4ModManager \
  --clean \
  main.py
```

**Key options:**
- `--onefile` - Bundle into single executable
- `--windowed` - No console window (GUI only)
- `--icon` - Application icon
- `--add-data` - Include assets folder
- `--name` - Executable name
- `--clean` - Clean cache before building

## Triggering Workflows

### Automatic Triggers

**On Push:**
```bash
git push origin main          # Triggers test + lint jobs
git push origin develop       # Triggers test + lint jobs
```

**On Pull Request:**
```bash
gh pr create --base main      # Triggers test + lint jobs
```

**On Tag Push (Release):**
```bash
git tag v1.0.0
git push origin v1.0.0        # Triggers all jobs + release
```

### Manual Trigger

Via GitHub UI:
1. Go to **Actions** tab
2. Select **CI/CD Pipeline** workflow
3. Click **Run workflow**
4. Choose branch
5. Click **Run workflow** button

Via CLI:
```bash
gh workflow run ci.yml --ref main
```

## Badges

Add these badges to README.md:

```markdown
[![CI/CD Pipeline](https://github.com/USER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/USER/REPO/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/USER/REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/USER/REPO)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
```

**Replace `USER/REPO` with your GitHub username and repository name.**

## Coverage Reporting

### Codecov Setup

1. Sign up at [codecov.io](https://codecov.io)
2. Connect your GitHub repository
3. No token required for public repositories
4. Coverage automatically uploaded after tests run

### Coverage Configuration

See `.codecov.yml`:
- **Project target:** 90%
- **Patch target:** 85%
- **Ignored:** Tests, `__init__.py`, setup files

### Viewing Coverage

- **Web:** Visit `https://codecov.io/gh/USER/REPO`
- **PR Comments:** Codecov bot comments on pull requests
- **Badge:** Shows current coverage percentage

## Release Process

### Semantic Versioning

Follow [semver.org](https://semver.org):
- `v1.0.0` - Major release (breaking changes)
- `v1.1.0` - Minor release (new features)
- `v1.1.1` - Patch release (bug fixes)

### Creating a Release

1. **Update version** in `pyproject.toml`:
   ```toml
   version = "1.0.0"
   ```

2. **Commit changes:**
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 1.0.0"
   git push origin main
   ```

3. **Create and push tag:**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

4. **Wait for CI/CD:**
   - Tests run on all platforms
   - Linting checks pass
   - Executables built for Windows/Mac/Linux
   - GitHub Release created automatically

5. **Verify release:**
   - Go to `https://github.com/USER/REPO/releases`
   - Check changelog is correct
   - Download and test executables

## Troubleshooting

### Build Fails on PyInstaller

**Issue:** Missing dependencies or import errors

**Solution:**
1. Add hidden imports to `.spec` file:
   ```python
   hiddenimports=['pkg_name']
   ```
2. Or use `--hidden-import` flag:
   ```bash
   pyinstaller --hidden-import=pkg_name ...
   ```

### Tests Fail on Specific Platform

**Issue:** Platform-specific path or behavior differences

**Solution:**
1. Use `platform.system()` checks in code
2. Mock platform in tests with `@pytest.mark.windows`
3. Skip platform-specific tests:
   ```python
   @pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
   ```

### Coverage Upload Fails

**Issue:** Codecov authentication or network error

**Solution:**
1. Check Codecov is configured for repository
2. Verify `codecov/codecov-action@v3` is latest version
3. Check `coverage.xml` file was generated
4. Review Codecov status at [status.codecov.io](https://status.codecov.io)

### Release Not Created

**Issue:** Tag doesn't trigger release workflow

**Solution:**
1. Verify tag matches pattern `v*.*.*` exactly
2. Check workflow file uses `startsWith(github.ref, 'refs/tags/v')`
3. Ensure `contents: write` permission is set
4. Review Actions logs for error messages

### Artifact Upload Fails

**Issue:** Build artifacts not found or path incorrect

**Solution:**
1. Check `dist/` directory contents in logs
2. Verify PyInstaller completed successfully
3. Update artifact path in workflow:
   ```yaml
   path: dist/Sims4ModManager*
   ```

## Local Testing

Before pushing, test locally:

### Run Tests
```bash
pytest --cov=src --cov-report=term
```

### Check Formatting
```bash
black --check src tests
```

### Run Linter
```bash
ruff check src tests
```

### Type Check
```bash
mypy src --ignore-missing-imports
```

### Build Executable
```bash
pip install pyinstaller
pyinstaller main.spec  # Or use command from workflow
```

## CI/CD Best Practices

1. **Keep workflows fast** - Use caching for dependencies
2. **Fail fast** - Use `fail-fast: false` in matrix for comprehensive results
3. **Use artifacts** - Save build outputs for debugging
4. **Tag releases** - Use semantic versioning for tags
5. **Update dependencies** - Keep GitHub Actions versions current
6. **Monitor coverage** - Maintain 90%+ test coverage
7. **Review security** - Address Bandit/Safety warnings
8. **Document changes** - Write clear commit messages for changelogs

## Maintenance

### Updating Workflows

1. Edit `.github/workflows/ci.yml`
2. Test changes on feature branch first
3. Create PR to main branch
4. Review workflow results in PR checks
5. Merge when all checks pass

### Updating Dependencies

GitHub Dependabot automatically creates PRs for:
- GitHub Actions version updates
- Python package security updates

Review and merge Dependabot PRs regularly.

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyInstaller Documentation](https://pyinstaller.org)
- [Codecov Documentation](https://docs.codecov.com)
- [Semantic Versioning](https://semver.org)
