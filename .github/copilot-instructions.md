
# Sims 4 Pixel Mod Manager - AI Coding Instructions

## Project Overview
Security-first Sims 4 mod manager with alphabetical load order and 8-bit retro UI.

**Tech Stack:** Python 3.10+ | tkinter | PyInstaller  
**Theme:** 8-bit retro pixel art aesthetic

## Architecture

### Key Components
- **Mod Scanner** (`scanner.py`): Detects/catalogs mod files with hash validation
- **Mod Installer** (`installer.py`): Handles file ops with CRC32 verification
- **Load Order Manager** (`load_order.py`): Alphabetical sorting with slot-based prefixes
- **Security Layer** (`security.py`): Path encryption, file validation, sandbox execution
- **Conflict Detector** (`conflict_detector.py`): DBPF parser for resource ID conflict analysis
- **UI Layer** (`ui/`): tkinter-based 8-bit styled interface

### UI Architecture
```
src/ui/
├── main_window.py          # Primary application window (tk.Tk subclass)
├── pixel_theme.py          # Theme engine + DPI awareness
├── widgets/
│   ├── pixel_button.py     # Custom Button with 8-bit styling
│   ├── pixel_listbox.py    # Drag-drop enabled Listbox
│   ├── chunky_frame.py     # Bordered container with pixel corners
│   ├── progress_bar.py     # Segmented 8-bit progress widget
│   └── mod_card.py         # Visual mod display component
├── dialogs/
│   ├── settings_dialog.py  # Config editor (encrypted paths)
│   ├── progress_dialog.py  # Modal deployment progress
│   ├── confirm_dialog.py   # Yes/No with 8-bit styling
│   └── about_dialog.py     # Version/credits
└── animations.py           # Smooth transitions (hover, press, pulse)
```

**UI Rules:**
- `main_window.py`: Layout + event wiring only (NO business logic)
- `widgets/`: Inherit from tk.Button/tk.Canvas for custom rendering
- `dialogs/`: tk.Toplevel subclasses for modals
- `pixel_theme.py`: Singleton pattern for colors/fonts/DPI
- `animations.py`: 60fps using `.after()` loops (16ms intervals)

### Data Flow
```
User selects mod → Hash validation → Conflict check → 
Load order assignment → Encrypted backup → Install to Mods/ → Verify hash
```

## Development Setup

### Prerequisites
- Python 3.10 or higher
- tkinter (included with Python on Windows)
- PyInstaller for building executables

### Installation
```bash
# Clone and setup
git clone <repo>
cd sims4_pixel_mod_manager
pip install -r requirements.txt
```

### Running the Project
```bash
# Development
python main.py

# Build standalone executable
pyinstaller --onefile --windowed main.py

# Run tests
pytest tests/ -v
```

## Sims 4 Modding Context

### File Types
- `.package` - Standard mod format (tuning, scripts, CAS items)
- `.ts4script` - Python script mods (require Script Mods enabled)
- `.bpi` - Blender project interchange files

### Important Paths
- **Sims 4 Mods Folder**: `Documents/Electronic Arts/The Sims 4/Mods/`
- **Game Install**: Varies by platform (Origin, Steam, EA App)
- **Tray Folder**: `Documents/Electronic Arts/The Sims 4/Tray/` (saved households/lots)

### Mod Conflicts
- Multiple mods editing the same tuning XML can conflict
- Script mods may conflict if they override the same game methods
- CAS (Create-a-Sim) items rarely conflict but can duplicate

## Coding Conventions

### Path Handling - CRITICAL
```python
from pathlib import Path

# ✅ ALWAYS use pathlib.Path
def scan_mods(path: Path) -> dict[str, list[Path]]:
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    
# ❌ NEVER use os.path
# import os.path  # Don't do this
```

