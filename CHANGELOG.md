# Changelog

All notable changes to Sims 4 Pixel Mod Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed - 2026-01-01
- Fixed missing dependencies preventing application startup
- Fixed log directory creation with `parents=True` parameter
- Fixed duplicate `setup_logging()` function in main.py
- Fixed MainWindow.run() method call - now uses correct `root.mainloop()`
- Added requirements.txt and requirements-dev.txt for easier dependency installation

### Added - 2026-01-01
- Created QUICKSTART.md for 60-second setup guide
- Added comprehensive troubleshooting section to documentation
- Updated README.md with corrected installation instructions
- Updated INSTALLATION.md with multiple installation methods

## [1.0.0] - 2026-01-XX

### Added
- Initial release of Sims 4 Pixel Mod Manager
- Drag-and-drop mod organization with alphabetical load order
- 8-bit retro UI with NES color palette
- Security-first mod scanning (entropy analysis, magic bytes, Python syntax validation)
- Automatic backup system with CRC32 verification
- Thread-safe deployment with transactional rollback
- DBPF conflict detection
- Auto-update system via GitHub releases
- First-run setup wizard
- Multi-platform support (Windows, macOS, Linux)
- Comprehensive keyboard shortcuts (Ctrl+S/G/D/B/,, F1, F5)
- JSON logging with rotation and categorization
- Encrypted configuration storage
- DPI awareness for high-resolution displays

### Security
- File size limits (500MB default)
- Entropy threshold (7.5) blocks suspicious files
- Magic byte validation for .package and .ts4script files
- Python AST syntax validation for .py scripts
- 30-second timeout protection for file operations
- Script depth validation (max 1 level per Sims 4 requirements)

### Technical
- Python 3.10-3.12 compatible
- Single-file executable via PyInstaller
- 95%+ test coverage for core modules
- Thread-safe singleton pattern for shared state
- Observer pattern for UI updates
- CI/CD via GitHub Actions

## [Unreleased]

### Planned
- Steam/Origin game detection improvements
- Mod conflict resolution UI
- Load order profiles (save/load different configurations)
- Mod search and filtering
- Statistics dashboard (total mods, space used, deploy history)
- Dark/light theme toggle
- Localization (French, Spanish, German)
  - Mock fixtures for all test scenarios

### Technical Details
- Python 3.10+ required
- tkinter-based GUI with custom widgets
- Platform-specific config storage
- Type hints throughout codebase
- Pathlib for cross-platform path handling

### Known Issues
- Script mods (`.ts4script`) must be placed in root Mods folder
- Load order limited to 999 slots
- Mod scanning can be slow for 100+ mods (background threading implemented)

### Security Notes
- All user paths encrypted in config.json
- File operations use context managers
- Pre/post-operation hash validation
- Sandbox timeout prevents infinite loops

---

## Version History Template

### [X.Y.Z] - YYYY-MM-DD

#### Added
- New features

#### Changed
- Changes in existing functionality

#### Deprecated
- Soon-to-be removed features

#### Removed
- Removed features

#### Fixed
- Bug fixes

#### Security
- Security patches

---

## Commit Message Format

Use conventional commits for automatic changelog generation:

```
feat: Add mod conflict resolution dialog
fix: Correct load order sorting for ZZZ_ prefix
docs: Update README with installation steps
style: Format code with Black
refactor: Simplify backup restore logic
test: Add integration tests for deployment
chore: Update dependencies
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code restructuring (no behavior change)
- `perf`: Performance improvement
- `test`: Add/update tests
- `chore`: Maintenance (dependencies, build, etc.)

**Scope (optional):**
- `(ui)`: User interface
- `(core)`: Core engine
- `(security)`: Security features
- `(build)`: Build system
- `(ci)`: CI/CD pipeline

**Examples:**
```
feat(ui): Add drag-drop reordering in load order list
fix(core): Prevent crash when mods folder missing
docs: Add code signing instructions to BUILD.md
test(integration): Add full deployment workflow test
```

---

## Release Process

1. **Update Version**
   ```bash
   # Update VERSION file
   echo "1.1.0" > VERSION
   
   # Commit
   git add VERSION CHANGELOG.md
   git commit -m "chore: Bump version to 1.1.0"
   ```

2. **Create Tag**
   ```bash
   git tag -a v1.1.0 -m "Release v1.1.0"
   git push origin v1.1.0
   ```

3. **GitHub Actions automatically:**
   - Runs tests on all platforms
   - Builds executables (Windows, macOS, Linux)
   - Creates GitHub Release
   - Attaches executables to release
   - Generates changelog from commits

4. **Manual Steps (if needed):**
   - Edit release notes on GitHub
   - Add screenshots or demos
   - Pin important releases
   - Announce on community channels

---

## Links

- [GitHub Repository](https://github.com/yourusername/sims4_pixel_mod_manager)
- [Issue Tracker](https://github.com/yourusername/sims4_pixel_mod_manager/issues)
- [Releases](https://github.com/yourusername/sims4_pixel_mod_manager/releases)
- [Contributing Guide](CONTRIBUTING.md)
