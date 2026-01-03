<div align="center">

# 🎮 Sims 4 Pixel Mod Manager

### *Security-first mod management with 8-bit retro aesthetics*

[![CI/CD Pipeline](https://github.com/yourusername/sims4-pixel-mod-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/sims4-pixel-mod-manager/actions)
[![Code Coverage](https://img.shields.io/badge/coverage-85.78%25-brightgreen)](https://github.com/yourusername/sims4-pixel-mod-manager)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/badge/linter-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![Downloads](https://img.shields.io/github/downloads/yourusername/sims4-pixel-mod-manager/total.svg)](https://github.com/yourusername/sims4-pixel-mod-manager/releases)

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Documentation](#-documentation) • [Contributing](#-contributing)

![Demo](docs/assets/demo.gif)

*Drag. Drop. Deploy. Manage your Sims 4 mods with confidence.*

</div>

---

## 🌟 Why Pixel Mod Manager?

Managing Sims 4 mods shouldn't be a chore. **Pixel Mod Manager** brings security, organization, and a touch of nostalgia to your modding workflow:

- 🛡️ **No More Broken Saves**: Every mod is verified before installation
- 📂 **Crystal Clear Organization**: Alphabetical load order that just works
- ⚡ **Lightning Fast**: Scan 100+ mods in seconds
- 🎨 **Beautiful UI**: 8-bit pixel art meets modern functionality
- 🔍 **Smart Conflict Detection**: Know which mods play nicely together
- 💾 **One-Click Backups**: Restore your setup in seconds

## ✨ Features

### 🔒 Security-First Architecture
- **CRC32 Hash Verification**: Every file operation validated
- **Sandboxed Scanning**: 30-second timeout prevents infinite loops
- **Encrypted Configuration**: Your paths protected with Fernet encryption
- **High-Entropy Detection**: Automatically flags suspicious files
- **500MB Size Limits**: Protection against oversized malicious mods

### 📋 Intelligent Load Order Management
- **Alphabetical Slots**: 001-999 prefix system for predictable loading
- **Drag-and-Drop**: Reorder mods visually with instant feedback
- **Category Organization**: Script Mods, CAS, Build/Buy, Gameplay, etc.
- **ZZZ_ Override Support**: Sims 4 convention for last-load mods
- **Script Mod Detection**: Auto-places .ts4script files in root folder

### ⚠️ Advanced Conflict Detection
- **DBPF Parser**: Analyzes .package file resource IDs
- **Real-Time Warnings**: See conflicts before deployment
- **Resource Mapping**: Shows which mods modify the same game files
- **Pre-Deployment Validation**: Catches issues early

### 🎨 8-bit Retro Interface
- **Pixel-Perfect UI**: Custom tkinter widgets with chunky borders
- **Press Start 2P Font**: Authentic retro typography
- **Smooth Animations**: 60fps hover effects and transitions
- **DPI-Aware**: Crisp rendering on high-resolution displays
- **Theme Engine**: Consistent 8-bit aesthetic throughout

### 🔄 Cross-Platform Support
- **Windows**: Full Origin/Steam/EA App detection via registry
- **macOS**: Steam path detection, .app bundle distribution
- **Linux**: Steam Proton support, DEB package format

### 💾 Backup & Restore System
- **Encrypted Backups**: ZIP archives with manifest.json
- **One-Click Restore**: Rollback to any previous state
- **Automatic Backups**: Before every deployment
- **Incremental Snapshots**: Only changed files backed up
- **Backup History**: Track all restore points

### ⚡ Performance Optimized
- **Background Threading**: UI never freezes during long operations
- **Progress Tracking**: Real-time feedback on scans and deployments
- **Lazy Loading**: Assets loaded on-demand
- **Efficient Caching**: Reduce redundant file operations
- **< 500ms Response**: Instant UI feedback guaranteed

## 📦 Installation

### Option 1: Standalone Executable (Recommended)

Download the latest version for your platform:

| Platform | Download | Size |
|----------|----------|------|
| 🪟 **Windows** | [Sims4ModManager.exe](https://github.com/yourusername/sims4-pixel-mod-manager/releases/latest) | ~40 MB |
| 🍎 **macOS** | [Sims4ModManager.dmg](https://github.com/yourusername/sims4-pixel-mod-manager/releases/latest) | ~45 MB |
| 🐧 **Linux** | [Sims4ModManager.deb](https://github.com/yourusername/sims4-pixel-mod-manager/releases/latest) | ~35 MB |

**Windows:**
```powershell
# Download and run installer
.\Sims4ModManager-Setup.exe

# Or portable executable
.\Sims4ModManager.exe
```

**macOS:**
```bash
# Mount DMG and drag to Applications
open Sims4ModManager.dmg
# Or use installer

# First run: Allow in System Preferences > Security
```

**Linux (Ubuntu/Debian):**
```bash
# Install DEB package
sudo dpkg -i sims4modmanager_1.0.0_amd64.deb

# Run from terminal
sims4modmanager

# Or from application menu
```

### Option 2: From Source (Developers)

#### Quick Install (60 seconds)
See [QUICKSTART.md](QUICKSTART.md) for the fastest setup method.

#### Detailed Installation
```bash
# Clone repository
git clone https://github.com/yourusername/sims4-pixel-mod-manager.git
cd sims4-pixel-mod-manager

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or install with development dependencies
pip install -r requirements-dev.txt

# Run application
python main.py
```

**Alternative: Install from pyproject.toml**
```bash
# Install as editable package with all dependencies
pip install -e .

# With dev dependencies
pip install -e ".[dev]"
```

**System Requirements:**
- Python 3.10 or higher
- 2 GB RAM
- 100 MB disk space
- Windows 10+, macOS 10.13+, or Linux (Ubuntu 20.04+)

## 🚀 Quick Start

### First Launch Setup

1. **Launch the application**
   - Windows: Double-click `Sims4ModManager.exe`
   - macOS: Open from Applications folder
   - Linux: Run `sims4modmanager` in terminal

2. **Configure paths** (Settings → Preferences)
   - **Mods Folder**: `Documents/Electronic Arts/The Sims 4/Mods`
   - **Incoming Folder**: Where you download new mods
   - **Backup Folder**: Safe location for backups

3. **Scan your existing mods** (Optional)
   - Click **SCAN ACTIVE MODS** to catalog currently installed mods
   - Review detected conflicts

4. **Add new mods**
   - Click **SCAN INCOMING** to find downloaded mods
   - Drag mods to appropriate load order slots
   - Click **GENERATE STRUCTURE** to preview organization

5. **Deploy**
   - Click **DEPLOY** to install mods with automatic backup
   - Watch progress and verify success

### Basic Workflow

```
📥 Download Mod → 📂 Scan Incoming → 🎯 Assign to Slot → 
🏗️ Generate Structure → 🚀 Deploy → ✅ Backup Created
```

## 📖 Usage

### Managing Load Order

**Understanding Slots:**
```
001_ScriptMods/     ← MUST be in root Mods/ (Sims 4 requirement)
002_CAS/            ← Create-a-Sim items (clothes, hair, etc.)
003_BuildBuy/       ← Furniture, build mode objects
004_Gameplay/       ← Tuning mods, gameplay changes
...
999_Overrides/      ← Major overhauls
ZZZ_AlwaysLast/     ← Load these last (Sims 4 convention)
```

**Best Practices:**
1. **Script mods** (.ts4script) → Root folder only (001_ScriptMods/)
2. **CAS items** → 002_CAS/ (rarely conflict)
3. **Tuning mods** → Higher slots (load order matters)
4. **UI mods** → Later slots (override default UI)
5. **ZZZ_ prefix** → Reserved for mods that must load last

### Conflict Resolution

When conflicts are detected:

1. **Review Warning**: Red indicator shows conflicting mods
2. **Check Details**: Click to see which resource IDs overlap
3. **Choose Strategy**:
   - **Keep Both**: If mods modify different aspects
   - **Remove One**: If functionality duplicates
   - **Load Order**: Place override mod later (higher slot)
4. **Test In-Game**: Some conflicts are harmless

**Common Conflict Types:**
- ✅ **Safe**: Different CAS items with same name
- ⚠️ **Warning**: Two mods editing same tuning XML
- ❌ **Critical**: Script mods overriding same game methods

### Backup & Restore

**Create Backup:**
```
Settings → Create Backup → Enter description → Save
```

Backups include:
- All installed mods
- Load order configuration
- Manifest with timestamps
- Encrypted with your config key

**Restore Backup:**
```
Settings → Restore Backup → Select backup → Confirm
```

**Automatic Backups:**
- Before every deployment
- Stored in configured backup folder
- Named with timestamp: `backup_2026-01-01_160000.zip`

### Advanced Features

**Hot Reload** (Linux/macOS):
- Use watchdog to detect new mods
- Automatically refreshes incoming folder

**Batch Operations:**
- Select multiple mods (Ctrl+Click)
- Assign all to same slot
- Bulk enable/disable

**Export Load Order:**
```
File → Export Load Order → save_as_text.txt
```

Share with friends or keep as reference!

## 🛠️ Troubleshooting

### Common Issues

#### Application Won't Start

**Windows:**
```powershell
# Check Python version
python --version  # Should be 3.10+

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Run with verbose logging
python main.py --log-level DEBUG
```

**macOS:**
```bash
# Remove quarantine attribute
xattr -cr /Applications/Sims4ModManager.app

# Grant permissions
System Preferences → Security & Privacy → Allow
```

**Linux:**
```bash
# Install missing dependencies
sudo apt install python3-tk

# Check executable permissions
chmod +x /usr/bin/sims4modmanager
```

#### Mods Folder Not Detected

1. **Manual Configuration**: Settings → Set path manually
2. **Check Game Install**:
   - Origin/EA App: `C:\Program Files\EA Games\The Sims 4`
   - Steam: `C:\Program Files (x86)\Steam\steamapps\common\The Sims 4`
3. **Verify Mods Folder Exists**: `Documents\Electronic Arts\The Sims 4\Mods`

#### Deployment Fails

**Error: "Permission Denied"**
- Close The Sims 4 before deployment
- Run as administrator (Windows)
- Check file permissions

**Error: "Checksum Mismatch"**
- File corruption detected
- Re-download mod from trusted source
- Check disk for errors

**Error: "Deployment Rolled Back"**
- Automatic rollback on failure
- Check logs in `logs/deploy.log`
- Restore from backup if needed

#### Conflicts Not Detected

- DBPF parser only works on .package files
- Script mods conflicts require manual review
- Some conflicts only apparent in-game

#### Performance Issues

**Slow Scanning:**
```python
# Reduce max mods per scan
# Edit config: "max_scan_mods": 50
```

**UI Freezing:**
- Update to latest version (threading improvements)
- Close other resource-intensive applications
- Check system resources (RAM, CPU)

### Error Messages Explained

| Error | Meaning | Solution |
|-------|---------|----------|
| `FileNotFoundError` | Mod file missing | Re-scan incoming folder |
| `PermissionError` | No write access | Close game, run as admin |
| `HashMismatchError` | File corrupted | Re-download mod |
| `TimeoutError` | Scan took too long | Reduce mods per scan |
| `ConflictError` | Resource ID collision | Resolve or ignore conflict |

### Getting Help

1. **Check Docs**: [User Guide](docs/USER_GUIDE.md) • [FAQ](docs/USER_GUIDE.md#faq)
2. **Search Issues**: [GitHub Issues](https://github.com/yourusername/sims4-pixel-mod-manager/issues)
3. **Ask Community**: [Discord](https://discord.gg/your-server) • [Reddit](https://reddit.com/r/sims4modmanager)
4. **Report Bug**: Use [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml)

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [User Guide](docs/USER_GUIDE.md) | Complete usage manual with screenshots |
| [Developer Docs](docs/DEVELOPER.md) | Architecture and API documentation |
| [Build Guide](BUILD.md) | Building executables from source |
| [Contributing](CONTRIBUTING.md) | How to contribute to the project |
| [Changelog](CHANGELOG.md) | Version history and breaking changes |
| [CI/CD Guide](.github/CI_CD_GUIDE.md) | Continuous integration setup |

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Quick Contribution

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feat/amazing-feature`
3. **Commit** changes: `git commit -m 'feat: Add amazing feature'`
4. **Push** to branch: `git push origin feat/amazing-feature`
5. **Open** a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/sims4-pixel-mod-manager.git
cd sims4-pixel-mod-manager

# Add upstream remote
git remote add upstream https://github.com/yourusername/sims4-pixel-mod-manager.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest -v

# Check code quality
black src tests
ruff check src tests
mypy src
```

### Contribution Guidelines

- ✅ **Tests Required**: 90%+ coverage for new code
- ✅ **Code Style**: Black + Ruff formatting
- ✅ **Type Hints**: All functions must have type annotations
- ✅ **Documentation**: Docstrings for public APIs
- ✅ **Commit Format**: Use [Conventional Commits](https://www.conventionalcommits.org/)

**Commit Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Formatting (no logic change)
- `refactor:` Code restructuring
- `test:` Add/update tests
- `chore:` Maintenance

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

## 🏆 Credits

### Core Team
- **[Your Name]** - *Creator & Lead Developer* - [@yourusername](https://github.com/yourusername)

### Special Thanks
- **Press Start 2P Font** - [codeman38](https://www.fontspace.com/codeman38)
- **Sims 4 Community** - Testing and feedback
- **DBPF Format Documentation** - [SimsWiki](http://simswiki.info/)

### Built With
- [Python 3.10+](https://python.org) - Core language
- [tkinter](https://docs.python.org/3/library/tkinter.html) - GUI framework
- [Pillow](https://python-pillow.org/) - Image processing
- [cryptography](https://cryptography.io/) - Encryption
- [psutil](https://github.com/giampaolo/psutil) - Process management
- [pytest](https://pytest.org/) - Testing framework
- [PyInstaller](https://pyinstaller.org/) - Executable building

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2026 PixelWorks

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

## ⚠️ Disclaimer

**This is an unofficial tool and is not affiliated with Electronic Arts or Maxis.**

- Use at your own risk
- Always backup your saves before modding
- Mod authors retain rights to their creations
- Check mod licenses before redistribution

## 🌟 Support the Project

If you find this tool useful, consider:

- ⭐ **Star the repository** on GitHub
- 🐛 **Report bugs** to help improve stability
- 💡 **Suggest features** via GitHub Discussions
- 🤝 **Contribute code** through pull requests
- 📢 **Share with friends** in the Sims community

## 📮 Contact

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/sims4-pixel-mod-manager/issues)
- **GitHub Discussions**: [Ask questions or share ideas](https://github.com/yourusername/sims4-pixel-mod-manager/discussions)
- **Email**: your.email@example.com

---

<div align="center">

**Made with 💚 and ☕ for the Sims 4 community**

[⬆ Back to Top](#-sims-4-pixel-mod-manager)

</div>
