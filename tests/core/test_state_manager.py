"""Tests for thread-safe state management."""

import threading
import time
from pathlib import Path

import pytest

from src.core.state_manager import ApplicationState, AppState, StateManager


class TestApplicationState:
    """Test ApplicationState dataclass."""

    def test_default_values(self):
        """Test default state values."""
        state = ApplicationState()

        assert state.app_state == AppState.INITIALIZING
        assert state.game_path is None
        assert state.mods_path is None
        assert state.incoming_mods == []
        assert state.active_mods == {}  # Dict, not list
        assert state.last_deploy is None
        assert state.total_deploys == 0
        assert state.is_game_running is False
        assert state.current_operation is None
        assert state.progress == 0.0

    def test_custom_values(self):
        """Test creating state with custom values."""
        state = ApplicationState(app_state=AppState.SCANNING, total_deploys=5, progress=0.5)

        assert state.app_state == AppState.SCANNING
        assert state.total_deploys == 5
        assert state.progress == 0.5


class TestAppState:
    """Test AppState enum."""

    def test_all_states_exist(self):
        """Test all expected states exist."""
        expected_states = [
            "INITIALIZING",
            "READY",
            "SCANNING",
            "GENERATING",
            "DEPLOYING",
            "BACKING_UP",
            "ERROR",
        ]

        for state_name in expected_states:
            assert hasattr(AppState, state_name)

    def test_state_values_unique(self):
        """Test each state has unique value."""
        states = [
            AppState.INITIALIZING,
            AppState.READY,
            AppState.SCANNING,
            AppState.GENERATING,
            AppState.DEPLOYING,
            AppState.BACKING_UP,
            AppState.ERROR,
        ]

        assert len(states) == len(set(states))


