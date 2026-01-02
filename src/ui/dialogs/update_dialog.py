"""Update notification dialog."""

import tkinter as tk


class UpdateDialog(tk.Toplevel):
    """Update notification with changelog.

    Usage:
        dialog = UpdateDialog(parent, current="1.0.0", latest="1.1.0", changelog="...")
        if dialog.show():
            # User wants to download
    """

    def __init__(self, parent, current: str, latest: str, changelog: str):
        """Initialize update dialog.

        Args:
            parent: Parent window
            current: Current version
            latest: Latest version
            changelog: Changelog text
        """
        super().__init__(parent)

        self.result = False
        self.current_version = current
        self.latest_version = latest
        self.changelog_text = changelog

        # Window setup
        self.title("📦 Update Available")
        self.geometry("600x450")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Apply theme
        self.configure(bg="#1a1a1a")

        self._build_ui()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        """Build dialog UI."""
        from ..widgets.chunky_frame import ChunkyFrame
        from ..widgets.pixel_button import PixelButton

        # Header
        tk.Label(
            self,
            text="🚀 New Update Available!",
            font=("Courier New", 14, "bold"),
            fg="#00e0ff",
            bg="#1a1a1a",
        ).pack(pady=20)

        # Version info
        version_frame = ChunkyFrame(self, border_color="#ff6ec7", border_width=3)
        version_frame.pack(padx=20, pady=10, fill=tk.X)
        content = version_frame.get_content_frame()

        tk.Label(
            content,
            text=f"Current: v{self.current_version}",
            font=("Courier New", 10),
            fg="#ffffff",
            bg="#1a1a1a",
        ).pack(pady=5)

        tk.Label(
            content,
            text=f"Latest: v{self.latest_version}",
            font=("Courier New", 10, "bold"),
            fg="#00ff00",
            bg="#1a1a1a",
        ).pack(pady=5)

        # Changelog
        tk.Label(
            self,
            text="📝 What's New:",
            font=("Courier New", 10, "bold"),
            fg="#ff6ec7",
            bg="#1a1a1a",
        ).pack(anchor="w", padx=20, pady=(10, 5))

        changelog_frame = ChunkyFrame(self, border_color="#00e0ff", border_width=3)
        changelog_frame.pack(padx=20, pady=5, fill=tk.BOTH, expand=True)

        # Scrollable text
        text_content = changelog_frame.get_content_frame()

        scrollbar = tk.Scrollbar(text_content)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.changelog_text_widget = tk.Text(
            text_content,
            font=("Consolas", 9),
            bg="#2a2a2a",
            fg="#00ff00",
            wrap=tk.WORD,
            state=tk.DISABLED,
            yscrollcommand=scrollbar.set,
        )
        self.changelog_text_widget.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.changelog_text_widget.yview)

        # Insert changelog
        self.changelog_text_widget.config(state=tk.NORMAL)
        self.changelog_text_widget.insert("1.0", self.changelog_text)
        self.changelog_text_widget.config(state=tk.DISABLED)

        # Buttons
        button_frame = tk.Frame(self, bg="#1a1a1a")
        button_frame.pack(pady=20)

        PixelButton(button_frame, text="⬇️ Download", command=self._download, width=150).pack(
            side=tk.LEFT, padx=5
        )

        PixelButton(button_frame, text="Later", command=self._cancel, width=100).pack(
            side=tk.LEFT, padx=5
        )

    def _download(self) -> None:
        """Handle download button."""
        self.result = True
        self.destroy()

    def _cancel(self) -> None:
        """Handle cancel button."""
        self.result = False
        self.destroy()

    def show(self) -> bool:
        """Show dialog and wait for result.

        Returns:
            True if user wants to download, False otherwise
        """
        self.wait_window()
        return self.result
