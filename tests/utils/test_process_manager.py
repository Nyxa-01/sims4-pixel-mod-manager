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
        assert manager.close_launchers is False
        assert manager._terminated_processes == []

    def test_initialization_with_launcher_close(self) -> None:
        """Test manager with launcher close enabled."""
        manager = GameProcessManager(close_launchers=True)
        assert manager.close_launchers is True

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

    @patch("time.time")
    @patch("psutil.process_iter")
    @patch("time.sleep")
    def test_close_game_safely_force_kill(
        self,
        mock_sleep: Mock,
        mock_process_iter: Mock,
        mock_time: Mock,
        manager: GameProcessManager,
        mock_game_process: Mock,
    ) -> None:
        """Test force kill after graceful timeout."""
        # Mock time progression to force timeout:
        # - start_time = 0 (first call in wait_for_game_exit)
        # - Loop iterations check time.time() twice per iteration (while condition + next iteration)
        # - Need to exceed timeout=1 to exit wait loop and trigger force kill
        mock_time.side_effect = [
            0,  # start_time
            0.3,  # First while check
            0.6,  # Second while check
            0.9,  # Third while check
            1.2,  # Fourth while check - exceeds timeout, exits loop
        ]

        # Process persists through wait period, only dies after force kill
        mock_process_iter.side_effect = [
            [mock_game_process],  # get_game_processes() in close_game_safely
            [mock_game_process],  # is_game_running() check #1 in wait loop
            [mock_game_process],  # is_game_running() check #2 in wait loop
            [mock_game_process],  # is_game_running() check #3 in wait loop
            [mock_game_process],  # get_game_processes() after wait timeout (for force kill)
            [],  # Final is_game_running() check after kill
        ]

        result = manager.close_game_safely(timeout=1)

        assert result is True
        mock_game_process.terminate.assert_called_once()
        mock_game_process.kill.assert_called_once()

    @patch("psutil.process_iter")
    @patch("time.sleep")
    def test_wait_for_game_exit_success(
        self,
        mock_sleep: Mock,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test waiting for game exit successfully."""
        # First call: game running, second call: game exited
        mock_process_iter.side_effect = [
            [MagicMock(info={"name": "TS4_x64.exe"})],
            [],
        ]

        result = manager.wait_for_game_exit(timeout=5)

        assert result is True

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
    ) -> None:
        """Test timeout when waiting for game exit."""
        # Game never exits
        mock_process_iter.return_value = [mock_game_process]

        # Simulate time passing
        mock_time.side_effect = [0, 11]  # Start, then past timeout

        result = manager.wait_for_game_exit(timeout=10)

        assert result is False

    @patch("psutil.process_iter")
    @patch("time.sleep")
    def test_close_launchers(
        self,
        mock_sleep: Mock,
        mock_process_iter: Mock,
        manager: GameProcessManager,
        mock_launcher_process: Mock,
    ) -> None:
        """Test closing launcher processes."""
        # First call: launcher exists, second: launcher gone
        mock_process_iter.side_effect = [
            [mock_launcher_process],  # Initial detection
            [],  # After terminate
        ]

        # Call via class to bypass method shadowing (self.close_launchers is bool)
        result = GameProcessManager.close_launchers(manager)

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


class TestProcessManagerExceptionPaths:
    """Tests for process manager exception handling and edge cases."""

    @patch("psutil.process_iter")
    def test_close_game_process_no_longer_exists(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test handling process that exits before termination."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "TS4_x64.exe", "pid": 12345}
        mock_proc.pid = 12345
        mock_proc.name.return_value = "TS4_x64.exe"
        mock_proc.terminate.side_effect = psutil.NoSuchProcess(12345)

        mock_process_iter.side_effect = [
            [mock_proc],  # Initial detection
            [],  # After termination (process gone)
        ]

        # Should handle gracefully (process already gone)
        result = manager.close_game_safely()
        assert result is True

    @patch("psutil.process_iter")
    def test_close_game_zombie_process(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test handling zombie processes."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "TS4_x64.exe", "pid": 12345}
        mock_proc.status.return_value = psutil.STATUS_ZOMBIE

        mock_process_iter.return_value = [mock_proc]

        # Should still attempt termination
        result = manager.close_game_safely()
        assert isinstance(result, bool)

    @patch("psutil.process_iter")
    def test_force_kill_failure(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test handling force kill failure during terminate."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "TS4_x64.exe", "pid": 12345}
        mock_proc.pid = 12345
        mock_proc.name.return_value = "TS4_x64.exe"
        # AccessDenied during terminate raises immediately
        mock_proc.terminate.side_effect = psutil.AccessDenied(12345)

        mock_process_iter.return_value = [mock_proc]

        with pytest.raises(GameProcessError, match="(Insufficient permissions|administrator)"):
            manager.close_game_safely(timeout=0)

    @patch("psutil.process_iter")
    @patch("subprocess.Popen")
    def test_restore_process_launch_failure(
        self,
        mock_popen: Mock,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test handling process restore failure."""
        manager._terminated_processes.append(
            {
                "pid": 12345,
                "name": "TS4_x64.exe",
                "exe": "C:/nonexistent/game.exe",
            }
        )

        mock_popen.side_effect = FileNotFoundError("Exe not found")

        # Should handle gracefully
        result = manager.restore_processes()
        assert isinstance(result, bool)

    @patch("psutil.process_iter")
    def test_multiple_concurrent_game_instances(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test handling multiple game instances running."""
        proc1 = MagicMock()
        proc1.info = {"name": "TS4_x64.exe", "pid": 111}

        proc2 = MagicMock()
        proc2.info = {"name": "TS4_x64.exe", "pid": 222}

        mock_process_iter.side_effect = [
            [proc1, proc2],  # Initial detection
            [],  # After termination
        ]

        result = manager.close_game_safely()

        assert result is True
        # Both should be terminated
        proc1.terminate.assert_called_once()
        proc2.terminate.assert_called_once()

    @patch("psutil.process_iter")
    def test_process_exit_during_enumeration(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test handling process that exits during enumeration."""
        mock_proc = MagicMock()
        # First access succeeds, second raises NoSuchProcess
        mock_proc.info.side_effect = [
            {"name": "TS4_x64.exe", "pid": 12345},
            psutil.NoSuchProcess(12345),
        ]

        mock_process_iter.return_value = [mock_proc]

        # Should handle gracefully
        processes = manager.get_game_processes()
        assert isinstance(processes, list)

    @patch("psutil.process_iter")
    def test_close_game_timeout_zero(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test immediate force kill with zero timeout."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "TS4_x64.exe", "pid": 12345}
        mock_proc.pid = 12345
        mock_proc.name.return_value = "TS4_x64.exe"
        mock_proc.exe.return_value = "C:/game.exe"

        # Need multiple calls: get_game_processes, wait loop, is_game_running after force kill
        mock_process_iter.side_effect = [
            [mock_proc],  # Initial detection
            [mock_proc],  # wait_for_game_exit check (still running)
            [mock_proc],  # Force kill: get_game_processes
            [
                mock_proc
            ],  # After kill: is_game_running check (still there - force kill failed in test)
        ]

        result = manager.close_game_safely(timeout=0)

        # With mocked process still present after kill, returns False
        assert result is False
        mock_proc.terminate.assert_called()
        mock_proc.kill.assert_called()

    @patch("time.time")
    @patch("psutil.process_iter")
    def test_wait_for_exit_time_calculation(
        self,
        mock_process_iter: Mock,
        mock_time: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test wait_for_game_exit time calculation."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "TS4_x64.exe"}

        # Simulate time progression
        mock_time.side_effect = [0, 2, 4, 6]  # Each check is 2 seconds
        mock_process_iter.side_effect = [
            [mock_proc],  # t=0: Still running
            [mock_proc],  # t=2: Still running
            [],  # t=4: Exited
        ]

        result = manager.wait_for_game_exit(timeout=10)

        assert result is True

    @patch("psutil.process_iter")
    def test_get_terminated_processes_details(
        self,
        mock_process_iter: Mock,
        manager: GameProcessManager,
    ) -> None:
        """Test terminated process tracking includes full details."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "TS4_x64.exe", "pid": 12345}
        mock_proc.exe.return_value = "C:/Sims4/game.exe"

        mock_process_iter.side_effect = [
            [mock_proc],
            [],
        ]

        manager.close_game_safely()
        terminated = manager.get_terminated_processes()

        assert len(terminated) == 1
        assert "name" in terminated[0]
        assert "pid" in terminated[0]
        assert "exe" in terminated[0]

    def test_context_manager_exception_safety(
        self,
        manager: GameProcessManager,
    ) -> None:
        """Test context manager handles exceptions properly."""
        with pytest.raises(ValueError):
            with manager:
                raise ValueError("Test exception")

        # Manager should still exit cleanly

    @patch("psutil.process_iter")
    def test_launcher_close_with_no_game(
        self,
        mock_process_iter: Mock,
    ) -> None:
        """Test closing launchers when game is not running."""
        # Instance variable close_launchers shadows method, call via class
        manager = GameProcessManager()

        mock_launcher = MagicMock()
        mock_launcher.info = {"name": "Origin.exe", "pid": 99999}
        mock_launcher.pid = 99999
        mock_launcher.name.return_value = "Origin.exe"

        # Mock get_launcher_processes: initial call, then after terminate
        mock_process_iter.side_effect = [
            [mock_launcher],  # Initial get_launcher_processes
            [],  # After terminate, launchers gone
        ]

        # Call method via class to avoid shadowing
        result = GameProcessManager.close_launchers(manager)

        assert result is True
        mock_launcher.terminate.assert_called_once()