class TestStateManager:
    """Test singleton state manager."""

    def setup_method(self):
        """Reset singleton before each test."""
        StateManager.reset_instance()

    def teardown_method(self):
        """Clean up after each test."""
        StateManager.reset_instance()

    def test_singleton_pattern(self):
        """Test only one instance exists."""
        sm1 = StateManager.get_instance()
        sm2 = StateManager.get_instance()

        assert sm1 is sm2

    def test_direct_init_after_instance_raises_error(self):
        """Test direct initialization is prevented after get_instance."""
        StateManager.get_instance()  # Create instance

        with pytest.raises(RuntimeError, match="Use StateManager.get_instance()"):
            StateManager()

    def test_reset_instance(self):
        """Test instance can be reset."""
        sm1 = StateManager.get_instance()
        StateManager.reset_instance()
        sm2 = StateManager.get_instance()

        assert sm1 is not sm2

    def test_get_state_returns_copy(self):
        """Test state mutations don't affect manager."""
        sm = StateManager.get_instance()
        state1 = sm.get_state()
        state1.total_deploys = 999

        state2 = sm.get_state()
        assert state2.total_deploys == 0  # Unchanged

    def test_set_state(self):
        """Test state transitions."""
        sm = StateManager.get_instance()
        sm.set_state(AppState.SCANNING)

        state = sm.get_state()
        assert state.app_state == AppState.SCANNING

    def test_update_paths(self):
        """Test path updates."""
        sm = StateManager.get_instance()

        game_path = Path("/path/to/game")
        mods_path = Path("/path/to/mods")

        sm.update_paths(game_path=game_path, mods_path=mods_path)

        state = sm.get_state()
        assert state.game_path == game_path
        assert state.mods_path == mods_path

    def test_update_paths_partial(self):
        """Test updating only one path."""
        sm = StateManager.get_instance()

        game_path = Path("/path/to/game")
        sm.update_paths(game_path=game_path)

        state = sm.get_state()
        assert state.game_path == game_path
        assert state.mods_path is None

    def test_set_incoming_mods(self):
        """Test setting incoming mod list."""
        sm = StateManager.get_instance()

        mods = [Path("mod1.package"), Path("mod2.package")]
        sm.set_incoming_mods(mods)

        state = sm.get_state()
        assert len(state.incoming_mods) == 2
        assert Path("mod1.package") in state.incoming_mods

    def test_set_active_mods(self):
        """Test setting active mod list."""
        sm = StateManager.get_instance()

        mods = {"Mods": [Path("active1.package"), Path("active2.package")]}
        sm.set_active_mods(mods)

        state = sm.get_state()
        assert "Mods" in state.active_mods
        assert len(state.active_mods["Mods"]) == 2

    def test_increment_deploy_count(self):
        """Test deploy counter increment."""
        sm = StateManager.get_instance()

        sm.increment_deploy_count()
        sm.increment_deploy_count()

        state = sm.get_state()
        assert state.total_deploys == 2

    def test_set_game_running(self):
        """Test setting game running status."""
        sm = StateManager.get_instance()

        sm.set_game_running(True)
        state = sm.get_state()
        assert state.is_game_running is True

        sm.set_game_running(False)
        state = sm.get_state()
        assert state.is_game_running is False

    def test_set_operation(self):
        """Test setting current operation."""
        sm = StateManager.get_instance()

        sm.set_operation("Copying files", 0.5)

        state = sm.get_state()
        assert state.current_operation == "Copying files"
        assert state.progress == 0.5

    def test_set_operation_without_progress(self):
        """Test setting operation without progress."""
        sm = StateManager.get_instance()

        sm.set_operation("Loading")

        state = sm.get_state()
        assert state.current_operation == "Loading"
        assert state.progress == 0.0

    def test_observer_pattern(self):
        """Test observer notifications."""
        sm = StateManager.get_instance()
        observed_states = []

        def observer(state: ApplicationState):
            observed_states.append(state.app_state)

        sm.register_observer(observer)
        sm.set_state(AppState.SCANNING)
        sm.set_state(AppState.DEPLOYING)

        assert AppState.SCANNING in observed_states
        assert AppState.DEPLOYING in observed_states
        assert len(observed_states) == 2

    def test_multiple_observers(self):
        """Test multiple observers receive notifications."""
        sm = StateManager.get_instance()

        calls1 = []
        calls2 = []

        def observer1(state: ApplicationState):
            calls1.append(state.app_state)

        def observer2(state: ApplicationState):
            calls2.append(state.app_state)

        sm.register_observer(observer1)
        sm.register_observer(observer2)

        sm.set_state(AppState.SCANNING)

        assert len(calls1) == 1
        assert len(calls2) == 1
        assert calls1[0] == AppState.SCANNING
        assert calls2[0] == AppState.SCANNING

    def test_unregister_observer(self):
        """Test observer removal."""
        sm = StateManager.get_instance()
        call_count = []

        def observer(state: ApplicationState):
            call_count.append(1)

        sm.register_observer(observer)
        sm.set_state(AppState.SCANNING)

        sm.unregister_observer(observer)
        sm.set_state(AppState.DEPLOYING)

        assert len(call_count) == 1  # Only first call

    def test_unregister_nonexistent_observer(self):
        """Test unregistering non-registered observer doesn't error."""
        sm = StateManager.get_instance()

        def observer(state: ApplicationState):
            pass

        # Should not raise
        sm.unregister_observer(observer)

    def test_thread_safety_concurrent_state_changes(self):
        """Test concurrent state changes are safe."""
        sm = StateManager.get_instance()
        errors = []

        def worker():
            try:
                for _i in range(50):
                    sm.set_state(AppState.SCANNING)
                    sm.get_state()
                    sm.set_state(AppState.DEPLOYING)
                    sm.get_state()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_thread_safety_concurrent_increments(self):
        """Test deploy counter is thread-safe."""
        sm = StateManager.get_instance()
        errors = []

        def worker():
            try:
                for _i in range(100):
                    sm.increment_deploy_count()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        state = sm.get_state()
        assert state.total_deploys == 1000  # 10 threads × 100 increments

    def test_thread_safety_observer_notifications(self):
        """Test observer notifications are thread-safe."""
        sm = StateManager.get_instance()
        observed_count = []
        errors = []
        lock = threading.Lock()

        def observer(state: ApplicationState):
            with lock:
                observed_count.append(1)

        sm.register_observer(observer)

        def worker():
            try:
                for _i in range(20):
                    sm.set_state(AppState.SCANNING)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(observed_count) == 100  # 5 threads × 20 notifications

    def test_nested_lock_acquisition(self):
        """Test nested lock acquisition doesn't deadlock."""
        sm = StateManager.get_instance()

        def observer(state: ApplicationState):
            # Observer tries to read state (nested lock)
            current = sm.get_state()
            assert current is not None

        sm.register_observer(observer)

        # This should not deadlock
        sm.set_state(AppState.SCANNING)

        state = sm.get_state()
        assert state.app_state == AppState.SCANNING
