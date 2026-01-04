"""Tests for game process manager."""

from unittest.mock import MagicMock, Mock, patch

import psutil
import pytest

from src.core.exceptions import GameProcessError
from src.utils.process_manager import (
    GAME_PROCESS_NAMES,
    LAUNCHER_PROCESS_NAMES,
    GameProcessManager,
    check_game_status,
)


@pytest.fixture
def manager() -> GameProcessManager:
    """Create GameProcessManager instance.

    Returns:
        GameProcessManager instance
    """
    return GameProcessManager()


@pytest.fixture
def mock_game_process() -> Mock:
    """Create mock game process.

    Returns:
        Mock psutil.Process for game
    """
    proc = MagicMock(spec=psutil.Process)
    proc.pid = 12345
    proc.name.return_value = "TS4_x64.exe"
    proc.exe.return_value = "C:/Program Files/The Sims 4/Game/Bin/TS4_x64.exe"
    proc.info = {"pid": 12345, "name": "TS4_x64.exe"}
    return proc


@pytest.fixture
def mock_launcher_process() -> Mock:
    """Create mock launcher process.

    Returns:
        Mock psutil.Process for launcher
    """
    proc = MagicMock(spec=psutil.Process)
    proc.pid = 67890
    proc.name.return_value = "Origin.exe"
    proc.exe.return_value = "C:/Program Files (x86)/Origin/Origin.exe"
    proc.info = {"pid": 67890, "name": "Origin.exe"}
    return proc


