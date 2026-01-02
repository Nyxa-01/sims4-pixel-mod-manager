"""8-bit styled button with hover/press animations."""

import logging
import tkinter as tk
from collections.abc import Callable

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
        **kwargs: object,
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
        """Pre-render button surfaces for each state."""
        self.surfaces = {
            "normal": PixelAssetManager.create_button_surface(
                self.width, self.height, self.theme.COLORS["primary"], "normal"
            ),
            "hover": PixelAssetManager.create_button_surface(
                self.width, self.height, self.theme.COLORS["primary_hover"], "hover"
            ),
            "pressed": PixelAssetManager.create_button_surface(
                self.width, self.height, self.theme.COLORS["primary"], "pressed"
            ),
        }

    def _render(self) -> None:
        """Redraw button in current state."""
        self.delete("all")

        # Draw button surface
        self.create_image(0, 0, image=self.surfaces[self.state], anchor="nw")

        # Draw text (centered)
        text_y = self.height // 2
        if self.state == "pressed":
            text_y += 2  # Shift text down with button

        self.create_text(
            self.width // 2,
            text_y,
            text=self.text,
            fill=self.theme.COLORS["text"],
            font=self.theme.get_font(8),
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
