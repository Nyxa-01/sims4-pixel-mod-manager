"""Sims 4 Pixel Mod Manager - Main entry point."""

import ctypes
import logging
import platform
import sys
import tkinter as tk
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.state_manager import StateManager
from src.ui.main_window import MainWindow
from src.ui.splash_screen import SplashScreen
from src.utils.config_manager import ConfigManager
from src.utils.logger import setup_exception_logging, setup_logging
from src.utils.updater import Updater


def enable_dpi_awareness() -> None:
    """Enable DPI awareness for high-DPI displays.

    Makes GUI look crisp on high-resolution Windows displays.
    Supports Windows 8.1+ (per-monitor v2) and Windows Vista+ (system-wide).
    """
    if platform.system() != "Windows":
        return

    try:
        # Try Windows 8.1+ per-monitor DPI awareness v2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            # Fallback to Vista+ system DPI awareness
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass  # DPI awareness not available


def check_for_updates(root: tk.Tk) -> None:
    """Check for updates on startup (silent mode)."""
    try:
        updater = Updater(
            owner="yourusername",  # TODO: Update with actual GitHub username
            repo="sims4_pixel_mod_manager",
        )
        # Silent check - only shows dialog if update available
        updater.check_on_startup(root, silent=True)
    except Exception as e:
        logging.warning(f"Update check failed: {e}")


def main() -> None:
    """Application entry point."""
    try:
        # Enable high-DPI support (Windows 8.1+ and Vista+)
        enable_dpi_awareness()

        # Read version from VERSION file
        version_file = Path(__file__).parent / "VERSION"
        version = version_file.read_text().strip() if version_file.exists() else "1.0.0"

        # Show splash screen
        splash = SplashScreen(version=version)
        splash.show()

        # Setup logging
        splash.update_progress(0.1, "Setting up logging...")
        log_dir = Path.home() / ".sims4_mod_manager" / "logs"
        setup_logging(log_dir=log_dir, level="INFO")
        setup_exception_logging()
        logger = logging.getLogger(__name__)
        logger.info(f"Starting Sims 4 Pixel Mod Manager v{version}")

        # Load configuration
        splash.update_progress(0.3, "Loading configuration...")
        config_dir = Path.home() / ".sims4_mod_manager"
        config_manager = ConfigManager.get_instance(config_dir)

        # Initialize state manager
        splash.update_progress(0.5, "Initializing state...")
        state_manager = StateManager.get_instance()

        # Load paths from config
        splash.update_progress(0.7, "Loading paths...")
        game_path = config_manager.get("paths.game_path")
        mods_path = config_manager.get("paths.mods_path")

        if game_path and mods_path:
            state_manager.update_paths(game_path=Path(game_path), mods_path=Path(mods_path))

        # Create root window
        splash.update_progress(0.9, "Creating UI...")
        root = tk.Tk()

        # Initialize main window
        app = MainWindow(root)

        # Close splash
        splash.update_progress(1.0, "Ready!")
        splash.close()

        # Check for updates after UI loads (non-blocking)
        root.after(2000, lambda: check_for_updates(root))

        # Run application
        logger.info("Application ready")
        root.mainloop()

    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.info("Application terminated by user")
        sys.exit(0)

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception(f"Fatal error: {e}")

        # Close splash on error
        try:
            if "splash" in locals():
                splash.close()
        except Exception:
            pass

        # Show error dialog
        try:
            import tkinter.messagebox as mb

            mb.showerror(
                "Startup Error",
                f"Failed to start application:\n\n{str(e)}\n\nCheck logs for details.",
            )
        except Exception:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()
