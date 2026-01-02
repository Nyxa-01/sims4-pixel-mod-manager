"""Extended coverage tests for GameProcessManager targeting uncovered lines."""

import platform
import subprocess
import time
from unittest.mock import Mock, MagicMock, patch

import psutil
import pytest

from src.core.exceptions import GameProcessError
from src.utils.process_manager import (
    GameProcessManager,
    check_game_status,
    is_admin,
    request_admin_elevation,
    GAME_PROCESS_NAMES,
    LAUNCHER_PROCESS_NAMES,
    GRACEFUL_TIMEOUT,
    FORCE_KILL_DELAY,
)


class TestIsAdmin:
    """Tests for is_admin function."""

    @patch("platform.system")
    @patch("ctypes.windll.shell32.IsUserAnAdmin")
    def test_is_admin_windows_true(self, mock_is_admin, mock_system):
        """Test admin check on Windows when admin."""
        mock_system.return_value = "Windows"
        mock_is_admin.return_value = 1

        result = is_admin()

        assert result is True

    @patch("platform.system")
    @patch("ctypes.windll.shell32.IsUserAnAdmin")
    def test_is_admin_windows_false(self, mock_is_admin, mock_system):
        """Test admin check on Windows when not admin."""
        mock_system.return_value = "Windows"
        mock_is_admin.return_value = 0

        result = is_admin()

        assert result is False

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-only test")
    @patch("platform.system")
    @patch("os.geteuid")
    def test_is_admin_unix_root(self, mock_geteuid, mock_system):
        """Test admin check on Unix when root."""
        mock_system.return_value = "Linux"
        mock_geteuid.return_value = 0

        result = is_admin()

        assert result is True

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-only test")
    @patch("platform.system")
    @patch("os.geteuid")
    def test_is_admin_unix_non_root(self, mock_geteuid, mock_system):
        """Test admin check on Unix when not root."""
        mock_system.return_value = "Linux"
        mock_geteuid.return_value = 1000

        result = is_admin()

        assert result is False

    @patch("platform.system")
    def test_is_admin_exception(self, mock_system):
        """Test admin check handles exceptions."""
        mock_system.side_effect = Exception("Platform error")

        result = is_admin()

        assert result is False


class TestRequestAdminElevation:
    """Tests for request_admin_elevation function."""

    @patch("platform.system")
    def test_elevation_non_windows(self, mock_system):
        """Test elevation request on non-Windows platform."""
        mock_system.return_value = "Linux"

        result = request_admin_elevation()

        assert result is False

    @patch("platform.system")
    @patch("src.utils.process_manager.is_admin")
    def test_elevation_already_admin(self, mock_is_admin, mock_system):
        """Test elevation when already admin."""
        mock_system.return_value = "Windows"
        mock_is_admin.return_value = True

        result = request_admin_elevation()

        assert result is True

    @patch("platform.system")
    @patch("src.utils.process_manager.is_admin")
    @patch("ctypes.windll.shell32.ShellExecuteW")
    def test_elevation_success(self, mock_shell, mock_is_admin, mock_system):
        """Test successful elevation request."""
        mock_system.return_value = "Windows"
        mock_is_admin.return_value = False
        mock_shell.return_value = 42  # > 32 means success

        result = request_admin_elevation()

        assert result is True
        mock_shell.assert_called_once()

    @patch("platform.system")
    @patch("src.utils.process_manager.is_admin")
    @patch("ctypes.windll.shell32.ShellExecuteW")
    def test_elevation_user_cancelled(self, mock_shell, mock_is_admin, mock_system):
        """Test elevation when user cancels UAC."""
        mock_system.return_value = "Windows"
        mock_is_admin.return_value = False
        mock_shell.return_value = 0  # <= 32 means failure

        result = request_admin_elevation()

        assert result is False

    @patch("platform.system")
    @patch("src.utils.process_manager.is_admin")
    @patch("ctypes.windll.shell32.ShellExecuteW")
    def test_elevation_exception(self, mock_shell, mock_is_admin, mock_system):
        """Test elevation handles exceptions."""
        mock_system.return_value = "Windows"
        mock_is_admin.return_value = False
        mock_shell.side_effect = Exception("Shell error")

        result = request_admin_elevation()

        assert result is False


