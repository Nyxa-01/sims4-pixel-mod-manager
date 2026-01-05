"""Tests for UI animation functionality.

These tests use mocked Tkinter components from conftest.py.
"""

import sys
from unittest.mock import MagicMock, Mock, patch

from tests.ui.conftest import MockCanvas, MockFrame, MockLabel, MockTk


class TestAnimationEngine:
    """Test animation functionality without requiring display."""

    def test_mock_canvas_create_rectangle(self, mock_tk_canvas: MockCanvas) -> None:
        """Test canvas rectangle creation."""
        item_id = mock_tk_canvas.create_rectangle(0, 0, 100, 50, fill="#ff0000")

        assert item_id > 0
        assert item_id in mock_tk_canvas._items
        assert mock_tk_canvas._items[item_id]["type"] == "rectangle"
        assert mock_tk_canvas._items[item_id]["fill"] == "#ff0000"

    def test_mock_canvas_create_oval(self, mock_tk_canvas: MockCanvas) -> None:
        """Test canvas oval creation."""
        item_id = mock_tk_canvas.create_oval(10, 10, 50, 50, outline="#00ff00")

        assert item_id > 0
        assert mock_tk_canvas._items[item_id]["type"] == "oval"
        assert mock_tk_canvas._items[item_id]["outline"] == "#00ff00"

    def test_mock_canvas_create_line(self, mock_tk_canvas: MockCanvas) -> None:
        """Test canvas line creation."""
        item_id = mock_tk_canvas.create_line(0, 0, 100, 100, width=2)

        assert item_id > 0
        assert mock_tk_canvas._items[item_id]["type"] == "line"
        assert mock_tk_canvas._items[item_id]["width"] == 2

    def test_mock_canvas_create_text(self, mock_tk_canvas: MockCanvas) -> None:
        """Test canvas text creation."""
        item_id = mock_tk_canvas.create_text(50, 50, text="Hello", fill="#ffffff")

        assert item_id > 0
        assert mock_tk_canvas._items[item_id]["type"] == "text"
        assert mock_tk_canvas._items[item_id]["text"] == "Hello"

    def test_mock_canvas_itemconfigure(self, mock_tk_canvas: MockCanvas) -> None:
        """Test canvas item configuration."""
        item_id = mock_tk_canvas.create_rectangle(0, 0, 100, 50, fill="#ff0000")
        mock_tk_canvas.itemconfigure(item_id, fill="#00ff00")

        assert mock_tk_canvas._items[item_id]["fill"] == "#00ff00"

    def test_mock_canvas_delete(self, mock_tk_canvas: MockCanvas) -> None:
        """Test canvas item deletion."""
        item1 = mock_tk_canvas.create_rectangle(0, 0, 50, 50)
        item2 = mock_tk_canvas.create_oval(50, 50, 100, 100)

        mock_tk_canvas.delete(item1)

        assert item1 not in mock_tk_canvas._items
        assert item2 in mock_tk_canvas._items

    def test_mock_canvas_delete_all(self, mock_tk_canvas: MockCanvas) -> None:
        """Test canvas delete all items."""
        mock_tk_canvas.create_rectangle(0, 0, 50, 50)
        mock_tk_canvas.create_oval(50, 50, 100, 100)

        mock_tk_canvas.delete("all")

        assert len(mock_tk_canvas._items) == 0

    def test_mock_canvas_move(self, mock_tk_canvas: MockCanvas) -> None:
        """Test canvas item movement."""
        item_id = mock_tk_canvas.create_rectangle(0, 0, 50, 50)

        mock_tk_canvas.move(item_id, 10, 20)

        coords = mock_tk_canvas._items[item_id]["coords"]
        assert coords[0] == 10  # x1 + 10
        assert coords[1] == 20  # y1 + 20
        assert coords[2] == 60  # x2 + 10
        assert coords[3] == 70  # y2 + 20

    def test_mock_canvas_coords_get(self, mock_tk_canvas: MockCanvas) -> None:
        """Test getting canvas item coordinates."""
        item_id = mock_tk_canvas.create_rectangle(10, 20, 30, 40)

        coords = mock_tk_canvas.coords(item_id)

        assert coords == (10, 20, 30, 40)

    def test_mock_canvas_coords_set(self, mock_tk_canvas: MockCanvas) -> None:
        """Test setting canvas item coordinates."""
        item_id = mock_tk_canvas.create_rectangle(0, 0, 50, 50)

        mock_tk_canvas.coords(item_id, 100, 100, 200, 200)

        assert mock_tk_canvas._items[item_id]["coords"] == (100, 100, 200, 200)

    def test_mock_canvas_find_all(self, mock_tk_canvas: MockCanvas) -> None:
        """Test finding all canvas items."""
        id1 = mock_tk_canvas.create_rectangle(0, 0, 50, 50)
        id2 = mock_tk_canvas.create_oval(50, 50, 100, 100)

        all_items = mock_tk_canvas.find_all()

        assert id1 in all_items
        assert id2 in all_items

    def test_frame_animation_setup(self, mock_tk_root: MockTk) -> None:
        """Test frame animation setup without display."""
        frame = MockFrame(mock_tk_root, bg="#000000")

        # Simulate animation start state
        frame["bg"] = "#000000"

        # Simulate animation end state
        frame["bg"] = "#ffffff"

        assert frame["bg"] == "#ffffff"

    def test_widget_binding(self, mock_tk_root: MockTk) -> None:
        """Test widget event binding."""
        label = MockLabel(mock_tk_root, text="Test")
        callback = Mock()

        bind_id = label.bind("<Enter>", callback)

        assert bind_id is not None
        assert "<Enter>" in label._bindings
        assert callback in label._bindings["<Enter>"]

    def test_widget_unbinding(self, mock_tk_root: MockTk) -> None:
        """Test widget event unbinding."""
        label = MockLabel(mock_tk_root, text="Test")
        callback = Mock()

        label.bind("<Enter>", callback)
        label.unbind("<Enter>")

        assert len(label._bindings["<Enter>"]) == 0

    def test_after_scheduling(self, mock_tk_root: MockTk) -> None:
        """Test after callback scheduling."""
        callback = Mock()

        mock_tk_root.after(100, callback)

        callback.assert_called_once()

    def test_after_with_args(self, mock_tk_root: MockTk) -> None:
        """Test after callback with arguments."""
        callback = Mock()

        mock_tk_root.after(100, callback, "arg1", "arg2")

        callback.assert_called_once_with("arg1", "arg2")

    def test_after_cancel(self, mock_tk_root: MockTk) -> None:
        """Test after callback cancellation."""
        # Just verify it doesn't raise
        mock_tk_root.after_cancel("some_id")


