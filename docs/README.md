# Documentation

## User Guide

### Installation

See main [README.md](../README.md) for installation instructions.

### First Time Setup

1. **Launch Application**
   ```bash
   python main.py
   ```

2. **Configure Paths**
   - Click Settings → Configure Paths
   - Set your Sims 4 Mods folder location
   - Typically: `Documents\Electronic Arts\The Sims 4\Mods\`

3. **Scan for Mods**
   - Click the SCAN button
   - Application will detect all installed mods
   - Review detected mods in the list

4. **Organize Load Order**
   - Drag mods to reorder within categories
   - Script mods will automatically stay at root level
   - Use categories to group similar mods

5. **Deploy**
   - Click DEPLOY to apply load order
   - Backup is created automatically
   - Launch The Sims 4 to test

## Developer Guide

### Architecture

See [.github/copilot-instructions.md](../.github/copilot-instructions.md) for detailed architecture documentation.

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_scanner.py -v

# With coverage
pytest --cov=src --cov-report=html
```

### Code Style

```bash
# Format
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

### Building Executable

```bash
pyinstaller --onefile --windowed --name="Sims4ModManager" main.py
```

## API Reference

### Core Modules

#### scanner.py
- `ModFile`: Represents a mod file with metadata
- `ModScanner`: Scans directories for mods

#### installer.py
- `ModInstaller`: Handles mod installation with verification

#### load_order.py
- `LoadOrderManager`: Manages alphabetical slot-based load order

#### security.py
- `PathEncryption`: Encrypts/decrypts config paths
- `validate_path_security()`: Validates path safety

#### conflict_detector.py
- `DBPFParser`: Parses .package files for resource IDs
- `ConflictDetector`: Detects mod conflicts

### UI Modules

#### main_window.py
- `MainWindow`: Primary application window

#### pixel_theme.py
- `PixelTheme`: 8-bit theme singleton
- `PixelAssetManager`: Programmatic asset generation

## Troubleshooting

### Common Issues

**Q: Font doesn't look right**
A: Download Press Start 2P font and place in `assets/fonts/`

**Q: Script mods not working**
A: Ensure they're installed at root Mods/ level, not in subfolders

**Q: Mod conflicts detected**
A: Load order determines priority. Later mods override earlier ones.

**Q: Encryption key lost**
A: Key is in `%LOCALAPPDATA%\Sims4ModManager\.encryption.key`. Backup this file!

## Contributing

Contributions welcome! Please:
1. Follow existing code style (Black formatter)
2. Add tests for new features
3. Update documentation
4. Submit PR with clear description
