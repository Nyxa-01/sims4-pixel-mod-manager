"""Progress dialog for long-running operations."""

import tkinter as tk
from collections.abc import Callable


class ProgressDialog(tk.Toplevel):
    """Modal progress dialog with cancel button.

    Usage:
        dialog = ProgressDialog(parent, title="Deploying...")
        dialog.set_progress(0.5, "Copying files...")
        dialog.show()
    """

    def __init__(self, parent, title: str = "Progress", cancelable: bool = True):
        """Initialize progress dialog.

        Args:
            parent: Parent window
            title: Dialog title
            cancelable: Whether cancel button is shown
        """
        super().__init__(parent)

        self.cancelled = False
        self.cancel_callback: Callable[[], None] | None = None

        # Window setup
        self.title(title)
        self.geometry("500x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Apply theme
        self.configure(bg="#1a1a1a")

        self._build_ui(cancelable)

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self, cancelable: bool) -> None:
        """Build dialog UI."""
        from ..widgets.pixel_button import PixelButton
        from ..widgets.progress_bar import PixelProgressBar

        # Title label
        self.title_label = tk.Label(
            self, text="Processing...", font=("Courier New", 12, "bold"), fg="#00e0ff", bg="#1a1a1a"
        )
        self.title_label.pack(pady=20)

        # Progress bar
        self.progress_bar = PixelProgressBar(self, segments=20, width=450, height=32)
        self.progress_bar.pack(pady=10)

        # Status label
        self.status_label = tk.Label(
            self, text="Initializing...", font=("Courier New", 9), fg="#00ff00", bg="#1a1a1a"
        )
        self.status_label.pack(pady=10)

        # Cancel button
        if cancelable:
            button_frame = tk.Frame(self, bg="#1a1a1a")
            button_frame.pack(pady=10)

            self.cancel_button = PixelButton(
                button_frame, text="❌ Cancel", command=self._cancel, width=120
            )
            self.cancel_button.pack()

    def set_progress(self, progress: float, status: str = "") -> None:
        """Update progress.

        Args:
            progress: Progress from 0.0 to 1.0
            status: Status message
        """
        self.progress_bar.set_progress(progress)
        if status:
            self.status_label.configure(text=status)
        self.update_idletasks()

    def set_title(self, title: str) -> None:
        """Update title.

        Args:
            title: New title text
        """
        self.title_label.configure(text=title)
        self.update_idletasks()

    def on_cancel(self, callback: Callable[[], None]) -> None:
        """Register cancel callback.

        Args:
            callback: Function called when cancelled
        """
        self.cancel_callback = callback

    def _cancel(self) -> None:
        """Handle cancel button."""
        self.cancelled = True
        if self.cancel_callback:
            self.cancel_callback()
        self.destroy()

    def _on_close(self) -> None:
        """Handle window close."""
        self._cancel()

    def show(self) -> None:
        """Show dialog (non-blocking)."""
        self.update_idletasks()
