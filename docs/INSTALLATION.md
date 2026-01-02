# Installation Guide

## System Requirements

### Minimum
- **OS**: Windows 10/11, macOS 11+, Ubuntu 20.04+
- **RAM**: 4GB
- **Storage**: 100MB + space for backups
- **Python**: 3.10+ (if running from source)

### Recommended
- **OS**: Windows 11 or macOS 13+
- **RAM**: 8GB+
- **Storage**: 1GB+ for backups
- **Display**: 1920x1080 or higher

---

## Installation Methods

### Option 1: Standalone Executable (Recommended)

**Windows**:
1. Download `Sims4ModManager-v1.0.0-Windows.exe` from [Releases](https://github.com/yourusername/sims4-mod-manager/releases)
2. Run the executable
3. Follow the first-run setup wizard

**macOS**:
1. Download `Sims4ModManager-v1.0.0-macOS.dmg`
2. Open DMG and drag to Applications
3. Right-click → Open (first time only, to bypass Gatekeeper)
4. Follow the setup wizard

**Linux**:
1. Download `Sims4ModManager-v1.0.0-Linux.AppImage`
2. Make executable: `chmod +x Sims4ModManager-v1.0.0-Linux.AppImage`
3. Run: `./Sims4ModManager-v1.0.0-Linux.AppImage`

---

### Option 2: From Source

**Requirements**:
- Python 3.10-3.12
- pip

**Quick Start** (see [QUICKSTART.md](../QUICKSTART.md) for detailed guide):

**Steps**:
```bash
# Clone repository
git clone https://github.com/yourusername/sims4-mod-manager.git
cd sims4-mod-manager

# Create virtual environment
python -m venv venv

# Activate (Windows PowerShell)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies (Option 1: using requirements.txt)
pip install -r requirements.txt

# Install dependencies (Option 2: using pyproject.toml)
pip install -e .

# Install with dev tools
pip install -r requirements-dev.txt

# Run application
python main.py
```

**Troubleshooting**:
- If you get `ModuleNotFoundError`, make sure you've installed dependencies
- Required packages: `pillow`, `psutil`, `watchdog`, `cryptography`
- See [QUICKSTART.md](../QUICKSTART.md) for common issues and solutions

---

## First-Run Setup

On first launch, the setup wizard will guide you through:

1. **Welcome** - Overview and features

2. **Path Configuration**:
   - **Game Install**: Auto-detected or browse manually
     - Windows: `C:\Program Files\Electronic Arts\The Sims 4`
     - macOS: `/Applications/The Sims 4.app`
   - **Mods Folder**: Usually `Documents/Electronic Arts/The Sims 4/Mods`

3. **Options**:
   - Enable auto-backup before deployment
   - Check for updates on startup
   - Close game automatically before deployment

---

## Configuration

**Configuration is stored in**:
- Windows: `%USERPROFILE%\.sims4_mod_manager\config.json`
- macOS/Linux: `~/.sims4_mod_manager/config.json`

**Logs are stored in**:
- Windows: `%USERPROFILE%\.sims4_mod_manager\logs\`
- macOS/Linux: `~/.sims4_mod_manager/logs/`

---

## Troubleshooting

### "Game path not found"
- Manually browse to your Sims 4 installation folder
- Look for `Game/Bin/TS4_x64.exe` (Windows) or `The Sims 4.app` (macOS)

### "Permission denied" errors
- **Windows**: Run as Administrator (right-click → Run as Administrator)
- **macOS/Linux**: Ensure you have write permissions to Mods folder

### "DLL load failed" (Windows)
- Install [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Application won't start
- Check logs in `~/.sims4_mod_manager/logs/error.log`
- Report issues on [GitHub Issues](https://github.com/yourusername/sims4-mod-manager/issues)

---

## Uninstallation

### Standalone Executable
- **Windows**: Delete executable + `%USERPROFILE%\.sims4_mod_manager`
- **macOS**: Remove from Applications + `~/.sims4_mod_manager`
- **Linux**: Delete AppImage + `~/.sims4_mod_manager`

### From Source
```bash
# Deactivate venv
deactivate

# Remove directory
rm -rf sims4-mod-manager
```

**Note**: Uninstalling does NOT remove your mods or game files.