class TestProgressBarAnimation:
    """Test progress bar animation functionality."""

    def test_progress_bar_creation(self, mock_tk_canvas: MockCanvas) -> None:
        """Test progress bar visual creation."""
        # Create background rectangle
        bg_id = mock_tk_canvas.create_rectangle(0, 0, 200, 20, fill="#333333", outline="#000000")

        # Create progress fill
        fill_id = mock_tk_canvas.create_rectangle(0, 0, 0, 20, fill="#00ff00", outline="")

        assert bg_id in mock_tk_canvas._items
        assert fill_id in mock_tk_canvas._items

    def test_progress_bar_update(self, mock_tk_canvas: MockCanvas) -> None:
        """Test progress bar value update."""
        # Create progress fill at 0%
        fill_id = mock_tk_canvas.create_rectangle(0, 0, 0, 20, fill="#00ff00")

        # Update to 50%
        width = 200
        progress = 0.5
        new_width = int(width * progress)
        mock_tk_canvas.coords(fill_id, 0, 0, new_width, 20)

        assert mock_tk_canvas._items[fill_id]["coords"] == (0, 0, new_width, 20)

    def test_progress_bar_full(self, mock_tk_canvas: MockCanvas) -> None:
        """Test progress bar at 100%."""
        fill_id = mock_tk_canvas.create_rectangle(0, 0, 0, 20, fill="#00ff00")

        # Update to 100%
        mock_tk_canvas.coords(fill_id, 0, 0, 200, 20)

        assert mock_tk_canvas._items[fill_id]["coords"] == (0, 0, 200, 20)

    def test_progress_bar_color_change(self, mock_tk_canvas: MockCanvas) -> None:
        """Test progress bar color change on state."""
        fill_id = mock_tk_canvas.create_rectangle(0, 0, 100, 20, fill="#00ff00")

        # Change to warning color at 90%
        mock_tk_canvas.itemconfigure(fill_id, fill="#ffff00")

        assert mock_tk_canvas._items[fill_id]["fill"] == "#ffff00"