### Type Hints - REQUIRED
All functions must have complete type hints:
```python
def install_mod(source: Path, dest: Path, slot: int) -> bool:
    """Install mod with load order slot."""
    pass

def get_conflicts(mod: Path) -> list[str]:
    """Returns list of conflicting mod names."""
    pass
```

### File Operations - ALWAYS Context Managers
```python
# ✅ Required pattern
with open(path, 'rb') as f:
    data = f.read()

# ❌ Never leave files open
f = open(path)  # Don't do this
```

### Path Validation - Pre-Operation
```python
def copy_mod(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Source missing: {src}")
    if not dst.parent.exists():
        dst.parent.mkdir(parents=True)
    # ... proceed with copy
```

## Security Rules - NON-NEGOTIABLE

### File Integrity
```python
import zlib

def hash_file(path: Path) -> int:
    """CRC32 hash for verification."""
    with open(path, 'rb') as f:
        return zlib.crc32(f.read())

# Hash before and after ALL file operations
pre_hash = hash_file(source)
shutil.copy2(source, dest)
post_hash = hash_file(dest)
assert pre_hash == post_hash, "File corruption detected"
```

### Scan Timeouts
- Sandbox all mod scans with 30-second timeout
- Use `multiprocessing` with `timeout` parameter
- Kill processes that exceed limit

### File Size Limits
```python
MAX_MOD_SIZE = 500 * 1024 * 1024  # 500MB

if path.stat().st_size > MAX_MOD_SIZE:
    raise ValueError(f"Mod exceeds 500MB limit: {path}")
```

### Config Encryption
```python
from cryptography.fernet import Fernet

# Encrypt all user paths in config.json
# Use Fernet symmetric encryption
# Store key in Windows Credential Manager or keyring
```

### Configuration Storage
**Platform-specific config locations:**
```python
def get_config_path() -> Path:
    """Platform-aware config directory."""
    if platform.system() == "Windows":
        # %LOCALAPPDATA%\Sims4ModManager\config.json
        base = Path(os.getenv("LOCALAPPDATA"))
    elif platform.system() == "Darwin":  # Mac
        # ~/Library/Application Support/Sims4ModManager/config.json
        base = Path.home() / "Library" / "Application Support"
    else:  # Linux
        # ~/.config/sims4modmgr/config.json
        base = Path.home() / ".config"
    
    config_dir = base / "Sims4ModManager"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"
```

**Directory structure:**
```
Windows: %LOCALAPPDATA%\Sims4ModManager\
├── config.json          # Encrypted user settings
├── .encryption.key      # Fernet key (auto-generated, NEVER commit)
├── logs/
│   ├── app.log
│   └── deploy.log
└── backups/
    └── backup_2026-01-01_160000.zip
```

**Security checklist:**
- Add `.encryption.key` to `.gitignore` (CRITICAL)
- Set permissions: `chmod 600` on Unix systems
- Backup key on first run (warn user)
- All paths in config.json MUST be encrypted with Fernet

## Load Order System

### Prefix Format
```
001_ScriptMods/
002_CAS/
003_BuildBuy/
...
999_Overrides/
ZZZ_AlwaysLast/
```

### Rules
- **Slot format**: `{slot:03d}_CategoryName/`
- **Alphabetical within slots**: Natural sort order
- **Script mods**: MUST be in root Mods/ folder (no nesting)
- **ZZZ_ prefix**: Always loads last (Sims 4 convention)

### Implementation Example
```python
def format_load_order(category: str, slot: int) -> str:
    """Returns formatted prefix."""
    return f"{slot:03d}_{category}"

def is_script_mod(path: Path) -> bool:
    """Check if mod requires root placement."""
    return path.suffix == '.ts4script'

def validate_script_placement(path: Path, mods_root: Path) -> bool:
    """Scripts cannot be nested in subfolders."""
    if is_script_mod(path):
        return path.parent == mods_root
    return True
```

## Conflict Detection - DBPF Parsing

