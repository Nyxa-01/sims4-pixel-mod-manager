# Distribution Checklist

Complete checklist for releasing Sims 4 Pixel Mod Manager

## Pre-Release Testing

### Functional Testing
- [ ] Mod scanning works for all file types (.package, .ts4script, .py)
- [ ] Load order assignment and reordering functional
- [ ] Drag-and-drop mod organization works smoothly
- [ ] Deployment completes without errors
- [ ] Backup creation and restoration successful
- [ ] Rollback works on deployment failure
- [ ] Conflict detection identifies overlapping mods
- [ ] Game detection finds all installation paths (Origin, Steam, EA App)
- [ ] Settings persist across restarts
- [ ] Help dialog displays correctly

### Platform Testing
- [ ] **Windows 10/11**
  - [ ] Executable runs without errors
  - [ ] Registry game detection works
  - [ ] File paths handle spaces correctly
  - [ ] Admin privileges not required
  - [ ] Antivirus doesn't flag application
  
- [ ] **macOS (Intel)**
  - [ ] .app bundle opens without security warnings
  - [ ] Game detection via Steam paths works
  - [ ] File permissions correct
  - [ ] Notarization complete (if signed)
  
- [ ] **macOS (Apple Silicon)**
  - [ ] Rosetta 2 compatibility verified
  - [ ] Native ARM build tested
  
- [ ] **Linux (Ubuntu/Debian)**
  - [ ] Executable has correct permissions
  - [ ] Dependencies met (tkinter, etc.)
  - [ ] .desktop file installs correctly

### Security Testing
- [ ] CRC32 hash verification catches corruption
- [ ] Path encryption working in config.json
- [ ] High-entropy files rejected
- [ ] 500MB file size limit enforced
- [ ] Sandbox timeout prevents hangs
- [ ] No unsafe file operations (outside Mods folder)

### Performance Testing
- [ ] Scan 100+ mods completes in <30 seconds
- [ ] Deployment handles 60+ mods smoothly
- [ ] UI remains responsive during long operations
- [ ] Memory usage stays reasonable (<500MB)
- [ ] No memory leaks after repeated operations

## Build Artifacts

### Required Files
- [ ] **Executables**
  - [ ] `Sims4ModManager.exe` (Windows)
  - [ ] `Sims4ModManager.app` (macOS Intel)
  - [ ] `Sims4ModManager.app` (macOS ARM)
  - [ ] `Sims4ModManager` (Linux)

- [ ] **Checksums**
  - [ ] `Sims4ModManager.exe.sha256`
  - [ ] `Sims4ModManager.app.sha256`
  - [ ] `Sims4ModManager.sha256` (Linux)

- [ ] **Installers (Optional)**
  - [ ] `Sims4ModManager-Setup.exe` (Inno Setup)
  - [ ] `Sims4ModManager.dmg` (macOS disk image)
  - [ ] `sims4modmanager_1.0.0_amd64.deb` (Debian package)

- [ ] **Documentation**
  - [ ] `README.md` with screenshots
  - [ ] `CHANGELOG.md` with version notes
  - [ ] `LICENSE` file (MIT)
  - [ ] `BUILD.md` with build instructions

### Verification
- [ ] All executables launch without errors
- [ ] SHA256 checksums match
- [ ] File sizes reasonable (Windows: ~30-50MB)
- [ ] VirusTotal scan clean (0 detections)
- [ ] Code signatures valid (if signed)

## Documentation

### README.md
- [ ] Project description clear
- [ ] Screenshots included (main window, settings, deployment)
- [ ] Installation instructions for all platforms
- [ ] System requirements listed
- [ ] Quick start guide
- [ ] FAQ section
- [ ] Troubleshooting common issues
- [ ] Link to full documentation
- [ ] Badges (CI/CD, coverage, license, etc.)

### User Documentation
- [ ] How to scan mods
- [ ] Understanding load order
- [ ] Resolving conflicts
- [ ] Backup and restore guide
- [ ] Configuration options explained
- [ ] Keyboard shortcuts listed
- [ ] Known limitations documented

### Developer Documentation
- [ ] Architecture overview
- [ ] Setup instructions
- [ ] Testing guide
- [ ] Contributing guidelines
- [ ] Code style requirements
- [ ] API documentation (if applicable)

## GitHub Release

### Release Page Setup
- [ ] Tag follows semantic versioning (v1.0.0)
- [ ] Release title clear (e.g., "v1.0.0 - Initial Release")
- [ ] Release notes comprehensive:
  - [ ] What's new
  - [ ] Bug fixes
  - [ ] Known issues
  - [ ] Breaking changes
  - [ ] Upgrade instructions
  
- [ ] All platform executables attached
- [ ] Checksums file attached
- [ ] Source code archive included
- [ ] Release marked as "Latest"