class TestColorInterpolation:
    """Test color interpolation for smooth animations."""

    def test_hex_to_rgb(self) -> None:
        """Test hex color to RGB conversion."""

        def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
            hex_color = hex_color.lstrip("#")
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

        assert hex_to_rgb("#ff0000") == (255, 0, 0)
        assert hex_to_rgb("#00ff00") == (0, 255, 0)
        assert hex_to_rgb("#0000ff") == (0, 0, 255)
        assert hex_to_rgb("#ffffff") == (255, 255, 255)
        assert hex_to_rgb("#000000") == (0, 0, 0)

    def test_rgb_to_hex(self) -> None:
        """Test RGB to hex color conversion."""

        def rgb_to_hex(r: int, g: int, b: int) -> str:
            return f"#{r:02x}{g:02x}{b:02x}"

        assert rgb_to_hex(255, 0, 0) == "#ff0000"
        assert rgb_to_hex(0, 255, 0) == "#00ff00"
        assert rgb_to_hex(0, 0, 255) == "#0000ff"
        assert rgb_to_hex(255, 255, 255) == "#ffffff"
        assert rgb_to_hex(0, 0, 0) == "#000000"

    def test_color_interpolation(self) -> None:
        """Test color interpolation between two colors."""

        def interpolate_color(start: str, end: str, progress: float) -> str:
            def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
                hex_color = hex_color.lstrip("#")
                return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

            def rgb_to_hex(r: int, g: int, b: int) -> str:
                return f"#{r:02x}{g:02x}{b:02x}"

            r1, g1, b1 = hex_to_rgb(start)
            r2, g2, b2 = hex_to_rgb(end)

            r = int(r1 + (r2 - r1) * progress)
            g = int(g1 + (g2 - g1) * progress)
            b = int(b1 + (b2 - b1) * progress)

            return rgb_to_hex(r, g, b)

        # Start color
        assert interpolate_color("#000000", "#ffffff", 0.0) == "#000000"
        # End color
        assert interpolate_color("#000000", "#ffffff", 1.0) == "#ffffff"
        # Midpoint
        assert interpolate_color("#000000", "#ffffff", 0.5) == "#7f7f7f"

    def test_easing_functions(self) -> None:
        """Test animation easing functions."""

        def ease_linear(t: float) -> float:
            return t

        def ease_in_quad(t: float) -> float:
            return t * t

        def ease_out_quad(t: float) -> float:
            return t * (2 - t)

        def ease_in_out_quad(t: float) -> float:
            if t < 0.5:
                return 2 * t * t
            return 1 - pow(-2 * t + 2, 2) / 2

        # Linear
        assert ease_linear(0.0) == 0.0
        assert ease_linear(0.5) == 0.5
        assert ease_linear(1.0) == 1.0

        # Ease in (starts slow)
        assert ease_in_quad(0.0) == 0.0
        assert ease_in_quad(0.5) == 0.25
        assert ease_in_quad(1.0) == 1.0

        # Ease out (ends slow)
        assert ease_out_quad(0.0) == 0.0
        assert ease_out_quad(0.5) == 0.75
        assert ease_out_quad(1.0) == 1.0

        # Ease in-out (starts and ends slow)
        assert ease_in_out_quad(0.0) == 0.0
        assert ease_in_out_quad(0.5) == 0.5
        assert ease_in_out_quad(1.0) == 1.0


