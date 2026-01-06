"""Smooth 60fps animations for UI transitions."""

import logging
import tkinter as tk
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def animate_scale(
    widget: tk.Widget,
    target_scale: float,
    duration_ms: int = 100,
    on_complete: Optional[Callable[[], None]] = None,
) -> None:
    """Animate widget scale transition.

    Args:
        widget: Widget to animate
        target_scale: Target scale factor (1.0 = original)
        duration_ms: Animation duration in milliseconds
        on_complete: Optional callback when animation completes
    """
    try:
        start_width = widget.winfo_width()
        start_height = widget.winfo_height()
    except tk.TclError:
        logger.warning("Widget not ready for animation")
        return

    if start_width <= 1 or start_height <= 1:
        # Widget not rendered yet
        return

    steps = duration_ms // 16  # 60fps = ~16ms per frame
    if steps < 1:
        steps = 1

    delta_scale = (target_scale - 1.0) / steps
    current_step = 0

    def step() -> None:
        nonlocal current_step

        if current_step >= steps:
            if on_complete:
                on_complete()
            return

        scale = 1.0 + (delta_scale * current_step)
        new_width = int(start_width * scale)
        new_height = int(start_height * scale)

        try:
            widget.configure(width=new_width, height=new_height)  # type: ignore[call-arg]
        except tk.TclError:
            return  # Widget destroyed

        current_step += 1
        widget.after(16, step)

    step()


def animate_fade(
    widget: tk.Label,
    target_alpha: float,
    duration_ms: int = 200,
    on_complete: Optional[Callable[[], None]] = None,
) -> None:
    """Animate label text fade (color interpolation).

    Args:
        widget: Label widget to fade
        target_alpha: Target alpha (0.0-1.0)
        duration_ms: Animation duration
        on_complete: Optional callback
    """
    # Note: True alpha not supported in tkinter, simulate with color interpolation
    steps = duration_ms // 16
    if steps < 1:
        steps = 1

    # Parse current color
    try:
        current_color = widget.cget("fg")
    except tk.TclError:
        return

    current_step = 0

    def step() -> None:
        nonlocal current_step

        if current_step >= steps:
            if on_complete:
                on_complete()
            return

        # Interpolate alpha by mixing with background
        alpha = target_alpha * (current_step / steps)
        # Simplified: just adjust brightness
        # TODO: Implement proper color interpolation

        current_step += 1
        widget.after(16, step)

    step()


def pulse_widget(
    widget: tk.Widget,
    scale_amount: float = 1.05,
    duration_ms: int = 200,
) -> None:
    """Create pulse effect (scale up and down).

    Args:
        widget: Widget to pulse
        scale_amount: Maximum scale factor
        duration_ms: Total pulse duration
    """

    def scale_down() -> None:
        animate_scale(widget, 1.0, duration_ms // 2)

    animate_scale(widget, scale_amount, duration_ms // 2, on_complete=scale_down)
