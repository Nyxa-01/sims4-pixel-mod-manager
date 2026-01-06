"""Safe game process manager for deployment preparation.

This module provides safe detection and termination of Sims 4 and
related launcher processes to prevent file locks during mod deployment.
"""

import ctypes
import logging
import platform
import sys
import time
from typing import Optional

import psutil

from src.core.exceptions import GameProcessError

logger = logging.getLogger(__name__)


def is_admin() -> bool:
    """Check if running with administrator privileges.

    Returns:
        True if admin/root, False otherwise
    """
    try:
        if platform.system() == "Windows":
            return bool(ctypes.windll.shell32.IsUserAnAdmin() != 0)  # type: ignore[attr-defined]
        else:
            # Unix: Check if running as root
            import os

            return os.geteuid() == 0
    except Exception:
        return False


def request_admin_elevation() -> bool:
    """Request admin elevation (Windows only).

    Returns:
        True if elevation granted, False otherwise

    Note:
        On Windows, this will restart the app with UAC prompt.
        User must handle restart logic.
    """
    if platform.system() != "Windows":
        logger.warning("Admin elevation only supported on Windows")
        return False

    if is_admin():
        return True  # Already admin

    try:
        script = sys.argv[0]
        params = " ".join(sys.argv[1:])

        # Request elevation via ShellExecute
        ret = ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )

        # If ret > 32, elevation succeeded (app will restart)
        # If ret <= 32, user cancelled or error
        return bool(ret > 32)

    except Exception as e:
        logger.error(f"Admin elevation failed: {e}")
        return False


# Process names to monitor
GAME_PROCESS_NAMES = [
    "TS4_x64.exe",
    "TS4.exe",
    "Sims4.exe",
]

LAUNCHER_PROCESS_NAMES = [
    "Origin.exe",
    "EADesktop.exe",  # EA App
]

# Termination timeouts
GRACEFUL_TIMEOUT = 10  # seconds
FORCE_KILL_DELAY = 2  # seconds after graceful attempt