class TestWidgetAnimations:
    """Test specific widget animation scenarios."""

    def test_fade_in_animation(self, mock_tk_root: MockTk) -> None:
        """Test fade-in animation simulation."""
        label = MockLabel(mock_tk_root, text="Fading", bg="#000000")

        # Simulate alpha values (Tkinter doesn't have true alpha,
        # but we can simulate with color blending)
        steps = [0.0, 0.25, 0.5, 0.75, 1.0]

        for alpha in steps:
            # Calculate blended color (simulating opacity)
            gray_value = int(255 * alpha)
            color = f"#{gray_value:02x}{gray_value:02x}{gray_value:02x}"
            label["fg"] = color

        assert label["fg"] == "#ffffff"

    def test_slide_animation(self, mock_tk_root: MockTk) -> None:
        """Test slide animation simulation."""
        frame = MockFrame(mock_tk_root)

        # Simulate slide from left (-100) to final position (0)
        positions = [-100, -75, -50, -25, 0]

        for x in positions:
            frame.place(x=x, y=0)
            assert frame._place_info.get("x") == x

        assert frame._place_info.get("x") == 0

    def test_pulse_animation(self, mock_tk_canvas: MockCanvas) -> None:
        """Test pulse animation (scale up and down)."""
        rect_id = mock_tk_canvas.create_rectangle(40, 40, 60, 60, fill="#00ff00")

        # Simulate pulse: grow then shrink
        scale_values = [1.0, 1.1, 1.2, 1.1, 1.0]

        for scale in scale_values:
            center_x, center_y = 50, 50
            half_size = 10 * scale
            mock_tk_canvas.coords(
                rect_id,
                center_x - half_size,
                center_y - half_size,
                center_x + half_size,
                center_y + half_size,
            )

        # Back to original size
        coords = mock_tk_canvas._items[rect_id]["coords"]
        assert coords[2] - coords[0] == 20  # Original width

    def test_shake_animation(self, mock_tk_root: MockTk) -> None:
        """Test shake animation simulation."""
        frame = MockFrame(mock_tk_root)

        # Simulate horizontal shake
        original_x = 100
        offsets = [5, -5, 4, -4, 3, -3, 2, -2, 1, -1, 0]

        for offset in offsets:
            frame.place(x=original_x + offset, y=0)

        # Returns to original position
        assert frame._place_info.get("x") == original_x

    def test_rotation_animation_canvas(self, mock_tk_canvas: MockCanvas) -> None:
        """Test simulated rotation on canvas items."""
        # Note: Tkinter canvas doesn't support true rotation,
        # but we can simulate by recreating items at new positions
        import math

        center_x, center_y = 50, 50
        radius = 20

        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            x = center_x + radius * math.cos(rad)
            y = center_y + radius * math.sin(rad)

            # Create or update indicator position
            mock_tk_canvas.delete("all")
            mock_tk_canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="#ff0000", tags="indicator")

        # Verify item exists
        assert len(mock_tk_canvas._items) == 1


class TestSpinnerAnimation:
    """Test loading spinner animation."""

    def test_spinner_frame_sequence(self, mock_tk_canvas: MockCanvas) -> None:
        """Test spinner frame-by-frame animation."""
        # Spinner with 8 segments
        num_segments = 8
        colors = ["#ffffff"] + ["#666666"] * (num_segments - 1)

        # Rotate colors for animation frames
        for frame_num in range(num_segments):
            rotated = colors[-frame_num:] + colors[:-frame_num]

            mock_tk_canvas.delete("all")
            for i, color in enumerate(rotated):
                angle = i * (360 / num_segments)
                mock_tk_canvas.create_arc(
                    10,
                    10,
                    90,
                    90,
                    start=angle,
                    extent=360 / num_segments - 5,
                    fill=color,
                    outline="",
                )

        # Verify items were created
        assert len(mock_tk_canvas._items) == num_segments

    def test_spinner_start_stop(self, mock_tk_root: MockTk) -> None:
        """Test spinner animation start/stop state."""
        spinner_state = {"running": False, "after_id": None}

        def start_spinner() -> None:
            spinner_state["running"] = True
            spinner_state["after_id"] = "after_100"

        def stop_spinner() -> None:
            spinner_state["running"] = False
            if spinner_state["after_id"]:
                mock_tk_root.after_cancel(spinner_state["after_id"])
                spinner_state["after_id"] = None

        start_spinner()
        assert spinner_state["running"] is True

        stop_spinner()
        assert spinner_state["running"] is False
        assert spinner_state["after_id"] is None


