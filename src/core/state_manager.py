"""Thread-safe application state manager.

Provides centralized state management with observer pattern for UI updates.
All state mutations are protected by locks for thread safety.
"""

import copy
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from threading import Lock, RLock
from typing import Optional


logger = logging.getLogger(__name__)


class AppState(Enum):
    """Application lifecycle states."""

    INITIALIZING = "initializing"
    READY = "ready"
    SCANNING = "scanning"
    GENERATING = "generating"
    DEPLOYING = "deploying"
    BACKING_UP = "backing_up"
    ERROR = "error"


@dataclass
class ModFile:
    """Represents a mod file with metadata."""

    path: Path
    size: int
    hash: str
    mod_type: str
    category: str
    is_valid: bool
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class ApplicationState:
    """Application state data structure."""

    app_state: AppState = AppState.INITIALIZING
    game_path: Path | None = None
    mods_path: Path | None = None
    incoming_mods: list[ModFile] = field(default_factory=list)
    active_mods: dict[str, list[ModFile]] = field(default_factory=dict)
    last_deploy: datetime | None = None
    total_deploys: int = 0
    is_game_running: bool = False
    current_operation: str | None = None
    progress: float = 0.0  # 0.0 to 1.0


class StateManager:
    """Thread-safe singleton state manager with observer pattern.

    Usage:
        state = StateManager.get_instance()
        state.set_state(AppState.SCANNING)
        state.register_observer(my_callback)
    """

    _instance: Optional["StateManager"] = None
    _lock: Lock = Lock()

    def __init__(self) -> None:
        """Private constructor. Use get_instance() instead."""
        if StateManager._instance is not None:
            raise RuntimeError("Use StateManager.get_instance() instead")

        self._state = ApplicationState()
        self._state_lock = RLock()  # Reentrant lock for nested calls
        self._observers: list[Callable[[ApplicationState], None]] = []
        self._observers_lock = Lock()

        logger.info("StateManager initialized")

    @classmethod
    def get_instance(cls) -> "StateManager":
        """Get singleton instance (thread-safe).

        Returns:
            StateManager singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-checked locking
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing only)."""
        with cls._lock:
            cls._instance = None

    def get_state(self) -> ApplicationState:
        """Get current state snapshot (thread-safe).

        Returns:
            Copy of current application state
        """
        with self._state_lock:
            # Return a copy to prevent external modification
            return copy.deepcopy(self._state)

    def set_state(self, new_state: AppState) -> None:
        """Set application state (thread-safe).

        Args:
            new_state: New application state
        """
        with self._state_lock:
            old_state = self._state.app_state
            self._state.app_state = new_state
            logger.info(f"State transition: {old_state.value} → {new_state.value}")
            self._notify_observers()

    def update_paths(self, game_path: Path | None = None, mods_path: Path | None = None) -> None:
        """Update game paths (thread-safe).

        Args:
            game_path: Path to Sims 4 installation
            mods_path: Path to Mods folder
        """
        with self._state_lock:
            if game_path is not None:
                self._state.game_path = game_path
                logger.info(f"Game path updated: {game_path}")
            if mods_path is not None:
                self._state.mods_path = mods_path
                logger.info(f"Mods path updated: {mods_path}")
            self._notify_observers()

    def set_incoming_mods(self, mods: list[ModFile]) -> None:
        """Set incoming mods list (thread-safe).

        Args:
            mods: List of scanned mod files
        """
        with self._state_lock:
            self._state.incoming_mods = mods
            logger.info(f"Incoming mods updated: {len(mods)} files")
            self._notify_observers()

    def set_active_mods(self, mods: dict[str, list[ModFile]]) -> None:
        """Set active mods by category (thread-safe).

        Args:
            mods: Dictionary mapping category to mod files
        """
        with self._state_lock:
            self._state.active_mods = mods
            total = sum(len(files) for files in mods.values())
            logger.info(f"Active mods updated: {total} files in {len(mods)} categories")
            self._notify_observers()

    def increment_deploy_count(self) -> None:
        """Increment deployment counter (thread-safe)."""
        with self._state_lock:
            self._state.total_deploys += 1
            self._state.last_deploy = datetime.now()
            logger.info(f"Deploy count: {self._state.total_deploys}")
            self._notify_observers()

    def set_game_running(self, is_running: bool) -> None:
        """Set game running status (thread-safe).

        Args:
            is_running: True if game is running
        """
        with self._state_lock:
            self._state.is_game_running = is_running
            logger.info(f"Game running: {is_running}")
            self._notify_observers()

    def set_operation(self, operation: str | None, progress: float = 0.0) -> None:
        """Set current operation and progress (thread-safe).

        Args:
            operation: Description of current operation (None if idle)
            progress: Progress from 0.0 to 1.0
        """
        with self._state_lock:
            self._state.current_operation = operation
            self._state.progress = max(0.0, min(1.0, progress))
            self._notify_observers()

    def register_observer(self, callback: Callable[[ApplicationState], None]) -> None:
        """Register observer for state changes.

        Args:
            callback: Function called with state on each change
        """
        with self._observers_lock:
            if callback not in self._observers:
                self._observers.append(callback)
                logger.debug(f"Observer registered: {callback.__name__}")

    def unregister_observer(self, callback: Callable[[ApplicationState], None]) -> None:
        """Unregister observer.

        Args:
            callback: Previously registered callback
        """
        with self._observers_lock:
            if callback in self._observers:
                self._observers.remove(callback)
                logger.debug(f"Observer unregistered: {callback.__name__}")

    def _notify_observers(self) -> None:
        """Notify all observers of state change (internal)."""
        state_copy = self.get_state()  # Get copy outside observer lock

        with self._observers_lock:
            for observer in self._observers:
                try:
                    observer(state_copy)
                except Exception as e:
                    logger.error(f"Observer {observer.__name__} failed: {e}")
