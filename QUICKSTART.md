# 🚀 Quick Start Guide

## Get Up and Running in 60 Seconds

### Prerequisites
- Python 3.10 or higher installed
- Git (for cloning the repository)

### Installation

#### Step 1: Clone the Repository
```bash
git clone <your-repo-url>
cd sims4_pixel_mod_manager
```

#### Step 2: Create Virtual Environment
```bash
python -m venv venv
```

#### Step 3: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
venv\Scripts\activate
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

#### Step 4: Install Dependencies
```bash
pip install pillow psutil watchdog cryptography
```

**Or install from pyproject.toml:**
```bash
pip install -e .
```

#### Step 5: Run the Application
```bash
python main.py
```

That's it! The app should launch with a splash screen and the main UI.

---

## Common Issues

### Issue: "ModuleNotFoundError: No module named 'psutil'"
**Solution:** Install dependencies using pip:
```bash
pip install pillow psutil watchdog cryptography
```

### Issue: "FileNotFoundError: logs directory"
**Solution:** Already fixed in latest version. The app auto-creates the log directory.

### Issue: "AttributeError: 'MainWindow' object has no attribute 'run'"
**Solution:** Already fixed in latest version. Uses `root.mainloop()` instead.

### Issue: Update check fails with 404 error
**Solution:** This is expected if GitHub repository URL isn't configured. Update in `main.py`:
```python
updater = Updater(
    owner="your-github-username",
    repo="sims4_pixel_mod_manager"
)
```

---

## First Run Setup

When you launch the app for the first time:

1. **Splash Screen** appears with loading progress
2. **Main Window** opens with 8-bit retro UI
3. **Click Settings** (gear icon) to configure:
   - **Mods Library**: Where you download mods to
   - **Sims 4 Mods Folder**: Usually `Documents/Electronic Arts/The Sims 4/Mods/`
   - **ActiveMods Folder**: Staging area for organized mods

---

## Basic Workflow

1. **SCAN** - Click to scan your mods library
2. **REVIEW** - Check detected mods and any conflicts
3. **GENERATE** - Organize mods with load order prefixes
4. **DEPLOY** - Copy to Sims 4 Mods folder

---

## Development Setup

### Install Dev Dependencies
```bash
pip install -e ".[dev]"
```

This includes:
- pytest (testing framework)
- pytest-cov (coverage reporting)
- black (code formatter)
- ruff (linter)
- mypy (type checker)

### Run Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Build Executable
```bash
python build.py
```

---

## Directory Structure
```
sims4_pixel_mod_manager/
├── main.py                 # Entry point
├── pyproject.toml          # Dependencies and metadata
├── VERSION                 # Version file
├── src/
│   ├── core/              # Core engine (scanner, installer, load order)
│   ├── ui/                # UI components (tkinter widgets)
│   └── utils/             # Utilities (logging, config, backup)
├── tests/                 # Test suite
├── docs/                  # Documentation
├── logs/                  # Auto-generated logs
└── venv/                  # Virtual environment (auto-created)
```

---

## What's Next?

- **Configure paths** in Settings to match your system
- **Add mods** to your Mods Library folder
- **Scan and deploy** using the main workflow
- **Check logs** if you encounter issues: `logs/app.log`

For detailed documentation, see:
- [README.md](README.md) - Full features and documentation
- [docs/USER_GUIDE.md](docs/USER_GUIDE.md) - Complete user manual
- [docs/DEVELOPER.md](docs/DEVELOPER.md) - Contributing and development guide

---

## Support

Having issues? Check:
1. **Logs folder**: `logs/app.log` for detailed error messages
2. **GitHub Issues**: Report bugs or request features
3. **Documentation**: Full guides in the `docs/` folder

Happy modding! 🎮✨
