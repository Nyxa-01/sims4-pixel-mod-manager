#!/usr/bin/env python3
"""
Cross-platform build automation for Sims 4 Pixel Mod Manager
Handles PyInstaller builds, version embedding, code signing, and verification

Usage:
    python build.py --platform windows --sign
    python build.py --platform macos --sign --notarize
    python build.py --platform linux
    python build.py --all  # Build for all platforms
"""

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


class BuildConfig:
    """Build configuration and platform detection."""

    # Supported platforms
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"

    # Executable extensions
    EXT_MAP = {
        WINDOWS: ".exe",
        MACOS: ".app",
        LINUX: "",
    }

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.spec_file = self.project_root / "build.spec"

        # Detect current platform
        system = platform.system()
        if system == "Windows":
            self.native_platform = self.WINDOWS
        elif system == "Darwin":
            self.native_platform = self.MACOS
        else:
            self.native_platform = self.LINUX

    def get_executable_name(self, target_platform: str) -> str:
        """Get platform-specific executable name."""
        base = "Sims4ModManager"
        if target_platform == self.MACOS:
            return f"{base}.app"
        elif target_platform == self.WINDOWS:
            return f"{base}.exe"
        return base

    def get_version(self) -> str:
        """Extract version from git tags or fallback to default."""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                # Strip 'v' prefix if present
                return version.lstrip("v")
        except FileNotFoundError:
            pass

        # Fallback: check VERSION file
        version_file = self.project_root / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()

        return "1.0.0"


