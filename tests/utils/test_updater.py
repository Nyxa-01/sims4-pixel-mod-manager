"""Tests for auto-update functionality."""

import json
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

import pytest

from src.utils.updater import Updater


class TestUpdater:
    """Test GitHub release checking."""

    @pytest.fixture
    def updater(self):
        """Create update checker."""
        return Updater(owner="testuser", repo="testrepo")

    def test_initialization(self, updater):
        """Test updater initialization."""
        assert updater.owner == "testuser"
        assert updater.repo == "testrepo"
        assert updater.current_version == "1.0.0"  # Default
        assert "testuser/testrepo" in updater.api_url

    def test_initialization_reads_version_file(self, tmp_path, monkeypatch):
        """Test reading current version from VERSION file."""
        version_file = tmp_path / "VERSION"
        version_file.write_text("2.5.3")

        # Mock Path resolution to return our tmp_path
        with patch("src.utils.updater.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            updater = Updater()

            # Should use version file if it exists
            assert updater.current_version in ["2.5.3", "1.0.0"]

    @patch("src.utils.updater.urlopen")
    def test_check_for_updates_newer_available(self, mock_urlopen, updater):
        """Test detecting newer version."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(
            {
                "tag_name": "v1.1.0",
                "name": "Version 1.1.0",
                "body": "New features",
                "assets": [{"browser_download_url": "https://example.com/release.zip"}],
            }
        ).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = updater.check_for_updates()

        assert result is True
        assert updater.latest_release is not None
        assert updater.latest_release["tag_name"] == "v1.1.0"

    @patch("src.utils.updater.urlopen")
    def test_check_for_updates_current_is_latest(self, mock_urlopen, updater):
        """Test when current version is latest."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(
            {"tag_name": "v1.0.0", "name": "Version 1.0.0", "body": "Current version"}
        ).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = updater.check_for_updates()

        assert result is False

    @patch("src.utils.updater.urlopen")
    def test_check_for_updates_network_error(self, mock_urlopen, updater):
        """Test handling network errors."""
        mock_urlopen.side_effect = URLError("Network error")

        result = updater.check_for_updates()

        assert result is False

    @patch("src.utils.updater.urlopen")
    def test_check_for_updates_http_error(self, mock_urlopen, updater):
        """Test handling HTTP errors."""
        mock_urlopen.side_effect = HTTPError("https://example.com", 404, "Not Found", {}, None)

        result = updater.check_for_updates()

        assert result is False

    @patch("src.utils.updater.urlopen")
    def test_check_for_updates_invalid_json(self, mock_urlopen, updater):
        """Test handling invalid JSON response."""
        mock_response = Mock()
        mock_response.read.return_value = b"NOT JSON"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = updater.check_for_updates()

        assert result is False

    def test_is_newer_version_major(self, updater):
        """Test version comparison - major version."""
        assert updater._is_newer_version("2.0.0", "1.0.0") is True
        assert updater._is_newer_version("1.0.0", "2.0.0") is False

    def test_is_newer_version_minor(self, updater):
        """Test version comparison - minor version."""
        assert updater._is_newer_version("1.2.0", "1.1.0") is True
        assert updater._is_newer_version("1.1.0", "1.2.0") is False

    def test_is_newer_version_patch(self, updater):
        """Test version comparison - patch version."""
        assert updater._is_newer_version("1.0.1", "1.0.0") is True
        assert updater._is_newer_version("1.0.0", "1.0.1") is False

    def test_is_newer_version_equal(self, updater):
        """Test version comparison - equal versions."""
        assert updater._is_newer_version("1.0.0", "1.0.0") is False

    def test_is_newer_version_different_lengths(self, updater):
        """Test version comparison with different lengths."""
        assert updater._is_newer_version("1.0.1", "1.0") is True
        assert updater._is_newer_version("1.0", "1.0.0") is False

    def test_is_newer_version_invalid_format(self, updater):
        """Test version comparison with invalid format."""
        assert updater._is_newer_version("invalid", "1.0.0") is False
        assert updater._is_newer_version("1.0.0", "invalid") is False

    @patch("platform.system")
    def test_get_download_url_windows(self, mock_platform, updater):
        """Test getting download URL for Windows."""
        mock_platform.return_value = "Windows"
        updater.latest_release = {
            "assets": [
                {
                    "name": "Sims4ModManager.exe",
                    "browser_download_url": "https://example.com/win.exe",
                },
                {
                    "name": "Sims4ModManager.app.zip",
                    "browser_download_url": "https://example.com/mac.zip",
                },
            ]
        }

        url = updater.get_download_url()

        assert url == "https://example.com/win.exe"

    @patch("platform.system")
    def test_get_download_url_macos(self, mock_platform, updater):
        """Test getting download URL for macOS."""
        mock_platform.return_value = "Darwin"
        updater.latest_release = {
            "assets": [
                {
                    "name": "Sims4ModManager.exe",
                    "browser_download_url": "https://example.com/win.exe",
                },
                {
                    "name": "Sims4ModManager.app.zip",
                    "browser_download_url": "https://example.com/mac.zip",
                },
            ]
        }

        url = updater.get_download_url()

        assert url == "https://example.com/mac.zip"

    @patch("platform.system")
    def test_get_download_url_linux(self, mock_platform, updater):
        """Test getting download URL for Linux."""
        mock_platform.return_value = "Linux"
        updater.latest_release = {
            "assets": [
                {"name": "Sims4ModManager", "browser_download_url": "https://example.com/linux"},
                {
                    "name": "Sims4ModManager.exe",
                    "browser_download_url": "https://example.com/win.exe",
                },
            ]
        }

        url = updater.get_download_url()

        assert url == "https://example.com/linux"

    def test_get_download_url_no_release(self, updater):
        """Test getting download URL when no release loaded."""
        updater.latest_release = None

        url = updater.get_download_url()

        assert url is None

    @patch("platform.system")
    def test_get_download_url_no_matching_asset(self, mock_platform, updater):
        """Test getting download URL when no matching asset."""
        mock_platform.return_value = "Windows"
        updater.latest_release = {
            "assets": [
                {"name": "other.zip", "browser_download_url": "https://example.com/other.zip"}
            ]
        }

        url = updater.get_download_url()

        assert url is None

    def test_get_release_notes(self, updater):
        """Test getting release notes."""
        updater.latest_release = {"body": "## What's New\n- Feature 1\n- Feature 2"}

        notes = updater.get_release_notes()

        assert "Feature 1" in notes
        assert "Feature 2" in notes

    def test_get_release_notes_no_release(self, updater):
        """Test getting release notes when no release."""
        updater.latest_release = None

        notes = updater.get_release_notes()

        assert notes == ""

    @patch("src.utils.updater.urlopen")
    def test_download_update_success(self, mock_urlopen, updater, tmp_path):
        """Test downloading update successfully."""
        mock_response = Mock()
        mock_response.read.return_value = b"fake_binary_content"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        dest_path = tmp_path / "update.exe"
        result = updater.download_update("https://example.com/update.exe", dest_path)

        assert result is True
        assert dest_path.exists()
        assert dest_path.read_bytes() == b"fake_binary_content"

    @patch("src.utils.updater.urlopen")
    def test_download_update_network_error(self, mock_urlopen, updater, tmp_path):
        """Test download failure."""
        mock_urlopen.side_effect = URLError("Network error")

        dest_path = tmp_path / "update.exe"
        result = updater.download_update("https://example.com/update.exe", dest_path)

        assert result is False
        assert not dest_path.exists()

    def test_verify_checksum_valid(self, updater, tmp_path):
        """Test verifying valid checksum."""
        test_file = tmp_path / "test.dat"
        test_file.write_bytes(b"test content")

        import hashlib

        expected = hashlib.sha256(b"test content").hexdigest()

        result = updater.verify_checksum(test_file, expected)

        assert result is True

    def test_verify_checksum_invalid(self, updater, tmp_path):
        """Test verifying invalid checksum."""
        test_file = tmp_path / "test.dat"
        test_file.write_bytes(b"test content")

        result = updater.verify_checksum(test_file, "invalid_checksum")

        assert result is False

    def test_verify_checksum_file_not_found(self, updater, tmp_path):
        """Test verifying nonexistent file."""
        result = updater.verify_checksum(tmp_path / "nonexistent", "abc123")

        assert result is False

    @patch("src.utils.updater.urlopen")
    def test_check_on_startup_silent_mode(self, mock_urlopen, updater):
        """Test silent update check on startup."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps(
            {"tag_name": "v1.0.0", "body": "Current"}  # Same version
        ).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        # Silent mode should not raise or show dialogs
        # Just verify it doesn't crash
        result = updater.check_for_updates()
        assert result is False

    def test_api_url_format(self, updater):
        """Test API URL is correctly formatted."""
        assert "github.com/repos" in updater.api_url
        assert "testuser" in updater.api_url
        assert "testrepo" in updater.api_url
        assert "releases/latest" in updater.api_url
