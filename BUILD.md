# Building Sims 4 Pixel Mod Manager

Complete guide to building executables and installers for all platforms.

## Prerequisites

### All Platforms
- Python 3.10 or higher
- Git (for version detection)
- PyInstaller 5.0+

```bash
pip install pyinstaller
```

### Windows
- **Optional:** Windows SDK (for code signing)
  - Download: https://developer.microsoft.com/windows/downloads/windows-sdk/
  - Provides SignTool.exe
- **Optional:** Inno Setup (for installer creation)
  - Download: https://jrsoftware.org/isinfo.php

### macOS
- Xcode Command Line Tools
  ```bash
  xcode-select --install
  ```
- **Optional:** Apple Developer ID certificate (for code signing)

### Linux
- Standard build tools
  ```bash
  # Ubuntu/Debian
  sudo apt install python3-tk dpkg-dev rpm
  
  # Fedora/RHEL
  sudo dnf install python3-tkinter rpm-build
  ```

## Quick Start

### Basic Build (Current Platform)

```bash
# Clean build
python build.py --clean

# Build with code signing (if certificates available)
python build.py --sign

# Build with all options
python build.py --clean --sign
```

Executable will be in `dist/` directory:
- Windows: `dist/Sims4ModManager.exe`
- macOS: `dist/Sims4ModManager.app`
- Linux: `dist/Sims4ModManager`

### Create Installer (Optional)

```bash
# Native installer for current platform
python scripts/build_installer.py

# Specific format
python scripts/build_installer.py --format inno   # Windows
python scripts/build_installer.py --format dmg    # macOS
python scripts/build_installer.py --format deb    # Linux
```

Installers will be in `installers/` directory.

## Detailed Instructions

### Windows Build

#### 1. Basic Executable

```powershell
# Build
python build.py --clean

# Verify
.\dist\Sims4ModManager.exe

# Check size (should be ~30-50MB)
(Get-Item .\dist\Sims4ModManager.exe).Length / 1MB
```

#### 2. Code Signing (Optional)

**Requirements:**
- Code signing certificate (.pfx file)
- Certificate password

```powershell
# Sign during build
python build.py --sign --cert-path "C:\path\to\cert.pfx"

# Verify signature
signtool verify /pa dist\Sims4ModManager.exe
```

#### 3. Create Installer

```powershell
# Build Inno Setup installer
python scripts\build_installer.py --format inno

# Installer location
.\installers\Sims4ModManager-1.0.0-Setup.exe
```

**Installer Features:**
- Start Menu shortcuts
- Desktop icon (optional)
- Uninstaller
- File associations (optional)
- Registry entries (optional)

### macOS Build

#### 1. Basic App Bundle

```bash
# Build
python build.py --clean

# Verify
open dist/Sims4ModManager.app

# Check bundle structure
tree dist/Sims4ModManager.app
```

#### 2. Code Signing (Optional)

**Requirements:**
- Apple Developer account
- Developer ID Application certificate
- Installed in Keychain

```bash
# List available identities
security find-identity -v -p codesigning

# Sign during build
python build.py --sign --identity "Developer ID Application: Your Name (TEAMID)"

# Verify signature
codesign --verify --deep --strict dist/Sims4ModManager.app
codesign --display --verbose=4 dist/Sims4ModManager.app
```

#### 3. Notarization (Required for macOS 10.15+)

```bash
# 1. Create app-specific password at appleid.apple.com

# 2. Store credentials (one-time)
xcrun notarytool store-credentials "AC_PASSWORD" \
  --apple-id "your@email.com" \
  --team-id "TEAMID" \
  --password "app-specific-password"

# 3. Create ZIP of signed app
ditto -c -k --keepParent dist/Sims4ModManager.app dist/Sims4ModManager.zip

# 4. Submit for notarization
xcrun notarytool submit dist/Sims4ModManager.zip \
  --keychain-profile "AC_PASSWORD" \
  --wait

# 5. Staple ticket to app
xcrun stapler staple dist/Sims4ModManager.app

# 6. Verify
spctl --assess --verbose dist/Sims4ModManager.app
```

#### 4. Create DMG

```bash
# Build DMG disk image
python scripts/build_installer.py --format dmg

# DMG location
./installers/Sims4ModManager-1.0.0.dmg

# Test mount
hdiutil attach installers/Sims4ModManager-1.0.0.dmg
```

### Linux Build

#### 1. Basic Executable

```bash
# Build
python build.py --clean

# Make executable
chmod +x dist/Sims4ModManager

# Verify
./dist/Sims4ModManager

# Check dependencies
ldd dist/Sims4ModManager
```

#### 2. Create DEB Package

```bash
# Build Debian package
python scripts/build_installer.py --format deb

# Package location
./installers/sims4modmanager_1.0.0_amd64.deb

# Test install
sudo dpkg -i installers/sims4modmanager_1.0.0_amd64.deb

# Run
sims4modmanager

# Uninstall
sudo dpkg -r sims4modmanager
```

#### 3. Create RPM Package (TODO)

```bash
# RPM building not yet implemented
# Contributions welcome!
```

## Build Configuration

### build.spec

PyInstaller spec file with platform-specific settings:

```python
# Key settings
hiddenimports = ['tkinter', 'cryptography', 'PIL', 'psutil']
excludes = ['pytest', 'black', 'mypy']  # Dev dependencies
datas = [('assets', 'assets')]  # Bundle assets

# Platform-specific
if sys.platform == 'win32':
    icon_file = 'assets/icon.ico'
elif sys.platform == 'darwin':
    icon_file = 'assets/icon.icns'
else:
    icon_file = 'assets/icon.png'
```

### VERSION File

Controls application version:

```bash
# Update version
echo "1.0.0" > VERSION

# Or use git tags
git tag v1.0.0
# build.py will auto-detect from git
```

## Advanced Topics

### Custom Icons

**Windows (.ico):**
```bash
# Create from PNG (requires ImageMagick)
magick convert icon.png -define icon:auto-resize=256,128,64,48,32,16 assets/icon.ico
```

**macOS (.icns):**
```bash
# Create iconset
mkdir MyIcon.iconset
sips -z 16 16     icon.png --out MyIcon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out MyIcon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out MyIcon.iconset/icon_32x32.png
# ... (more sizes)

# Convert to icns
iconutil -c icns MyIcon.iconset -o assets/icon.icns
```

**Linux (.png):**
```bash
# 512x512 PNG recommended
cp icon.png assets/icon.png
```

### UPX Compression

Reduce executable size with UPX:

```bash
# Install UPX
# Windows: Download from https://upx.github.io/
# macOS: brew install upx
# Linux: sudo apt install upx-ucl

# Build with UPX (automatic in build.spec)
python build.py

# Manually compress
upx --best dist/Sims4ModManager.exe
```

**Note:** Some antivirus flags UPX-compressed executables. Test before release.

### Debugging Build Issues

#### Import Errors

```bash
# List all imports
pyinstaller --log-level=DEBUG build.spec

# Add missing imports to hiddenimports in build.spec
```

#### Missing Assets

```bash
# Verify assets bundled
# Windows
7z l dist\Sims4ModManager.exe | findstr assets

# macOS/Linux
unzip -l dist/Sims4ModManager | grep assets
```

#### Runtime Errors

```bash
# Enable console for debugging
# Edit build.spec: console=True

# Rebuild
python build.py --clean
```

### Cross-Compilation Limitations

**PyInstaller requires native builds:**
- Build Windows .exe on Windows
- Build macOS .app on macOS
- Build Linux binary on Linux

**Solution:** Use CI/CD (GitHub Actions) for multi-platform builds.

## CI/CD Integration

### GitHub Actions

Workflow automatically builds on tag push:

```bash
# Create release
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions will:
# 1. Build on Windows, macOS, Linux
# 2. Run tests
# 3. Create release
# 4. Upload executables
```

See `.github/workflows/ci.yml` for details.

### Local Multi-Platform Build

Use Docker or VMs:

```bash
# Windows (via Wine - not recommended)
# macOS (via OSX Cross - complex)
# Linux (via Docker)

docker run -v $(pwd):/app python:3.10 bash -c "
  cd /app
  pip install -r requirements.txt
  python build.py
"
```

## Troubleshooting

### "Module not found" at runtime

**Fix:** Add to `hiddenimports` in build.spec

### Executable too large (>100MB)

**Fix:**
1. Enable UPX compression
2. Exclude unnecessary modules
3. Use `--exclude-module` for large unused libraries

### Antivirus false positive

**Fix:**
1. Submit to antivirus vendor as false positive
2. Code sign executable
3. Upload to VirusTotal and share link
4. Disable UPX compression

### macOS "App is damaged" error

**Fix:**
1. Code sign the app
2. Notarize with Apple
3. Users can bypass: `xattr -cr Sims4ModManager.app`

### Linux missing libraries

**Fix:**
```bash
# Check dependencies
ldd dist/Sims4ModManager

# Install missing
sudo apt install libxcb-xinerama0 libxcb-cursor0
```

## Distribution

### File Naming Convention

```
Sims4ModManager-{version}-{platform}.{ext}

Examples:
Sims4ModManager-1.0.0-Windows.exe
Sims4ModManager-1.0.0-macOS-Intel.app.zip
Sims4ModManager-1.0.0-macOS-ARM.app.zip
Sims4ModManager-1.0.0-Linux.tar.gz
```

### Checksums

```bash
# Generate SHA256
cd dist

# Windows
certutil -hashfile Sims4ModManager.exe SHA256

# macOS/Linux
shasum -a 256 Sims4ModManager.app > checksums.sha256
```

### Release Package Contents

```
release/
├── Sims4ModManager-1.0.0-Windows.exe
├── Sims4ModManager-1.0.0-Windows.exe.sha256
├── Sims4ModManager-1.0.0-macOS.app.zip
├── Sims4ModManager-1.0.0-macOS.app.zip.sha256
├── Sims4ModManager-1.0.0-Linux.tar.gz
├── Sims4ModManager-1.0.0-Linux.tar.gz.sha256
├── README.md
├── CHANGELOG.md
└── LICENSE
```

## References

- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [Windows Code Signing](https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool)
- [Apple Notarization](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Debian Packaging](https://www.debian.org/doc/manuals/maint-guide/)
- [RPM Packaging](https://rpm-packaging-guide.github.io/)