**The Sims 4 uses DBPF (Database Packed File) format.** Conflicts occur when multiple mods modify the same resource ID.

```python
# src/core/conflict_detector.py
from struct import unpack

class DBPFParser:
    """Parse Sims 4 .package files for resource conflict detection."""
    
    DBPF_MAGIC = b'DBPF'  # File signature
    
    @staticmethod
    def parse_package(path: Path) -> set[tuple]:
        """Extract resource IDs from .package file.
        
        Returns:
            Set of (type_id, group_id, instance_id) tuples
        """
        with open(path, 'rb') as f:
            # Verify DBPF header
            magic = f.read(4)
            if magic != DBPFParser.DBPF_MAGIC:
                raise ValueError(f"Invalid .package file: {path}")
            
            # Read header
            version = unpack('<I', f.read(4))[0]
            f.seek(36)  # Skip to index position
            index_pos = unpack('<I', f.read(4))[0]
            index_count = unpack('<I', f.read(4))[0]
            
            # Jump to resource index
            f.seek(index_pos)
            resources = set()
            
            for _ in range(index_count):
                type_id = unpack('<I', f.read(4))[0]
                group_id = unpack('<I', f.read(4))[0]
                instance_id = unpack('<Q', f.read(8))[0]  # 64-bit
                resources.add((type_id, group_id, instance_id))
                f.read(8)  # Skip position/size
            
            return resources

class ConflictDetector:
    """Detect mod conflicts using resource ID analysis."""
    
    def scan_for_conflicts(self, mods: list[ModFile]) -> dict[str, list[str]]:
        """Find mods that modify the same game resources.
        
        Returns:
            Dict mapping resource IDs to conflicting mod names
        """
        resource_map: dict[tuple, list[str]] = {}
        
        for mod in mods:
            if mod.mod_type != "package":
                continue
            
            try:
                resources = DBPFParser.parse_package(mod.path)
                for resource_id in resources:
                    if resource_id not in resource_map:
                        resource_map[resource_id] = []
                    resource_map[resource_id].append(mod.path.name)
            except Exception as e:
                logging.warning(f"Failed to parse {mod.path}: {e}")
        
        # Filter to only conflicts (2+ mods touching same resource)
        conflicts = {
            f"{rid[0]:08X}_{rid[1]:08X}_{rid[2]:016X}": mods
            for rid, mods in resource_map.items()
            if len(mods) > 1
        }
        
        return conflicts
```

**When to run conflict detection:**
- After SCAN (show warnings before deployment)
- Before GENERATE (final validation)
- Performance: ~10ms/file, use background thread for 100+ mods

## Asset Management - 8-bit UI

**Generate pixel art assets programmatically with PIL (no external files needed):**

```python
# src/ui/pixel_theme.py
from PIL import Image, ImageTk, ImageDraw, ImageFont

class PixelAssetManager:
    """Generate 8-bit pixel art assets programmatically."""
    
    @staticmethod
    def create_button_surface(width: int, height: int, color: str, 
                               state: str = "normal") -> ImageTk.PhotoImage:
        """Render button with pixel-perfect borders + shadows.
        
        Args:
            state: "normal"|"hover"|"pressed"
        """
        img = Image.new("RGB", (width, height), "#000000")
        draw = ImageDraw.Draw(img)
        
        # Base fill
        draw.rectangle([4, 4, width-5, height-5], fill=color)
        
        # Chunky 4px border
        border_color = "#1D4ED8"
        draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=4)
        
        if state == "hover":
            draw.rectangle([0, 0, width-1, height-1], outline="#06B6D4", width=2)
        elif state == "pressed":
            # Shift down 2px (simulate press)
            img = img.crop((0, 2, width, height))
            img_new = Image.new("RGB", (width, height), "#000000")
            img_new.paste(img, (0, 0))
            img = img_new
        
        return ImageTk.PhotoImage(img)
```

