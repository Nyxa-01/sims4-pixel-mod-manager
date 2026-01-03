"""First-run setup wizard dialog."""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional, Dict, Any


class WizardDialog(tk.Toplevel):
    """Multi-page setup wizard.

    Usage:
        wizard = WizardDialog(parent)
        result = wizard.show()
    """

    def __init__(self, parent):
        """Initialize wizard dialog.

        Args:
            parent: Parent window
        """
        super().__init__(parent)

        self.result: Optional[Dict[str, Any]] = None
        self.current_page = 0
        self.pages = ["welcome", "paths", "options"]

        # Window setup
        self.title("🧙 Setup Wizard")
        self.geometry("700x500")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Apply theme
        self.configure(bg="#1a1a1a")

        # Variables
        self.game_path_var = tk.StringVar()
        self.mods_path_var = tk.StringVar()
        self.auto_backup_var = tk.BooleanVar(value=True)
        self.auto_update_var = tk.BooleanVar(value=True)

        self._build_ui()
        self._show_page(0)

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        """Build wizard UI."""
        from ..widgets.pixel_button import PixelButton

        # Content area
        self.content_frame = tk.Frame(self, bg="#1a1a1a")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Navigation buttons
        nav_frame = tk.Frame(self, bg="#1a1a1a")
        nav_frame.pack(pady=20)

        self.back_button = PixelButton(nav_frame, text="← Back", command=self._go_back, width=100)
        self.back_button.pack(side=tk.LEFT, padx=5)

        self.next_button = PixelButton(nav_frame, text="Next →", command=self._go_next, width=100)
        self.next_button.pack(side=tk.LEFT, padx=5)

        self.finish_button = PixelButton(
            nav_frame, text="✓ Finish", command=self._finish, width=100
        )
        self.finish_button.pack(side=tk.LEFT, padx=5)
        self.finish_button.pack_forget()  # Hidden until last page

    def _clear_content(self) -> None:
        """Clear content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_page(self, page_num: int) -> None:
        """Show specific page.

        Args:
            page_num: Page index
        """
        self.current_page = page_num
        self._clear_content()

        if page_num == 0:
            self._build_welcome_page()
        elif page_num == 1:
            self._build_paths_page()
        elif page_num == 2:
            self._build_options_page()

        # Update navigation
        self.back_button.configure(state=tk.NORMAL if page_num > 0 else tk.DISABLED)

        if page_num == len(self.pages) - 1:
            self.next_button.pack_forget()
            self.finish_button.pack(side=tk.LEFT, padx=5)
        else:
            self.finish_button.pack_forget()
            self.next_button.pack(side=tk.LEFT, padx=5)

    def _build_welcome_page(self) -> None:
        """Build welcome page."""
        tk.Label(
            self.content_frame,
            text="🎮 Welcome to Sims 4 Pixel Mod Manager!",
            font=("Courier New", 14, "bold"),
            fg="#ff6ec7",
            bg="#1a1a1a",
        ).pack(pady=30)

        tk.Label(
            self.content_frame,
            text="This wizard will help you set up your mod manager.\n\n"
            "You'll need:\n"
            "• Sims 4 installation path\n"
            "• Mods folder location\n\n"
            "Click Next to continue.",
            font=("Courier New", 10),
            fg="#00ff00",
            bg="#1a1a1a",
            justify=tk.LEFT,
        ).pack(pady=20)

    def _build_paths_page(self) -> None:
        """Build paths configuration page."""
        from ..widgets.pixel_button import PixelButton

        tk.Label(
            self.content_frame,
            text="📂 Configure Paths",
            font=("Courier New", 12, "bold"),
            fg="#00e0ff",
            bg="#1a1a1a",
        ).pack(pady=20)

        # Game path
        tk.Label(
            self.content_frame,
            text="Sims 4 Installation:",
            font=("Courier New", 10),
            fg="#00ff00",
            bg="#1a1a1a",
        ).pack(anchor="w", padx=20, pady=(10, 5))

        game_frame = tk.Frame(self.content_frame, bg="#1a1a1a")
        game_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Entry(
            game_frame,
            textvariable=self.game_path_var,
            font=("Consolas", 10),
            bg="#2a2a2a",
            fg="#ffffff",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        PixelButton(game_frame, text="📁", command=self._browse_game, width=50).pack(side=tk.LEFT)

        # Mods path
        tk.Label(
            self.content_frame,
            text="Mods Folder:",
            font=("Courier New", 10),
            fg="#00ff00",
            bg="#1a1a1a",
        ).pack(anchor="w", padx=20, pady=(20, 5))

        mods_frame = tk.Frame(self.content_frame, bg="#1a1a1a")
        mods_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Entry(
            mods_frame,
            textvariable=self.mods_path_var,
            font=("Consolas", 10),
            bg="#2a2a2a",
            fg="#ffffff",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        PixelButton(mods_frame, text="📁", command=self._browse_mods, width=50).pack(side=tk.LEFT)

        # Auto-detect button
        PixelButton(
            self.content_frame, text="🔍 Auto-Detect Paths", command=self._auto_detect, width=200
        ).pack(pady=20)

    def _build_options_page(self) -> None:
        """Build options page."""
        tk.Label(
            self.content_frame,
            text="⚙️ Preferences",
            font=("Courier New", 12, "bold"),
            fg="#ff6ec7",
            bg="#1a1a1a",
        ).pack(pady=20)

        tk.Checkbutton(
            self.content_frame,
            text="Auto-backup before deployment",
            variable=self.auto_backup_var,
            font=("Courier New", 10),
            fg="#00ff00",
            bg="#1a1a1a",
            selectcolor="#2a2a2a",
        ).pack(anchor="w", padx=40, pady=10)

        tk.Checkbutton(
            self.content_frame,
            text="Check for updates on startup",
            variable=self.auto_update_var,
            font=("Courier New", 10),
            fg="#00ff00",
            bg="#1a1a1a",
            selectcolor="#2a2a2a",
        ).pack(anchor="w", padx=40, pady=10)

        tk.Label(
            self.content_frame,
            text="Click Finish to complete setup.",
            font=("Courier New", 9),
            fg="#00e0ff",
            bg="#1a1a1a",
        ).pack(pady=30)

    def _browse_game(self) -> None:
        """Browse for game path."""
        path = filedialog.askdirectory(title="Select Sims 4 Installation")
        if path:
            self.game_path_var.set(path)

    def _browse_mods(self) -> None:
        """Browse for mods path."""
        path = filedialog.askdirectory(title="Select Mods Folder")
        if path:
            self.mods_path_var.set(path)

    def _auto_detect(self) -> None:
        """Auto-detect game paths."""
        messagebox.showinfo("Auto-Detect", "Auto-detection not yet implemented")

    def _go_back(self) -> None:
        """Go to previous page."""
        if self.current_page > 0:
            self._show_page(self.current_page - 1)

    def _go_next(self) -> None:
        """Go to next page."""
        # Validate current page
        if self.current_page == 1:
            if not self.game_path_var.get() or not self.mods_path_var.get():
                messagebox.showerror("Error", "Please configure all paths")
                return

        if self.current_page < len(self.pages) - 1:
            self._show_page(self.current_page + 1)

    def _finish(self) -> None:
        """Finish wizard."""
        self.result = {
            "game_path": self.game_path_var.get(),
            "mods_path": self.mods_path_var.get(),
            "auto_backup": self.auto_backup_var.get(),
            "check_updates": self.auto_update_var.get(),
        }
        self.destroy()

    def show(self) -> Optional[Dict[str, Any]]:
        """Show wizard and wait for result.

        Returns:
            Configuration dict or None if cancelled
        """
        self.wait_window()
        return self.result
