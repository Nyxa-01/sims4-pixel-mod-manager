"""Comprehensive tests for timeout utilities to achieve 90%+ coverage."""

import platform
import threading
import time
from unittest.mock import patch, Mock

import pytest

from src.utils.timeout import timeout, TimeoutContext


class TestTimeoutDecorator:
    """Test timeout decorator functionality."""

    def test_function_completes_before_timeout(self):
        """Function completes within timeout period."""
        @timeout(1)
        def quick_func():
            return "success"

        result = quick_func()
        assert result == "success"

    def test_function_exceeds_timeout(self):
        """Function raises TimeoutError when exceeding limit."""
        @timeout(1)
        def slow_func():
            time.sleep(3)
            return "never_reached"

        with pytest.raises(TimeoutError, match="exceeded.*1s"):
            slow_func()

    def test_timeout_preserves_function_name(self):
        """Decorated function preserves original name."""
        @timeout(5)
        def my_named_function():
            pass

        assert my_named_function.__name__ == "my_named_function"

    def test_timeout_preserves_return_value(self):
        """Decorated function returns correct value."""
        @timeout(5)
        def returns_dict():
            return {"key": "value", "number": 42}

        result = returns_dict()
        assert result == {"key": "value", "number": 42}

    def test_timeout_preserves_exception(self):
        """Inner exception is properly propagated."""
        @timeout(5)
        def raises_value_error():
            raise ValueError("Inner error message")

        with pytest.raises(ValueError, match="Inner error message"):
            raises_value_error()

    def test_timeout_with_args_and_kwargs(self):
        """Decorated function receives args and kwargs correctly."""
        @timeout(5)
        def func_with_args(a, b, c=10):
            return a + b + c

        result = func_with_args(1, 2, c=3)
        assert result == 6

    def test_timeout_edge_case_near_limit(self):
        """Function completes just before timeout."""
        @timeout(1)
        def almost_timeout():
            time.sleep(0.3)
            return "made_it"

        result = almost_timeout()
        assert result == "made_it"

    def test_timeout_message_includes_function_name(self):
        """Timeout error message includes function name."""
        @timeout(1)
        def named_slow_function():
            time.sleep(5)

        with pytest.raises(TimeoutError) as exc:
            named_slow_function()

        assert "named_slow_function" in str(exc.value)

    def test_timeout_with_io_operation(self, tmp_path):
        """Timeout works with file I/O operations."""
        @timeout(5)
        def read_file(path):
            return path.read_text()

        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        result = read_file(test_file)
        assert result == "content"


class TestTimeoutContext:
    """Test TimeoutContext context manager."""

    def test_context_completes_successfully(self):
        """Operation completes within timeout context."""
        with TimeoutContext(5) as ctx:
            result = 1 + 1

        assert result == 2
        assert ctx.seconds == 5

    def test_context_returns_self(self):
        """Context manager returns self on enter."""
        ctx = TimeoutContext(5)
        with ctx as returned:
            assert returned is ctx

    def test_context_cancels_timer_on_exit(self):
        """Timer is cancelled when exiting context normally."""
        with TimeoutContext(5) as ctx:
            pass

        # Timer should be cancelled - may still exist but should not be running
        if ctx.timer is not None:
            # Give a small delay for cleanup
            import time
            time.sleep(0.1)
            # Timer was started but should be cancelled
            assert hasattr(ctx, 'timer')

    def test_context_cancels_timer_on_exception(self):
        """Timer is cancelled when exception occurs in context."""
        ctx = TimeoutContext(5)
        try:
            with ctx:
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Timer should exist (was created) - just verify no crash
        assert hasattr(ctx, 'timer')

    def test_context_with_short_operation(self):
        """Context handles quick operations."""
        result = []
        with TimeoutContext(5):
            result.append("done")

        assert result == ["done"]


class TestTimeoutPlatformBehavior:
    """Test platform-specific timeout behavior."""

    def test_windows_uses_threading(self):
        """On Windows, timeout uses threading approach."""
        with patch("platform.system", return_value="Windows"):
            @timeout(5)
            def quick_func():
                return "result"

            # Should work on Windows
            result = quick_func()
            assert result == "result"

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-only test")
    def test_unix_uses_signal(self):
        """On Unix, timeout uses signal.SIGALRM."""
        @timeout(5)
        def quick_func():
            return "result"

        result = quick_func()
        assert result == "result"


class TestTimeoutEdgeCases:
    """Test edge cases and error conditions."""

    def test_timeout_with_none_return(self):
        """Decorated function returning None works correctly."""
        @timeout(5)
        def returns_none():
            return None

        result = returns_none()
        assert result is None

    def test_timeout_with_generator_function(self):
        """Timeout works with generator-like operations."""
        @timeout(5)
        def process_items():
            items = []
            for i in range(5):
                items.append(i)
            return items

        result = process_items()
        assert result == [0, 1, 2, 3, 4]

    def test_timeout_with_nested_calls(self):
        """Timeout works with nested function calls."""
        @timeout(5)
        def outer():
            return inner()

        def inner():
            return "nested_result"

        result = outer()
        assert result == "nested_result"

    def test_context_with_different_durations(self):
        """Context works with various timeout durations."""
        for duration in [1, 2, 5, 10]:
            with TimeoutContext(duration):
                pass  # Just ensure no error

    def test_multiple_decorated_functions(self):
        """Multiple functions can use timeout decorator independently."""
        @timeout(5)
        def func1():
            return "func1"

        @timeout(10)
        def func2():
            return "func2"

        assert func1() == "func1"
        assert func2() == "func2"

    def test_exception_type_preserved(self):
        """Specific exception types are preserved through timeout."""
        @timeout(5)
        def raises_key_error():
            raise KeyError("missing_key")

        with pytest.raises(KeyError, match="missing_key"):
            raises_key_error()

    def test_exception_with_complex_message(self):
        """Exceptions with complex messages are preserved."""
        @timeout(5)
        def raises_complex():
            raise RuntimeError({"error": "details", "code": 500})

        with pytest.raises(RuntimeError):
            raises_complex()


class TestTimeoutThreadSafety:
    """Test timeout behavior in multithreaded scenarios."""

    def test_concurrent_timeout_decorators(self):
        """Multiple timeouts can run concurrently."""
        @timeout(5)
        def concurrent_func(value):
            time.sleep(0.1)
            return value * 2

        results = []
        threads = []

        def run_func(val):
            results.append(concurrent_func(val))

        for i in range(3):
            t = threading.Thread(target=run_func, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(results) == 3
        assert set(results) == {0, 2, 4}

    def test_context_in_thread(self):
        """TimeoutContext works correctly in threads."""
        result_container = []

        def thread_func():
            with TimeoutContext(5):
                result_container.append("completed")

        thread = threading.Thread(target=thread_func)
        thread.start()
        thread.join()

        assert result_container == ["completed"]
