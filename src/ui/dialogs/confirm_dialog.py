"""Simple confirmation dialog."""

import tkinter as tk


class ConfirmDialog(tk.Toplevel):
    """Yes/No confirmation with 8-bit styling.

    Usage:
        if ConfirmDialog.ask(parent, "Delete mod?", "This cannot be undone"):
            # User clicked Yes
    """

    def __init__(self, parent, title: str, message: str, icon: str = "❓"):
        """Initialize confirmation dialog.

        Args:
            parent: Parent window
            title: Dialog title
            message: Message text
            icon: Icon emoji (default: ❓)
        """
        super().__init__(parent)

        self.result = False

        # Window setup
        self.title(title)
        self.geometry("450x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Apply theme
        self.configure(bg="#1a1a1a")

        self._build_ui(icon, message)

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self, icon: str, message: str) -> None:
        """Build dialog UI.

        Args:
            icon: Icon emoji
            message: Message text
        """
        from ..widgets.pixel_button import PixelButton

        # Icon
        tk.Label(self, text=icon, font=("Courier New", 32), fg="#00e0ff", bg="#1a1a1a").pack(
            pady=20
        )

        # Message
        tk.Label(
            self, text=message, font=("Courier New", 10), fg="#ffffff", bg="#1a1a1a", wraplength=400
        ).pack(pady=10)

        # Buttons
        button_frame = tk.Frame(self, bg="#1a1a1a")
        button_frame.pack(pady=20)

        PixelButton(button_frame, text="✓ Yes", command=self._confirm, width=100).pack(
            side=tk.LEFT, padx=10
        )

        PixelButton(button_frame, text="✗ No", command=self._cancel, width=100).pack(
            side=tk.LEFT, padx=10
        )

        # Bind Enter/Escape
        self.bind("<Return>", lambda e: self._confirm())
        self.bind("<Escape>", lambda e: self._cancel())

    def _confirm(self) -> None:
        """Handle confirm button."""
        self.result = True
        self.destroy()

    def _cancel(self) -> None:
        """Handle cancel button."""
        self.result = False
        self.destroy()

    def show(self) -> bool:
        """Show dialog and wait for result.

        Returns:
            True if confirmed, False otherwise
        """
        self.wait_window()
        return self.result

    @classmethod
    def ask(cls, parent, title: str, message: str, icon: str = "❓") -> bool:
        """Convenience method to show confirmation.

        Args:
            parent: Parent window
            title: Dialog title
            message: Message text
            icon: Icon emoji

        Returns:
            True if confirmed, False otherwise
        """
        dialog = cls(parent, title, message, icon)
        return dialog.show()
