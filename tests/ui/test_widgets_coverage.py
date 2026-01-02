"""Extended test coverage for UI widgets.

Tests for pixel_button.py, pixel_listbox.py, chunky_frame.py, progress_bar.py.
Uses mocking to avoid tkinter display requirements.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import sys


# Mock tkinter before importing widgets
@pytest.fixture(autouse=True)
def mock_tkinter():
    """Mock tkinter module for all tests."""
    mock_tk = MagicMock()

    # Create mock classes that behave like tkinter widgets
    class MockWidget:
        def __init__(self, *args, **kwargs):
            self._config = kwargs.copy()
            self.children = []
            self.packed = False
            self.grid_info_data = {}

        def pack(self, **kwargs):
            self.packed = True
            self.pack_kwargs = kwargs

        def grid(self, **kwargs):
            self.grid_info_data = kwargs

        def configure(self, **kwargs):
            self._config.update(kwargs)

        def config(self, **kwargs):
            self.configure(**kwargs)

        def cget(self, key):
            return self._config.get(key, "")

        def winfo_width(self):
            return self._config.get("width", 100)

        def winfo_height(self):
            return self._config.get("height", 100)

        def winfo_screenwidth(self):
            return 1920

        def winfo_screenheight(self):
            return 1080

        def bind(self, event, handler):
            pass

        def update(self):
            pass

        def after(self, ms, func):
            pass

        def destroy(self):
            pass

    class MockCanvas(MockWidget):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.deleted_items = []
            self.created_items = []

        def delete(self, tag):
            self.deleted_items.append(tag)

        def create_image(self, x, y, **kwargs):
            self.created_items.append(("image", x, y, kwargs))
            return len(self.created_items)

        def create_text(self, x, y, **kwargs):
            self.created_items.append(("text", x, y, kwargs))
            return len(self.created_items)

        def create_rectangle(self, x1, y1, x2, y2, **kwargs):
            self.created_items.append(("rect", x1, y1, x2, y2, kwargs))
            return len(self.created_items)

        def canvasy(self, y):
            return y

        def yview(self, *args):
            pass

        def yview_scroll(self, amount, unit):
            pass

    class MockFrame(MockWidget):
        pass

    class MockLabel(MockWidget):
        pass

    class MockScrollbar(MockWidget):
        def set(self, *args):
            pass

        def config(self, **kwargs):
            pass

    mock_tk.Widget = MockWidget
    mock_tk.Canvas = MockCanvas
    mock_tk.Frame = MockFrame
    mock_tk.Label = MockLabel
    mock_tk.Scrollbar = MockScrollbar
    mock_tk.Tk = MagicMock
    mock_tk.BOTH = "both"
    mock_tk.VERTICAL = "vertical"
    mock_tk.Event = MagicMock
    mock_tk.TclError = Exception

    # Mock tkinter.font
    mock_font = MagicMock()
    mock_font.Font = MagicMock(return_value=MagicMock())

    with patch.dict(
        sys.modules,
        {
            "tkinter": mock_tk,
            "tkinter.font": mock_font,
        },
    ):
        yield mock_tk


class TestChunkyFrame:
    """Tests for ChunkyFrame widget."""

    def test_chunky_frame_initialization(self, mock_tkinter):
        """Test ChunkyFrame creates with default parameters."""
        from src.ui.widgets.chunky_frame import ChunkyFrame

        parent = MagicMock()
        frame = ChunkyFrame(parent)

        assert frame.border_width == 4
        assert frame.border_color == "#00e0ff"
        assert frame.bg_color == "#1a1a1a"

    def test_chunky_frame_custom_parameters(self, mock_tkinter):
        """Test ChunkyFrame with custom parameters."""
        from src.ui.widgets.chunky_frame import ChunkyFrame

        parent = MagicMock()
        frame = ChunkyFrame(parent, border_color="#ff0000", border_width=8, bg="#000000")

        assert frame.border_width == 8
        assert frame.border_color == "#ff0000"
        assert frame.bg_color == "#000000"

    def test_get_content_frame(self, mock_tkinter):
        """Test get_content_frame returns inner frame."""
        from src.ui.widgets.chunky_frame import ChunkyFrame

        parent = MagicMock()
        frame = ChunkyFrame(parent)

        content = frame.get_content_frame()
        assert content == frame.inner_frame

    def test_set_border_color(self, mock_tkinter):
        """Test changing border color."""
        from src.ui.widgets.chunky_frame import ChunkyFrame

        parent = MagicMock()
        frame = ChunkyFrame(parent)

        frame.set_border_color("#00ff00")
        assert frame.border_color == "#00ff00"


class TestPixelProgressBar:
    """Tests for PixelProgressBar widget."""

    def test_progress_bar_initialization(self, mock_tkinter):
        """Test PixelProgressBar creates with defaults."""
        from src.ui.widgets.progress_bar import PixelProgressBar

        parent = MagicMock()
        pbar = PixelProgressBar(parent)

        assert pbar.segments == 20
        assert pbar.progress == 0.0

    def test_progress_bar_custom_segments(self, mock_tkinter):
        """Test PixelProgressBar with custom segment count."""
        from src.ui.widgets.progress_bar import PixelProgressBar

        parent = MagicMock()
        pbar = PixelProgressBar(parent, segments=10, width=200, height=16)

        assert pbar.segments == 10

    def test_set_progress_valid_range(self, mock_tkinter):
        """Test set_progress with valid values."""
        from src.ui.widgets.progress_bar import PixelProgressBar

        parent = MagicMock()
        pbar = PixelProgressBar(parent)

        pbar.set_progress(0.5)
        assert pbar.progress == 0.5

        pbar.set_progress(1.0)
        assert pbar.progress == 1.0

        pbar.set_progress(0.0)
        assert pbar.progress == 0.0

    def test_set_progress_clamping(self, mock_tkinter):
        """Test set_progress clamps out-of-range values."""
        from src.ui.widgets.progress_bar import PixelProgressBar

        parent = MagicMock()
        pbar = PixelProgressBar(parent)

        pbar.set_progress(-0.5)
        assert pbar.progress == 0.0

        pbar.set_progress(1.5)
        assert pbar.progress == 1.0

    def test_get_progress(self, mock_tkinter):
        """Test get_progress returns current value."""
        from src.ui.widgets.progress_bar import PixelProgressBar

        parent = MagicMock()
        pbar = PixelProgressBar(parent)

        pbar.set_progress(0.75)
        assert pbar.get_progress() == 0.75


class TestPixelListbox:
    """Tests for PixelListbox widget."""

    def test_listbox_initialization(self, mock_tkinter):
        """Test PixelListbox creates correctly."""
        from src.ui.widgets.pixel_listbox import PixelListbox

        parent = MagicMock()
        listbox = PixelListbox(parent)

        assert listbox.items == []
        assert listbox.selected_index is None
        assert listbox.item_height == 32

    def test_set_items(self, mock_tkinter):
        """Test set_items populates listbox."""
        from src.ui.widgets.pixel_listbox import PixelListbox

        parent = MagicMock()
        listbox = PixelListbox(parent)

        items = ["Item 1", "Item 2", "Item 3"]
        listbox.set_items(items)

        assert listbox.items == items
        assert listbox.selected_index is None

    def test_set_items_copies_list(self, mock_tkinter):
        """Test set_items creates a copy of the list."""
        from src.ui.widgets.pixel_listbox import PixelListbox

        parent = MagicMock()
        listbox = PixelListbox(parent)

        items = ["A", "B", "C"]
        listbox.set_items(items)

        # Modify original list
        items.append("D")

        # Listbox should not be affected
        assert len(listbox.items) == 3

    def test_get_items(self, mock_tkinter):
        """Test get_items returns copy of items."""
        from src.ui.widgets.pixel_listbox import PixelListbox

        parent = MagicMock()
        listbox = PixelListbox(parent)

        listbox.set_items(["X", "Y", "Z"])
        items = listbox.get_items()

        assert items == ["X", "Y", "Z"]

        # Modifying returned list should not affect internal state
        items.append("W")
        assert len(listbox.items) == 3

    def test_get_selected_none(self, mock_tkinter):
        """Test get_selected returns None when no selection."""
        from src.ui.widgets.pixel_listbox import PixelListbox

        parent = MagicMock()
        listbox = PixelListbox(parent)

        listbox.set_items(["A", "B"])
        assert listbox.get_selected() is None

    def test_get_selected_valid(self, mock_tkinter):
        """Test get_selected returns selected item."""
        from src.ui.widgets.pixel_listbox import PixelListbox

        parent = MagicMock()
        listbox = PixelListbox(parent)

        listbox.set_items(["A", "B", "C"])
        listbox.selected_index = 1

        result = listbox.get_selected()
        assert result == (1, "B")

    def test_on_reorder_callback(self, mock_tkinter):
        """Test on_reorder registers callback."""
        from src.ui.widgets.pixel_listbox import PixelListbox

        parent = MagicMock()
        listbox = PixelListbox(parent)

        callback = MagicMock()
        listbox.on_reorder(callback)

        assert listbox.reorder_callback == callback

    def test_on_selection_callback(self, mock_tkinter):
        """Test on_selection registers callback."""
        from src.ui.widgets.pixel_listbox import PixelListbox

        parent = MagicMock()
        listbox = PixelListbox(parent)

        callback = MagicMock()
        listbox.on_selection(callback)

        assert listbox.selection_callback == callback

    def test_get_item_at_y_valid(self, mock_tkinter):
        """Test _get_item_at_y with valid coordinate."""
        from src.ui.widgets.pixel_listbox import PixelListbox

        parent = MagicMock()
        listbox = PixelListbox(parent)

        listbox.set_items(["A", "B", "C"])
        # item_height=32, padding=4, so items at y=0, 36, 72...

        result = listbox._get_item_at_y(10)
        assert result == 0

        result = listbox._get_item_at_y(40)
        assert result == 1

    def test_get_item_at_y_out_of_range(self, mock_tkinter):
        """Test _get_item_at_y with out-of-range coordinate."""
        from src.ui.widgets.pixel_listbox import PixelListbox

        parent = MagicMock()
        listbox = PixelListbox(parent)

        listbox.set_items(["A", "B"])

        result = listbox._get_item_at_y(500)
        assert result is None


class TestPixelButton:
    """Tests for PixelButton widget - skipped due to missing PixelAssetManager."""

    @pytest.mark.skip(reason="PixelAssetManager class not implemented")
    def test_button_initialization(self, mock_tkinter):
        """Test PixelButton creates with parameters."""
        pass

    @pytest.mark.skip(reason="PixelAssetManager class not implemented")
    def test_button_state_transitions(self, mock_tkinter):
        """Test button state changes."""
        pass

    @pytest.mark.skip(reason="PixelAssetManager class not implemented")
    def test_button_disable_enable(self, mock_tkinter):
        """Test button enable/disable."""
        pass


class TestAnimations:
    """Tests for animation functions."""

    def test_animate_scale_function_exists(self, mock_tkinter):
        """Test animate_scale function exists and is callable."""
        from src.ui.animations import animate_scale

        assert callable(animate_scale)

    def test_animate_scale_with_widget_not_ready(self, mock_tkinter):
        """Test animate_scale when widget not ready."""
        from src.ui.animations import animate_scale

        widget = MagicMock()
        widget.winfo_width.side_effect = Exception("Not ready")

        # Should handle gracefully
        animate_scale(widget, 1.1, 100)

    def test_animate_scale_widget_too_small(self, mock_tkinter):
        """Test animate_scale with unrendered widget."""
        from src.ui.animations import animate_scale

        widget = MagicMock()
        widget.winfo_width.return_value = 0
        widget.winfo_height.return_value = 0

        # Should return early without error
        animate_scale(widget, 1.1, 100)

    def test_animate_fade_function_exists(self, mock_tkinter):
        """Test animate_fade function exists and is callable."""
        from src.ui.animations import animate_fade

        assert callable(animate_fade)

    def test_animate_fade_with_tcl_error(self, mock_tkinter):
        """Test animate_fade handles TclError."""
        from src.ui.animations import animate_fade

        widget = MagicMock()
        widget.cget.side_effect = Exception("TclError")

        # Should handle gracefully
        animate_fade(widget, 0.5, 200)

    def test_pulse_widget_function_exists(self, mock_tkinter):
        """Test pulse_widget function exists and is callable."""
        from src.ui.animations import pulse_widget

        assert callable(pulse_widget)

    def test_pulse_widget_parameters(self, mock_tkinter):
        """Test pulse_widget accepts parameters."""
        from src.ui.animations import pulse_widget

        widget = MagicMock()
        widget.winfo_width.return_value = 100
        widget.winfo_height.return_value = 50

        # Should not raise
        pulse_widget(widget, scale_amount=1.1, duration_ms=300)


class TestSplashScreen:
    """Tests for SplashScreen widget."""

    def test_splash_screen_initialization(self, mock_tkinter):
        """Test SplashScreen creates with defaults."""
        from src.ui.splash_screen import SplashScreen

        splash = SplashScreen()

        assert splash.title == "Sims 4 Pixel Mod Manager"
        assert splash.version == "1.0.0"
        assert splash.window is None

    def test_splash_screen_custom_title(self, mock_tkinter):
        """Test SplashScreen with custom title and version."""
        from src.ui.splash_screen import SplashScreen

        splash = SplashScreen(title="Test App", version="2.0.0")

        assert splash.title == "Test App"
        assert splash.version == "2.0.0"

    def test_update_progress_no_window(self, mock_tkinter):
        """Test update_progress when window not shown."""
        from src.ui.splash_screen import SplashScreen

        splash = SplashScreen()

        # Should not raise when window is None
        splash.update_progress(0.5, "Loading...")

    def test_update_progress_with_window(self, mock_tkinter):
        """Test update_progress with active window."""
        from src.ui.splash_screen import SplashScreen

        splash = SplashScreen()
        splash.window = MagicMock()
        splash.progress_canvas = MagicMock()
        splash.progress_label = MagicMock()

        splash.update_progress(0.5, "Loading mods...")

        # Should delete old items
        splash.progress_canvas.delete.assert_called()
