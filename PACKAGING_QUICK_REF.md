# 📦 Packaging & Distribution Quick Reference

Fast reference for building and releasing Sims 4 Pixel Mod Manager.

## 🚀 Quick Commands

### Build Executables

```bash
# Current platform (clean build)
python build.py --clean

# With code signing
python build.py --sign --cert-path "path/to/cert.pfx"  # Windows
python build.py --sign --identity "Developer ID"       # macOS
```

**Output:** `dist/Sims4ModManager{.exe|.app|}`

### Create Installers

```bash
# Native format
python scripts/build_installer.py

# Specific format
python scripts/build_installer.py --format inno  # Windows Setup
python scripts/build_installer.py --format dmg   # macOS DMG
python scripts/build_installer.py --format deb   # Linux DEB
```

**Output:** `installers/Sims4ModManager-{version}-{format}`

### Generate Checksums

```bash
# PowerShell (Windows)
cd dist
certutil -hashfile Sims4ModManager.exe SHA256 > Sims4ModManager.exe.sha256

# Bash (macOS/Linux)
cd dist
shasum -a 256 Sims4ModManager* > checksums.sha256
```

### Release to GitHub

```bash
# 1. Update version
echo "1.1.0" > VERSION

# 2. Update changelog
# Edit CHANGELOG.md

# 3. Commit and tag
git add VERSION CHANGELOG.md
git commit -m "chore: Release v1.1.0"
git tag -a v1.1.0 -m "Release v1.1.0"

# 4. Push (triggers CI/CD)
git push origin main
git push origin v1.1.0
```

**GitHub Actions will:**
- Build on Windows, macOS, Linux
- Run tests
- Create release
- Attach executables

## 📁 File Structure

```
Key Files:
├── build.spec              # PyInstaller config
├── build.py                # Build automation
├── VERSION                 # Current version (1.0.0)
├── scripts/
│   └── build_installer.py  # Installer creation
├── src/utils/
│   └── updater.py          # Auto-update system
└── dist/                   # Build output
    ├── Sims4ModManager*
    ├── *.sha256
    └── version.json
```

## 🔧 Build System

### build.py Options

```bash
python build.py [OPTIONS]

--platform {windows|macos|linux|current}  # Target platform
--clean                                    # Clean before build
--sign                                     # Sign executable
--cert-path PATH                           # Windows certificate
--identity "ID"                            # macOS Developer ID
--notarize                                 # macOS notarization
--no-verify                                # Skip checksum
```

### build.spec Configuration

```python
# Hidden imports (add if import errors)
hiddenimports = [
    'tkinter',
    'cryptography',
    'PIL',
    'psutil',
    'watchdog',
    # Add more here
]

# Excludes (reduce size)
excludes = [
    'pytest',
    'black',
    'mypy',
]

# Asset bundling
datas = [
    ('assets', 'assets'),
]
```

## 🔐 Code Signing

### Windows

```powershell
# Requirements
- Code signing certificate (.pfx)
- Windows SDK (SignTool)

# Sign
python build.py --sign --cert-path "cert.pfx"

# Verify
signtool verify /pa dist\Sims4ModManager.exe
```

### macOS

```bash
# Requirements
- Apple Developer account
- Developer ID certificate

# Sign
python build.py --sign --identity "Developer ID Application: Name"

# Notarize (required for 10.15+)
xcrun notarytool submit dist/Sims4ModManager.app.zip \
  --apple-id "email" --password "app-password" --team-id "ID" --wait
xcrun stapler staple dist/Sims4ModManager.app

# Verify
codesign --verify --deep dist/Sims4ModManager.app
spctl --assess --verbose dist/Sims4ModManager.app
```

## 🧪 Testing

### Test Build

```bash
# Run executable
dist/Sims4ModManager           # macOS/Linux
dist\Sims4ModManager.exe       # Windows

# Verify assets
unzip -l dist/Sims4ModManager | grep assets  # Unix
7z l dist\Sims4ModManager.exe | findstr assets  # Windows

# Check size (should be 30-50MB)
du -h dist/Sims4ModManager*
```

### Test Installer

```bash
# Windows
installers\Sims4ModManager-Setup.exe /SILENT

# macOS
hdiutil attach installers/Sims4ModManager.dmg
# Drag to Applications

# Linux
sudo dpkg -i installers/sims4modmanager_1.0.0_amd64.deb
sims4modmanager
```

## 🔄 Auto-Update System

### Integration in main.py

