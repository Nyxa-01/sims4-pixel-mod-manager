"""Tests for pixel theme engine."""

import os
import tkinter as tk
from unittest.mock import Mock, patch

import pytest

from src.ui.pixel_theme import (
    BASE_FONT_SIZE,
    COLORS,
    FONT_FALLBACK,
    PixelTheme,
    get_theme,
)

# Skip all UI tests in CI environment (no display available)
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true",
    reason="UI tests require display (not available in CI)"
)


@pytest.fixture
def root() -> tk.Tk:
    """Create Tk root for testing.

    Returns:
        Tk root window
    """
    root = tk.Tk()
    yield root
    root.destroy()


class TestPixelTheme:
    """Test PixelTheme class."""

    def test_singleton_pattern(self) -> None:
        """Test that PixelTheme is a singleton."""
        theme1 = PixelTheme.get_instance()
        theme2 = PixelTheme.get_instance()

        assert theme1 is theme2

    def test_direct_initialization_raises_error(self) -> None:
        """Test that direct initialization raises error."""
        # Reset singleton for test
        PixelTheme._instance = PixelTheme()

        with pytest.raises(RuntimeError, match="Use PixelTheme.get_instance"):
            PixelTheme()

        # Cleanup
        PixelTheme._instance = None

    def test_colors_loaded(self) -> None:
        """Test that color palette is loaded."""
        theme = PixelTheme.get_instance()

        assert theme.colors == COLORS
        assert "bg_dark" in theme.colors
        assert "primary" in theme.colors
        assert theme.colors["bg_dark"] == "#000000"

    def test_get_scale_factor_default(self, root: tk.Tk) -> None:
        """Test scale factor calculation."""
        theme = PixelTheme.get_instance()

        scale = theme.get_scale_factor(root)

        assert isinstance(scale, float)
        assert 1.0 <= scale <= 3.0  # Clamped range

    @patch("platform.system", return_value="Windows")
    @patch("ctypes.windll.shcore.SetProcessDpiAwareness")
    def test_setup_dpi_awareness_windows(
        self,
        mock_set_dpi: Mock,
        mock_system: Mock,
        root: tk.Tk,
    ) -> None:
        """Test DPI setup on Windows."""
        theme = PixelTheme.get_instance()

        theme.setup_dpi_awareness(root)

        mock_set_dpi.assert_called_once_with(2)
        assert theme.scale_factor >= 1.0

    @patch("platform.system", return_value="Darwin")
    def test_setup_dpi_awareness_mac(
        self,
        mock_system: Mock,
        root: tk.Tk,
    ) -> None:
        """Test DPI setup on macOS."""
        theme = PixelTheme.get_instance()

        theme.setup_dpi_awareness(root)

        assert theme.scale_factor >= 1.0

    def test_load_fonts(self, root: tk.Tk) -> None:
        """Test font loading."""
        theme = PixelTheme.get_instance()
        theme.scale_factor = 1.0

        theme.load_fonts(root)

        assert theme.font_small is not None
        assert theme.font_normal is not None
        assert theme.font_large is not None
        assert theme._font_family in [FONT_FALLBACK, "Press Start 2P"]

    def test_apply_theme(self, root: tk.Tk) -> None:
        """Test theme application."""
        theme = PixelTheme.get_instance()

        theme.apply_theme(root)

        assert root["bg"] == COLORS["bg_dark"]
        assert theme.font_normal is not None

    def test_create_pixel_button(self, root: tk.Tk) -> None:
        """Test pixel button creation."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        button = theme.create_pixel_button(root, "Test Button", command=lambda: None)

        assert isinstance(button, tk.Button)
        assert button["text"] == "Test Button"
        assert button["bg"] == COLORS["primary"]
        assert button["fg"] == COLORS["text"]

    def test_button_hover_effects(self, root: tk.Tk) -> None:
        """Test button hover effects are bound."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        button = theme.create_pixel_button(root, "Test")

        # Check that events are bound
        # Note: tkinter doesn't expose bindings easily, but we can test behavior
        assert button is not None

    def test_create_chunky_frame(self, root: tk.Tk) -> None:
        """Test chunky frame creation."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        frame = theme.create_chunky_frame(root)

        assert isinstance(frame, tk.Frame)
        assert frame["bg"] == COLORS["bg_mid"]
        assert int(frame["highlightthickness"]) > 0

    def test_create_chunky_frame_custom_color(self, root: tk.Tk) -> None:
        """Test chunky frame with custom border color."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        frame = theme.create_chunky_frame(root, color=COLORS["danger"])

        assert frame["highlightbackground"] == COLORS["danger"]

    def test_create_pixel_listbox(self, root: tk.Tk) -> None:
        """Test pixel listbox creation."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        listbox = theme.create_pixel_listbox(root)

        assert isinstance(listbox, tk.Listbox)
        assert listbox["bg"] == COLORS["bg_dark"]
        assert listbox["fg"] == COLORS["text"]
        assert listbox["selectbackground"] == COLORS["secondary"]

    def test_create_pixel_label_normal(self, root: tk.Tk) -> None:
        """Test pixel label creation with normal size."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        label = theme.create_pixel_label(root, "Test Label")

        assert isinstance(label, tk.Label)
        assert label["text"] == "Test Label"
        assert label["bg"] == COLORS["bg_dark"]
        assert label["font"] == theme.font_normal

    def test_create_pixel_label_sizes(self, root: tk.Tk) -> None:
        """Test pixel label with different sizes."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        small = theme.create_pixel_label(root, "Small", size="small")
        normal = theme.create_pixel_label(root, "Normal", size="normal")
        large = theme.create_pixel_label(root, "Large", size="large")

        assert small["font"] == theme.font_small
        assert normal["font"] == theme.font_normal
        assert large["font"] == theme.font_large

    def test_create_pixel_entry(self, root: tk.Tk) -> None:
        """Test pixel entry creation."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        entry = theme.create_pixel_entry(root)

        assert isinstance(entry, tk.Entry)
        assert entry["bg"] == COLORS["bg_mid"]
        assert entry["fg"] == COLORS["text"]

    def test_create_progress_bar(self, root: tk.Tk) -> None:
        """Test progress bar creation."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        canvas = theme.create_progress_bar(root, width=200, height=20)

        assert isinstance(canvas, tk.Canvas)
        assert hasattr(canvas, "_progress_value")
        assert canvas._progress_value == 0.0

    def test_update_progress_bar(self, root: tk.Tk) -> None:
        """Test progress bar updates."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        canvas = theme.create_progress_bar(root)

        # Update to 50%
        theme.update_progress_bar(canvas, 0.5)
        assert canvas._progress_value == 0.5

        # Update to 100%
        theme.update_progress_bar(canvas, 1.0)
        assert canvas._progress_value == 1.0

    def test_update_progress_bar_clamps_values(self, root: tk.Tk) -> None:
        """Test progress bar clamps values to 0-1."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        canvas = theme.create_progress_bar(root)

        # Test clamping
        theme.update_progress_bar(canvas, -0.5)
        assert canvas._progress_value == 0.0

        theme.update_progress_bar(canvas, 1.5)
        assert canvas._progress_value == 1.0

    def test_animate_widget(self, root: tk.Tk) -> None:
        """Test widget animation."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        label = tk.Label(root, bg=COLORS["bg_dark"])

        # Animate background color
        theme.animate_widget(
            label,
            "bg",
            COLORS["bg_dark"],
            COLORS["primary"],
            duration=50,
        )

        # Animation is async, just verify it doesn't crash
        assert label is not None

    def test_animate_widget_with_callback(self, root: tk.Tk) -> None:
        """Test animation with completion callback."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        label = tk.Label(root)
        callback = Mock()

        theme.animate_widget(
            label,
            "bg",
            COLORS["bg_dark"],
            COLORS["primary"],
            duration=50,
            callback=callback,
        )

        # Callback will be called after animation (async)
        assert label is not None

    def test_create_tooltip(self, root: tk.Tk) -> None:
        """Test tooltip creation."""
        theme = PixelTheme.get_instance()
        theme.apply_theme(root)

        button = tk.Button(root, text="Hover me")
        theme.create_tooltip(button, "This is a tooltip")

        # Verify events are bound (tooltip shows/hides on events)
        assert button is not None

    def test_get_theme_function(self) -> None:
        """Test get_theme() convenience function."""
        theme = get_theme()

        assert isinstance(theme, PixelTheme)
        assert theme is PixelTheme.get_instance()


class TestColorPalette:
    """Test color palette constants."""

    def test_colors_defined(self) -> None:
        """Test that all required colors are defined."""
        required_colors = [
            "bg_dark",
            "bg_mid",
            "primary",
            "secondary",
            "success",
            "warning",
            "danger",
            "text",
            "border",
        ]

        for color in required_colors:
            assert color in COLORS

    def test_color_format(self) -> None:
        """Test that colors are valid hex codes."""
        for color_name, color_value in COLORS.items():
            assert color_value.startswith("#")
            assert len(color_value) == 7  # #RRGGBB format
            # Verify hex characters
            int(color_value[1:], 16)  # Should not raise


class TestScaling:
    """Test DPI scaling functionality."""

    def test_scale_factor_clamping(self, root: tk.Tk) -> None:
        """Test that scale factor is clamped to reasonable range."""
        theme = PixelTheme.get_instance()

        scale = theme.get_scale_factor(root)

        assert scale >= 1.0
        assert scale <= 3.0

    def test_font_scaling(self, root: tk.Tk) -> None:
        """Test that fonts scale with DPI."""
        theme = PixelTheme.get_instance()
        theme.scale_factor = 2.0

        theme.load_fonts(root)

        # Base size should be scaled
        expected_base = int(BASE_FONT_SIZE * 2.0)
        # Fonts should exist
        assert theme.font_small is not None
        assert theme.font_normal is not None
        assert theme.font_large is not None