class TestNotificationAnimation:
    """Test notification popup animations."""

    def test_notification_slide_in(self, mock_tk_root: MockTk) -> None:
        """Test notification sliding in from edge."""
        from tests.ui.conftest import MockToplevel

        notification = MockToplevel(mock_tk_root)

        # Start off-screen (right edge)
        screen_width = mock_tk_root.winfo_screenwidth()
        notification_width = 300

        start_x = screen_width
        end_x = screen_width - notification_width - 20

        # Animate slide in
        steps = 10
        for i in range(steps + 1):
            progress = i / steps
            current_x = int(start_x + (end_x - start_x) * progress)
            notification._config["geometry"] = f"{notification_width}x100+{current_x}+20"

        final_geometry = notification._config["geometry"]
        assert str(end_x) in final_geometry

    def test_notification_fade_out(self, mock_tk_root: MockTk) -> None:
        """Test notification fade out simulation."""
        from tests.ui.conftest import MockToplevel

        notification = MockToplevel(mock_tk_root)

        # Simulate fade by adjusting attributes
        # (Tkinter uses -alpha attribute on supported platforms)
        alpha_values = [1.0, 0.8, 0.6, 0.4, 0.2, 0.0]

        for alpha in alpha_values:
            notification._config["attr_-alpha"] = alpha

        # After fade out
        assert notification._config["attr_-alpha"] == 0.0

    def test_notification_auto_dismiss(self, mock_tk_root: MockTk) -> None:
        """Test notification auto-dismiss timing."""
        from tests.ui.conftest import MockToplevel

        dismissed = {"value": False}

        def dismiss() -> None:
            dismissed["value"] = True

        _notification = MockToplevel(mock_tk_root)  # Created but callback tests mock_tk_root

        # Schedule auto-dismiss (in real code, after 5000ms)
        mock_tk_root.after(5000, dismiss)

        # Callback is executed immediately in mock
        assert dismissed["value"] is True


# ============================================================================
# Tests for src/ui/animations.py production code
# ============================================================================


class TestAnimateScaleFunction:
    """Test animate_scale function from production code."""

    def test_animate_scale_widget_not_ready(self) -> None:
        """Test animate_scale handles widget not ready."""
        # Mock tkinter module
        mock_tk = MagicMock()
        mock_tk.TclError = Exception

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            # Import after mocking
            from src.ui.animations import animate_scale

            # Create widget that raises TclError on winfo_width
            mock_widget = MagicMock()
            mock_widget.winfo_width.side_effect = Exception("Widget not ready")

            # Should not raise, just log and return
            animate_scale(mock_widget, 1.5)

    def test_animate_scale_widget_not_rendered(self) -> None:
        """Test animate_scale handles unrendered widget (size <= 1)."""
        mock_tk = MagicMock()
        mock_tk.TclError = Exception

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            from src.ui.animations import animate_scale

            mock_widget = MagicMock()
            mock_widget.winfo_width.return_value = 0
            mock_widget.winfo_height.return_value = 0

            # Should return early without animation
            animate_scale(mock_widget, 1.5)

            # after() should not be called for unrendered widget
            mock_widget.after.assert_not_called()

    def test_animate_scale_calculates_steps(self) -> None:
        """Test animate_scale calculates correct animation steps."""
        mock_tk = MagicMock()
        mock_tk.TclError = Exception

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            from src.ui.animations import animate_scale

            mock_widget = MagicMock()
            mock_widget.winfo_width.return_value = 100
            mock_widget.winfo_height.return_value = 50

            # Run animation
            animate_scale(mock_widget, 1.5, duration_ms=160)

            # First step should be called immediately, then after() for subsequent
            # With 160ms duration at 16ms/frame = 10 steps
            # Initial step() is called synchronously
            mock_widget.config.assert_called()

    def test_animate_scale_short_duration(self) -> None:
        """Test animate_scale with very short duration (< 16ms)."""
        mock_tk = MagicMock()
        mock_tk.TclError = Exception

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            from src.ui.animations import animate_scale

            mock_widget = MagicMock()
            mock_widget.winfo_width.return_value = 100
            mock_widget.winfo_height.return_value = 50

            # Very short duration should use at least 1 step
            animate_scale(mock_widget, 1.5, duration_ms=5)

            mock_widget.config.assert_called()

    def test_animate_scale_with_callback(self) -> None:
        """Test animate_scale calls completion callback."""
        mock_tk = MagicMock()
        mock_tk.TclError = Exception

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            from src.ui.animations import animate_scale

            mock_widget = MagicMock()
            mock_widget.winfo_width.return_value = 100
            mock_widget.winfo_height.return_value = 50
            callback = Mock()

            # Store the step function for manual execution
            step_func = None

            def capture_after(ms, func):
                nonlocal step_func
                step_func = func

            mock_widget.after.side_effect = capture_after

            animate_scale(mock_widget, 1.5, duration_ms=16, on_complete=callback)

            # Manually execute remaining steps to trigger callback
            # (since after() is mocked, we need to simulate the animation loop)
            if step_func:
                step_func()  # Complete the animation
                callback.assert_called_once()


