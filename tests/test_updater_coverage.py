"""Extended coverage tests for the Updater module targeting uncovered lines."""

import io
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from urllib.error import HTTPError, URLError

import pytest

from src.utils.updater import Updater


class TestUpdaterCoverageExtended:
    """Additional tests targeting uncovered lines in Updater."""

    @pytest.fixture
    def updater(self):
        """Create update checker."""
        return Updater(owner="testuser", repo="testrepo")

    def test_download_update_success(self, updater, tmp_path):
        """Test successful update download (covers download_update flow)."""
        dest_file = tmp_path / "update.exe"
        test_content = b"fake_executable_content"

        mock_response = Mock()
        mock_response.read.return_value = test_content
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("src.utils.updater.urlopen", return_value=mock_response):
            result = updater.download_update(
                "https://example.com/update.exe",
                dest_file
            )

        assert result is True
        assert dest_file.exists()
        assert dest_file.read_bytes() == test_content

    def test_download_update_network_error(self, updater, tmp_path):
        """Test download failure on network error."""
        dest_file = tmp_path / "update.exe"

        with patch("src.utils.updater.urlopen", side_effect=URLError("Connection failed")):
            result = updater.download_update(
                "https://example.com/update.exe",
                dest_file
            )

        assert result is False
        assert not dest_file.exists()

    def test_download_update_http_error(self, updater, tmp_path):
        """Test download failure on HTTP error."""
        dest_file = tmp_path / "update.exe"

        with io.BytesIO(b"") as fp:
            http_error = HTTPError("https://example.com", 500, "Server Error", {}, fp)
            with patch("src.utils.updater.urlopen", side_effect=http_error):
                result = updater.download_update(
                    "https://example.com/update.exe",
                    dest_file
                )

        assert result is False

    def test_verify_checksum_valid(self, updater, tmp_path):
        """Test checksum verification with valid hash."""
        test_file = tmp_path / "test.exe"
        test_content = b"test file content"
        test_file.write_bytes(test_content)

        # Calculate actual SHA256
        import hashlib
        expected_hash = hashlib.sha256(test_content).hexdigest()

        result = updater.verify_checksum(test_file, expected_hash)
        assert result is True

    def test_verify_checksum_invalid(self, updater, tmp_path):
        """Test checksum verification with wrong hash."""
        test_file = tmp_path / "test.exe"
        test_file.write_bytes(b"test content")

        result = updater.verify_checksum(test_file, "wrong_hash")
        assert result is False

    def test_verify_checksum_file_not_found(self, updater, tmp_path):
        """Test checksum verification with missing file."""
        missing_file = tmp_path / "nonexistent.exe"

        result = updater.verify_checksum(missing_file, "any_hash")
        assert result is False

    def test_verify_checksum_large_file(self, updater, tmp_path):
        """Test checksum with chunked reading (large file simulation)."""
        test_file = tmp_path / "large.exe"
        # Create file larger than 8192 bytes to test chunked reading
        large_content = b"x" * 20000
        test_file.write_bytes(large_content)

        import hashlib
        expected_hash = hashlib.sha256(large_content).hexdigest()

        result = updater.verify_checksum(test_file, expected_hash)
        assert result is True

    def test_get_release_notes(self, updater):
        """Test getting release notes from latest release."""
        updater.latest_release = {
            "tag_name": "v1.1.0",
            "body": "## Release Notes\n- Bug fixes\n- New features"
        }

        notes = updater.get_release_notes()
        assert "Bug fixes" in notes
        assert "New features" in notes

    def test_get_release_notes_no_release(self, updater):
        """Test getting release notes when no release exists."""
        updater.latest_release = None

        notes = updater.get_release_notes()
        assert notes == ""

    def test_get_release_notes_empty_body(self, updater):
        """Test getting release notes with empty body."""
        updater.latest_release = {"tag_name": "v1.0.0"}

        notes = updater.get_release_notes()
        assert notes == ""

    def test_get_download_url_no_release(self, updater):
        """Test download URL when no release exists."""
        updater.latest_release = None

        url = updater.get_download_url()
        assert url is None

    @patch("platform.system")
    def test_get_download_url_unknown_platform(self, mock_platform, updater):
        """Test download URL for unknown platform."""
        mock_platform.return_value = "FreeBSD"
        updater.latest_release = {
            "assets": [
                {"name": "release.exe", "browser_download_url": "https://example.com/win.exe"}
            ]
        }

        url = updater.get_download_url()
        assert url is None

    @patch("platform.system")
    def test_get_download_url_no_matching_asset(self, mock_platform, updater):
        """Test download URL when no matching asset exists."""
        mock_platform.return_value = "Windows"
        updater.latest_release = {
            "assets": [
                {"name": "source.tar.gz", "browser_download_url": "https://example.com/src.tar.gz"}
            ]
        }

        url = updater.get_download_url()
        assert url is None

    @patch("platform.system")
    def test_get_download_url_empty_assets(self, mock_platform, updater):
        """Test download URL with empty assets list."""
        mock_platform.return_value = "Windows"
        updater.latest_release = {"assets": []}

        url = updater.get_download_url()
        assert url is None


