"""Settings dialog for configuration management."""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...utils.config_manager import ConfigManager


class SettingsDialog(tk.Toplevel):
    """Modal settings dialog.

    Usage:
        dialog = SettingsDialog(parent, config_manager)
        result = dialog.show()
    """

    def __init__(self, parent: tk.Tk, config_manager: "ConfigManager") -> None:
        """Initialize settings dialog.

        Args:
            parent: Parent window
            config_manager: ConfigManager instance
        """
        super().__init__(parent)

        self.config_manager = config_manager
        self.result: dict[str, Any] | None = None

        # Window setup
        self.title("⚙️ Settings")
        self.geometry("600x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Apply theme
        self.configure(bg="#1a1a1a")

        self._build_ui()
        self._load_config()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        """Build dialog UI."""
        from ..widgets.chunky_frame import ChunkyFrame
        from ..widgets.pixel_button import PixelButton

        # Paths section
        paths_frame = ChunkyFrame(self, border_color="#00e0ff")
        paths_frame.pack(padx=20, pady=10, fill=tk.X)

        content = paths_frame.get_content_frame()

        tk.Label(
            content,
            text="📂 Paths",
            font=("Courier New", 10, "bold"),
            fg="#00e0ff",
            bg="#1a1a1a",
        ).pack(pady=5)

        # Game path
        tk.Label(
            content,
            text="Game Install:",
            font=("Courier New", 9),
            fg="#00ff00",
            bg="#1a1a1a",
        ).pack(anchor="w", padx=10, pady=(5, 0))

        game_frame = tk.Frame(content, bg="#1a1a1a")
        game_frame.pack(fill=tk.X, padx=10, pady=5)

        self.game_path_var = tk.StringVar()
        tk.Entry(
            game_frame,
            textvariable=self.game_path_var,
            font=("Consolas", 10),
            bg="#2a2a2a",
            fg="#ffffff",
            insertbackground="#00ff00",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        PixelButton(game_frame, text="📁", command=self._browse_game_path, width=50).pack(
            side=tk.LEFT
        )

        # Mods path
        tk.Label(
            content,
            text="Mods Folder:",
            font=("Courier New", 9),
            fg="#00ff00",
            bg="#1a1a1a",
        ).pack(anchor="w", padx=10, pady=(10, 0))

        mods_frame = tk.Frame(content, bg="#1a1a1a")
        mods_frame.pack(fill=tk.X, padx=10, pady=5)

        self.mods_path_var = tk.StringVar()
        tk.Entry(
            mods_frame,
            textvariable=self.mods_path_var,
            font=("Consolas", 10),
            bg="#2a2a2a",
            fg="#ffffff",
            insertbackground="#00ff00",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        PixelButton(mods_frame, text="📁", command=self._browse_mods_path, width=50).pack(
            side=tk.LEFT
        )

        # Options section
        options_frame = ChunkyFrame(self, border_color="#ff6ec7")
        options_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        opt_content = options_frame.get_content_frame()

        tk.Label(
            opt_content,
            text="⚙️ Options",
            font=("Courier New", 10, "bold"),
            fg="#ff6ec7",
            bg="#1a1a1a",
        ).pack(pady=5)

        # Auto backup
        self.auto_backup_var = tk.BooleanVar()
        tk.Checkbutton(
            opt_content,
            text="Auto-backup before deploy",
            variable=self.auto_backup_var,
            font=("Courier New", 9),
            fg="#00ff00",
            bg="#1a1a1a",
            selectcolor="#2a2a2a",
            activebackground="#1a1a1a",
            activeforeground="#00e0ff",
        ).pack(anchor="w", padx=10, pady=5)

        # Auto update
        self.auto_update_var = tk.BooleanVar()
        tk.Checkbutton(
            opt_content,
            text="Check for updates on startup",
            variable=self.auto_update_var,
            font=("Courier New", 9),
            fg="#00ff00",
            bg="#1a1a1a",
            selectcolor="#2a2a2a",
            activebackground="#1a1a1a",
            activeforeground="#00e0ff",
        ).pack(anchor="w", padx=10, pady=5)

        # Close game before deploy
        self.close_game_var = tk.BooleanVar()
        tk.Checkbutton(
            opt_content,
            text="Close game before deploy",
            variable=self.close_game_var,
            font=("Courier New", 9),
            fg="#00ff00",
            bg="#1a1a1a",
            selectcolor="#2a2a2a",
            activebackground="#1a1a1a",
            activeforeground="#00e0ff",
        ).pack(anchor="w", padx=10, pady=5)

        # Buttons
        button_frame = tk.Frame(self, bg="#1a1a1a")
        button_frame.pack(pady=20)

        PixelButton(button_frame, text="💾 Save", command=self._save, width=120).pack(
            side=tk.LEFT, padx=5
        )
        PixelButton(button_frame, text="❌ Cancel", command=self._cancel, width=120).pack(
            side=tk.LEFT, padx=5
        )

    def _load_config(self) -> None:
        """Load config into UI."""
        self.game_path_var.set(str(self.config_manager.get("game_path", "")))
        self.mods_path_var.set(str(self.config_manager.get("mods_path", "")))
        self.auto_backup_var.set(self.config_manager.get("auto_backup", True))
        self.auto_update_var.set(self.config_manager.get("check_updates", True))
        self.close_game_var.set(self.config_manager.get("close_game_before_deploy", True))

    def _browse_game_path(self) -> None:
        """Browse for game path."""
        path = filedialog.askdirectory(title="Select Sims 4 Install Folder")
        if path:
            self.game_path_var.set(path)

    def _browse_mods_path(self) -> None:
        """Browse for mods path."""
        path = filedialog.askdirectory(title="Select Mods Folder")
        if path:
            self.mods_path_var.set(path)

    def _save(self) -> None:
        """Save settings."""
        # Validate paths
        game_path = Path(self.game_path_var.get())
        mods_path = Path(self.mods_path_var.get())

        if not game_path.exists():
            messagebox.showerror("Error", "Game path does not exist")
            return

        if not mods_path.exists():
            messagebox.showerror("Error", "Mods path does not exist")
            return

        # Save config
        self.result = {
            "game_path": str(game_path),
            "mods_path": str(mods_path),
            "auto_backup": self.auto_backup_var.get(),
            "check_updates": self.auto_update_var.get(),
            "close_game_before_deploy": self.close_game_var.get(),
        }

        for key, value in self.result.items():
            self.config_manager.set(key, value)

        self.destroy()

    def _cancel(self) -> None:
        """Cancel dialog."""
        self.result = None
        self.destroy()

    def show(self) -> dict[str, Any] | None:
        """Show dialog and wait for result.

        Returns:
            Config dict or None if cancelled
        """
        self.wait_window()
        return self.result
