"""Error display dialog with details expander."""

import tkinter as tk
from typing import Optional


class ErrorDialog(tk.Toplevel):
    """Error display with expandable details and recovery hints.
    
    Usage:
        ErrorDialog.show_error(
            parent, 
            "Failed to install mod",
            details="FileNotFoundError: ...",
            hint="Check mod file exists"
        )
    """
    
    def __init__(self, parent, message: str, details: Optional[str] = None, 
                 hint: Optional[str] = None):
        """Initialize error dialog.
        
        Args:
            parent: Parent window
            message: Error message
            details: Technical details (exception traceback)
            hint: Recovery hint for user
        """
        super().__init__(parent)
        
        self.error_message = message
        self.error_details = details or "No additional details"
        self.recovery_hint = hint
        self.details_expanded = False
        
        # Window setup
        self.title("❌ Error")
        self.geometry("500x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Apply theme
        self.configure(bg="#1a1a1a")
        
        self._build_ui()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
    
    def _build_ui(self) -> None:
        """Build dialog UI."""
        from ..widgets.chunky_frame import ChunkyFrame
        from ..widgets.pixel_button import PixelButton
        
        # Error icon
        tk.Label(
            self, text="❌", font=("Courier New", 48),
            fg="#ff0000", bg="#1a1a1a"
        ).pack(pady=20)
        
        # Message
        tk.Label(
            self, text=self.error_message, font=("Courier New", 10, "bold"),
            fg="#ffffff", bg="#1a1a1a", wraplength=450
        ).pack(pady=10)
        
        # Recovery hint
        if self.recovery_hint:
            hint_frame = ChunkyFrame(self, border_color="#00e0ff", border_width=2)
            hint_frame.pack(padx=20, pady=10, fill=tk.X)
            
            tk.Label(
                hint_frame.get_content_frame(), text=f"💡 {self.recovery_hint}",
                font=("Courier New", 9), fg="#00ff00", bg="#1a1a1a", 
                wraplength=430, justify=tk.LEFT
            ).pack(padx=5, pady=5)
        
        # Details expander
        details_button_frame = tk.Frame(self, bg="#1a1a1a")
        details_button_frame.pack(pady=10)
        
        self.details_button = PixelButton(
            details_button_frame, text="▶ Show Details", command=self._toggle_details, width=150
        )
        self.details_button.pack()
        
        # Details frame (hidden initially)
        self.details_frame = ChunkyFrame(self, border_color="#ff6ec7", border_width=2)
        
        scrollbar = tk.Scrollbar(self.details_frame.get_content_frame())
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.details_text = tk.Text(
            self.details_frame.get_content_frame(), font=("Consolas", 8),
            bg="#2a2a2a", fg="#ff6ec7", wrap=tk.WORD, height=8,
            yscrollcommand=scrollbar.set
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.details_text.yview)
        
        self.details_text.insert("1.0", self.error_details)
        self.details_text.config(state=tk.DISABLED)
        
        # OK button
        ok_button_frame = tk.Frame(self, bg="#1a1a1a")
        ok_button_frame.pack(pady=10)
        PixelButton(ok_button_frame, text="OK", command=self._close, width=100).pack()
        
        # Bind Escape
        self.bind("<Escape>", lambda e: self._close())
    
    def _toggle_details(self) -> None:
        """Toggle details visibility."""
        if self.details_expanded:
            self.details_frame.pack_forget()
            # Re-render button with new text
            self.details_button.text = "▶ Show Details"
            self.details_button._render()
            self.geometry("500x300")
        else:
            self.details_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
            # Re-render button with new text
            self.details_button.text = "▼ Hide Details"
            self.details_button._render()
            self.geometry("500x550")
        
        self.details_expanded = not self.details_expanded
    
    def _close(self) -> None:
        """Handle OK button."""
        self.destroy()
    
    def show(self) -> None:
        """Show dialog and wait."""
        self.wait_window()
    
    @classmethod
    def show_error(cls, parent, message: str, details: Optional[str] = None,
                   hint: Optional[str] = None) -> None:
        """Convenience method to show error.
        
        Args:
            parent: Parent window
            message: Error message
            details: Technical details
            hint: Recovery hint
        """
        dialog = cls(parent, message, details, hint)
        dialog.show()