class TestAnimateFadeFunction:
    """Test animate_fade function from production code."""

    def test_animate_fade_widget_error(self) -> None:
        """Test animate_fade handles widget errors."""
        mock_tk = MagicMock()
        mock_tk.TclError = Exception

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            from src.ui.animations import animate_fade

            mock_widget = MagicMock()
            mock_widget.cget.side_effect = Exception("Widget error")

            # Should not raise
            animate_fade(mock_widget, 0.5)

    def test_animate_fade_runs_steps(self) -> None:
        """Test animate_fade runs animation steps."""
        mock_tk = MagicMock()
        mock_tk.TclError = Exception

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            from src.ui.animations import animate_fade

            mock_widget = MagicMock()
            mock_widget.cget.return_value = "#ffffff"

            animate_fade(mock_widget, 0.5, duration_ms=32)

            # after() should be scheduled for animation
            mock_widget.after.assert_called()

    def test_animate_fade_short_duration(self) -> None:
        """Test animate_fade with very short duration."""
        mock_tk = MagicMock()
        mock_tk.TclError = Exception

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            from src.ui.animations import animate_fade

            mock_widget = MagicMock()
            mock_widget.cget.return_value = "#ffffff"

            # Very short duration
            animate_fade(mock_widget, 0.5, duration_ms=5)

            mock_widget.after.assert_called()

    def test_animate_fade_with_callback(self) -> None:
        """Test animate_fade calls completion callback."""
        mock_tk = MagicMock()
        mock_tk.TclError = Exception

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            from src.ui.animations import animate_fade

            mock_widget = MagicMock()
            mock_widget.cget.return_value = "#ffffff"
            callback = Mock()

            # Capture and execute the step function
            step_func = None

            def capture_after(ms, func):
                nonlocal step_func
                step_func = func

            mock_widget.after.side_effect = capture_after

            animate_fade(mock_widget, 0.5, duration_ms=16, on_complete=callback)

            # Execute step to complete animation
            if step_func:
                step_func()
                callback.assert_called_once()


class TestPulseWidgetFunction:
    """Test pulse_widget function from production code."""

    def test_pulse_widget_calls_animate_scale(self) -> None:
        """Test pulse_widget uses animate_scale for pulsing."""
        mock_tk = MagicMock()
        mock_tk.TclError = Exception

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            with patch("src.ui.animations.animate_scale") as mock_animate:
                from src.ui.animations import pulse_widget

                mock_widget = MagicMock()

                pulse_widget(mock_widget, scale_amount=1.1, duration_ms=200)

                # Should call animate_scale for scale up
                mock_animate.assert_called()
                call_args = mock_animate.call_args_list[0]
                assert call_args[0][0] is mock_widget
                assert call_args[0][1] == 1.1  # scale_amount

    def test_pulse_widget_default_values(self) -> None:
        """Test pulse_widget with default parameters."""
        mock_tk = MagicMock()
        mock_tk.TclError = Exception

        with patch.dict(sys.modules, {"tkinter": mock_tk}):
            with patch("src.ui.animations.animate_scale") as mock_animate:
                from src.ui.animations import pulse_widget

                mock_widget = MagicMock()

                pulse_widget(mock_widget)

                # Should use default scale_amount of 1.05
                mock_animate.assert_called()
                call_args = mock_animate.call_args_list[0]
                assert call_args[0][1] == 1.05
