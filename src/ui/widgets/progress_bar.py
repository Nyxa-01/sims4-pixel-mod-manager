"""Segmented 8-bit progress bar with pixel blocks.

Displays progress as filled pixel segments.
"""

import tkinter as tk
from typing import Any


class PixelProgressBar(tk.Canvas):
    """Segmented progress bar with 8-bit styling.

    Usage:
        pbar = PixelProgressBar(parent, segments=10, width=300, height=24)
        pbar.set_progress(0.75)  # 75%
    """

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel | tk.Widget,
        segments: int = 20,
        width: int = 400,
        height: int = 32,
        **kwargs: Any,
    ) -> None:
        """Initialize progress bar.

        Args:
            parent: Parent widget
            segments: Number of progress segments
            width: Canvas width
            height: Canvas height
        """
        super().__init__(
            parent,
            width=width,
            height=height,
            bg="#1a1a1a",
            highlightthickness=0,
            **kwargs,
        )

        self.segments = segments
        self.progress = 0.0  # 0.0 to 1.0
        self.segment_width = (width - 8) / segments
        self.segment_height = height - 8

        self._render()

    def set_progress(self, progress: float) -> None:
        """Set progress value.

        Args:
            progress: Progress from 0.0 to 1.0
        """
        self.progress = max(0.0, min(1.0, progress))
        self._render()

    def get_progress(self) -> float:
        """Get current progress.

        Returns:
            Progress from 0.0 to 1.0
        """
        return self.progress

    def _render(self) -> None:
        """Render progress bar."""
        self.delete("all")

        filled_segments = int(self.progress * self.segments)

        for i in range(self.segments):
            x = 4 + i * self.segment_width

            if i < filled_segments:
                # Filled segment
                fill_color = "#00ff00" if self.progress < 1.0 else "#00e0ff"
                self.create_rectangle(
                    x,
                    4,
                    x + self.segment_width - 2,
                    4 + self.segment_height,
                    fill=fill_color,
                    outline="",
                    width=0,
                )
            else:
                # Empty segment
                self.create_rectangle(
                    x,
                    4,
                    x + self.segment_width - 2,
                    4 + self.segment_height,
                    fill="#2a2a2a",
                    outline="#444444",
                    width=1,
                )

        # Border
        self.create_rectangle(
            2,
            2,
            self.winfo_width() - 2,
            self.winfo_height() - 2,
            outline="#00e0ff",
            width=2,
        )
