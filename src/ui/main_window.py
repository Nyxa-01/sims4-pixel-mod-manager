"""Main window UI for Sims 4 Pixel Mod Manager.

This module provides the primary application interface with drag-drop
mod management, load order visualization, and deployment controls.
"""

import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Optional

from src.core.deploy_engine import DeployEngine
from src.core.exceptions import (
    DeployError,
    LoadOrderError,
    ModManagerException,
    ModScanError,
)
from src.core.load_order_engine import LoadOrderEngine
from src.core.mod_scanner import ModFile, ModScanner
from src.utils.backup import BackupManager
from src.utils.config_manager import ConfigManager
from src.utils.game_detector import GameDetector
from src.utils.process_manager import GameProcessManager
from src.ui.pixel_theme import PixelTheme

logger = logging.getLogger(__name__)

# Window configuration
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_TITLE = "SIMS 4 PIXEL MOD MANAGER"


class MainWindow:
    """Main application window with drag-drop mod management.

    Example:
        >>> root = tk.Tk()
        >>> app = MainWindow(root)
        >>> root.mainloop()
    """

    def __init__(self, root: tk.Tk) -> None:
        """Initialize main window.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.theme = PixelTheme.get_instance()

        # Core managers
        self.config = ConfigManager.get_instance()
        self.scanner = ModScanner()
        self.load_order_engine = LoadOrderEngine()
        self.deploy_engine = DeployEngine()
        self.backup_manager = BackupManager()
        self.game_detector = GameDetector()

        # State
        self.incoming_mods: list[ModFile] = []
        self.load_order_slots: dict[str, tk.Listbox] = {}
        self.current_operation: Optional[threading.Thread] = None

        # UI Components
        self.status_label: Optional[tk.Label] = None
        self.progress_bar: Optional[tk.Canvas] = None

        self._setup_window()
        self._create_menu_bar()
        self._create_ui()
        self._bind_shortcuts()

        logger.info("Main window initialized")

    def _setup_window(self) -> None:
        """Configure root window properties."""
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(600, 400)

        # Apply theme
        self.theme.apply_theme(self.root)

        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (WINDOW_WIDTH // 2)
        y = (self.root.winfo_screenheight() // 2) - (WINDOW_HEIGHT // 2)
        self.root.geometry(f"+{x}+{y}")

    def _create_menu_bar(self) -> None:
        """Create menu bar with File, Tools, Help."""
        menubar = tk.Menu(
            self.root, bg=self.theme.colors["bg_dark"], fg=self.theme.colors["text"]
        )

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="Open Incoming Folder...",
            command=self._open_incoming_folder,
            accelerator="Ctrl+O",
        )
        file_menu.add_command(
            label="Refresh", command=self._refresh_display, accelerator="F5"
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(
            label="Scan Mods", command=self._scan_mods, accelerator="Ctrl+S"
        )
        tools_menu.add_command(
            label="Generate Load Order",
            command=self._generate_load_order,
            accelerator="Ctrl+G",
        )
        tools_menu.add_command(
            label="Deploy", command=self._deploy_mods, accelerator="Ctrl+D"
        )
        tools_menu.add_command(
            label="Backup", command=self._create_backup, accelerator="Ctrl+B"
        )
        tools_menu.add_separator()
        tools_menu.add_command(
            label="Settings...", command=self._open_settings, accelerator="Ctrl+,"
        )
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(
            label="Documentation", command=self._show_help, accelerator="F1"
        )
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _create_ui(self) -> None:
        """Create main UI layout."""
        # Header
        self._create_header()

        # Main content area (Incoming + Load Order)
        content_frame = self.theme.create_chunky_frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        # Left panel: Incoming mods
        self._create_incoming_panel(content_frame)

        # Right panel: Load order slots
        self._create_load_order_panel(content_frame)

        # Status bar
        self._create_status_bar()

    def _create_header(self) -> None:
        """Create header with title and action buttons."""
        header = self.theme.create_chunky_frame(
            self.root, color=self.theme.colors["primary"]
        )
        header.pack(fill=tk.X, padx=10, pady=10)

        # Title
        title_label = self.theme.create_pixel_label(
            header,
            WINDOW_TITLE,
            size="large",
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)

        # Action buttons
        button_frame = tk.Frame(header, bg=self.theme.colors["bg_mid"])
        button_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        scan_btn = self.theme.create_pixel_button(
            button_frame, "SCAN", command=self._scan_mods
        )
        scan_btn.pack(side=tk.LEFT, padx=5)

        generate_btn = self.theme.create_pixel_button(
            button_frame, "GENERATE", command=self._generate_structure
        )
        generate_btn.pack(side=tk.LEFT, padx=5)

        deploy_btn = self.theme.create_pixel_button(
            button_frame, "DEPLOY", command=self._deploy_mods
        )
        deploy_btn.pack(side=tk.LEFT, padx=5)

    def _create_incoming_panel(self, parent: tk.Frame) -> None:
        """Create incoming mods panel.

        Args:
            parent: Parent frame
        """
        incoming_frame = tk.Frame(parent, bg=self.theme.colors["bg_dark"])
        incoming_frame.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(10, 5), pady=10
        )
        incoming_frame.config(width=250)

        # Label
        label = self.theme.create_pixel_label(
            incoming_frame, "INCOMING MODS", size="normal"
        )
        label.pack(anchor=tk.W, pady=(0, 10))

        # Listbox with scrollbar
        listbox_frame = tk.Frame(incoming_frame, bg=self.theme.colors["bg_dark"])
        listbox_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.incoming_listbox = self.theme.create_pixel_listbox(
            listbox_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED,
        )
        self.incoming_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.incoming_listbox.yview)

        # Bind double-click to assign
        self.incoming_listbox.bind("<Double-Button-1>", self._assign_mod_to_slot)

        # Count label
        self.incoming_count_label = self.theme.create_pixel_label(
            incoming_frame,
            "0 mods",
            size="small",
        )
        self.incoming_count_label.pack(anchor=tk.W, pady=(10, 0))

    def _create_load_order_panel(self, parent: tk.Frame) -> None:
        """Create load order slots panel.

        Args:
            parent: Parent frame
        """
        load_order_frame = tk.Frame(parent, bg=self.theme.colors["bg_dark"])
        load_order_frame.pack(
            side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=10
        )

        # Label
        label = self.theme.create_pixel_label(
            load_order_frame, "LOAD ORDER", size="normal"
        )
        label.pack(anchor=tk.W, pady=(0, 10))

        # Scrollable slots
        canvas = tk.Canvas(
            load_order_frame,
            bg=self.theme.colors["bg_dark"],
            highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(load_order_frame, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.colors["bg_dark"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create slot widgets
        for slot_prefix, description, _ in self.load_order_engine.slots:
            self._create_slot_widget(scrollable_frame, slot_prefix, description)

    def _create_slot_widget(
        self, parent: tk.Frame, prefix: str, description: str
    ) -> None:
        """Create individual load order slot.

        Args:
            parent: Parent frame
            prefix: Slot prefix (e.g., "000_Core")
            description: Slot description
        """
        slot_frame = self.theme.create_chunky_frame(parent)
        slot_frame.pack(fill=tk.X, pady=5)

        # Header
        header_label = self.theme.create_pixel_label(
            slot_frame,
            f"{prefix} - {description}",
            size="small",
        )
        header_label.pack(anchor=tk.W, padx=10, pady=(5, 0))

        # Listbox for mods
        listbox = self.theme.create_pixel_listbox(
            slot_frame,
            height=4,
            selectmode=tk.EXTENDED,
        )
        listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Store reference
        self.load_order_slots[prefix] = listbox

        # Enable drag-drop (simplified - full implementation would use drag events)
        listbox.bind("<Double-Button-1>", lambda e: self._remove_from_slot(prefix))

    def _create_status_bar(self) -> None:
        """Create status bar with progress."""
        status_frame = self.theme.create_chunky_frame(
            self.root, color=self.theme.colors["secondary"]
        )
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

        # Status text
        self.status_label = self.theme.create_pixel_label(
            status_frame,
            "STATUS: Ready",
            size="small",
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Progress bar
        self.progress_bar = self.theme.create_progress_bar(
            status_frame,
            width=200,
            height=15,
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=10, pady=5)

    def _bind_shortcuts(self) -> None:
        """Bind keyboard shortcuts.

        Shortcuts:
            Ctrl+S: Scan incoming mods
            Ctrl+G: Generate load order
            Ctrl+D: Deploy mods to game
            Ctrl+B: Create backup
            Ctrl+,: Open settings
            F1: Show help
            F5: Refresh display
        """
        self.root.bind("<Control-s>", lambda e: self._scan_mods())
        self.root.bind("<Control-g>", lambda e: self._generate_load_order())
        self.root.bind("<Control-d>", lambda e: self._deploy_mods())
        self.root.bind("<Control-b>", lambda e: self._create_backup())
        self.root.bind("<Control-comma>", lambda e: self._open_settings())
        self.root.bind("<F1>", lambda e: self._show_help())
        self.root.bind("<F5>", lambda e: self._refresh_display())

        # Legacy shortcuts (keep for compatibility)
        self.root.bind("<Control-o>", lambda e: self._open_incoming_folder())

    def _update_status(self, message: str, progress: float = 0.0) -> None:
        """Update status bar.

        Args:
            message: Status message
            progress: Progress value (0.0-1.0)
        """
        if self.status_label:
            self.status_label.config(text=f"STATUS: {message}")

        if self.progress_bar:
            self.theme.update_progress_bar(self.progress_bar, progress)

        self.root.update_idletasks()

    def _scan_mods(self) -> None:
        """Scan incoming folder for mods."""
        self._update_status("Scanning mods...", 0.1)

        try:
            # Get incoming path from config
            incoming_path = Path(self.config.get("incoming_folder", ""))

            if not incoming_path.exists():
                # Prompt user for folder
                folder_str = filedialog.askdirectory(
                    title="Select Incoming Mods Folder"
                )
                if not folder_str:
                    self._update_status("Scan cancelled", 0.0)
                    return

                incoming_path = Path(folder_str)
                self.config.set("incoming_folder", str(incoming_path))
                self.config._save_config()

            # Run scan in background
            def scan_thread() -> None:
                try:
                    mods_by_category = self.scanner.scan_folder(incoming_path)

                    # Flatten to list
                    self.incoming_mods = []
                    for category, mods in mods_by_category.items():
                        self.incoming_mods.extend(mods)

                    # Update UI (must be on main thread)
                    self.root.after(0, self._update_incoming_list)
                    self.root.after(
                        0,
                        lambda: self._update_status(
                            f"Scanned {len(self.incoming_mods)} mods", 1.0
                        ),
                    )

                except Exception as e:
                    logger.error(f"Scan failed: {e}")
                    self.root.after(0, lambda: self._show_error("Scan Failed", str(e)))
                    self.root.after(0, lambda: self._update_status("Scan failed", 0.0))

            thread = threading.Thread(target=scan_thread, daemon=True)
            thread.start()

        except Exception as e:
            logger.error(f"Scan setup failed: {e}")
            self._show_error("Scan Error", str(e))
            self._update_status("Ready", 0.0)

    def _update_incoming_list(self) -> None:
        """Update incoming listbox with scanned mods."""
        self.incoming_listbox.delete(0, tk.END)

        for mod in self.incoming_mods:
            display_name = mod.path.name
            if not mod.is_valid:
                display_name += " [INVALID]"

            self.incoming_listbox.insert(tk.END, display_name)

        # Update count
        self.incoming_count_label.config(text=f"{len(self.incoming_mods)} mods")

    def _generate_structure(self) -> None:
        """Generate ActiveMods structure from load order."""
        self._update_status("Generating structure...", 0.3)

        try:
            # Get output path
            active_mods_path = Path(
                self.config.get("active_mods_folder", "./ActiveMods")
            )
            active_mods_path.mkdir(parents=True, exist_ok=True)

            # Collect mods from slots
            mods_by_slot: dict[str, list[ModFile]] = {}

            for prefix, listbox in self.load_order_slots.items():
                slot_mods = []
                for idx in range(listbox.size()):
                    mod_name = listbox.get(idx)
                    # Find corresponding ModFile
                    for mod in self.incoming_mods:
                        if mod.path.name == mod_name:
                            slot_mods.append(mod)
                            break

                if slot_mods:
                    mods_by_slot[prefix] = slot_mods

            # Generate structure
            self.load_order_engine.generate_structure(mods_by_slot, active_mods_path)

            self._update_status(f"Structure generated: {active_mods_path}", 1.0)
            messagebox.showinfo(
                "Success", f"ActiveMods structure created at:\n{active_mods_path}"
            )

        except Exception as e:
            logger.error(f"Structure generation failed: {e}")
            self._show_error("Generation Failed", str(e))
            self._update_status("Generation failed", 0.0)

    def _deploy_mods(self) -> None:
        """Deploy mods to game folder."""
        # Confirm game is not running
        if self.game_detector.is_game_running():
            response = messagebox.askyesno(
                "Game Running",
                "The Sims 4 is currently running. Close the game before deployment?\n\n"
                "The game will be closed automatically if you continue.",
            )

            if not response:
                self._update_status("Deployment cancelled", 0.0)
                return

        # Confirm deployment
        response = messagebox.askyesno(
            "Confirm Deployment",
            "This will deploy mods to your game folder.\n\n"
            "A backup will be created automatically.\n\n"
            "Continue?",
        )

        if not response:
            self._update_status("Deployment cancelled", 0.0)
            return

        # Run deployment in background
        def deploy_thread() -> None:
            try:
                self.root.after(0, lambda: self._update_status("Deploying...", 0.2))

                # Get paths
                active_mods_path = Path(
                    self.config.get("active_mods_folder", "./ActiveMods")
                )
                game_mods_path = self.game_detector.detect_mods_path()

                if not game_mods_path:
                    raise DeployError("Could not detect game Mods folder")

                # Progress callback
                def progress_callback(step: str, pct: float) -> None:
                    self.root.after(0, lambda: self._update_status(step, pct / 100.0))

                # Deploy with transaction
                with self.deploy_engine.transaction():
                    success = self.deploy_engine.deploy(
                        active_mods_path,
                        game_mods_path,
                        progress_callback=progress_callback,
                        close_game=True,
                    )

                if success:
                    self.root.after(
                        0,
                        lambda: messagebox.showinfo(
                            "Success", "Mods deployed successfully!"
                        ),
                    )
                    self.root.after(
                        0, lambda: self._update_status("Deployed successfully", 1.0)
                    )

            except Exception as e:
                logger.error(f"Deployment failed: {e}")
                self.root.after(
                    0, lambda: self._show_error("Deployment Failed", str(e))
                )
                self.root.after(
                    0, lambda: self._update_status("Deployment failed", 0.0)
                )

        thread = threading.Thread(target=deploy_thread, daemon=True)
        thread.start()

    def _create_backup(self) -> None:
        """Create backup of current mods."""
        self._update_status("Creating backup...", 0.2)

        try:
            active_mods_path = Path(
                self.config.get("active_mods_folder", "./ActiveMods")
            )
            backup_dir = Path(self.config.get("backup_folder", "./backups"))

            if not active_mods_path.exists():
                messagebox.showwarning("No Mods", "ActiveMods folder does not exist.")
                self._update_status("Ready", 0.0)
                return

            # Progress callback
            def progress_callback(pct: float) -> None:
                self.root.after(
                    0, lambda: self._update_status("Creating backup...", pct / 100.0)
                )

            # Create backup
            backup_path = self.backup_manager.create_backup(
                active_mods_path,
                backup_dir,
                progress_callback=progress_callback,
            )

            self._update_status(f"Backup created: {backup_path.name}", 1.0)
            messagebox.showinfo("Success", f"Backup created:\n{backup_path}")

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            self._show_error("Backup Failed", str(e))
            self._update_status("Backup failed", 0.0)

    def _assign_mod_to_slot(self, event: tk.Event) -> None:
        """Assign selected mod to a slot.

        Args:
            event: Double-click event
        """
        selection = self.incoming_listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        if idx >= len(self.incoming_mods):
            return

        mod = self.incoming_mods[idx]

        # Auto-assign to appropriate slot
        slot = self.load_order_engine.assign_mod_to_slot(mod)

        # Add to slot listbox
        if slot in self.load_order_slots:
            self.load_order_slots[slot].insert(tk.END, mod.path.name)
            logger.info(f"Assigned {mod.path.name} to {slot}")

    def _remove_from_slot(self, slot: str) -> None:
        """Remove selected mod from slot.

        Args:
            slot: Slot prefix
        """
        listbox = self.load_order_slots.get(slot)
        if not listbox:
            return

        selection = listbox.curselection()
        if not selection:
            return

        for idx in reversed(selection):
            listbox.delete(idx)

    def _open_incoming_folder(self) -> None:
        """Open file dialog to select incoming folder."""
        folder = filedialog.askdirectory(title="Select Incoming Mods Folder")
        if folder:
            self.config.set("incoming_folder", folder)
            self.config._save_config()
            self._scan_mods()

    def _open_settings(self) -> None:
        """Open settings dialog."""
        SettingsDialog(self.root, self.config)

    def _show_help(self) -> None:
        """Show help documentation."""
        HelpDialog(self.root)

    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            f"{WINDOW_TITLE}\n\n"
            "Version: 1.0.0\n"
            "Security-first Sims 4 mod manager\n"
            "with alphabetical load order\n\n"
            "© 2026\n"
            "GitHub: github.com/yourusername/sims4_pixel_mod_manager",
        )

    def _show_error(self, title: str, message: str) -> None:
        """Show error dialog.

        Args:
            title: Dialog title
            message: Error message
        """
        messagebox.showerror(title, message)

    def _generate_load_order(self) -> None:
        """Alias for _generate_structure for keyboard shortcut."""
        self._generate_structure()

    def _refresh_display(self) -> None:
        """Refresh mod lists and display.

        Re-scans incoming folder and updates UI.
        """
        logger.info("Refreshing display")
        self._scan_mods()


class SettingsDialog:
    """Settings configuration dialog."""

    def __init__(self, parent: tk.Tk, config: ConfigManager) -> None:
        """Initialize settings dialog.

        Args:
            parent: Parent window
            config: Config manager instance
        """
        self.config = config
        self.theme = PixelTheme.get_instance()

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.theme.apply_theme(self.dialog)

        self._create_ui()

    def _create_ui(self) -> None:
        """Create settings UI."""
        # Title
        title = self.theme.create_pixel_label(self.dialog, "SETTINGS", size="large")
        title.pack(pady=20)

        # Settings frame
        settings_frame = self.theme.create_chunky_frame(self.dialog)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Incoming folder
        self._create_path_setting(
            settings_frame,
            "Incoming Folder:",
            "incoming_folder",
            "./incoming",
        )

        # Active mods folder
        self._create_path_setting(
            settings_frame,
            "ActiveMods Folder:",
            "active_mods_folder",
            "./ActiveMods",
        )

        # Backup folder
        self._create_path_setting(
            settings_frame,
            "Backup Folder:",
            "backup_folder",
            "./backups",
        )

        # Buttons
        button_frame = tk.Frame(self.dialog, bg=self.theme.colors["bg_dark"])
        button_frame.pack(pady=20)

        save_btn = self.theme.create_pixel_button(
            button_frame, "SAVE", command=self._save
        )
        save_btn.pack(side=tk.LEFT, padx=5)

        cancel_btn = self.theme.create_pixel_button(
            button_frame, "CANCEL", command=self.dialog.destroy
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def _create_path_setting(
        self,
        parent: tk.Frame,
        label_text: str,
        config_key: str,
        default: str,
    ) -> None:
        """Create path setting row.

        Args:
            parent: Parent frame
            label_text: Label text
            config_key: Config key
            default: Default value
        """
        row = tk.Frame(parent, bg=self.theme.colors["bg_mid"])
        row.pack(fill=tk.X, padx=10, pady=5)

        label = self.theme.create_pixel_label(row, label_text, size="small")
        label.pack(anchor=tk.W, pady=5)

        entry = self.theme.create_pixel_entry(row)
        entry.insert(0, self.config.get(config_key, default))
        entry.pack(fill=tk.X, pady=5)

        # Store reference
        setattr(self, f"entry_{config_key}", entry)

    def _save(self) -> None:
        """Save settings."""
        try:
            # Get values from entries
            for key in ["incoming_folder", "active_mods_folder", "backup_folder"]:
                entry = getattr(self, f"entry_{key}", None)
                if entry:
                    value = entry.get()
                    self.config.set(key, value)

            self.config._save_config()
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{e}")


class HelpDialog:
    """Help documentation dialog."""

    def __init__(self, parent: tk.Tk) -> None:
        """Initialize help dialog.

        Args:
            parent: Parent window
        """
        self.theme = PixelTheme.get_instance()

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Help")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)

        self.theme.apply_theme(self.dialog)

        self._create_ui()

    def _create_ui(self) -> None:
        """Create help UI."""
        # Title
        title = self.theme.create_pixel_label(self.dialog, "HELP", size="large")
        title.pack(pady=20)

        # Help text
        text_frame = self.theme.create_chunky_frame(self.dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        help_text = scrolledtext.ScrolledText(
            text_frame,
            font=self.theme.font_small,
            bg=self.theme.colors["bg_mid"],
            fg=self.theme.colors["text"],
            wrap=tk.WORD,
        )
        help_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        help_text.insert(
            tk.END,
            """
SIMS 4 PIXEL MOD MANAGER - HELP

QUICK START:
1. Click SCAN to detect mods in Incoming folder
2. Double-click mods to assign to load order slots
3. Click GENERATE to create ActiveMods structure
4. Click DEPLOY to install to game folder

KEYBOARD SHORTCUTS:
Ctrl+O  - Open incoming folder
Ctrl+D  - Deploy mods
Ctrl+B  - Create backup
Ctrl+S  - Open settings
F1      - Show this help

LOAD ORDER SLOTS:
000_Core       - Core scripts and frameworks
010_Libraries  - Shared dependencies
020_MainMods   - Gameplay overhauls
030_Tuning     - XML tuning mods
040_CC         - Custom content
ZZZ_Overrides  - Override mods (load last)

FEATURES:
- Automatic backup before deployment
- CRC32 hash verification
- Conflict detection
- Game process management
- Encrypted config storage

For more information, visit the GitHub repository.
        """,
        )

        help_text.config(state=tk.DISABLED)

        # Close button
        close_btn = self.theme.create_pixel_button(
            self.dialog,
            "CLOSE",
            command=self.dialog.destroy,
        )
        close_btn.pack(pady=20)


def run_application() -> None:
    """Run the application."""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    run_application()