class TestUpdaterUIComponents:
    """Tests for UI-related updater functionality."""

    @pytest.fixture
    def updater(self):
        """Create update checker."""
        return Updater(owner="testuser", repo="testrepo")

    @patch("tkinter.messagebox.askyesno")
    def test_prompt_update_dialog_accepted(self, mock_askyesno, updater):
        """Test update dialog when user accepts."""
        mock_parent = Mock()
        updater.latest_release = {
            "tag_name": "v1.1.0",
            "body": "New version"
        }
        mock_askyesno.return_value = True

        # Mock the download handler
        with patch.object(updater, "_handle_update_download"):
            updater.prompt_update_dialog(mock_parent)

        mock_askyesno.assert_called_once()

    @patch("tkinter.messagebox.askyesno")
    def test_prompt_update_dialog_declined(self, mock_askyesno, updater):
        """Test update dialog when user declines."""
        mock_parent = Mock()
        updater.latest_release = {
            "tag_name": "v1.1.0",
            "body": "New version"
        }
        mock_askyesno.return_value = False

        with patch.object(updater, "_handle_update_download") as mock_download:
            updater.prompt_update_dialog(mock_parent)

        # Download should not be called
        mock_download.assert_not_called()

    def test_prompt_update_dialog_no_release(self, updater):
        """Test update dialog when no release exists."""
        mock_parent = Mock()
        updater.latest_release = None

        # Should return early without showing dialog
        with patch("tkinter.messagebox.askyesno") as mock_askyesno:
            updater.prompt_update_dialog(mock_parent)

        mock_askyesno.assert_not_called()

    @patch("tkinter.messagebox.askyesno")
    def test_prompt_update_dialog_long_notes_truncated(self, mock_askyesno, updater):
        """Test that long release notes are truncated."""
        mock_parent = Mock()
        long_notes = "x" * 500  # More than 300 chars
        updater.latest_release = {
            "tag_name": "v1.1.0",
            "body": long_notes
        }
        mock_askyesno.return_value = False

        updater.prompt_update_dialog(mock_parent)

        # Check the call args for truncation
        call_args = mock_askyesno.call_args
        message = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("message", "")
        assert "..." in message

    @patch("tkinter.messagebox.showinfo")
    def test_check_on_startup_no_update_verbose(self, mock_showinfo, updater):
        """Test startup check shows message when not silent."""
        mock_parent = Mock()

        with patch.object(updater, "check_for_updates", return_value=False):
            updater.check_on_startup(mock_parent, silent=False)

        mock_showinfo.assert_called_once()

    def test_check_on_startup_no_update_silent(self, updater):
        """Test startup check is silent when no update."""
        mock_parent = Mock()

        with patch.object(updater, "check_for_updates", return_value=False):
            with patch("tkinter.messagebox.showinfo") as mock_showinfo:
                updater.check_on_startup(mock_parent, silent=True)

        mock_showinfo.assert_not_called()

    def test_check_on_startup_update_available(self, updater):
        """Test startup check prompts when update available."""
        mock_parent = Mock()

        with patch.object(updater, "check_for_updates", return_value=True):
            with patch.object(updater, "prompt_update_dialog") as mock_dialog:
                updater.check_on_startup(mock_parent, silent=True)

        mock_dialog.assert_called_once_with(mock_parent)


class TestHandleUpdateDownload:
    """Tests for _handle_update_download method."""

    @pytest.fixture
    def updater(self):
        """Create update checker."""
        return Updater(owner="testuser", repo="testrepo")

    @patch("tkinter.messagebox.showerror")
    @patch.object(Updater, "get_download_url", return_value=None)
    def test_handle_download_no_url(self, mock_get_url, mock_showerror, updater):
        """Test download handler when no URL available."""
        mock_parent = Mock()

        updater._handle_update_download(mock_parent)

        mock_showerror.assert_called_once()

    @patch("tkinter.Toplevel")
    @patch("tkinter.Label")
    @patch("tkinter.messagebox.showinfo")
    @patch.object(Updater, "get_download_url")
    @patch.object(Updater, "download_update")
    @patch("platform.system")
    @patch("subprocess.run")
    def test_handle_download_success_windows(
        self,
        mock_subprocess,
        mock_platform,
        mock_download,
        mock_get_url,
        mock_showinfo,
        mock_label,
        mock_toplevel,
        updater
    ):
        """Test successful download on Windows."""
        mock_parent = Mock()
        mock_platform.return_value = "Windows"
        mock_get_url.return_value = "https://example.com/Sims4ModManager.exe"
        mock_download.return_value = True

        # Mock the Toplevel dialog
        mock_dialog = Mock()
        mock_toplevel.return_value = mock_dialog

        updater._handle_update_download(mock_parent)

        mock_showinfo.assert_called_once()
        mock_subprocess.assert_called_once()

    @patch("tkinter.Toplevel")
    @patch("tkinter.Label")
    @patch("tkinter.messagebox.showerror")
    @patch.object(Updater, "get_download_url")
    @patch.object(Updater, "download_update")
    def test_handle_download_failure(
        self,
        mock_download,
        mock_get_url,
        mock_showerror,
        mock_label,
        mock_toplevel,
        updater
    ):
        """Test download failure handling."""
        mock_parent = Mock()
        mock_get_url.return_value = "https://example.com/update.exe"
        mock_download.return_value = False

        mock_dialog = Mock()
        mock_toplevel.return_value = mock_dialog

        updater._handle_update_download(mock_parent)

        mock_showerror.assert_called_once()
