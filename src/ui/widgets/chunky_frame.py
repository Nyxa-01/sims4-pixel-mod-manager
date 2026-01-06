"""Chunky bordered frame with 8-bit pixel aesthetic.

Provides container with thick retro borders.
"""

import tkinter as tk
from typing import Any


class ChunkyFrame(tk.Frame):
    """Frame with thick pixel borders.

    Usage:
        frame = ChunkyFrame(parent, border_color="#00e0ff", border_width=4)
        content = tk.Label(frame, text="Content")
        content.pack(padx=10, pady=10)
    """

    def __init__(
        self,
        parent: tk.Widget,
        border_color: str = "#00e0ff",
        border_width: int = 4,
        bg: str = "#1a1a1a",
        **kwargs: Any,
    ) -> None:
        """Initialize chunky frame.

        Args:
            parent: Parent widget
            border_color: Border color
            border_width: Border thickness in pixels
            bg: Background color
        """
        super().__init__(parent, bg=border_color, **kwargs)

        self.border_width = border_width
        self.border_color = border_color
        self.bg_color = bg

        # Inner frame for content
        self.inner_frame = tk.Frame(self, bg=bg)
        self.inner_frame.pack(padx=border_width, pady=border_width, fill=tk.BOTH, expand=True)

    def get_content_frame(self) -> tk.Frame:
        """Get inner frame for adding content.

        Returns:
            Inner content frame
        """
        return self.inner_frame

    def set_border_color(self, color: str) -> None:
        """Change border color.

        Args:
            color: New border color
        """
        self.border_color = color
        self.configure(bg=color)
