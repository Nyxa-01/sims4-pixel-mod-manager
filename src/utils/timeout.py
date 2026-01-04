"""Timeout decorator for file operations with cross-platform support.

This module provides a timeout decorator that works on both Windows and Unix systems,
enforcing time limits on potentially long-running file operations to prevent hangs.
"""

import platform
import signal
import threading
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

T = TypeVar("T")


def timeout(seconds: int) -> Callable:
    """Timeout decorator for file operations.

    Enforces a time limit on function execution. On Unix systems, uses signal.SIGALRM
    for precise timing. On Windows, uses threading.Timer as signals are not fully supported.

    Args:
        seconds: Maximum execution time in seconds

    Returns:
        Decorated function that will raise TimeoutError if exceeded

    Example:
        >>> @timeout(30)
        ... def scan_large_file(path: Path) -> dict:
        ...     # Long-running operation
        ...     return data

        >>> try:
        ...     result = scan_large_file(huge_mod)
        ... except TimeoutError:
        ...     logger.error("Scan exceeded 30 second limit")

    Raises:
        TimeoutError: If function execution exceeds time limit
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if platform.system() == "Windows":
                # Windows: Use threading approach (less precise but works)
                result_container: list[Any] = [TimeoutError(f"{func.__name__} exceeded {seconds}s")]

                def target() -> None:
                    """Execute function in separate thread."""
                    try:
                        result_container[0] = func(*args, **kwargs)
                    except Exception as e:
                        result_container[0] = e

                thread = threading.Thread(target=target, daemon=True)
                thread.start()
                thread.join(timeout=seconds)

                if thread.is_alive():
                    # Thread still running - timeout occurred
                    raise TimeoutError(
                        f"{func.__name__} exceeded {seconds}s timeout. "
                        f"Operation may be stuck or file too large."
                    )

                # Check if exception occurred
                if isinstance(result_container[0], Exception):
                    raise result_container[0]

                return result_container[0]

            else:
                # Unix: Use signal.SIGALRM (more precise)
                def timeout_handler(signum: int, frame: Any) -> None:
                    """Signal handler for timeout."""
                    raise TimeoutError(
                        f"{func.__name__} exceeded {seconds}s timeout. "
                        f"Operation may be stuck or file too large."
                    )

                # Set up signal handler
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)

                try:
                    return func(*args, **kwargs)
                finally:
                    # Always restore original handler and cancel alarm
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)

        return wrapper

    return decorator


class TimeoutContext:
    """Context manager for timeout operations (alternative to decorator).

    Example:
        >>> with TimeoutContext(30) as timer:
        ...     scan_large_folder(path)
    """

    def __init__(self, seconds: int):
        """Initialize timeout context.

        Args:
            seconds: Maximum execution time
        """
        self.seconds = seconds
        self.timer: threading.Timer | None = None

    def __enter__(self) -> "TimeoutContext":
        """Start timeout timer."""
        if platform.system() != "Windows":
            signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self.seconds)
        else:
            # Windows: Use threading timer
            self.timer = threading.Timer(
                self.seconds, lambda: (_ for _ in ()).throw(TimeoutError("Operation timeout"))
            )
            self.timer.start()

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Cancel timeout timer."""
        if platform.system() != "Windows":
            signal.alarm(0)
        else:
            if self.timer:
                self.timer.cancel()

    def _timeout_handler(self, signum: int, frame: Any) -> None:
        """Signal handler for Unix systems."""
        raise TimeoutError(f"Operation exceeded {self.seconds}s timeout")