```python
from src.utils.updater import Updater

# Check on startup (silent)
updater = Updater(owner="user", repo="repo")
updater.check_on_startup(root_window, silent=True)

# Manual check (Help menu)
def check_updates():
    updater = Updater()
    if updater.check_for_updates():
        updater.prompt_update_dialog(root_window)
    else:
        messagebox.showinfo("No Updates", "Latest version installed.")
```

### Update Process

1. App checks GitHub API on startup
2. Compares semantic versions
3. Shows update dialog if newer
4. Downloads to temp directory
5. Verifies SHA256 checksum
6. Prompts user to install

## 📊 Build Metrics

| Platform | Build Time | Size (UPX) | Installer Size |
|----------|------------|------------|----------------|
| Windows  | 2-4 min    | 30-50 MB   | 35-60 MB       |
| macOS    | 3-5 min    | 35-55 MB   | 40-65 MB       |
| Linux    | 2-4 min    | 30-50 MB   | 30-55 MB       |

## 🛡️ Security Checklist

- [ ] Build on clean system
- [ ] Code sign executables
- [ ] Generate SHA256 checksums
- [ ] Upload to VirusTotal
- [ ] Verify signatures
- [ ] Test on target platforms
- [ ] Include checksums in release

## 📝 Release Checklist

**Pre-Release:**
- [ ] Update VERSION file
- [ ] Update CHANGELOG.md
- [ ] Run all tests: `pytest -v`
- [ ] Build locally: `python build.py --clean`
- [ ] Test executable
- [ ] Create installers

**Release:**
- [ ] Commit changes
- [ ] Create git tag: `git tag v1.0.0`
- [ ] Push tag: `git push origin v1.0.0`
- [ ] Wait for CI/CD
- [ ] Download artifacts
- [ ] Test downloaded executables

**Post-Release:**
- [ ] Upload checksums to release
- [ ] Update release notes
- [ ] Add screenshots
- [ ] Announce on community channels
- [ ] Monitor for issues

## 🔗 Quick Links

- **Build Guide:** [BUILD.md](BUILD.md)
- **Distribution Checklist:** [DISTRIBUTION_CHECKLIST.md](DISTRIBUTION_CHECKLIST.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **CI/CD:** [.github/workflows/ci.yml](.github/workflows/ci.yml)
- **Summary:** [PACKAGING_SUMMARY.md](PACKAGING_SUMMARY.md)

## 🆘 Troubleshooting

### Build Fails: "Module not found"
**Fix:** Add to `hiddenimports` in build.spec

### Executable Too Large (>100MB)
**Fix:**
```python
# build.spec
excludes = ['pandas', 'numpy', 'matplotlib']  # Unused large libs
upx = True  # Enable compression
```

### Antivirus False Positive
**Fix:**
1. Code sign executable
2. Upload to VirusTotal
3. Submit false positive to vendor
4. Disable UPX if needed: `upx = False`

### macOS "App is Damaged"
**Fix:**
```bash
# User workaround
xattr -cr /Applications/Sims4ModManager.app

# Proper fix: Code sign + notarize
```

### Linux Missing Libraries
**Fix:**
```bash
# Check dependencies
ldd dist/Sims4ModManager

# Install missing
sudo apt install python3-tk libxcb-xinerama0
```

## 💡 Tips

- **Clean builds:** Always use `--clean` for releases
- **Version sync:** Keep VERSION, CHANGELOG, and git tags in sync
- **Test platforms:** Build and test on native OS (no cross-compile)
- **Code signing:** Reduces false positives, increases trust
- **Checksums:** Always generate and publish SHA256
- **CI/CD:** Use GitHub Actions for multi-platform builds
- **UPX:** Great for size, may trigger antiviruses
- **Notarization:** Required for macOS 10.15+ (Catalina)

## 🎯 Common Workflows

### Development Build (Fast)
```bash
python build.py
./dist/Sims4ModManager
```

### Release Build (Full)
```bash
# 1. Clean build with signing
python build.py --clean --sign

# 2. Create installer
python scripts/build_installer.py

# 3. Generate checksums
cd dist && shasum -a 256 * > checksums.sha256

# 4. Test everything
./dist/Sims4ModManager
```

### CI/CD Release
```bash
git tag v1.0.0
git push origin v1.0.0
# Wait for GitHub Actions
# Download from Releases page
```

---

**Questions?** See [BUILD.md](BUILD.md) for detailed instructions or [DISTRIBUTION_CHECKLIST.md](DISTRIBUTION_CHECKLIST.md) for complete workflow.
