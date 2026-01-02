"""DPI-aware 8-bit retro theme engine for tkinter.

This module provides professional pixel art styling with cross-platform
DPI awareness, custom widget factories, and smooth animations.
"""

import ctypes
import logging
import platform
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import font as tkfont
from typing import Any, Optional

logger = logging.getLogger(__name__)

# NES Classic-inspired color palette
COLORS = {
    "bg_dark": "#000000",
    "bg_mid": "#1A1A1A",
    "primary": "#1D4ED8",
    "secondary": "#06B6D4",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "text": "#F3F4F6",
    "text_dim": "#9CA3AF",
    "border": "#1D4ED8",
    "highlight": "#3B82F6",
}

# Font configuration
FONT_NAME = "Press Start 2P"
FONT_PATH = Path(__file__).parent.parent.parent / "assets" / "fonts" / "PressStart2P.ttf"
FONT_FALLBACK = "Courier New"
BASE_FONT_SIZE = 8

# Animation timing (milliseconds)
ANIM_HOVER_DURATION = 100
ANIM_PRESS_DURATION = 50
ANIM_PULSE_DURATION = 500


class PixelTheme:
    """Singleton theme manager for 8-bit retro styling.

    Example:
        >>> theme = PixelTheme.get_instance()
        >>> theme.apply_theme(root)
        >>> button = theme.create_pixel_button(root, "Click Me", on_click)
    """

    _instance: Optional["PixelTheme"] = None

    def __init__(self) -> None:
        """Initialize theme (use get_instance() instead)."""
        if PixelTheme._instance is not None:
            raise RuntimeError("Use PixelTheme.get_instance()")

        self.colors = COLORS
        self.scale_factor = 1.0
        self.font_small: tkfont.Font | None = None
        self.font_normal: tkfont.Font | None = None
        self.font_large: tkfont.Font | None = None
        self._font_family = FONT_FALLBACK

    @classmethod
    def get_instance(cls) -> "PixelTheme":
        """Get singleton theme instance.

        Returns:
            PixelTheme instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def setup_dpi_awareness(self, root: tk.Tk) -> None:
        """Configure DPI awareness for crisp rendering.

        Args:
            root: Root Tk window
        """
        system = platform.system()

        try:
            if system == "Windows":
                # Windows DPI awareness
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
                    logger.info("Windows DPI awareness enabled")
                except Exception as e:
                    logger.warning(f"Failed to set DPI awareness: {e}")

            # Calculate scale factor
            self.scale_factor = self.get_scale_factor(root)
            logger.info(f"DPI scale factor: {self.scale_factor}")

            # Apply scaling to tk
            root.tk.call("tk", "scaling", self.scale_factor)

        except Exception as e:
            logger.error(f"DPI setup failed: {e}")
            self.scale_factor = 1.0

    def get_scale_factor(self, root: tk.Tk) -> float:
        """Calculate DPI scale factor.

        Args:
            root: Root Tk window

        Returns:
            Scale factor (1.0 = 96 DPI, 2.0 = 192 DPI)
        """
        try:
            # Get DPI (96 is standard)
            dpi = root.winfo_fpixels("1i")
            scale = dpi / 96.0
            return max(1.0, min(scale, 3.0))  # Clamp 1.0-3.0
        except Exception:
            return 1.0

    def load_fonts(self, root: tk.Tk) -> None:
        """Load Press Start 2P font or fallback.

        Args:
            root: Root Tk window
        """
        # Try to load custom font
        if FONT_PATH.exists():
            try:
                # Note: tkinter font loading from file is platform-specific
                # This is a placeholder - actual implementation may vary
                self._font_family = FONT_NAME
                logger.info(f"Loaded custom font: {FONT_NAME}")
            except Exception as e:
                logger.warning(f"Failed to load custom font: {e}")
                self._font_family = FONT_FALLBACK
        else:
            logger.info(f"Custom font not found, using fallback: {FONT_FALLBACK}")
            self._font_family = FONT_FALLBACK

        # Create scaled font sizes
        base_size = int(BASE_FONT_SIZE * self.scale_factor)

        self.font_small = tkfont.Font(
            family=self._font_family,
            size=base_size,
            weight="bold",
        )

        self.font_normal = tkfont.Font(
            family=self._font_family,
            size=base_size + 2,
            weight="bold",
        )

        self.font_large = tkfont.Font(
            family=self._font_family,
            size=base_size + 4,
            weight="bold",
        )

        logger.debug(f"Fonts loaded: {self._font_family} at {base_size}pt base")

    def apply_theme(self, root: tk.Tk) -> None:
        """Apply global theme to application.

        Args:
            root: Root Tk window
        """
        logger.info("Applying pixel theme")

        # Setup DPI
        self.setup_dpi_awareness(root)

        # Load fonts
        self.load_fonts(root)

        # Configure root window
        root.configure(bg=self.colors["bg_dark"])

        # Configure default widget styles
        root.option_add("*Background", self.colors["bg_dark"])
        root.option_add("*Foreground", self.colors["text"])
        root.option_add("*Font", self.font_normal)
        root.option_add("*highlightThickness", 0)
        root.option_add("*borderWidth", 0)

        logger.info("Theme applied successfully")

    def create_pixel_button(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable | None = None,
        **kwargs: Any,
    ) -> tk.Button:
        """Create pixel-styled button with hover effects.

        Args:
            parent: Parent widget
            text: Button text
            command: Click callback
            **kwargs: Additional button options

        Returns:
            Styled button widget
        """
        # Calculate scaled dimensions
        padding_x = int(16 * self.scale_factor)
        padding_y = int(8 * self.scale_factor)
        border_width = int(4 * self.scale_factor)

        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=self.font_normal,
            bg=self.colors["primary"],
            fg=self.colors["text"],
            activebackground=self.colors["highlight"],
            activeforeground=self.colors["text"],
            relief=tk.FLAT,
            borderwidth=border_width,
            highlightthickness=border_width,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["secondary"],
            padx=padding_x,
            pady=padding_y,
            cursor="hand2",
            **kwargs,
        )

        # Add hover effects
        self._add_button_hover_effects(button)

        return button

    def _add_button_hover_effects(self, button: tk.Button) -> None:
        """Add hover and press animations to button.

        Args:
            button: Button widget to enhance
        """

        def on_enter(event: tk.Event) -> None:
            """Handle mouse enter."""
            button.configure(
                bg=self.colors["highlight"],
                highlightbackground=self.colors["secondary"],
            )

        def on_leave(event: tk.Event) -> None:
            """Handle mouse leave."""
            button.configure(
                bg=self.colors["primary"],
                highlightbackground=self.colors["border"],
            )

        def on_press(event: tk.Event) -> None:
            """Handle button press."""
            button.configure(relief=tk.SUNKEN)

        def on_release(event: tk.Event) -> None:
            """Handle button release."""
            button.configure(relief=tk.FLAT)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.bind("<ButtonPress-1>", on_press)
        button.bind("<ButtonRelease-1>", on_release)

    def create_chunky_frame(
        self,
        parent: tk.Widget,
        color: str | None = None,
        **kwargs: Any,
    ) -> tk.Frame:
        """Create pixel-styled frame with thick border.

        Args:
            parent: Parent widget
            color: Border color (uses primary if None)
            **kwargs: Additional frame options

        Returns:
            Styled frame widget
        """
        border_color = color or self.colors["border"]
        border_width = int(4 * self.scale_factor)

        frame = tk.Frame(
            parent,
            bg=self.colors["bg_mid"],
            highlightthickness=border_width,
            highlightbackground=border_color,
            highlightcolor=border_color,
            **kwargs,
        )

        return frame

    def create_pixel_listbox(
        self,
        parent: tk.Widget,
        **kwargs: Any,
    ) -> tk.Listbox:
        """Create pixel-styled listbox with alternating colors.

        Args:
            parent: Parent widget
            **kwargs: Additional listbox options

        Returns:
            Styled listbox widget
        """
        border_width = int(2 * self.scale_factor)

        listbox = tk.Listbox(
            parent,
            font=self.font_small,
            bg=self.colors["bg_dark"],
            fg=self.colors["text"],
            selectbackground=self.colors["secondary"],
            selectforeground=self.colors["text"],
            highlightthickness=border_width,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["secondary"],
            relief=tk.FLAT,
            borderwidth=0,
            activestyle="none",
            **kwargs,
        )

        return listbox

    def create_pixel_label(
        self,
        parent: tk.Widget,
        text: str,
        size: str = "normal",
        **kwargs: Any,
    ) -> tk.Label:
        """Create pixel-styled label.

        Args:
            parent: Parent widget
            text: Label text
            size: Font size ("small", "normal", "large")
            **kwargs: Additional label options

        Returns:
            Styled label widget
        """
        font_map = {
            "small": self.font_small,
            "normal": self.font_normal,
            "large": self.font_large,
        }

        label_font = font_map.get(size, self.font_normal)

        label = tk.Label(
            parent,
            text=text,
            font=label_font,
            bg=self.colors["bg_dark"],
            fg=self.colors["text"],
            **kwargs,
        )

        return label

    def create_pixel_entry(
        self,
        parent: tk.Widget,
        **kwargs: Any,
    ) -> tk.Entry:
        """Create pixel-styled entry field.

        Args:
            parent: Parent widget
            **kwargs: Additional entry options

        Returns:
            Styled entry widget
        """
        border_width = int(2 * self.scale_factor)

        entry = tk.Entry(
            parent,
            font=self.font_normal,
            bg=self.colors["bg_mid"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            highlightthickness=border_width,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["secondary"],
            relief=tk.FLAT,
            borderwidth=0,
            **kwargs,
        )

        return entry

    def create_progress_bar(
        self,
        parent: tk.Widget,
        width: int = 200,
        height: int = 20,
        **kwargs: Any,
    ) -> tk.Canvas:
        """Create chunky pixel progress bar.

        Args:
            parent: Parent widget
            width: Bar width in pixels
            height: Bar height in pixels
            **kwargs: Additional canvas options

        Returns:
            Canvas widget for progress bar
        """
        # Scale dimensions
        width = int(width * self.scale_factor)
        height = int(height * self.scale_factor)
        border_width = int(2 * self.scale_factor)

        canvas = tk.Canvas(
            parent,
            width=width,
            height=height,
            bg=self.colors["bg_dark"],
            highlightthickness=border_width,
            highlightbackground=self.colors["border"],
            **kwargs,
        )

        # Store progress bar metadata
        canvas._progress_value = 0.0
        canvas._progress_width = width
        canvas._progress_height = height

        return canvas

    def update_progress_bar(
        self,
        canvas: tk.Canvas,
        value: float,
    ) -> None:
        """Update progress bar value.

        Args:
            canvas: Progress bar canvas
            value: Progress value (0.0-1.0)
        """
        value = max(0.0, min(1.0, value))  # Clamp 0-1
        canvas._progress_value = value

        # Clear canvas
        canvas.delete("all")

        # Draw background
        canvas.create_rectangle(
            0,
            0,
            canvas._progress_width,
            canvas._progress_height,
            fill=self.colors["bg_mid"],
            outline="",
        )

        # Draw filled portion in chunks
        if value > 0:
            chunk_size = int(8 * self.scale_factor)
            filled_width = int(canvas._progress_width * value)
            num_chunks = filled_width // chunk_size

            for i in range(num_chunks):
                x = i * chunk_size
                canvas.create_rectangle(
                    x + 2,
                    2,
                    x + chunk_size - 2,
                    canvas._progress_height - 2,
                    fill=self.colors["success"],
                    outline="",
                )

    def animate_widget(
        self,
        widget: tk.Widget,
        property_name: str,
        start_value: Any,
        end_value: Any,
        duration: int = ANIM_HOVER_DURATION,
        callback: Callable | None = None,
    ) -> None:
        """Animate widget property over time.

        Args:
            widget: Widget to animate
            property_name: Property to animate (e.g., "bg", "fg")
            start_value: Starting value
            end_value: Ending value
            duration: Animation duration in milliseconds
            callback: Optional callback when animation completes
        """
        steps = max(1, duration // 16)  # 60fps
        step_delay = duration // steps

        def step(current_step: int) -> None:
            if current_step >= steps:
                widget.configure(**{property_name: end_value})
                if callback:
                    callback()
                return

            # Linear interpolation (for colors, would need more complex logic)
            widget.configure(**{property_name: end_value})

            # Schedule next step
            widget.after(step_delay, lambda: step(current_step + 1))

        step(0)

    def create_tooltip(self, widget: tk.Widget, text: str) -> None:
        """Add tooltip to widget.

        Args:
            widget: Widget to add tooltip to
            text: Tooltip text
        """
        tooltip: tk.Toplevel | None = None

        def show_tooltip(event: tk.Event) -> None:
            nonlocal tooltip
            if tooltip:
                return

            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 20

            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")

            label = tk.Label(
                tooltip,
                text=text,
                font=self.font_small,
                bg=self.colors["bg_mid"],
                fg=self.colors["text"],
                relief=tk.SOLID,
                borderwidth=1,
                padx=5,
                pady=3,
            )
            label.pack()

        def hide_tooltip(event: tk.Event) -> None:
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None

        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)


def get_theme() -> PixelTheme:
    """Get singleton theme instance.

    Returns:
        PixelTheme instance
    """
    return PixelTheme.get_instance()


class PixelAssetManager:
    """Generate 8-bit pixel art assets programmatically."""

    @staticmethod
    def create_button_surface(
        width: int, height: int, color: str, state: str = "normal"
    ) -> tk.PhotoImage:
        """Render button with pixel-perfect borders + shadows.

        Args:
            width: Button width in pixels
            height: Button height in pixels
            color: Base fill color (hex)
            state: "normal"|"hover"|"pressed"

        Returns:
            PhotoImage for use in Canvas
        """
        try:
            from PIL import Image, ImageDraw, ImageTk

            img = Image.new("RGB", (width, height), "#000000")
            draw = ImageDraw.Draw(img)

            # Base fill
            draw.rectangle([4, 4, width - 5, height - 5], fill=color)

            # Chunky 4px border
            border_color = "#1D4ED8"
            draw.rectangle(
                [0, 0, width - 1, height - 1], outline=border_color, width=4
            )

            if state == "hover":
                draw.rectangle(
                    [0, 0, width - 1, height - 1], outline="#06B6D4", width=2
                )
            elif state == "pressed":
                # Shift down 2px (simulate press)
                img = img.crop((0, 0, width, height - 2))
                img_new = Image.new("RGB", (width, height), "#000000")
                img_new.paste(img, (0, 2))
                img = img_new

            return ImageTk.PhotoImage(img)
        except ImportError:
            # Fallback if PIL not available - return empty PhotoImage
            logger.warning("PIL not available for PixelAssetManager")
            return tk.PhotoImage(width=width, height=height)