class GameProcessManager:
    """Context manager for safe game process handling.

    Example:
        >>> with GameProcessManager() as gpm:
        ...     if gpm.is_game_running():
        ...         success = gpm.close_game_safely()
        ...         if not success:
        ...             raise GameProcessError("Failed to close game")
    """

    def __init__(self, should_close_launchers: bool = False) -> None:
        """Initialize process manager.

        Args:
            should_close_launchers: Whether to also close Origin/EA App
        """
        self._should_close_launchers = should_close_launchers
        self._terminated_processes: list[dict] = []

    def __enter__(self) -> "GameProcessManager":
        """Enter context manager."""
        logger.debug("GameProcessManager context entered")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager and cleanup."""
        logger.debug("GameProcessManager context exited")
        # Context manager ensures proper cleanup

    def get_game_processes(self) -> list[psutil.Process]:
        """Get all running game processes.

        Returns:
            List of game process objects
        """
        processes: list[psutil.Process] = []

        try:
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    proc_name = proc.info.get("name", "")
                    if any(game.lower() in proc_name.lower() for game in GAME_PROCESS_NAMES):
                        processes.append(proc)
                        logger.debug(f"Found game process: {proc_name} (PID: {proc.pid})")

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            logger.error(f"Failed to enumerate processes: {e}")
            raise GameProcessError(
                "Failed to detect game processes",
                recovery_hint="Run application as administrator",
            ) from e

        return processes

    def get_launcher_processes(self) -> list[psutil.Process]:
        """Get all running launcher processes.

        Returns:
            List of launcher process objects
        """
        processes: list[psutil.Process] = []

        try:
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    proc_name = proc.info.get("name", "")
                    if any(
                        launcher.lower() in proc_name.lower() for launcher in LAUNCHER_PROCESS_NAMES
                    ):
                        processes.append(proc)
                        logger.debug(f"Found launcher process: {proc_name} (PID: {proc.pid})")

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            logger.warning(f"Failed to enumerate launcher processes: {e}")

        return processes

    def is_game_running(self) -> bool:
        """Check if any game process is running.

        Returns:
            True if game is detected
        """
        processes = self.get_game_processes()
        return len(processes) > 0

    def close_game_safely(self, timeout: int = GRACEFUL_TIMEOUT) -> bool:
        """Safely terminate game processes.

        Attempts graceful termination first, then force kill if needed.

        Args:
            timeout: Seconds to wait for graceful exit

        Returns:
            True if all processes successfully closed
        """
        processes = self.get_game_processes()

        if not processes:
            logger.info("No game processes to close")
            return True

        logger.info(f"Closing {len(processes)} game process(es)")

        # Store process info for potential restoration
        for proc in processes:
            try:
                self._terminated_processes.append(
                    {
                        "pid": proc.pid,
                        "name": proc.name(),
                        "exe": proc.exe(),
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Step 1: Graceful termination
        for proc in processes:
            try:
                logger.debug(f"Sending terminate signal to {proc.name()} (PID: {proc.pid})")
                proc.terminate()
            except psutil.NoSuchProcess:
                logger.debug(f"Process {proc.pid} already exited")
            except psutil.AccessDenied:
                logger.warning(f"Access denied for process {proc.pid}")
                raise GameProcessError(
                    f"Insufficient permissions to close {proc.name()}",
                    recovery_hint="Run application as administrator",
                )

        # Step 2: Wait for graceful exit
        if self.wait_for_game_exit(timeout):
            logger.info("Game closed gracefully")
            return True

        # Step 3: Force kill remaining processes
        logger.warning("Graceful close timeout, forcing termination")

        remaining = self.get_game_processes()
        for proc in remaining:
            try:
                logger.debug(f"Force killing {proc.name()} (PID: {proc.pid})")
                proc.kill()
                time.sleep(FORCE_KILL_DELAY)
            except psutil.NoSuchProcess:
                pass
            except psutil.AccessDenied:
                logger.error(f"Cannot force kill process {proc.pid}")
                raise GameProcessError(
                    f"Failed to terminate {proc.name()}",
                    recovery_hint="Manually close the game and retry",
                )

        # Final verification
        if self.is_game_running():
            logger.error("Failed to close all game processes")
            return False

        logger.info("Game forcefully closed")
        return True

    def close_launchers(self, timeout: int = GRACEFUL_TIMEOUT) -> bool:
        """Close launcher processes (Origin/EA App).

        Args:
            timeout: Seconds to wait for graceful exit

        Returns:
            True if all launchers successfully closed
        """
        processes = self.get_launcher_processes()

        if not processes:
            logger.info("No launcher processes to close")
            return True

        logger.info(f"Closing {len(processes)} launcher process(es)")

        # Graceful termination only for launchers
        for proc in processes:
            try:
                logger.debug(f"Terminating {proc.name()} (PID: {proc.pid})")
                proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.warning(f"Failed to terminate launcher: {e}")

        # Wait for exit
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.get_launcher_processes():
                logger.info("Launchers closed successfully")
                return True
            time.sleep(0.5)

        # Don't force kill launchers (user may have other games)
        remaining = self.get_launcher_processes()
        if remaining:
            logger.warning(f"{len(remaining)} launcher(s) still running")
            return False

        return True

    def wait_for_game_exit(self, timeout: int = GRACEFUL_TIMEOUT) -> bool:
        """Wait for game to exit.

        Args:
            timeout: Maximum seconds to wait

        Returns:
            True if game exited within timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if not self.is_game_running():
                logger.debug("Game exited")
                return True
            time.sleep(0.5)

        logger.warning(f"Game still running after {timeout}s")
        return False

    def get_terminated_processes(self) -> list[dict]:
        """Get list of processes that were terminated.

        Returns:
            List of process info dicts with pid, name, exe
        """
        return self._terminated_processes.copy()

    def restore_processes(self) -> bool:
        """Attempt to restore terminated processes.

        NOTE: This will restart the game/launchers if they were closed.
        Use only if deployment is cancelled by user.

        Returns:
            True if restoration was attempted
        """
        if not self._terminated_processes:
            logger.debug("No processes to restore")
            return False

        logger.info("Attempting to restore terminated processes")

        for proc_info in self._terminated_processes:
            try:
                import subprocess

                exe_path = proc_info.get("exe")
                if exe_path:
                    logger.debug(f"Restarting {proc_info['name']}")
                    subprocess.Popen(
                        [exe_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            except Exception as e:
                logger.warning(f"Failed to restore {proc_info['name']}: {e}")

        # Clear restoration list
        self._terminated_processes.clear()
        return True


def check_game_status() -> dict[str, bool]:
    """Quick status check for game and launchers.

    Returns:
        Dict with 'game_running' and 'launcher_running' keys
    """
    manager = GameProcessManager()

    return {
        "game_running": manager.is_game_running(),
        "launcher_running": len(manager.get_launcher_processes()) > 0,
    }