**Custom widget pattern:**
```python
# src/ui/widgets/pixel_button.py
class PixelButton(tk.Canvas):  # Use Canvas for custom rendering
    """8-bit styled button with hover/press animations."""
    
    def __init__(self, parent, text: str, command=None, **kwargs):
        self.width = kwargs.get("width", 120)
        self.height = kwargs.get("height", 40)
        super().__init__(parent, width=self.width, height=self.height, 
                         highlightthickness=0, **kwargs)
        
        # Pre-render button states (normal/hover/pressed)
        self.surfaces = {
            "normal": PixelAssetManager.create_button_surface(
                self.width, self.height, "#1D4ED8", "normal"
            ),
            # ... hover, pressed
        }
        
        self.bind("<Enter>", lambda e: self._set_state("hover"))
        self.bind("<ButtonPress-1>", lambda e: self._set_state("pressed"))
```

**Font embedding:**
- Download Press Start 2P from Google Fonts
- Save to `assets/fonts/Press_Start_2P.ttf`
- Fallback to Courier New if missing

**Animations (60fps):**
```python
# src/ui/animations.py
def animate_hover(widget, duration_ms: int = 100):
    """Smooth scale animation using tk.after()."""
    steps = duration_ms // 16  # 60fps = ~16ms per frame
    # ... implement scale interpolation
    widget.after(16, lambda: step(n + 1))
```

## Testing Strategy
- Pytest for unit tests
- Mock file operations with `pytest-mock`
- Test hash validation on corrupted files
- Verify load order sorting with edge cases (ZZZ_, numeric prefixes)
- Test DBPF parser with real .package files
- Integration tests for full install workflow

## External Dependencies
- `cryptography`: Path encryption (Fernet)
- `pytest`: Testing framework
- `tkinter`: GUI (standard library)
- `PyInstaller`: Standalone executable builder

## Common Workflows

### Adding New Mod Detection Logic
1. Add detection to `scanner.py` with type hints
2. Hash file and validate size (<500MB)
3. Determine load order category and slot
4. Add pytest tests in `tests/test_scanner.py`
5. Update UI to display in appropriate category

### Handling Mod Installation (Security-First)
```python
def install_mod_secure(source: Path, category: str, slot: int) -> bool:
    # 1. Validate path exists
    if not source.exists():
        raise FileNotFoundError(source)
    
    # 2. Check size limit
    if source.stat().st_size > MAX_MOD_SIZE:
        raise ValueError("Mod too large")
    
    # 3. Hash source file
    source_hash = hash_file(source)
    
    # 4. Check conflicts
    conflicts = detect_conflicts(source)
    if conflicts:
        # Prompt user or auto-resolve
        pass
    
    # 5. Create destination path with load order
    dest_dir = mods_folder / format_load_order(category, slot)
    dest_dir.mkdir(exist_ok=True)
    dest_file = dest_dir / source.name
    
    # 6. Verify script placement rule
    if is_script_mod(source):
        dest_file = mods_folder / source.name  # Root only
    
    # 7. Copy with context manager
    with open(source, 'rb') as src, open(dest_file, 'wb') as dst:
        shutil.copyfileobj(src, dst)
    
    # 8. Verify hash post-copy
    dest_hash = hash_file(dest_file)
    assert source_hash == dest_hash
    
    return True
```

## Known Gotchas
- Windows file path length limits (MAX_PATH = 260) can affect deeply nested mod folders
- Sims 4 only loads mods up to 1 subfolder deep in the Mods directory
- Script mods require specific Python versions depending on game patch
- Game updates often break script mods - version checking is critical

## Resources
- [Sims 4 Studio](https://sims4studio.com/) - Primary modding tool
- [Mod The Sims](https://modthesims.info/) - Mod repository and documentation
- [Creator Musings](https://www.creatormusings.com/) - Modding tutorials

---
*This file should be updated as the project evolves to reflect actual architectural decisions and patterns.*
