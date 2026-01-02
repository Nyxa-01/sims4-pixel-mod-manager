"""Modal dialogs with 8-bit styling."""

from .confirm_dialog import ConfirmDialog
from .error_dialog import ErrorDialog
from .progress_dialog import ProgressDialog
from .settings_dialog import SettingsDialog
from .update_dialog import UpdateDialog
from .wizard_dialog import WizardDialog

__all__ = [
    "ConfirmDialog",
    "ErrorDialog",
    "ProgressDialog",
    "SettingsDialog",
    "UpdateDialog",
    "WizardDialog",
]
