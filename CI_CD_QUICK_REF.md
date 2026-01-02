# CI/CD Quick Reference

## 🚀 Quick Commands

### Create Release
```bash
# 1. Update version in pyproject.toml
# 2. Commit and push
git add pyproject.toml
git commit -m "Bump version to 1.0.0"
git push origin main

# 3. Tag and push
git tag v1.0.0
git push origin v1.0.0

# CI/CD automatically builds and releases!
```

### Manual Workflow Trigger
```bash
gh workflow run ci.yml --ref main
```

### Local Pre-push Checks
```bash
pytest --cov=src --cov-report=term  # Tests
black --check src tests              # Formatting
ruff check src tests                 # Linting
mypy src --ignore-missing-imports    # Type checking
```

## 📊 Pipeline Overview

```
Push/PR → Test (9 combinations) → Lint → Build (3 platforms) → Release (tags only)
           ├─ Windows + Py3.10
           ├─ Windows + Py3.11
           ├─ Windows + Py3.12
           ├─ macOS + Py3.10
           ├─ macOS + Py3.11
           ├─ macOS + Py3.12
           ├─ Linux + Py3.10
           ├─ Linux + Py3.11
           └─ Linux + Py3.12
```

## 🔧 Jobs

| Job      | Runs On      | Duration | Depends On |
|----------|--------------|----------|------------|
| Test     | 3 OS × 3 Py  | ~5-10min | -          |
| Lint     | Ubuntu       | ~2min    | -          |
| Build    | 3 OS         | ~5-8min  | Test, Lint |
| Release  | Ubuntu       | ~2min    | Build      |
| Security | Ubuntu       | ~3min    | -          |

## 📁 Artifacts

| Name                          | Platform | Format |
|-------------------------------|----------|--------|
| Sims4ModManager-Windows.exe   | Windows  | .exe   |
| Sims4ModManager-macOS.app     | macOS    | .app   |
| Sims4ModManager-Linux         | Linux    | binary |

**Retention:** 30 days  
**Location:** Actions → Workflow Run → Artifacts

## 🏷️ Badges

```markdown
[![CI/CD Pipeline](https://github.com/USER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/USER/REPO/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/USER/REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/USER/REPO)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
```

## 🔄 Triggers

| Trigger           | Jobs Triggered          |
|-------------------|-------------------------|
| Push to main      | Test, Lint, Security    |
| Push to develop   | Test, Lint, Security    |
| Pull Request      | Test, Lint, Security    |
| Tag push (v*.*.*)| Test, Lint, Build, Release |
| Manual            | All                     |

## ✅ Checklist Before Release

- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md (optional)
- [ ] Run local tests: `pytest`
- [ ] Check formatting: `black --check src tests`
- [ ] Check linting: `ruff check src tests`
- [ ] Commit changes
- [ ] Push to main
- [ ] Create and push tag: `git tag v1.0.0 && git push origin v1.0.0`
- [ ] Wait for CI/CD (check Actions tab)
- [ ] Verify release created
- [ ] Download and test executables

## 🛠️ Troubleshooting

### Build Fails
```bash
# Check logs in GitHub Actions
# Common issues:
# - Missing dependencies: Update pyproject.toml
# - PyInstaller errors: Add --hidden-import
# - Path issues: Check --add-data syntax
```

### Tests Fail
```bash
# Run locally to debug:
pytest -v --tb=short
pytest tests/path/to/test.py -v  # Specific test
pytest -x  # Stop on first failure
```

### Coverage Below Target
```bash
# Generate HTML report:
pytest --cov=src --cov-report=html
# Open htmlcov/index.html
# Add tests for uncovered lines
```

## 📦 Dependencies

Auto-updated by Dependabot (weekly):
- GitHub Actions (Mondays 9am)
- Python packages (Mondays 10am)

## 🔐 Secrets (if needed)

For private releases or additional services:
```
Settings → Secrets → Actions → New repository secret
```

Common secrets:
- `CODECOV_TOKEN` (if private repo)
- `PYPI_TOKEN` (if publishing to PyPI)

## 📖 Documentation

- **Full Guide:** `.github/CI_CD_GUIDE.md`
- **Summary:** `CI_CD_SUMMARY.md`
- **This Card:** `CI_CD_QUICK_REF.md`

## 🎯 Coverage Targets

| Module | Target |
|--------|--------|
| Core   | 95%    |
| Utils  | 90%    |
| UI     | 60%    |
| Total  | 90%    |

## 🔗 Useful Links

- **Actions:** `github.com/USER/REPO/actions`
- **Releases:** `github.com/USER/REPO/releases`
- **Coverage:** `codecov.io/gh/USER/REPO`
- **Issues:** `github.com/USER/REPO/issues`

---

**Next Steps:**
1. Push to GitHub: `git push origin main`
2. Check Actions tab for first workflow run
3. Setup Codecov (optional for public repos)
4. Create first release: `git tag v1.0.0 && git push origin v1.0.0`
