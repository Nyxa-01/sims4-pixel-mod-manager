"""8-bit styled button with hover/press animations."""

import logging
import tkinter as tk
from collections.abc import Callable
from typing import Any

from ..pixel_theme import PixelTheme

logger = logging.getLogger(__name__)


class PixelButton(tk.Canvas):
    """Custom button with 8-bit pixel art styling."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], None] | None = None,
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
        self.width = self.theme.scale_size(width)
        self.height = self.theme.scale_size(height)

        super().__init__(
            parent,
            width=self.width,
            height=self.height,
            highlightthickness=0,
            bg=self.theme.COLORS["background"],
            **kwargs,
        )

        self.text = text
        self.command = command
        self.state = "normal"
        self.enabled = True

        # Pre-render button states
        self._render_surfaces()
        self._render()
        self._bind_events()

    def _render_surfaces(self) -> None:
        """Pre-render button color mappings for each state."""
        self.surface_colors = {
            "normal": self.theme.COLORS["primary"],
            "hover": self.theme.COLORS["primary_hover"],
            "pressed": self.theme.COLORS["primary"],
        }

    def _render(self) -> None:
        """Redraw button in current state."""
        self.delete("all")

        # Get colors for current state
        bg_color = self.surface_colors[self.state]

        # Draw button background with 8-bit style border
        border_width = 2
        if self.state == "pressed":
            # Pressed state: inset border
            self.create_rectangle(
                0,
                0,
                self.width - 1,
                self.height - 1,
                fill=bg_color,
                outline=self.theme.COLORS["border"],
            )
            # Inner shadow
            self.create_line(0, 0, self.width, 0, fill="#000000", width=border_width)
            self.create_line(0, 0, 0, self.height, fill="#000000", width=border_width)
        else:
            # Normal/hover state: raised border
            self.create_rectangle(
                0,
                0,
                self.width - 1,
                self.height - 1,
                fill=bg_color,
                outline=self.theme.COLORS["border"],
            )
            # Highlight on top and left
            self.create_line(0, 0, self.width, 0, fill="#ffffff", width=border_width)
            self.create_line(0, 0, 0, self.height, fill="#ffffff", width=border_width)
            # Shadow on bottom and right
            self.create_line(
                0, self.height - 1, self.width, self.height - 1, fill="#000000", width=border_width
            )
            self.create_line(
                self.width - 1, 0, self.width - 1, self.height, fill="#000000", width=border_width
            )

        # Draw text (centered)
        text_y = self.height // 2
        if self.state == "pressed":
            text_y += 2  # Shift text down with button

        font = self.theme.get_font(8) or "TkDefaultFont"
        self.create_text(
            self.width // 2,
            text_y,
            text=self.text,
            fill=self.theme.COLORS["text"],
            font=font,
            anchor="center",
        )

    def _bind_events(self) -> None:
        """Bind mouse events."""
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, event: tk.Event) -> None:
        """Handle mouse enter."""
        if self.enabled:
            self._set_state("hover")

    def _on_leave(self, event: tk.Event) -> None:
        """Handle mouse leave."""
        if self.enabled:
            self._set_state("normal")

    def _on_press(self, event: tk.Event) -> None:
        """Handle mouse press."""
        if self.enabled:
            self._set_state("pressed")

    def _on_release(self, event: tk.Event) -> None:
        """Handle mouse release."""
        if not self.enabled:
            return

        # Check if still hovering
        x, y = event.x, event.y
        if 0 <= x <= self.width and 0 <= y <= self.height:
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
        self.state = state
        self._render()

    def disable(self) -> None:
        """Disable button (grayed out, no interaction)."""
        self.enabled = False
        self.state = "normal"
        # TODO: Add disabled visual state
        self._render()

    def enable(self) -> None:
        """Enable button."""
        self.enabled = True
        self._render()
