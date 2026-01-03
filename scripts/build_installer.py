#!/usr/bin/env python3
"""
Installer generation script for Sims 4 Pixel Mod Manager
Creates platform-specific installers from built executables

Supported formats:
- Windows: Inno Setup (.exe installer)
- macOS: DMG disk image
- Linux: DEB and RPM packages
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


class InstallerBuilder:
    """Platform-specific installer creation."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.dist_dir = project_root / "dist"
        self.installers_dir = project_root / "installers"
        self.installers_dir.mkdir(exist_ok=True)

        # Read version
        version_file = project_root / "VERSION"
        self.version = version_file.read_text().strip() if version_file.exists() else "1.0.0"

    def build_windows_installer(self) -> Path:
        """Create Windows installer using Inno Setup."""
        print("🪟 Building Windows installer with Inno Setup...")

        # Check for Inno Setup compiler
        iscc = self._find_inno_setup()
        if not iscc:
            raise OSError("Inno Setup not found. Download from: https://jrsoftware.org/isinfo.php")

        # Locate executable
        exe_path = self.dist_dir / "Sims4ModManager.exe"
        if not exe_path.exists():
            raise FileNotFoundError(f"Executable not found: {exe_path}")

        # Create Inno Setup script
        iss_content = self._generate_inno_script(exe_path)
        iss_file = self.project_root / "installer.iss"
        iss_file.write_text(iss_content)

        try:
            # Compile installer
            cmd = [str(iscc), "/Q", str(iss_file)]  # /Q = quiet mode
            subprocess.run(cmd, check=True)

            installer_name = f"Sims4ModManager-{self.version}-Setup.exe"
            installer_path = self.installers_dir / installer_name

            # Move from Output directory
            output_exe = self.project_root / "Output" / "Sims4ModManagerSetup.exe"
            if output_exe.exists():
                shutil.move(str(output_exe), str(installer_path))
                (self.project_root / "Output").rmdir()

            print(f"✓ Windows installer: {installer_path}")
            return installer_path

        finally:
            if iss_file.exists():
                iss_file.unlink()

    def _generate_inno_script(self, exe_path: Path) -> str:
        """Generate Inno Setup script content."""
        return f"""
; Inno Setup Script for Sims 4 Pixel Mod Manager
[Setup]
AppName=Sims 4 Mod Manager
AppVersion={self.version}
AppPublisher=PixelWorks
AppPublisherURL=https://github.com/yourusername/sims4_pixel_mod_manager
DefaultDirName={{autopf}}\\Sims4ModManager
DefaultGroupName=Sims 4 Mod Manager
OutputBaseFilename=Sims4ModManagerSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile={self.project_root}\\assets\\icon.ico
UninstallDisplayIcon={{app}}\\Sims4ModManager.exe
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"

[Files]
Source: "{exe_path}"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{self.project_root}\\README.md"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{self.project_root}\\LICENSE"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\Sims 4 Mod Manager"; Filename: "{{app}}\\Sims4ModManager.exe"
Name: "{{group}}\\{{cm:UninstallProgram,Sims 4 Mod Manager}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\Sims 4 Mod Manager"; Filename: "{{app}}\\Sims4ModManager.exe"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\Sims4ModManager.exe"; Description: "{{cm:LaunchProgram,Sims 4 Mod Manager}}"; Flags: nowait postinstall skipifsilent
"""

    def _find_inno_setup(self) -> Path | None:
        """Locate Inno Setup compiler."""
        common_paths = [
            Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
            Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
            Path(r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe"),
        ]

        for path in common_paths:
            if path.exists():
                return path

        return None

    def build_macos_dmg(self) -> Path:
        """Create macOS DMG disk image."""
        print("🍎 Building macOS DMG...")

        # Locate app bundle
        app_path = self.dist_dir / "Sims4ModManager.app"
        if not app_path.exists():
            raise FileNotFoundError(f"App bundle not found: {app_path}")

        dmg_name = f"Sims4ModManager-{self.version}.dmg"
        dmg_path = self.installers_dir / dmg_name

        # Remove existing DMG
        if dmg_path.exists():
            dmg_path.unlink()

        # Create DMG with hdiutil
        cmd = [
            "hdiutil",
            "create",
            "-volname",
            "Sims 4 Mod Manager",
            "-srcfolder",
            str(app_path),
            "-ov",  # Overwrite
            "-format",
            "UDZO",  # Compressed
            str(dmg_path),
        ]

        subprocess.run(cmd, check=True)
        print(f"✓ macOS DMG: {dmg_path}")
        return dmg_path

    def build_linux_deb(self) -> Path:
        """Create Debian package."""
        print("🐧 Building Linux DEB package...")

        # Locate executable
        exe_path = self.dist_dir / "Sims4ModManager"
        if not exe_path.exists():
            raise FileNotFoundError(f"Executable not found: {exe_path}")

        # Create package structure
        pkg_name = f"sims4modmanager_{self.version}_amd64"
        pkg_dir = self.project_root / pkg_name

        # Create directories
        (pkg_dir / "DEBIAN").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "usr" / "bin").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "usr" / "share" / "applications").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "usr" / "share" / "pixmaps").mkdir(parents=True, exist_ok=True)

        # Copy executable
        shutil.copy(exe_path, pkg_dir / "usr" / "bin" / "sims4modmanager")
        (pkg_dir / "usr" / "bin" / "sims4modmanager").chmod(0o755)

        # Copy icon if exists
        icon_path = self.project_root / "assets" / "icon.png"
        if icon_path.exists():
            shutil.copy(icon_path, pkg_dir / "usr" / "share" / "pixmaps" / "sims4modmanager.png")

        # Create control file
        control_content = f"""Package: sims4modmanager
Version: {self.version}
Section: games
Priority: optional
Architecture: amd64
Maintainer: PixelWorks <contact@example.com>
Description: Sims 4 Pixel Mod Manager
 8-bit retro styled mod manager for The Sims 4.
 Provides secure mod installation, load order management,
 and conflict detection with a pixel art interface.
"""
        (pkg_dir / "DEBIAN" / "control").write_text(control_content)

        # Create .desktop file
        desktop_content = """[Desktop Entry]
Version=1.0
Type=Application
Name=Sims 4 Mod Manager
Comment=Manage Sims 4 mods with 8-bit style
Exec=/usr/bin/sims4modmanager
Icon=sims4modmanager
Terminal=false
Categories=Game;Utility;
"""
        (pkg_dir / "usr" / "share" / "applications" / "sims4modmanager.desktop").write_text(
            desktop_content
        )

        # Build DEB package
        deb_path = self.installers_dir / f"{pkg_name}.deb"
        cmd = ["dpkg-deb", "--build", str(pkg_dir), str(deb_path)]

        try:
            subprocess.run(cmd, check=True)
            print(f"✓ Linux DEB: {deb_path}")
            return deb_path
        finally:
            # Cleanup
            if pkg_dir.exists():
                shutil.rmtree(pkg_dir)

    def build_linux_rpm(self) -> Path:
        """Create RPM package."""
        print("🐧 Building Linux RPM package...")
        print("⚠️  RPM building requires 'rpmbuild' tool")
        print("    Install: sudo apt install rpm (Debian/Ubuntu)")
        print("    Or: sudo dnf install rpm-build (Fedora/RHEL)")

        # This is a placeholder - full RPM creation is complex
        raise NotImplementedError("RPM building not yet implemented")


def main():
    parser = argparse.ArgumentParser(description="Build installers for Sims 4 Mod Manager")
    parser.add_argument(
        "--format",
        choices=["inno", "dmg", "deb", "rpm", "all"],
        default="native",
        help="Installer format (default: native for current platform)",
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    builder = InstallerBuilder(project_root)

    try:
        system = platform.system()

        if args.format == "native":
            if system == "Windows":
                builder.build_windows_installer()
            elif system == "Darwin":
                builder.build_macos_dmg()
            elif system == "Linux":
                builder.build_linux_deb()
        elif args.format == "inno":
            builder.build_windows_installer()
        elif args.format == "dmg":
            builder.build_macos_dmg()
        elif args.format == "deb":
            builder.build_linux_deb()
        elif args.format == "rpm":
            builder.build_linux_rpm()
        elif args.format == "all":
            print("Building all formats for current platform...")
            if system == "Windows":
                builder.build_windows_installer()
            elif system == "Darwin":
                builder.build_macos_dmg()
            elif system == "Linux":
                builder.build_linux_deb()

        print("\n✅ Installer creation complete!")
        return 0

    except Exception as e:
        print(f"\n✗ Installer build failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