### Assets Naming
```
Sims4ModManager-1.0.0-Windows.exe
Sims4ModManager-1.0.0-macOS-Intel.app.zip
Sims4ModManager-1.0.0-macOS-ARM.app.zip
Sims4ModManager-1.0.0-Linux.tar.gz
checksums.sha256
```

## Community Preparation

### Pre-Launch
- [ ] Create GitHub repository (if not exists)
- [ ] Add topics: `sims4`, `mod-manager`, `python`, `tkinter`, `game-modding`
- [ ] Write compelling repository description
- [ ] Add repository social preview image (1280×640)
- [ ] Configure GitHub Pages (if docs site)

### Post-Launch Announcement
- [ ] Reddit r/thesims, r/sims4
- [ ] Mod The Sims forum post
- [ ] Creator Musings Discord
- [ ] Sims Community forums
- [ ] Twitter/X announcement
- [ ] YouTube demo video (optional)

### Support Channels
- [ ] GitHub Discussions enabled
- [ ] Issue templates configured
- [ ] PR template configured
- [ ] CONTRIBUTING.md guide
- [ ] CODE_OF_CONDUCT.md
- [ ] Response time expectations set

## Legal & Compliance

- [ ] LICENSE file present (MIT recommended)
- [ ] Copyright notices in source files
- [ ] Third-party licenses acknowledged
- [ ] No EA/Maxis copyrighted assets included
- [ ] Privacy policy (if collecting data)
- [ ] DMCA compliance (if user-generated content)

## Security Measures

### Code Signing
- [ ] **Windows:** SignTool with certificate
  - [ ] Certificate from trusted CA
  - [ ] Timestamp server used
  - [ ] Signature verified
  
- [ ] **macOS:** codesign with Developer ID
  - [ ] Developer ID certificate active
  - [ ] Hardened Runtime enabled
  - [ ] Notarized with Apple
  - [ ] Stapled to executable

### Distribution Security
- [ ] HTTPS only for download links
- [ ] SHA256 checksums published
- [ ] GPG signature available (optional)
- [ ] Release artifacts immutable
- [ ] No pre-release versions as "latest"

## VirusTotal Scanning

1. **Upload to VirusTotal**
   ```bash
   # Upload Windows executable
   curl --request POST \
     --url https://www.virustotal.com/vtapi/v2/file/scan \
     --form apikey=YOUR_API_KEY \
     --form file=@Sims4ModManager.exe
   ```

2. **Check Results**
   - [ ] 0 detections (ideal)
   - [ ] <5 detections (acceptable, usually false positives)
   - [ ] Review flagged engines
   - [ ] Add VirusTotal link to release notes

3. **False Positive Mitigation**
   - [ ] Submit to antivirus vendors as false positive
   - [ ] Add exclusion instructions to README
   - [ ] Consider different PyInstaller options

## Post-Release

### Immediate (Day 1)
- [ ] Monitor issue tracker for critical bugs
- [ ] Respond to initial user feedback
- [ ] Update documentation based on FAQs
- [ ] Pin important issues/discussions

### Week 1
- [ ] Collect analytics (download counts, stars, forks)
- [ ] Address high-priority bugs
- [ ] Plan v1.0.1 hotfix if needed
- [ ] Thank contributors and early adopters

### Month 1
- [ ] Review feature requests
- [ ] Plan roadmap for v1.1.0
- [ ] Update dependencies
- [ ] Improve documentation based on support tickets

## CI/CD Pipeline Verification

- [ ] GitHub Actions workflow passes
- [ ] All tests green (Windows, macOS, Linux)
- [ ] Code quality checks pass (Black, Ruff, Mypy)
- [ ] Security scans clean (Safety, Bandit)
- [ ] Coverage meets threshold (90%+)
- [ ] Build artifacts generated correctly
- [ ] Release workflow triggers on tag

## Final Checklist

- [ ] All tests passing
- [ ] All documentation complete
- [ ] All platform builds successful
- [ ] All checksums verified
- [ ] All security scans clean
- [ ] GitHub release created
- [ ] Community announcements posted
- [ ] Support channels ready
- [ ] Celebration! 🎉

---

## Quick Release Commands

```bash
# 1. Finalize version
echo "1.0.0" > VERSION
git add VERSION CHANGELOG.md
git commit -m "chore: Release v1.0.0"

# 2. Create tag
git tag -a v1.0.0 -m "Release v1.0.0 - Initial public release"
git push origin main
git push origin v1.0.0

# 3. GitHub Actions builds and releases automatically

# 4. Generate checksums locally (verification)
cd dist
sha256sum * > checksums.sha256

# 5. Test download and checksum
wget https://github.com/user/repo/releases/download/v1.0.0/Sims4ModManager.exe
sha256sum -c checksums.sha256
```

## Resources

- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [Inno Setup](https://jrsoftware.org/isinfo.php)
- [Apple Notarization Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Windows Code Signing](https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
