"""Splash screen displayed during app initialization."""

import tkinter as tk


class SplashScreen:
    """8-bit styled splash screen.

    Usage:
        splash = SplashScreen()
        splash.show()
        # ... initialization ...
        splash.update_progress(0.5, "Loading mods...")
        # ... more work ...
        splash.close()
    """

    def __init__(self, title: str = "Sims 4 Pixel Mod Manager", version: str = "1.0.0"):
        """Initialize splash screen.

        Args:
            title: Application title
            version: Version string
        """
        self.title = title
        self.version = version
        self.window: tk.Tk | None = None
        self.progress_label: tk.Label | None = None
        self.progress_canvas: tk.Canvas | None = None

    def show(self) -> None:
        """Display splash screen."""
        self.window = tk.Tk()
        self.window.title("")
        self.window.overrideredirect(True)  # No window decorations

        width = 400
        height = 300

        # Center on screen
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        # Background
        self.window.configure(bg="#1a1a1a")

        # Border
        border_frame = tk.Frame(self.window, bg="#00e0ff", bd=0)
        border_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        content_frame = tk.Frame(border_frame, bg="#1a1a1a", bd=0)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Title
        title_label = tk.Label(
            content_frame,
            text=self.title,
            font=("Courier New", 12, "bold"),
            fg="#00e0ff",
            bg="#1a1a1a",
        )
        title_label.pack(pady=(40, 10))

        # Version
        version_label = tk.Label(
            content_frame,
            text=f"v{self.version}",
            font=("Courier New", 8),
            fg="#ff6ec7",
            bg="#1a1a1a",
        )
        version_label.pack(pady=5)

        # Progress canvas
        self.progress_canvas = tk.Canvas(
            content_frame, width=300, height=24, bg="#1a1a1a", highlightthickness=0
        )
        self.progress_canvas.pack(pady=30)

        # Progress text
        self.progress_label = tk.Label(
            content_frame,
            text="Initializing...",
            font=("Courier New", 8),
            fg="#00ff00",
            bg="#1a1a1a",
        )
        self.progress_label.pack(pady=10)

        self.window.update()

    def update_progress(self, progress: float, message: str) -> None:
        """Update progress bar and message.

        Args:
            progress: Progress from 0.0 to 1.0
            message: Status message
        """
        if not self.window or not self.progress_canvas:
            return

        self.progress_canvas.delete("all")

        # Background
        self.progress_canvas.create_rectangle(
            0, 0, 300, 24, fill="#2a2a2a", outline="#00e0ff", width=2
        )

        # Progress bar (segmented)
        segments = 20
        filled_segments = int(progress * segments)
        segment_width = 300 / segments

        for i in range(filled_segments):
            x = i * segment_width + 2
            self.progress_canvas.create_rectangle(
                x, 2, x + segment_width - 4, 22, fill="#00ff00", outline=""
            )

        # Update message
        if self.progress_label:
            self.progress_label.config(text=message)

        self.window.update()

    def close(self) -> None:
        """Close splash screen."""
        if self.window:
            self.window.destroy()
            self.window = None