class TestGameProcessManager:
    """Test GameProcessManager class."""

    def test_initialization(self, manager: GameProcessManager) -> None:
        """Test manager initialization."""
        assert manager._should_close_launchers is False
        assert manager._terminated_processes == []

    def test_initialization_with_launcher_close(self) -> None:
        """Test manager with launcher close enabled."""
        manager = GameProcessManager(close_launchers=True)
        assert manager._should_close_launchers is True

    def test_context_manager(self, manager: GameProcessManager) -> None:
        """Test context manager protocol."""
        with manager as gpm:
            assert gpm is manager

    @patch("psutil.process_iter")
    def test_get_game_processes_found(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
        mock_game_process: Mock,
    ) -> None:
        """Test getting game processes when game is running."""
        mock_process_iter.return_value = [mock_game_process]

        processes = manager.get_game_processes()

        assert len(processes) == 1
        assert processes[0] == mock_game_process

    @patch("psutil.process_iter")
    def test_get_game_processes_not_found(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test getting game processes when none are running."""
        # Mock non-game process
        other_proc = MagicMock()
        other_proc.info = {"pid": 999, "name": "notepad.exe"}
        mock_process_iter.return_value = [other_proc]

        processes = manager.get_game_processes()

        assert len(processes) == 0

    @patch("psutil.process_iter")
    def test_get_game_processes_multiple(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test getting multiple game processes."""
        proc1 = MagicMock()
        proc1.info = {"pid": 111, "name": "TS4_x64.exe"}

        proc2 = MagicMock()
        proc2.info = {"pid": 222, "name": "TS4.exe"}

        mock_process_iter.return_value = [proc1, proc2]

        processes = manager.get_game_processes()

        assert len(processes) == 2

    @patch("psutil.process_iter")
    def test_get_game_processes_access_denied(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test handling AccessDenied during enumeration."""
        proc1 = MagicMock()
        proc1.info = {"pid": 111, "name": "TS4_x64.exe"}

        proc2 = MagicMock()
        proc2.info.side_effect = psutil.AccessDenied("denied")

        mock_process_iter.return_value = [proc1, proc2]

        # Should return found processes, skip denied
        processes = manager.get_game_processes()
        assert len(processes) == 1

    @patch("psutil.process_iter")
    def test_get_launcher_processes(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
        mock_launcher_process: Mock,
    ) -> None:
        """Test getting launcher processes."""
        mock_process_iter.return_value = [mock_launcher_process]

        processes = manager.get_launcher_processes()

        assert len(processes) == 1
        assert processes[0] == mock_launcher_process

    @patch("psutil.process_iter")
    def test_is_game_running_true(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
        mock_game_process: Mock,
    ) -> None:
        """Test game running detection."""
        mock_process_iter.return_value = [mock_game_process]

        assert manager.is_game_running() is True

    @patch("psutil.process_iter")
    def test_is_game_running_false(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test game not running detection."""
        mock_process_iter.return_value = []

        assert manager.is_game_running() is False

    @patch("psutil.process_iter")
    def test_close_game_safely_no_processes(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test closing when no game processes exist."""
        mock_process_iter.return_value = []

        result = manager.close_game_safely()

        assert result is True

    @patch("psutil.process_iter")
    @patch("time.sleep")
    def test_close_game_safely_graceful(
        self,
        mock_sleep: Mock,
        mock_process_iter: Mock,
        manager: GameProcessManager,
        mock_game_process: Mock,
    ) -> None:
        """Test graceful game closure."""
        # First call: process exists
        # Second call: process gone
        mock_process_iter.side_effect = [
            [mock_game_process],  # Initial detection
            [mock_game_process],  # After terminate
            [],  # Process exited
        ]

        result = manager.close_game_safely()

        assert result is True
        mock_game_process.terminate.assert_called_once()

    @patch("psutil.process_iter")
    def test_close_game_safely_access_denied(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
        mock_game_process: Mock,
    ) -> None:
        """Test handling AccessDenied during termination."""
        mock_process_iter.return_value = [mock_game_process]
        mock_game_process.terminate.side_effect = psutil.AccessDenied("denied")

        with pytest.raises(GameProcessError, match="Insufficient permissions"):
            manager.close_game_safely()

    @patch("psutil.process_iter")
    @patch("time.sleep")
    @patch("time.time")
    def test_close_game_safely_force_kill(
        self,
        mock_time: Mock,
        mock_sleep: Mock,
        mock_process_iter: Mock,
        manager: GameProcessManager,
        mock_game_process: Mock,
        disable_logging,
    ) -> None:
        """Test force kill after graceful timeout.

        This test verifies that when a process doesn't exit gracefully within
        the timeout period, close_game_safely will force kill it.
        """
        # Track state to control process_iter behavior
        force_kill_happened = [False]

        def process_iter_side_effect(*args, **kwargs):
            # After kill() is called, return empty list (process gone)
            if force_kill_happened[0]:
                return []
            # Otherwise return the process (still running)
            return [mock_game_process]

        mock_process_iter.side_effect = process_iter_side_effect

        # Track kill call to signal process termination
        def kill_side_effect():
            force_kill_happened[0] = True

        mock_game_process.kill.side_effect = kill_side_effect

        # Control time progression. The wait_for_game_exit loop calls time.time()
        # for start_time and each loop condition check.
        # We want the loop to iterate a few times before timing out.
        time_call_count = [0]

        def time_side_effect():
            time_call_count[0] += 1
            if time_call_count[0] == 1:
                return 0  # start_time
            elif time_call_count[0] <= 3:
                return 0.05  # Within 0.1s timeout, loop continues
            return 0.2  # Past timeout, loop exits

        mock_time.side_effect = time_side_effect

        # Use a small but non-zero timeout to actually exercise the loop
        result = manager.close_game_safely(timeout=0.1)

        assert result is True
        mock_game_process.terminate.assert_called_once()
        mock_game_process.kill.assert_called_once()
        # Verify sleep was called (loop iterated at least once)
        assert mock_sleep.call_count >= 1

    @patch("psutil.process_iter")
    @patch("time.sleep")
    @patch("time.time")
    def test_wait_for_game_exit_success(
        self,
        mock_time: Mock,
        mock_sleep: Mock,
        mock_process_iter: Mock,
        manager: GameProcessManager,
        disable_logging,
    ) -> None:
        """Test waiting for game exit successfully.

        Verifies that when the game exits before the timeout, the function
        returns True.
        """
        # Track process_iter calls to simulate game exiting after 2 checks
        process_iter_call_count = [0]

        def process_iter_side_effect(*args, **kwargs):
            process_iter_call_count[0] += 1
            if process_iter_call_count[0] <= 2:
                # Game still running
                return [MagicMock(info={"name": "TS4_x64.exe"})]
            # Game exited
            return []

        mock_process_iter.side_effect = process_iter_side_effect

        # Time stays within timeout
        mock_time.return_value = 0

        result = manager.wait_for_game_exit(timeout=5)

        assert result is True
        # Verify loop iterated at least once
        assert mock_sleep.call_count >= 1

    @patch("psutil.process_iter")
    @patch("time.sleep")
    @patch("time.time")
    def test_wait_for_game_exit_timeout(
        self,
        mock_time: Mock,
        mock_sleep: Mock,
        mock_process_iter: Mock,
        manager: GameProcessManager,
        mock_game_process: Mock,
        disable_logging,
    ) -> None:
        """Test timeout when waiting for game exit.

        Verifies that when the game doesn't exit within the timeout period,
        the function returns False after the loop has iterated multiple times.
        """
        # Game never exits - always return process
        mock_process_iter.return_value = [mock_game_process]

        # Simulate time progression with a generator that won't exhaust:
        # - Call 1: 0 (start_time)
        # - Calls 2-4: values within timeout (loop iterates)
        # - Calls 5+: value past timeout (loop exits)
        time_call_count = [0]

        def time_side_effect():
            time_call_count[0] += 1
            if time_call_count[0] == 1:
                return 0  # start_time
            elif time_call_count[0] <= 4:
                # Within timeout - return values that allow 2-3 loop iterations
                return (time_call_count[0] - 1) * 3  # 3, 6, 9 seconds
            # Past timeout - always return value > timeout
            return 15

        mock_time.side_effect = time_side_effect

        result = manager.wait_for_game_exit(timeout=10)

        assert result is False
        # Verify the loop actually iterated (sleep was called)
        assert mock_sleep.call_count >= 1

    @patch("psutil.process_iter")
    @patch("time.sleep")
    @patch("time.time")
    def test_close_launchers(
        self,
        mock_time: Mock,
        mock_sleep: Mock,
        mock_process_iter: Mock,
        manager: GameProcessManager,
        mock_launcher_process: Mock,
        disable_logging,
    ) -> None:
        """Test closing launcher processes.

        Verifies that launchers are terminated gracefully and the function
        returns True when they exit.
        """
        # Track calls: first call returns launcher, subsequent calls return empty
        call_count = [0]

        def process_iter_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return [mock_launcher_process]  # Initial detection
            return []  # Launcher exited after terminate

        mock_process_iter.side_effect = process_iter_side_effect

        # Time stays within timeout
        mock_time.return_value = 0

        result = manager.close_launchers()

        assert result is True
        mock_launcher_process.terminate.assert_called_once()

    @patch("psutil.process_iter")
    def test_get_terminated_processes(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
        mock_game_process: Mock,
    ) -> None:
        """Test tracking terminated processes."""
        mock_process_iter.side_effect = [
            [mock_game_process],  # Initial detection
            [],  # After terminate
        ]

        manager.close_game_safely()
        terminated = manager.get_terminated_processes()

        assert len(terminated) == 1
        assert terminated[0]["name"] == "TS4_x64.exe"
        assert terminated[0]["pid"] == 12345

    @patch("subprocess.Popen")
    def test_restore_processes(
        self,
        mock_popen: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test restoring terminated processes."""
        # Manually add terminated process
        manager._terminated_processes.append(
            {
                "pid": 12345,
                "name": "TS4_x64.exe",
                "exe": "C:/path/to/game.exe",
            }
        )

        result = manager.restore_processes()

        assert result is True
        mock_popen.assert_called_once()
        assert len(manager._terminated_processes) == 0

    def test_restore_processes_empty(self, manager: GameProcessManager) -> None:
        """Test restore when no processes were terminated."""
        result = manager.restore_processes()

        assert result is False

    @patch("psutil.process_iter")
    def test_check_game_status(
        self,
        mock_process_iter: Mock,
        mock_game_process: Mock,
        mock_launcher_process: Mock,
    ) -> None:
        """Test quick status check function."""
        mock_process_iter.return_value = [mock_game_process, mock_launcher_process]

        status = check_game_status()

        assert status["game_running"] is True
        assert status["launcher_running"] is True

    @patch("psutil.process_iter")
    def test_process_names_coverage(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test all defined process names are detected."""
        # Create mock process for each name
        game_procs = [MagicMock(info={"name": name}) for name in GAME_PROCESS_NAMES]
        launcher_procs = [MagicMock(info={"name": name}) for name in LAUNCHER_PROCESS_NAMES]

        mock_process_iter.return_value = game_procs + launcher_procs

        found_games = manager.get_game_processes()
        found_launchers = manager.get_launcher_processes()

        assert len(found_games) == len(GAME_PROCESS_NAMES)
        assert len(found_launchers) == len(LAUNCHER_PROCESS_NAMES)