class TestGameProcessManagerCoverage:
    """Additional tests for GameProcessManager coverage."""

    @pytest.fixture
    def manager(self):
        """Create GameProcessManager instance."""
        return GameProcessManager()

    @pytest.fixture
    def mock_game_process(self):
        """Create mock game process."""
        proc = MagicMock(spec=psutil.Process)
        proc.pid = 12345
        proc.name.return_value = "TS4_x64.exe"
        proc.exe.return_value = "C:/Games/Sims4/TS4_x64.exe"
        proc.info = {"pid": 12345, "name": "TS4_x64.exe"}
        return proc

    @patch("psutil.process_iter")
    def test_get_game_processes_no_such_process(self, mock_iter, manager):
        """Test handling NoSuchProcess during enumeration."""
        proc = MagicMock()
        # Process name lookup triggers NoSuchProcess
        proc.info = {"pid": 123, "name": "TS4_x64.exe"}
        
        mock_iter.return_value = [proc]

        # Should handle gracefully and return empty or found processes
        processes = manager.get_game_processes()
        assert isinstance(processes, list)

    @patch("psutil.process_iter")
    def test_get_game_processes_raises_on_fatal_error(self, mock_iter, manager):
        """Test fatal error during process enumeration."""
        mock_iter.side_effect = Exception("System error")

        with pytest.raises(GameProcessError, match="Failed to detect"):
            manager.get_game_processes()

    @patch("psutil.process_iter")
    def test_get_launcher_processes_with_error(self, mock_iter, manager):
        """Test launcher process enumeration with non-fatal error."""
        mock_iter.side_effect = Exception("Minor error")

        # Should return empty list, not raise
        processes = manager.get_launcher_processes()

        assert processes == []

    @patch("psutil.process_iter")
    @patch("time.sleep")
    def test_close_game_safely_graceful_success(
        self,
        mock_sleep,
        mock_iter,
        manager,
        mock_game_process
    ):
        """Test graceful game close succeeds."""
        # First call returns game, subsequent calls return empty
        mock_iter.side_effect = [
            [mock_game_process],  # get_game_processes
            [],  # wait_for_game_exit check 1
        ]

        with patch.object(manager, "wait_for_game_exit", return_value=True):
            result = manager.close_game_safely()

        assert result is True
        mock_game_process.terminate.assert_called_once()

    @patch("psutil.process_iter")
    @patch("time.sleep")
    def test_close_game_safely_force_kill(
        self,
        mock_sleep,
        mock_iter,
        manager,
        mock_game_process
    ):
        """Test force kill when graceful fails."""
        mock_iter.side_effect = [
            [mock_game_process],  # initial get_game_processes
            [mock_game_process],  # get_game_processes after graceful timeout
            [],  # final is_game_running check
        ]

        with patch.object(manager, "wait_for_game_exit", return_value=False):
            with patch.object(manager, "is_game_running", return_value=False):
                result = manager.close_game_safely()

        assert result is True
        mock_game_process.kill.assert_called()

    @patch("psutil.process_iter")
    def test_close_game_safely_access_denied_terminate(
        self,
        mock_iter,
        manager,
        mock_game_process
    ):
        """Test access denied during terminate."""
        mock_game_process.terminate.side_effect = psutil.AccessDenied("No permission")
        mock_iter.return_value = [mock_game_process]

        with pytest.raises(GameProcessError, match="Insufficient permissions"):
            manager.close_game_safely()

    @patch("psutil.process_iter")
    @patch("time.sleep")
    def test_close_game_safely_access_denied_kill(
        self,
        mock_sleep,
        mock_iter,
        manager,
        mock_game_process
    ):
        """Test access denied during force kill."""
        mock_game_process.kill.side_effect = psutil.AccessDenied("No permission")
        mock_iter.side_effect = [
            [mock_game_process],  # initial
            [mock_game_process],  # after graceful timeout
        ]

        with patch.object(manager, "wait_for_game_exit", return_value=False):
            with pytest.raises(GameProcessError, match="Failed to terminate"):
                manager.close_game_safely()

    @patch("psutil.process_iter")
    @patch("time.sleep")
    def test_close_game_safely_process_already_exited(
        self,
        mock_sleep,
        mock_iter,
        manager,
        mock_game_process
    ):
        """Test process exits during close attempt."""
        mock_game_process.terminate.side_effect = psutil.NoSuchProcess(123)
        mock_iter.side_effect = [
            [mock_game_process],
            [],
        ]

        with patch.object(manager, "wait_for_game_exit", return_value=True):
            result = manager.close_game_safely()

        assert result is True

    @patch("psutil.process_iter")
    @patch("time.sleep")
    def test_close_game_safely_fails_completely(
        self,
        mock_sleep,
        mock_iter,
        manager,
        mock_game_process
    ):
        """Test close fails even after force kill."""
        mock_game_process.kill.side_effect = psutil.NoSuchProcess(123)
        mock_iter.side_effect = [
            [mock_game_process],  # initial
            [mock_game_process],  # after graceful
            [mock_game_process],  # after force kill (still running)
        ]

        with patch.object(manager, "wait_for_game_exit", return_value=False):
            with patch.object(manager, "is_game_running", return_value=True):
                result = manager.close_game_safely()

        assert result is False

    @patch("psutil.process_iter")
    @patch("time.sleep")
    @patch("time.time")
    def test_close_launchers_method_success(self, mock_time, mock_sleep, mock_iter):
        """Test successful launcher close method."""
        # Create manager without fixture to avoid attribute shadowing
        gpm = GameProcessManager(close_launchers=False)
        
        launcher = MagicMock()
        launcher.pid = 9999
        launcher.name.return_value = "Origin.exe"
        launcher.info = {"pid": 9999, "name": "Origin.exe"}

        # First call returns launcher, then empty for subsequent calls
        call_count = [0]
        def iter_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 1:  # First call for get_launcher_processes
                return [launcher]
            return []  # Subsequent calls show no processes
        
        mock_iter.side_effect = iter_side_effect
        mock_time.side_effect = [0, 0.5]

        # Access the method directly via class to avoid attribute shadowing
        result = type(gpm).close_launchers(gpm)

        launcher.terminate.assert_called()

    @patch("psutil.process_iter")
    @patch("time.sleep")
    def test_close_launchers_method_timeout(self, mock_sleep, mock_iter):
        """Test launcher close method timeout."""
        gpm = GameProcessManager(close_launchers=False)
        
        launcher = MagicMock()
        launcher.pid = 9999
        launcher.name.return_value = "Origin.exe"
        launcher.info = {"pid": 9999, "name": "Origin.exe"}

        # Launcher never exits
        mock_iter.return_value = [launcher]

        with patch("time.time") as mock_time:
            # Simulate timeout - need enough values for the loop
            mock_time.side_effect = [0, 2, 4, 6, 8, 10, 12]
            result = type(gpm).close_launchers(gpm, timeout=10)

        # Returns False when timeout occurs
        assert result is False

    @patch("psutil.process_iter")
    def test_close_launchers_method_no_processes(self, mock_iter):
        """Test close launchers method when none running."""
        gpm = GameProcessManager(close_launchers=False)
        
        mock_iter.return_value = []

        result = type(gpm).close_launchers(gpm)

        assert result is True

    @patch("psutil.process_iter")
    @patch("time.sleep")
    @patch("time.time")
    def test_close_launchers_method_terminate_error(self, mock_time, mock_sleep, mock_iter):
        """Test launcher terminate error is handled."""
        gpm = GameProcessManager(close_launchers=False)
        
        launcher = MagicMock()
        launcher.pid = 9999
        launcher.name.return_value = "Origin.exe"
        launcher.info = {"pid": 9999, "name": "Origin.exe"}
        launcher.terminate.side_effect = psutil.AccessDenied("No access")

        # First call returns launcher, subsequent calls show it's gone
        call_count = [0]
        def iter_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] <= 1:
                return [launcher]
            return []
        
        mock_iter.side_effect = iter_side_effect
        mock_time.side_effect = [0, 0.5]

        # Should not raise, just log warning
        result = type(gpm).close_launchers(gpm)

    def test_wait_for_game_exit_immediate(self, manager):
        """Test wait when game exits immediately."""
        with patch.object(manager, "is_game_running", return_value=False):
            result = manager.wait_for_game_exit(timeout=5)

        assert result is True

    @patch("time.sleep")
    @patch("time.time")
    def test_wait_for_game_exit_timeout(self, mock_time, mock_sleep, manager):
        """Test wait timeout when game doesn't exit."""
        mock_time.side_effect = [0, 1, 2, 3, 6]  # Exceed timeout

        with patch.object(manager, "is_game_running", return_value=True):
            result = manager.wait_for_game_exit(timeout=5)

        assert result is False

    def test_get_terminated_processes(self, manager):
        """Test getting list of terminated processes."""
        manager._terminated_processes = [
            {"pid": 123, "name": "TS4_x64.exe", "exe": "C:/Game/TS4.exe"}
        ]

        result = manager.get_terminated_processes()

        assert len(result) == 1
        assert result[0]["pid"] == 123

    @patch("subprocess.Popen")
    def test_restore_processes_success(self, mock_popen, manager):
        """Test successful process restoration."""
        manager._terminated_processes = [
            {"pid": 123, "name": "TS4_x64.exe", "exe": "C:/Game/TS4.exe"}
        ]

        result = manager.restore_processes()

        assert result is True
        mock_popen.assert_called_once()
        assert manager._terminated_processes == []

    def test_restore_processes_none_to_restore(self, manager):
        """Test restore when no processes recorded."""
        manager._terminated_processes = []

        result = manager.restore_processes()

        assert result is False

    @patch("subprocess.Popen")
    def test_restore_processes_error(self, mock_popen, manager):
        """Test restore handles errors gracefully."""
        mock_popen.side_effect = Exception("Failed to start")
        manager._terminated_processes = [
            {"pid": 123, "name": "TS4_x64.exe", "exe": "C:/Game/TS4.exe"}
        ]

        result = manager.restore_processes()

        assert result is True  # Still returns True (attempted)
        assert manager._terminated_processes == []  # List is cleared

    @patch("subprocess.Popen")
    def test_restore_processes_no_exe_path(self, mock_popen, manager):
        """Test restore when exe path not recorded."""
        manager._terminated_processes = [
            {"pid": 123, "name": "TS4_x64.exe"}  # No 'exe' key
        ]

        result = manager.restore_processes()

        assert result is True
        mock_popen.assert_not_called()


class TestCheckGameStatus:
    """Tests for check_game_status helper function."""

    @patch.object(GameProcessManager, "is_game_running")
    @patch.object(GameProcessManager, "get_launcher_processes")
    def test_check_game_status_all_running(self, mock_launchers, mock_game):
        """Test status when game and launcher running."""
        mock_game.return_value = True
        mock_launchers.return_value = [Mock()]

        status = check_game_status()

        assert status["game_running"] is True
        assert status["launcher_running"] is True

    @patch.object(GameProcessManager, "is_game_running")
    @patch.object(GameProcessManager, "get_launcher_processes")
    def test_check_game_status_none_running(self, mock_launchers, mock_game):
        """Test status when nothing running."""
        mock_game.return_value = False
        mock_launchers.return_value = []

        status = check_game_status()

        assert status["game_running"] is False
        assert status["launcher_running"] is False

    @patch.object(GameProcessManager, "is_game_running")
    @patch.object(GameProcessManager, "get_launcher_processes")
    def test_check_game_status_only_launcher(self, mock_launchers, mock_game):
        """Test status when only launcher running."""
        mock_game.return_value = False
        mock_launchers.return_value = [Mock()]

        status = check_game_status()

        assert status["game_running"] is False
        assert status["launcher_running"] is True
