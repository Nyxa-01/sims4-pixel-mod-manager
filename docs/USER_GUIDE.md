# Sims 4 Pixel Mod Manager - User Guide

Complete step-by-step guide for managing your Sims 4 mods with confidence.

## Table of Contents

1. [Getting Started](#getting-started)
2. [First-Time Setup](#first-time-setup)
3. [Understanding the Interface](#understanding-the-interface)
4. [Managing Mods](#managing-mods)
5. [Load Order Best Practices](#load-order-best-practices)
6. [Backup & Restore](#backup--restore)
7. [Security Features](#security-features)
8. [Advanced Features](#advanced-features)
9. [FAQ](#faq)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### System Requirements

**Minimum:**
- Windows 10 / macOS 10.13 / Ubuntu 20.04
- Python 3.10+ (if running from source)
- 2 GB RAM
- 100 MB disk space

**Recommended:**
- Windows 11 / macOS 12+ / Ubuntu 22.04
- 4 GB RAM
- 500 MB disk space (for backups)
- The Sims 4 installed

### Installation

#### Windows
1. Download `Sims4ModManager-Setup.exe` from [Releases](https://github.com/yourusername/sims4-pixel-mod-manager/releases)
2. Run installer (Windows Defender may show warning - click "More info" → "Run anyway")
3. Follow installation wizard
4. Launch from Start Menu or Desktop shortcut

**First Run:**
- Windows may ask for permissions - click "Allow"
- Antivirus might scan the file (this is normal)

#### macOS
1. Download `Sims4ModManager.dmg`
2. Open DMG and drag app to Applications folder
3. First launch: Right-click app → "Open" (bypass Gatekeeper)
4. Grant permissions when prompted

**If "App is damaged" error:**
```bash
xattr -cr /Applications/Sims4ModManager.app
```

#### Linux (Debian/Ubuntu)
```bash
# Download DEB package
wget https://github.com/yourusername/sims4-pixel-mod-manager/releases/latest/sims4modmanager_1.0.0_amd64.deb

# Install
sudo dpkg -i sims4modmanager_1.0.0_amd64.deb

# Run from terminal
sims4modmanager

# Or find in application menu under "Games"
```

---

## First-Time Setup

### Initial Configuration

When you first launch, you'll be greeted with the setup wizard:

#### Step 1: Welcome Screen
- Introduction to features
- Link to this user guide
- Click **Next** to continue

#### Step 2: Locate Sims 4 Installation

The app will auto-detect your game install:

**Windows:**
- Origin/EA App: `C:\Program Files\EA Games\The Sims 4`
- Steam: `C:\Program Files (x86)\Steam\steamapps\common\The Sims 4`

**macOS:**
- Origin: `/Applications/The Sims 4.app`
- Steam: `~/Library/Application Support/Steam/steamapps/common/The Sims 4`

**Linux:**
- Steam Proton: `~/.steam/steam/steamapps/common/The Sims 4`

**Manual Selection:**
If auto-detection fails, click **Browse** and navigate to your game folder.

#### Step 3: Configure Folders

**Mods Folder** (Required):
- Default: `Documents/Electronic Arts/The Sims 4/Mods/`
- Where mods will be installed
- Must exist before deployment

**Incoming Folder** (Recommended):
- Where you download new mods
- Default: `Downloads/Sims4Mods/`
- Create if it doesn't exist

**Backup Folder** (Recommended):
- Where automatic backups are stored
- Default: `Documents/Sims4ModBackups/`
- Minimum 1 GB free space recommended

#### Step 4: Security Settings

**Encryption Key:**
- Automatically generated
- Protects your folder paths
- Stored securely in system keychain (Windows/macOS) or keyring (Linux)

**Scan Timeout:**
- Default: 30 seconds
- Prevents hanging on problematic mods
- Increase for very large mods (rare)

**File Size Limit:**
- Default: 500 MB per mod
- Protection against malicious files
- Most mods are < 50 MB

Click **Finish** to complete setup!

---

## Understanding the Interface

### Main Window Layout

```
┌──────────────────────────────────────────────────────┐
│  [SCAN] [GENERATE] [DEPLOY] [BACKUP]    [SETTINGS]  │ ← Action Bar
├──────────────────────────────────────────────────────┤
│                                                       │
│  📥 INCOMING MODS            📂 LOAD ORDER SLOTS     │
│  ┌─────────────────┐        ┌────────────────────┐  │
│  │ • ModFile1.pkg  │        │ 001_ScriptMods/    │  │
│  │ • ModFile2.pkg  │   →    │   script_mod.ts4...│  │
│  │ • Style.package │        ├────────────────────┤  │
│  │                 │        │ 002_CAS/           │  │
│  └─────────────────┘        │   hair_style.pkg   │  │
│                             ├────────────────────┤  │
│  ⚠️ 2 conflicts detected    │ 003_BuildBuy/      │  │
│                             │   furniture.pkg    │  │
│                             └────────────────────┘  │
│                                                      │
├──────────────────────────────────────────────────────┤
│  Status: Ready | Mods: 47 | Conflicts: 2 | v1.0.0   │ ← Status Bar
└──────────────────────────────────────────────────────┘
```

### Action Buttons

**SCAN** - Find new mods
- Scans Incoming Folder for .package, .ts4script, .py files
- Validates file integrity (CRC32)
- Detects conflicts automatically
- Shows progress dialog

**GENERATE** - Preview load order
- Creates folder structure preview
- Shows final mod placement
- No files are moved yet
- Safe to experiment

**DEPLOY** - Install mods
- **IMPORTANT:** Closes The Sims 4 if running
- Creates automatic backup
- Moves mods to Mods folder with prefixes
- Validates after deployment
- **Rollback on failure**

**BACKUP** - Manual backup
- Create named backup with description
- Independent of automatic backups
- Useful before major changes

**SETTINGS** - Configuration
- Change folder paths
- Adjust security settings
- View backup history
- Check for updates

### Load Order Slots Panel

Displays mods organized by category:

```
📁 001_ScriptMods/
   • script_mod.ts4script
   • python_script.py

📁 002_CAS/
   • hair_recolor_01.package
   • outfit_formal.package

📁 003_BuildBuy/
   • modern_furniture.package
```

**Drag & Drop:**
- Click and hold mod name
- Drag to different slot
- Drop to reassign
- Changes are not permanent until **DEPLOY**

**Right-Click Menu:**
- View Details
- Open Containing Folder
- Remove from Slot
- Check for Conflicts

### Status Bar

Shows real-time information:
- **Status**: Current operation (Ready/Scanning/Deploying)
- **Mods**: Total number of managed mods
- **Conflicts**: Number of detected conflicts
- **Version**: App version (click to check for updates)

---

## Managing Mods

### Adding New Mods

#### Method 1: Scan Incoming Folder

1. Download mods to your Incoming Folder
2. Click **SCAN** button
3. Review detected mods in left panel
4. Drag each mod to appropriate slot
5. Click **DEPLOY** when ready

#### Method 2: Drag & Drop (Windows/macOS)

1. Drag .package files directly onto app window
2. Mods appear in Incoming list
3. Assign to slots
4. Deploy

#### Method 3: Manual Add

1. Settings → Add Mod Manually
2. Browse to mod file
3. Select category
4. Confirm

### Organizing Mods

**By Category:**
```
001_ScriptMods/     → Script-based mods (.ts4script, .py)
002_CAS/            → Create-a-Sim (hair, clothes, accessories)
003_BuildBuy/       → Build/Buy mode objects
004_Gameplay/       → Gameplay modifications
005_UI/             → User interface changes
006_Worlds/         → New worlds/neighborhoods
...
999_Overrides/      → Major game overhauls
ZZZ_AlwaysLast/     → Mods that MUST load last
```

**Custom Slots:**
1. Right-click on slot
2. "Create New Slot"
3. Enter slot number (001-999) and name
4. Click OK

### Removing Mods

#### Temporary Disable

1. Right-click mod in slot
2. "Disable Mod"
3. Mod stays in slot but won't deploy
4. Re-enable anytime

#### Permanent Remove

1. Right-click mod
2. "Remove from Management"
3. Confirm deletion
4. **Original file remains in Incoming folder**

#### Uninstall from Game

1. Click **DEPLOY** with mod removed from all slots
2. Mod will be deleted from Mods folder during next deployment
3. Automatic backup created before removal

---

## Load Order Best Practices

### Understanding Load Order

**Why it matters:**
- Mods load alphabetically
- Later mods can override earlier mods
- Conflicts happen when multiple mods edit the same game file

**The Sims 4 Rules:**
1. **Script mods MUST be in root Mods/ folder** (not subfolders)
2. **1 subfolder depth maximum** (Mods/001_Category/mod.package ✅)
3. **ZZZ_ prefix always loads last** (game convention)

### Recommended Slot Organization

**001-020: Foundation**
```
001_ScriptMods/         ← MCCC, UI Cheats, script-based
002_CoreFixes/          ← Bug fixes, game patches
```

**021-050: Content Additions**
```
021_CAS_Hair/           ← Custom hair
022_CAS_Clothes/        ← Custom clothing
023_CAS_Accessories/    ← Jewelry, glasses, etc.
025_BuildBuy_Furniture/ ← Furniture CC
026_BuildBuy_Decor/     ← Decorative items
```

**051-100: Gameplay Mods**
```
051_Career/             ← New careers, job changes
052_Skills/             ← New skills, skill mods
053_Traits/             ← Custom traits
054_Aspirations/        ← New aspirations
055_Relationships/      ← Relationship mods
```

**101-900: Specialized**
```
101-200: World/Lot mods
201-300: Animation mods
301-400: Pet/animal mods
401-500: Toddler/child mods
501-600: Teen/adult mods
601-700: Elder mods
701-800: Supernatural mods
801-900: Seasonal mods
```

**901-999: Overrides & Last-Load**
```
901_UIOverhauls/        ← Major UI changes
950_GameplayOverhauls/  ← Total conversion mods
999_Overrides/          ← Override everything
ZZZ_AlwaysLast/         ← MUST load after everything
```

### Conflict Prevention Tips

1. **One mod per feature:** Avoid multiple mods doing the same thing
2. **Check compatibility:** Read mod descriptions for conflicts
3. **Update regularly:** Outdated mods often conflict
4. **Test in-game:** Some conflicts only appear during play
5. **Use conflict detector:** Review warnings before deploying

### Special Cases

**Script Mods:**
```
001_ScriptMods/
  • mc_command_center.ts4script  ✅ Root level
  • ui_cheats.ts4script           ✅ Root level
  
❌ WRONG:
001_ScriptMods/MCCC/mc_command_center.ts4script  ← Will NOT load!
```

**Override Mods:**
```
999_Overrides/
  • complete_ui_overhaul.package  ← Loads last, overrides all UI
```

**Multiple Versions:**
```
❌ Don't install:
  • hair_v1.package
  • hair_v2.package  ← Pick ONE version only
```

---

## Backup & Restore

### Automatic Backups

**When They Happen:**
- Before every deployment
- Before removing mods
- Before major configuration changes

**What's Included:**
- All mod files
- Load order configuration
- Folder structure
- Manifest with metadata

**Backup Location:**
```
~/Documents/Sims4ModBackups/
  backup_2026-01-01_120000.zip  ← Timestamp format
  backup_2026-01-01_150000.zip
  ...
```

### Manual Backups

**When to Create:**
- Before installing major mods
- Before game patches
- Before experimenting with load order
- Creating "known good" state

**How to Create:**
1. Click **BACKUP** button
2. Enter descriptive name: "Pre-StrangerVille Install"
3. Optional: Add notes about current setup
4. Click **Create Backup**
5. Wait for compression (30-60 seconds)
6. Confirmation message with file location

### Restoring Backups

**Full Restore:**
1. Settings → Backup History
2. Select backup from list
3. Preview contents (shows mods included)
4. Click **Restore**
5. Confirm: "This will replace all current mods"
6. Wait for restoration
7. **The Sims 4 will be closed if running**

**Partial Restore:**
1. Settings → Backup History
2. Select backup
3. Click **Browse Contents**
4. Check specific mods to restore
5. Click **Restore Selected**

**Emergency Restore:**
If app won't start:
```bash
# Extract backup manually
unzip backup_2026-01-01_120000.zip -d ~/temp_restore

# Copy to Mods folder
cp -r ~/temp_restore/* "~/Documents/Electronic Arts/The Sims 4/Mods/"
```

### Backup Best Practices

**Storage:**
- Keep at least 3 recent backups
- Delete old backups manually (Settings → Backup History → Clean Up)
- Store critical backups on external drive or cloud

**Naming:**
- Use descriptive names
- Include dates for context
- Examples:
  - "Pre-GamePatch-2026-01-15"
  - "Working-Setup-AllExpansions"
  - "Before-ModdingExperiment"

**Verification:**
- Test restores occasionally
- Check backup file size (should match mod collection)
- Review manifest.json for completeness

---

## Security Features

### File Integrity Validation

**CRC32 Hash Checking:**
Every file operation validates:
1. **Before Copy**: Generate hash of source
2. **After Copy**: Generate hash of destination
3. **Compare**: Hashes must match
4. **Alert**: Show error if mismatch detected

**Why It Matters:**
- Detects file corruption
- Prevents partial copies
- Catches disk errors early

### Sandboxed Scanning

**30-Second Timeout:**
- Prevents infinite loops in malicious mods
- Kills scan process if exceeded
- You can adjust: Settings → Security → Scan Timeout

**Isolated Process:**
- Mod scanning happens in separate thread
- UI remains responsive
- Crash won't affect main app

### Encrypted Configuration

**What's Encrypted:**
- Folder paths (Mods, Incoming, Backup)
- Encryption key location
- Sensitive settings

**Encryption Method:**
- Fernet symmetric encryption (cryptography library)
- 256-bit key
- Key stored in system keychain

**View Encrypted Config:**
```bash
# Linux/macOS
cat ~/.config/Sims4ModManager/config.json

# Shows encrypted data:
{
  "mods_folder": "gAAAAABh...",  ← Encrypted path
  "incoming_folder": "gAAAAABh...",
  ...
}
```

### High-Entropy Detection

**What It Detects:**
- Suspicious file patterns
- Encrypted or obfuscated code
- Potential malware

**Threshold:**
- Files with >7.5 entropy flagged
- Normal mods: 5-7 entropy
- Encrypted/compressed: 7.5-8

**When Flagged:**
- Manual review required
- Can override if false positive
- Mod still accessible but marked

### File Size Limits

**Default: 500 MB per mod**
- Protection against zip bombs
- Most Sims 4 mods < 50 MB
- Large worlds: 100-200 MB

**Override:**
Settings → Security → Max File Size
- Use with caution
- Only for trusted sources

### Safe Mode

**Enable for troubleshooting:**
Settings → Advanced → Safe Mode

**Restrictions:**
- No automatic operations
- Manual confirmation for everything
- Extended validation
- Verbose logging

---

## Advanced Features

### Conflict Detector

**How It Works:**
1. Parse .package files (DBPF format)
2. Extract resource IDs (type, group, instance)
3. Compare across all mods
4. Flag duplicates

**Interpreting Results:**
```
⚠️ Conflict Detected:

Resource: 0x123456_0xABCDEF_0x98765432
Mods:
  • mod_hair_recolor.package
  • mod_hair_retexture.package

Recommendation: Keep both (different textures)
```

**Conflict Types:**
- ✅ **Safe**: Multiple CAS items, different meshes
- ⚠️ **Warning**: Same XML tuning, different values
- ❌ **Critical**: Script files, same class names

### Batch Operations

**Selecting Multiple Mods:**
- **Ctrl+Click** (Windows/Linux) or **Cmd+Click** (macOS)
- Select multiple mods
- Right-click → Batch Actions

**Available Actions:**
- Assign All to Slot
- Enable/Disable All
- Check All for Updates
- Export List

### Export & Import

**Export Load Order:**
1. File → Export → Load Order
2. Choose format: JSON / Text / CSV
3. Save file

**Example JSON:**
```json
{
  "slots": {
    "001_ScriptMods": ["mccc.ts4script", "ui_cheats.ts4script"],
    "002_CAS": ["hair_01.package", "hair_02.package"]
  },
  "conflicts": [],
  "timestamp": "2026-01-01T12:00:00"
}
```

**Import Load Order:**
1. File → Import → Load Order
2. Select saved JSON file
3. Review changes
4. Apply

**Use Cases:**
- Share setups with friends
- Transfer between computers
- Document working configurations

### Hot Reload (Experimental)

**Auto-detect new mods:**
Settings → Advanced → Enable Hot Reload

**How It Works:**
- Watches Incoming Folder for changes
- Automatically scans new files
- Shows notification
- No manual SCAN needed

**Requirements:**
- watchdog library installed
- Sufficient system resources

---

## FAQ

### General

**Q: Is this safe to use?**
A: Yes. All operations are validated with CRC32 hashes, automatic backups created, and rollback on failure. Always backup your saves independently.

**Q: Will this break my game?**
A: No. The tool only organizes mods, doesn't modify game files. Bad mods can break your game (use trusted sources).

**Q: Does this work with pirated games?**
A: We don't support piracy. Buy The Sims 4 to support developers.

**Q: Can I use this with other mod managers?**
A: Not recommended. Choose one mod manager to avoid conflicts.

### Installation & Setup

**Q: Antivirus flags the executable as malicious.**
A: False positive. The .exe is not signed yet. Check VirusTotal link in releases. Add exception or build from source.

**Q: "App is damaged" on macOS.**
A: Run: `xattr -cr /Applications/Sims4ModManager.app`

**Q: Where is my config stored?**
- Windows: `%LOCALAPPDATA%\Sims4ModManager\`
- macOS: `~/Library/Application Support/Sims4ModManager/`
- Linux: `~/.config/Sims4ModManager/`

**Q: How do I uninstall?**
- Windows: Control Panel → Uninstall
- macOS: Delete from Applications
- Linux: `sudo dpkg -r sims4modmanager`

### Using the App

**Q: Why must script mods be in root folder?**
A: The Sims 4 only loads .ts4script files from the root Mods/ directory. This is a game limitation, not the tool's.

**Q: Can I have more than 999 slots?**
A: Yes, but alphabetical order continues (1000, 1001...). Keep under 999 for clarity.

**Q: What if I delete a mod accidentally?**
A: Restore from automatic backup (Settings → Backup History).

**Q: Can I rename slots?**
A: Yes. Right-click slot → Rename. Number prefix required.

**Q: How do I update mods?**
A: Download new version → Scan Incoming → Deploy (old version automatically replaced).

### Technical

**Q: What's DBPF?**
A: Database Packed File format used by The Sims 4. Contains mod resources with unique IDs.

**Q: Why CRC32 instead of SHA256?**
A: Speed. CRC32 is 10x faster for large files, sufficient for integrity checks (not security).

**Q: Can I run this on Linux via Wine?**
A: Use native Linux version (DEB package or from source). Wine adds unnecessary complexity.

**Q: Does this support command-line interface?**
A: Not yet. CLI mode planned for v2.0.

### Troubleshooting

**Q: Deployment failed, mods missing.**
A: Automatic rollback triggered. Check logs: `logs/deploy.log`. Restore backup if needed.

**Q: Conflicts detected but I don't see problems in-game.**
A: Not all conflicts are harmful. Test in-game and ignore if working.

**Q: Performance is slow with 500+ mods.**
A: Reduce max scans per operation (Settings → Performance → Batch Size). Consider pruning old mods.

**Q: Update check not working.**
A: Check internet connection. Verify GitHub API access: `https://api.github.com/repos/yourusername/sims4-pixel-mod-manager/releases/latest`

---

## Troubleshooting

### Application Issues

#### Won't Start / Immediate Crash

**Check Python version** (if from source):
```bash
python --version  # Must be 3.10+
```

**Check logs:**
- Windows: `%LOCALAPPDATA%\Sims4ModManager\logs\app.log`
- macOS/Linux: `~/.config/Sims4ModManager/logs/app.log`

**Reset configuration:**
```bash
# Backup first!
# Windows
mv %LOCALAPPDATA%\Sims4ModManager\config.json %LOCALAPPDATA%\Sims4ModManager\config.json.backup

# macOS/Linux
mv ~/.config/Sims4ModManager/config.json ~/.config/Sims4ModManager/config.json.backup

# Relaunch app
```

#### UI Issues

**Blurry on High-DPI displays:**
- Windows: Properties → Compatibility → Override DPI scaling
- Already handled in app but some systems need manual override

**Window too small/large:**
- Reset: Settings → Advanced → Reset Window Size

**Missing font (squares instead of text):**
- Install Press Start 2P font
- Download: https://fonts.google.com/specimen/Press+Start+2P

### Game Detection Issues

**Game not found:**

1. **Verify install location:**
   ```bash
   # Windows (check these)
   C:\Program Files\EA Games\The Sims 4
   C:\Program Files (x86)\Steam\steamapps\common\The Sims 4
   
   # macOS
   /Applications/The Sims 4.app
   ~/Library/Application Support/Steam/steamapps/common/The Sims 4
   
   # Linux
   ~/.steam/steam/steamapps/common/The Sims 4
   ```

2. **Check for GameVersion.txt:**
   ```
   (Game folder)/Game/Bin/GameVersion.txt
   ```
   
   If missing, repair game via Origin/Steam.

3. **Manual configuration:**
   - Settings → Game Path → Browse
   - Select game root folder (contains "Game" and "Data" folders)

### Deployment Issues

**"Permission Denied":**
1. Close The Sims 4 completely
2. Close Origin/EA App
3. Check file permissions:
   ```bash
   # Linux/macOS
   chmod -R u+w "~/Documents/Electronic Arts/The Sims 4/Mods/"
   ```
4. Run as administrator (Windows)

**"Checksum Mismatch":**
1. Re-download mod from source
2. Check disk health: `chkdsk` (Windows) / `fsck` (Linux)
3. Try different download location

**Rollback triggered:**
1. Check `logs/deploy.log` for errors
2. Common causes:
   - Disk full
   - File in use (game running)
   - Corrupted mod file
3. Fix issue and retry

### Performance Issues

**Slow scanning (100+ mods):**
```python
# Edit config.json
{
  "scan_batch_size": 50,  ← Reduce from 100
  "scan_parallel": false  ← Disable parallel scanning
}
```

**High CPU usage:**
- Close other applications
- Disable hot reload (Settings → Advanced)
- Reduce background operations

**Memory leaks:**
- Restart app after 10+ deployments
- Report issue with logs

### Mod-Specific Issues

**Script mod not loading in-game:**
1. Verify placed in root: `Mods/001_ScriptMods/mod.ts4script`
2. Check not in subfolder: ❌ `Mods/001_ScriptMods/MCCC/mod.ts4script`
3. Enable script mods in-game:
   ```
   Game Options → Other → Enable Script Mods ✅
   ```

**CAS items not showing:**
1. Clear game cache:
   ```
   Documents/Electronic Arts/The Sims 4/
     - localthumbcache.package  ← Delete these
     - cache/                   ← Delete folder
   ```
2. Restart game
3. Check mod is in 002_CAS/ slot

**Build/Buy items missing:**
1. Same as CAS (clear cache)
2. Verify mod is .package format
3. Check slot assignment (should be 003_BuildBuy/)

### Getting Additional Help

1. **GitHub Issues:**
   - [Search existing issues](https://github.com/yourusername/sims4-pixel-mod-manager/issues)
   - [Create new issue](https://github.com/yourusername/sims4-pixel-mod-manager/issues/new/choose)
   - Include logs and screenshots

2. **Discord Community:**
   - [Join server](https://discord.gg/your-invite)
   - #support channel
   - Share your setup details

3. **Email Support:**
   - your.email@example.com
   - Include app version, OS, error messages

---

## Appendix

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+O` | Open Settings |
| `Ctrl+S` | Scan Incoming Folder |
| `Ctrl+D` | Deploy Mods |
| `Ctrl+B` | Create Backup |
| `Ctrl+Z` | Undo (before deploy) |
| `Ctrl+F` | Find Mod |
| `Ctrl+A` | Select All Mods |
| `Ctrl+Q` | Quit Application |
| `F1` | Open Help |
| `F5` | Refresh View |

### File Formats Supported

- `.package` - Standard Sims 4 mod format
- `.ts4script` - Script mods (Python)
- `.py` - Python scripts (some mods)
- `.bpi` - Blender Project Interchange (rare)

### Glossary

- **DBPF**: Database Packed File (Sims 4 package format)
- **CRC32**: Cyclic Redundancy Check (error detection code)
- **Load Order**: Sequence in which mods are loaded by game
- **Slot**: Categorized folder with numeric prefix (001_Name/)
- **Conflict**: Multiple mods modifying same game resource
- **Resource ID**: Unique identifier for game asset (tuning, mesh, texture)
- **Manifest**: Metadata file tracking mod installations
- **Rollback**: Reverting changes after failed operation

### External Resources

- [Sims 4 Studio](https://sims4studio.com/) - Mod creation tool
- [Mod The Sims](https://modthesims.info/) - Mod repository
- [Creator Musings](https://www.creatormusings.com/) - Tutorials
- [SimsVIP](https://simsvip.com/) - News and mod lists
- [Carl's Sims 4 Guide](https://www.carls-sims-4-guide.com/) - Game info

---

**Need more help?** Visit the [GitHub repository](https://github.com/yourusername/sims4-pixel-mod-manager) or join our [Discord community](https://discord.gg/your-invite).

**Found a bug?** [Report it here](https://github.com/yourusername/sims4-pixel-mod-manager/issues/new?template=bug_report.yml).

**Have a feature idea?** [Suggest it here](https://github.com/yourusername/sims4-pixel-mod-manager/issues/new?template=feature_request.yml).

---

*Last updated: January 1, 2026 | Version 1.0.0*
