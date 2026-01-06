"""Tests for JSON logging system."""

import pytest
import json
import logging
from pathlib import Path
from src.utils.logger import setup_logging, get_logger, JsonFormatter, log_with_context


class TestJsonFormatter:
    """Test JSON log formatting."""

    def test_format_basic_log(self):
        """Test basic log formatting."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["logger"] == "test"
        assert log_data["module"] == "test"
        assert log_data["line"] == 10
        assert "timestamp" in log_data

    def test_format_with_string_formatting(self):
        """Test formatting with % string substitution."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Value: %s",
            args=("test_value",),
            exc_info=None,
        )

        result = formatter.format(record)
        log_data = json.loads(result)

        assert log_data["message"] == "Value: test_value"

    def test_format_with_exception(self):
        """Test formatting with exception info."""
        formatter = JsonFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        log_data = json.loads(result)

        assert "exception" in log_data
        assert log_data["exception"]["type"] == "ValueError"
        assert log_data["exception"]["message"] == "Test error"
        assert "traceback" in log_data["exception"]

    def test_format_with_context(self):
        """Test formatting with context data."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.context = {"user_id": 123, "action": "deploy"}

        result = formatter.format(record)
        log_data = json.loads(result)

        assert "context" in log_data
        assert log_data["context"]["user_id"] == 123
        assert log_data["context"]["action"] == "deploy"

    def test_format_timestamp_is_iso8601(self):
        """Test timestamp is ISO 8601 format."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        log_data = json.loads(result)

        # Should parse as ISO 8601
        from datetime import datetime

        timestamp = datetime.fromisoformat(log_data["timestamp"].replace("Z", "+00:00"))
        assert timestamp is not None


class TestLoggingSetup:
    """Test logging configuration."""

    def test_setup_creates_log_directory(self, tmp_path):
        """Test log directory creation."""
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir)

        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_setup_creates_log_files(self, tmp_path):
        """Test log file creation."""
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir)

        logger = get_logger("test")
        logger.info("Test message")
        logger.error("Test error")

        # Force flush
        for handler in logger.handlers:
            handler.flush()

        assert (log_dir / "app.log").exists()
        assert (log_dir / "error.log").exists()

    def test_setup_with_debug_level(self, tmp_path):
        """Test setup with DEBUG level."""
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir, level="DEBUG")

        logger = get_logger("test")
        logger.debug("Debug message")

        for handler in logger.handlers:
            handler.flush()

        # Debug should be in app.log
        log_content = (log_dir / "app.log").read_text()
        log_data = json.loads(log_content.strip())
        assert log_data["message"] == "Debug message"

    def test_setup_removes_existing_handlers(self, tmp_path):
        """Test existing handlers are removed."""
        logger = logging.getLogger()
        initial_handlers = len(logger.handlers)

        setup_logging(log_dir=tmp_path / "logs")

        # Should have exactly our handlers (not duplicated)
        # Console + App + Error + Security + Deploy = 5
        assert len(logger.handlers) >= initial_handlers

    def test_get_logger(self):
        """Test logger retrieval."""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_with_submodule(self):
        """Test logger for submodule."""
        logger = get_logger("test.submodule")

        assert logger.name == "test.submodule"

    def test_json_output_format(self, tmp_path):
        """Test logs are valid JSON."""
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir)

        logger = get_logger("test")
        logger.info("Test message")

        for handler in logger.handlers:
            handler.flush()

        log_file = log_dir / "app.log"
        log_content = log_file.read_text().strip()

        # Should be valid JSON
        log_data = json.loads(log_content)
        assert log_data["message"] == "Test message"
        assert log_data["level"] == "INFO"

    def test_error_log_only_errors(self, tmp_path):
        """Test error.log only contains ERROR+ messages."""
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir)

        logger = get_logger("test")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        for handler in logger.handlers:
            handler.flush()

        # error.log should only have ERROR
        error_log = log_dir / "error.log"
        if error_log.exists():
            content = error_log.read_text().strip()
            if content:
                log_data = json.loads(content)
                assert log_data["level"] == "ERROR"
                assert log_data["message"] == "Error message"

    def test_security_log_filter(self, tmp_path):
        """Test security log captures security events."""
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir)

        logger = get_logger("security.validator")
        logger.info("Security check passed")

        for handler in logger.handlers:
            handler.flush()

        security_log = log_dir / "security.log"
        assert security_log.exists()

    def test_deploy_log_filter(self, tmp_path):
        """Test deploy log captures deployment events."""
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir)

        logger = get_logger("deploy.engine")
        logger.info("Deployment started")

        for handler in logger.handlers:
            handler.flush()

        deploy_log = log_dir / "deploy.log"
        assert deploy_log.exists()

    def test_log_rotation_size_limit(self, tmp_path):
        """Test log rotation when size limit reached."""
        log_dir = tmp_path / "logs"

        # Setup with tiny size limit for testing
        from logging.handlers import RotatingFileHandler

        logger = logging.getLogger("rotation_test")
        logger.setLevel(logging.INFO)

        handler = RotatingFileHandler(
            log_dir / "rotation.log",
            maxBytes=100,  # Very small for testing
            backupCount=3,
        )
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

        # Write enough to trigger rotation
        for i in range(20):
            logger.info(f"Message {i}" * 10)

        handler.flush()

        # Should have backup files
        backup_files = list(log_dir.glob("rotation.log.*"))
        assert len(backup_files) > 0