class Builder:
    """Build automation orchestrator."""

    def __init__(self, config: BuildConfig):
        self.config = config
        self.version = config.get_version()

    def clean(self):
        """Remove previous build artifacts."""
        print("Cleaning previous builds...")
        if self.config.dist_dir.exists():
            shutil.rmtree(self.config.dist_dir)
        if self.config.build_dir.exists():
            shutil.rmtree(self.config.build_dir)
        print("[OK] Clean complete")

    def validate_environment(self):
        """Check required tools are installed."""
        print("Validating build environment...")

        # Check Python version
        py_version = sys.version_info
        if py_version < (3, 10):
            raise OSError(f"Python 3.10+ required, found {py_version.major}.{py_version.minor}")
        print(f"  [OK] Python {py_version.major}.{py_version.minor}.{py_version.micro}")

        # Check PyInstaller
        try:
            result = subprocess.run(
                ["pyinstaller", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            print(f"  [OK] PyInstaller {result.stdout.strip()}")
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            raise OSError("PyInstaller not found. Install: pip install pyinstaller") from e

        # Check spec file exists
        if not self.config.spec_file.exists():
            raise FileNotFoundError(f"Spec file not found: {self.config.spec_file}")
        print(f"  [OK] Spec file: {self.config.spec_file.name}")

    def build(self, target_platform: str) -> Path:
        """Run PyInstaller build for target platform."""
        print(f"\nBuilding for {target_platform}...")
        print(f"  Version: {self.version}")

        # Update spec file with version (in-memory modification)
        spec_content = self.config.spec_file.read_text()
        spec_content = spec_content.replace(
            "'CFBundleVersion': '1.0.0'", f"'CFBundleVersion': '{self.version}'"
        )
        spec_content = spec_content.replace(
            "'CFBundleShortVersionString': '1.0.0'",
            f"'CFBundleShortVersionString': '{self.version}'",
        )

        # Write temporary spec file
        temp_spec = self.config.spec_file.with_suffix(".temp.spec")
        temp_spec.write_text(spec_content)

        try:
            # Run PyInstaller
            cmd = ["pyinstaller", str(temp_spec), "--clean", "--noconfirm"]

            subprocess.run(cmd, check=True)

            # Locate built executable
            exe_name = self.config.get_executable_name(target_platform)
            exe_path = self.config.dist_dir / exe_name

            # Handle ONEDIR mode: PyInstaller creates a directory with exe inside
            if not exe_path.exists():
                # Check for ONEDIR structure (directory with same base name)
                base_name = exe_name.replace(".exe", "").replace(".app", "")
                onedir_path = self.config.dist_dir / base_name

                if onedir_path.is_dir():
                    if target_platform == BuildConfig.WINDOWS:
                        # Windows: exe inside directory
                        exe_path = onedir_path / f"{base_name}.exe"
                    elif target_platform == BuildConfig.MACOS:
                        # macOS: .app bundle is created by BUNDLE, check for it
                        app_bundle = self.config.dist_dir / f"{base_name}.app"
                        if app_bundle.exists():
                            exe_path = app_bundle
                        else:
                            exe_path = onedir_path
                    else:  # Linux
                        # Linux: executable inside directory (no extension)
                        exe_path = onedir_path / base_name

            if not exe_path.exists():
                raise FileNotFoundError(f"Build succeeded but executable not found: {exe_path}")

            print(f"[OK] Build complete: {exe_path}")
            return exe_path

        finally:
            # Clean up temp spec
            if temp_spec.exists():
                temp_spec.unlink()

    def sign_windows(self, exe_path: Path, cert_path: str | None = None):
        """Sign Windows executable with SignTool."""
        print("\nSigning Windows executable...")

        # Check for SignTool (Windows SDK)
        signtool = self._find_signtool()
        if not signtool:
            print("[WARNING] SignTool not found. Skipping signing.")
            print("          Install Windows SDK for code signing.")
            return

        if not cert_path:
            print("[WARNING] No certificate path provided. Skipping signing.")
            print("          Use --cert-path to specify certificate.")
            return

        cmd = [
            str(signtool),
            "sign",
            "/f",
            cert_path,
            "/t",
            "http://timestamp.digicert.com",  # Timestamp server
            "/v",  # Verbose
            str(exe_path),
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"[OK] Signed: {exe_path.name}")
        except subprocess.CalledProcessError as e:
            print(f"[FAIL] Signing failed: {e}")

    def sign_macos(self, app_path: Path, identity: str | None = None, notarize: bool = False):
        """Sign macOS app bundle with codesign."""
        print("\nSigning macOS app bundle...")

        if not identity:
            print("[WARNING] No signing identity provided. Skipping signing.")
            print("          Use --identity 'Developer ID Application: Your Name'")
            return

        # Sign the app
        cmd = [
            "codesign",
            "--force",
            "--deep",
            "--sign",
            identity,
            "--options",
            "runtime",  # Required for notarization
            str(app_path),
        ]

        try:
            subprocess.run(cmd, check=True)
            print(f"[OK] Signed: {app_path.name}")

            # Verify signature
            verify_cmd = ["codesign", "--verify", "--verbose", str(app_path)]
            subprocess.run(verify_cmd, check=True)
            print("[OK] Signature verified")

            if notarize:
                self._notarize_macos(app_path)

        except subprocess.CalledProcessError as e:
            print(f"[FAIL] Signing failed: {e}")

    def _notarize_macos(self, app_path: Path):
        """Submit app for Apple notarization."""
        print("\nSubmitting for notarization...")
        print("[WARNING] Notarization requires Apple Developer account and app-specific password.")
        print(
            "    See: https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution"
        )

        # This is a placeholder - actual notarization requires Apple ID credentials
        print("[WARNING] Automatic notarization not implemented. Manual steps:")
        print(f"    1. Create ZIP: ditto -c -k --keepParent {app_path} {app_path}.zip")
        print(
            f"    2. Submit: xcrun notarytool submit {app_path}.zip --apple-id <email> --password <password> --team-id <team>"
        )
        print("    3. Wait for approval email (5-15 minutes)")
        print("    4. Staple: xcrun stapler staple {app_path}")

    def _find_signtool(self) -> Path | None:
        """Locate SignTool.exe on Windows."""
        if platform.system() != "Windows":
            return None

        # Common Windows SDK paths
        sdk_paths = [
            Path(r"C:\Program Files (x86)\Windows Kits\10\bin"),
            Path(r"C:\Program Files\Windows Kits\10\bin"),
        ]

        for sdk_path in sdk_paths:
            if not sdk_path.exists():
                continue

            # Find latest version
            for arch_dir in sdk_path.glob("*/x64"):
                signtool = arch_dir / "signtool.exe"
                if signtool.exists():
                    return signtool

        return None

    def generate_checksums(self, exe_path: Path) -> dict[str, str]:
        """Generate SHA256 checksums for verification.

        Handles both single-file executables (Windows/macOS) and
        directory-based builds (Linux).
        """
        print(f"\nGenerating checksums for {exe_path.name}...")

        checksums = {}

        # Determine the actual file to checksum
        # On Linux, exe_path is a directory containing the executable
        if exe_path.is_dir():
            # Linux: Find the actual executable inside the directory
            actual_exe = exe_path / exe_path.name
            if not actual_exe.exists():
                # Fallback: look for any executable file
                for item in exe_path.iterdir():
                    if item.is_file() and not item.suffix:
                        actual_exe = item
                        break
            if not actual_exe.exists():
                print(f"[WARNING] No executable found in {exe_path}")
                return checksums
            target_file = actual_exe
            print(f"  Found executable: {target_file.name}")
        else:
            target_file = exe_path

        # SHA256
        sha256 = hashlib.sha256()
        with open(target_file, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        checksums["sha256"] = sha256.hexdigest()

        print(f"  SHA256: {checksums['sha256']}")

        # Write to file (next to the exe_path, not inside directory)
        checksum_file = exe_path.with_suffix(exe_path.suffix + ".sha256")
        checksum_file.write_text(f"{checksums['sha256']} *{target_file.name}\n")
        print(f"[OK] Checksums saved: {checksum_file.name}")

        return checksums

    def create_version_file(self):
        """Create version.json with build metadata."""
        print("\nCreating version metadata...")

        metadata = {
            "version": self.version,
            "build_date": subprocess.run(
                ["git", "log", "-1", "--format=%cd", "--date=iso"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            or "unknown",
            "commit_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            or "unknown",
            "platform": self.config.native_platform,
        }

        version_file = self.config.dist_dir / "version.json"
        with open(version_file, "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"[OK] Version file: {version_file}")


def main():
    parser = argparse.ArgumentParser(description="Build Sims 4 Pixel Mod Manager")
    parser.add_argument(
        "--platform",
        choices=["windows", "macos", "linux", "all"],
        default="current",
        help="Target platform (default: current platform)",
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean build artifacts before building"
    )
    parser.add_argument(
        "--sign", action="store_true", help="Sign executable (requires certificates)"
    )
    parser.add_argument("--cert-path", help="Path to Windows code signing certificate (.pfx)")
    parser.add_argument("--identity", help="macOS signing identity (Developer ID)")
    parser.add_argument(
        "--notarize", action="store_true", help="Notarize macOS app (requires Apple ID)"
    )
    parser.add_argument("--no-verify", action="store_true", help="Skip post-build verification")

    args = parser.parse_args()

    try:
        config = BuildConfig()
        builder = Builder(config)

        # Validate environment
        builder.validate_environment()

        # Clean if requested
        if args.clean:
            builder.clean()

        # Determine target platform
        if args.platform == "current":
            target_platform = config.native_platform
        elif args.platform == "all":
            print("[FAIL] Cross-platform builds not supported in this script.")
            print("  Build on each platform natively or use CI/CD pipeline.")
            return 1
        else:
            target_platform = args.platform

        # Check cross-compilation
        if target_platform != config.native_platform:
            print(f"[FAIL] Cannot build for {target_platform} on {config.native_platform}")
            print("  PyInstaller requires native builds on each platform.")
            return 1

        # Build
        exe_path = builder.build(target_platform)

        # Sign if requested
        if args.sign:
            if target_platform == BuildConfig.WINDOWS:
                builder.sign_windows(exe_path, args.cert_path)
            elif target_platform == BuildConfig.MACOS:
                builder.sign_macos(exe_path, args.identity, args.notarize)
            else:
                print("[WARNING] Code signing not implemented for Linux")

        # Generate checksums
        if not args.no_verify:
            builder.generate_checksums(exe_path)

        # Create version metadata
        builder.create_version_file()

        print("\n[SUCCESS] Build complete!")
        print(f"   Executable: {exe_path}")
        print(f"   Version: {builder.version}")

        return 0

    except Exception as e:
        print(f"\n[FAIL] Build failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
