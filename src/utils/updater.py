"""
Auto-update checker for Sims 4 Pixel Mod Manager
Checks GitHub releases for new versions and prompts user to update

Usage:
    from utils.updater import Updater

    updater = Updater()
    if updater.check_for_updates():
        updater.prompt_update_dialog(parent_window)
"""

import hashlib
import json
import logging
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)


class Updater:
    """Auto-update manager with GitHub releases integration."""

    GITHUB_API_URL = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
    CURRENT_VERSION = "1.0.0"  # Should match VERSION file

    def __init__(self, owner: str = "yourusername", repo: str = "sims4_pixel_mod_manager"):
        """
        Initialize updater.

        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
        """
        self.owner = owner
        self.repo = repo
        self.api_url = self.GITHUB_API_URL.format(owner=owner, repo=repo)
        self.latest_release: dict | None = None

        # Load current version from VERSION file
        version_file = Path(__file__).parent.parent.parent / "VERSION"
        if version_file.exists():
            self.current_version = version_file.read_text().strip()
        else:
            self.current_version = self.CURRENT_VERSION

    def check_for_updates(self, timeout: int = 5) -> bool:
        """
        Check if a new version is available.

        Args:
            timeout: Request timeout in seconds

        Returns:
            True if update available, False otherwise
        """
        try:
            logger.info("Checking for updates...")

            # Fetch latest release from GitHub API
            request = Request(self.api_url)
            request.add_header("Accept", "application/vnd.github.v3+json")

            with urlopen(request, timeout=timeout) as response:
                data = response.read()
                self.latest_release = json.loads(data.decode("utf-8"))

            latest_version = self.latest_release["tag_name"].lstrip("v")

            logger.info(f"Current: {self.current_version}, Latest: {latest_version}")

            # Compare versions
            if self._is_newer_version(latest_version, self.current_version):
                logger.info("Update available!")
                return True

            logger.info("Already up to date")
            return False

        except (URLError, HTTPError, KeyError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to check for updates: {e}")
            return False

    def _is_newer_version(self, latest: str, current: str) -> bool:
        """
        Compare semantic version strings.

        Args:
            latest: Latest version (e.g., "1.2.3")
            current: Current version (e.g., "1.2.0")

        Returns:
            True if latest > current
        """
        try:
            latest_parts = [int(x) for x in latest.split(".")]
            current_parts = [int(x) for x in current.split(".")]

            # Pad shorter version with zeros
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts += [0] * (max_len - len(latest_parts))
            current_parts += [0] * (max_len - len(current_parts))

            return latest_parts > current_parts

        except ValueError:
            logger.error("Invalid version format")
            return False

    def get_download_url(self) -> str | None:
        """
        Get download URL for current platform.

        Returns:
            Download URL or None if not found
        """
        if not self.latest_release:
            return None

        import platform

        system = platform.system()

        # Map platform to asset filename pattern
        patterns = {
            "Windows": "Sims4ModManager.exe",
            "Darwin": "Sims4ModManager.app.zip",  # macOS apps should be zipped for download
            "Linux": "Sims4ModManager",
        }

        target_pattern = patterns.get(system)
        if not target_pattern:
            logger.warning(f"No download pattern for platform: {system}")
            return None

        # Find matching asset
        for asset in self.latest_release.get("assets", []):
            if target_pattern in asset["name"]:
                url: str = asset["browser_download_url"]
                return url

        logger.warning(f"No asset found for pattern: {target_pattern}")
        return None

    def get_release_notes(self) -> str:
        """
        Get release notes for latest version.

        Returns:
            Release notes or empty string
        """
        if not self.latest_release:
            return ""

        body: str = self.latest_release.get("body", "") or ""
        return body

    def download_update(self, url: str, dest_path: Path) -> bool:
        """
        Download update file.

        Args:
            url: Download URL
            dest_path: Destination file path

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Downloading update from {url}...")

            with urlopen(url, timeout=30) as response:
                data = response.read()

            dest_path.write_bytes(data)
            logger.info(f"Downloaded to {dest_path}")
            return True

        except (URLError, HTTPError) as e:
            logger.error(f"Download failed: {e}")
            return False

    def verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """
        Verify downloaded file checksum.

        Args:
            file_path: Path to downloaded file
            expected_checksum: Expected SHA256 hash

        Returns:
            True if checksum matches, False otherwise
        """
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)

            actual = sha256.hexdigest()
            matches = actual == expected_checksum

            if not matches:
                logger.error(f"Checksum mismatch! Expected: {expected_checksum}, Got: {actual}")

            return matches

        except Exception as e:
            logger.error(f"Checksum verification failed: {e}")
            return False

    def prompt_update_dialog(self, parent: tk.Tk) -> None:
        """
        Show update dialog to user.

        Args:
            parent: Parent tkinter window
        """
        if not self.latest_release:
            return

        latest_version = self.latest_release["tag_name"].lstrip("v")
        release_notes = self.get_release_notes()

        # Truncate release notes if too long
        max_notes_length = 300
        if len(release_notes) > max_notes_length:
            release_notes = release_notes[:max_notes_length] + "..."

        message = (
            f"A new version is available!\n\n"
            f"Current version: {self.current_version}\n"
            f"Latest version: {latest_version}\n\n"
            f"Release notes:\n{release_notes}\n\n"
            f"Would you like to download the update?"
        )

        result = messagebox.askyesno(
            "Update Available",
            message,
            parent=parent,
        )

        if result:
            self._handle_update_download(parent)

    def _handle_update_download(self, parent: tk.Tk) -> None:
        """Handle update download and installation."""
        download_url = self.get_download_url()

        if not download_url:
            messagebox.showerror(
                "Update Error",
                "Could not find download for your platform.",
                parent=parent,
            )
            return

        # Download to temp directory
        temp_dir = Path(tempfile.gettempdir())
        filename = download_url.split("/")[-1]
        dest_path = temp_dir / filename

        # Show progress dialog
        progress_dialog = tk.Toplevel(parent)
        progress_dialog.title("Downloading Update")
        progress_dialog.geometry("400x100")
        progress_dialog.transient(parent)
        progress_dialog.grab_set()

        label = tk.Label(progress_dialog, text="Downloading update...", font=("Arial", 10))
        label.pack(pady=20)

        # Download in background (simplified - should use threading)
        success = self.download_update(download_url, dest_path)

        progress_dialog.destroy()

        if success:
            messagebox.showinfo(
                "Update Downloaded",
                f"Update downloaded to:\n{dest_path}\n\n"
                f"Please close the application and run the installer.",
                parent=parent,
            )

            # Open file location
            import platform

            if platform.system() == "Windows":
                import subprocess

                subprocess.run(["explorer", "/select,", str(dest_path)])
            elif platform.system() == "Darwin":
                import subprocess

                subprocess.run(["open", "-R", str(dest_path)])
        else:
            messagebox.showerror(
                "Download Failed",
                "Failed to download update. Please try again later.",
                parent=parent,
            )

    def check_on_startup(self, parent: tk.Tk, silent: bool = True) -> None:
        """
        Check for updates on application startup.

        Args:
            parent: Parent tkinter window
            silent: If True, only show dialog if update available
        """
        update_available = self.check_for_updates()

        if update_available:
            self.prompt_update_dialog(parent)
        elif not silent:
            messagebox.showinfo(
                "No Updates",
                "You are running the latest version.",
                parent=parent,
            )
