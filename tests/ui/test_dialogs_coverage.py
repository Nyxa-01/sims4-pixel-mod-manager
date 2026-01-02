"""Extended test coverage for UI dialogs.

Tests for confirm_dialog.py, error_dialog.py, progress_dialog.py,
settings_dialog.py, update_dialog.py, wizard_dialog.py.
These tests import and validate dialog class structures without instantiating them.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import importlib


class TestConfirmDialogStructure:
    """Tests for ConfirmDialog class structure."""

    def test_confirm_dialog_class_exists(self):
        """Test ConfirmDialog class can be imported with mocked tkinter."""
        mock_tk = MagicMock()
        mock_tk.Toplevel = MagicMock
        mock_tk.Label = MagicMock
        mock_tk.Frame = MagicMock
        mock_tk.LEFT = "left"

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            # Force reimport
            if "src.ui.dialogs.confirm_dialog" in sys.modules:
                del sys.modules["src.ui.dialogs.confirm_dialog"]

            from src.ui.dialogs.confirm_dialog import ConfirmDialog

            assert hasattr(ConfirmDialog, "__init__")
            assert hasattr(ConfirmDialog, "_confirm")
            assert hasattr(ConfirmDialog, "_cancel")
            assert hasattr(ConfirmDialog, "show")
            assert hasattr(ConfirmDialog, "ask")

    def test_confirm_dialog_classmethod(self):
        """Test ConfirmDialog.ask is a classmethod."""
        mock_tk = MagicMock()
        mock_tk.Toplevel = MagicMock
        mock_tk.Label = MagicMock
        mock_tk.Frame = MagicMock
        mock_tk.LEFT = "left"

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            if "src.ui.dialogs.confirm_dialog" in sys.modules:
                del sys.modules["src.ui.dialogs.confirm_dialog"]

            from src.ui.dialogs.confirm_dialog import ConfirmDialog

            # ask should be a classmethod
            assert hasattr(ConfirmDialog.ask, "__func__")


class TestErrorDialogStructure:
    """Tests for ErrorDialog class structure."""

    def test_error_dialog_class_exists(self):
        """Test ErrorDialog class can be imported."""
        mock_tk = MagicMock()
        mock_tk.Toplevel = MagicMock
        mock_tk.Label = MagicMock
        mock_tk.Frame = MagicMock
        mock_tk.Scrollbar = MagicMock
        mock_tk.Text = MagicMock
        mock_tk.RIGHT = "right"
        mock_tk.Y = "y"
        mock_tk.BOTH = "both"
        mock_tk.X = "x"
        mock_tk.WORD = "word"
        mock_tk.DISABLED = "disabled"

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            if "src.ui.dialogs.error_dialog" in sys.modules:
                del sys.modules["src.ui.dialogs.error_dialog"]

            from src.ui.dialogs.error_dialog import ErrorDialog

            assert hasattr(ErrorDialog, "__init__")
            assert hasattr(ErrorDialog, "_toggle_details")
            assert hasattr(ErrorDialog, "_close")
            assert hasattr(ErrorDialog, "show")
            assert hasattr(ErrorDialog, "show_error")

    def test_error_dialog_has_show_error_classmethod(self):
        """Test ErrorDialog.show_error is a classmethod."""
        mock_tk = MagicMock()
        mock_tk.Toplevel = MagicMock
        mock_tk.Label = MagicMock
        mock_tk.Frame = MagicMock
        mock_tk.Scrollbar = MagicMock
        mock_tk.Text = MagicMock
        mock_tk.RIGHT = "right"
        mock_tk.Y = "y"
        mock_tk.BOTH = "both"
        mock_tk.X = "x"
        mock_tk.WORD = "word"
        mock_tk.DISABLED = "disabled"

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            if "src.ui.dialogs.error_dialog" in sys.modules:
                del sys.modules["src.ui.dialogs.error_dialog"]

            from src.ui.dialogs.error_dialog import ErrorDialog

            assert hasattr(ErrorDialog.show_error, "__func__")


class TestProgressDialogStructure:
    """Tests for ProgressDialog class structure."""

    def test_progress_dialog_class_exists(self):
        """Test ProgressDialog class can be imported."""
        mock_tk = MagicMock()
        mock_tk.Toplevel = MagicMock
        mock_tk.Label = MagicMock
        mock_tk.Frame = MagicMock

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            if "src.ui.dialogs.progress_dialog" in sys.modules:
                del sys.modules["src.ui.dialogs.progress_dialog"]

            from src.ui.dialogs.progress_dialog import ProgressDialog

            assert hasattr(ProgressDialog, "__init__")
            assert hasattr(ProgressDialog, "set_progress")
            assert hasattr(ProgressDialog, "set_title")
            assert hasattr(ProgressDialog, "on_cancel")
            assert hasattr(ProgressDialog, "_cancel")
            assert hasattr(ProgressDialog, "show")


class TestSettingsDialogStructure:
    """Tests for SettingsDialog class structure."""

    def test_settings_dialog_class_exists(self):
        """Test SettingsDialog class can be imported."""
        mock_tk = MagicMock()
        mock_tk.Toplevel = MagicMock
        mock_tk.Label = MagicMock
        mock_tk.Frame = MagicMock
        mock_tk.Entry = MagicMock
        mock_tk.StringVar = MagicMock
        mock_tk.BooleanVar = MagicMock
        mock_tk.Checkbutton = MagicMock
        mock_tk.LEFT = "left"
        mock_tk.X = "x"
        mock_tk.BOTH = "both"
        mock_tk.END = "end"
        mock_tk.W = "w"

        # Also mock filedialog
        mock_filedialog = MagicMock()

        with patch.dict(sys.modules, {"tkinter": mock_tk, "tkinter.filedialog": mock_filedialog}):
            if "src.ui.dialogs.settings_dialog" in sys.modules:
                del sys.modules["src.ui.dialogs.settings_dialog"]

            from src.ui.dialogs.settings_dialog import SettingsDialog

            assert hasattr(SettingsDialog, "__init__")


class TestUpdateDialogStructure:
    """Tests for UpdateDialog class structure."""

    def test_update_dialog_class_exists(self):
        """Test UpdateDialog class can be imported."""
        mock_tk = MagicMock()
        mock_tk.Toplevel = MagicMock
        mock_tk.Label = MagicMock
        mock_tk.Frame = MagicMock
        mock_tk.Text = MagicMock
        mock_tk.Scrollbar = MagicMock
        mock_tk.BOTH = "both"
        mock_tk.Y = "y"
        mock_tk.RIGHT = "right"
        mock_tk.WORD = "word"
        mock_tk.DISABLED = "disabled"
        mock_tk.LEFT = "left"

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            if "src.ui.dialogs.update_dialog" in sys.modules:
                del sys.modules["src.ui.dialogs.update_dialog"]

            from src.ui.dialogs.update_dialog import UpdateDialog

            assert hasattr(UpdateDialog, "__init__")


class TestWizardDialogStructure:
    """Tests for WizardDialog class structure."""

    def test_wizard_dialog_class_exists(self):
        """Test WizardDialog class can be imported."""
        mock_tk = MagicMock()
        mock_tk.Toplevel = MagicMock
        mock_tk.Label = MagicMock
        mock_tk.Frame = MagicMock
        mock_tk.Entry = MagicMock
        mock_tk.StringVar = MagicMock
        mock_tk.BOTH = "both"
        mock_tk.X = "x"
        mock_tk.LEFT = "left"
        mock_tk.RIGHT = "right"
        mock_tk.W = "w"
        mock_tk.E = "e"
        mock_tk.END = "end"

        mock_filedialog = MagicMock()

        with patch.dict(sys.modules, {"tkinter": mock_tk, "tkinter.filedialog": mock_filedialog}):
            if "src.ui.dialogs.wizard_dialog" in sys.modules:
                del sys.modules["src.ui.dialogs.wizard_dialog"]

            from src.ui.dialogs.wizard_dialog import WizardDialog

            assert hasattr(WizardDialog, "__init__")


class TestDialogPackageInit:
    """Tests for dialogs __init__.py."""

    def test_dialog_package_imports(self):
        """Test dialogs package exposes expected classes."""
        mock_tk = MagicMock()
        mock_tk.Toplevel = MagicMock
        mock_tk.Label = MagicMock
        mock_tk.Frame = MagicMock
        mock_tk.Entry = MagicMock
        mock_tk.StringVar = MagicMock
        mock_tk.BooleanVar = MagicMock
        mock_tk.Checkbutton = MagicMock
        mock_tk.Text = MagicMock
        mock_tk.Scrollbar = MagicMock
        mock_tk.BOTH = "both"
        mock_tk.X = "x"
        mock_tk.Y = "y"
        mock_tk.LEFT = "left"
        mock_tk.RIGHT = "right"
        mock_tk.W = "w"
        mock_tk.E = "e"
        mock_tk.END = "end"
        mock_tk.WORD = "word"
        mock_tk.DISABLED = "disabled"

        mock_filedialog = MagicMock()

        with patch.dict(sys.modules, {"tkinter": mock_tk, "tkinter.filedialog": mock_filedialog}):
            # Clear cached imports
            for key in list(sys.modules.keys()):
                if "src.ui.dialogs" in key:
                    del sys.modules[key]

            from src.ui.dialogs import (
                ConfirmDialog,
                ErrorDialog,
                ProgressDialog,
                SettingsDialog,
            )

            assert ConfirmDialog is not None
            assert ErrorDialog is not None
            assert ProgressDialog is not None
            assert SettingsDialog is not None
