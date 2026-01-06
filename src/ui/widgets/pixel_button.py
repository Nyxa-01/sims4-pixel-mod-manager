"""8-bit styled button with hover/press animations."""

import logging
import tkinter as tk
from typing import Any, Callable, Optional, Union

from ..pixel_theme import PixelTheme

logger = logging.getLogger(__name__)


class PixelButton(tk.Canvas):
    """Custom button with 8-bit pixel art styling."""

    def __init__(
        self,
        parent: Union[tk.Tk, tk.Toplevel, tk.Widget],
        text: str,
        command: Optional[Callable[[], None]] = None,
        width: int = 120,
        height: int = 40,
        **kwargs: Any,
    ) -> None:
        """Initialize pixel button.

        Args:
            parent: Parent widget
            text: Button text
            command: Click callback
            width: Button width in pixels
            height: Button height in pixels
            **kwargs: Additional Canvas arguments
        """
        self.theme = PixelTheme.get_instance()
        self.btn_width = self.theme.scale_size(width)
        self.btn_height = self.theme.scale_size(height)

        super().__init__(
            parent,
            width=self.btn_width,
            height=self.btn_height,
            highlightthickness=0,
            bg=self.theme.colors["bg_dark"],
            **kwargs,
        )

        self.text = text
        self.command = command
        self.btn_state = "normal"
        self.enabled = True

        self._render()
        self._bind_events()

    def _render(self) -> None:
        """Redraw button in current state."""
        self.delete("all")

        # Determine colors based on state
        if self.btn_state == "hover":
            bg_color = self.theme.colors["highlight"]
        elif self.btn_state == "pressed":
            bg_color = self.theme.colors["secondary"]
        else:
            bg_color = self.theme.colors["primary"]

        # Draw button background
        border = 3
        self.create_rectangle(
            border,
            border,
            self.btn_width - border,
            self.btn_height - border,
            fill=bg_color,
            outline=self.theme.colors["border"],
            width=2,
        )

        # Draw text (centered)
        text_y = self.btn_height // 2
        if self.btn_state == "pressed":
            text_y += 2  # Shift text down with button

        text_kwargs: dict[str, Any] = {
            "text": self.text,
            "fill": self.theme.colors["text"],
            "anchor": "center",
        }
        btn_font = self.theme.get_font("small")
        if btn_font is not None:
            text_kwargs["font"] = btn_font

        self.create_text(
            self.btn_width // 2,
            text_y,
            **text_kwargs,
        )

    def _bind_events(self) -> None:
        """Bind mouse events."""
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, event: "tk.Event[Any]") -> None:
        """Handle mouse enter."""
        if self.enabled:
            self._set_state("hover")

    def _on_leave(self, event: "tk.Event[Any]") -> None:
        """Handle mouse leave."""
        if self.enabled:
            self._set_state("normal")

    def _on_press(self, event: "tk.Event[Any]") -> None:
        """Handle mouse press."""
        if self.enabled:
            self._set_state("pressed")

    def _on_release(self, event: "tk.Event[Any]") -> None:
        """Handle mouse release."""
        if not self.enabled:
            return

        # Check if still hovering
        x, y = event.x, event.y
        if 0 <= x <= self.btn_width and 0 <= y <= self.btn_height:
            self._set_state("hover")
            if self.command:
                try:
                    self.command()
                except Exception as e:
                    logger.error(f"Button command failed: {e}")
        else:
            self._set_state("normal")

    def _set_state(self, state: str) -> None:
        """Change button state and re-render.

        Args:
            state: "normal"|"hover"|"pressed"
        """
        self.btn_state = state
        self._render()

    def disable(self) -> None:
        """Disable button (grayed out, no interaction)."""
        self.enabled = False
        self.btn_state = "normal"
        # TODO: Add disabled visual state
        self._render()

    def enable(self) -> None:
        """Enable button."""
        self.enabled = True
        self._render()