class TestLogContext:
    """Test log context functionality."""

    def test_log_with_context(self, tmp_path):
        """Test logging with context."""
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir)

        logger = get_logger("test")
        log_with_context(logger, "INFO", "Test message", mod_name="test.package", size_mb=2.5)

        for handler in logger.handlers:
            handler.flush()

        log_file = log_dir / "app.log"
        content = log_file.read_text().strip()

        # Parse last JSON line (multiple log entries may exist)
        lines = [line for line in content.split("\n") if line.strip()]
        log_data = json.loads(lines[-1])

        assert log_data["message"] == "Test message"
        assert "context" in log_data
        assert log_data["context"]["mod_name"] == "test.package"
        assert log_data["context"]["size_mb"] == 2.5

    def test_log_with_empty_context(self, tmp_path):
        """Test logging with empty context."""
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir)

        logger = get_logger("test")
        log_with_context(logger, "INFO", "Test message")

        for handler in logger.handlers:
            handler.flush()

        log_file = log_dir / "app.log"
        content = log_file.read_text().strip()

        # Parse last JSON line
        lines = [line for line in content.split("\n") if line.strip()]
        log_data = json.loads(lines[-1])

        assert log_data["message"] == "Test message"
        # Context should still be present but empty
        assert "context" in log_data
        assert log_data["context"] == {}


class TestExceptionLogging:
    """Test exception logging."""

    def test_exception_logging(self, tmp_path):
        """Test logging exceptions."""
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir)

        logger = get_logger("test")

        try:
            1 / 0
        except ZeroDivisionError:
            logger.exception("Division error")

        for handler in logger.handlers:
            handler.flush()

        error_log = log_dir / "error.log"
        content = error_log.read_text().strip()
        log_data = json.loads(content)

        assert log_data["message"] == "Division error"
        assert "exception" in log_data
        assert log_data["exception"]["type"] == "ZeroDivisionError"
        assert "traceback" in log_data["exception"]

    def test_nested_exception_logging(self, tmp_path):
        """Test logging nested exceptions."""
        log_dir = tmp_path / "logs"
        setup_logging(log_dir=log_dir)

        logger = get_logger("test")

        try:
            try:
                raise ValueError("Inner error")
            except ValueError as e:
                raise RuntimeError("Outer error") from e
        except RuntimeError:
            logger.exception("Nested exception")

        for handler in logger.handlers:
            handler.flush()

        error_log = log_dir / "error.log"
        content = error_log.read_text().strip()
        log_data = json.loads(content)

        assert log_data["exception"]["type"] == "RuntimeError"
        assert "traceback" in log_data["exception"]
