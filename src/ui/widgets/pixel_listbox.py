"""Drag-and-drop enabled listbox with 8-bit styling.

Supports reordering items via drag-drop for load order management.
"""

import tkinter as tk
from tkinter import font as tkfont
from typing import List, Callable, Optional, Tuple


class PixelListbox(tk.Canvas):
    """Listbox with drag-drop reordering and pixel styling.
    
    Usage:
        listbox = PixelListbox(parent, width=400, height=300)
        listbox.set_items(["Item 1", "Item 2", "Item 3"])
        listbox.on_reorder(my_callback)
    """
    
    def __init__(self, parent, width: int = 400, height: int = 300, **kwargs):
        """Initialize pixel listbox.
        
        Args:
            parent: Parent widget
            width: Canvas width
            height: Canvas height
        """
        super().__init__(parent, width=width, height=height, 
                        bg="#1a1a1a", highlightthickness=0, **kwargs)
        
        self.items: List[str] = []
        self.selected_index: Optional[int] = None
        self.drag_start_index: Optional[int] = None
        self.item_height = 32
        self.padding = 4
        
        # Callbacks
        self.reorder_callback: Optional[Callable[[List[str]], None]] = None
        self.selection_callback: Optional[Callable[[int, str], None]] = None
        
        # Font
        try:
            self.item_font = tkfont.Font(family="Press Start 2P", size=8)
        except Exception:
            self.item_font = tkfont.Font(family="Courier New", size=10)
        
        # Scrollbar
        self.scrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL, command=self.yview)
        self.configure(yscrollcommand=self.scrollbar.set)
        
        # Bindings
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Motion>", self._on_hover)
    
    def set_items(self, items: List[str]) -> None:
        """Set listbox items.
        
        Args:
            items: List of item strings
        """
        self.items = items.copy()
        self.selected_index = None
        self._render()
    
    def get_items(self) -> List[str]:
        """Get current items list.
        
        Returns:
            List of item strings
        """
        return self.items.copy()
    
    def get_selected(self) -> Optional[Tuple[int, str]]:
        """Get selected item.
        
        Returns:
            Tuple of (index, item) or None
        """
        if self.selected_index is not None and 0 <= self.selected_index < len(self.items):
            return (self.selected_index, self.items[self.selected_index])
        return None
    
    def on_reorder(self, callback: Callable[[List[str]], None]) -> None:
        """Register callback for item reordering.
        
        Args:
            callback: Function called with new item order
        """
        self.reorder_callback = callback
    
    def on_selection(self, callback: Callable[[int, str], None]) -> None:
        """Register callback for item selection.
        
        Args:
            callback: Function called with (index, item)
        """
        self.selection_callback = callback
    
    def _render(self) -> None:
        """Render all items."""
        self.delete("all")
        
        y_offset = self.padding
        
        for i, item in enumerate(self.items):
            # Background
            bg_color = "#ff6ec7" if i == self.selected_index else "#2a2a2a"
            self.create_rectangle(
                self.padding, y_offset,
                self.winfo_width() - self.padding, y_offset + self.item_height,
                fill=bg_color, outline="#00e0ff", width=2, tags=f"item_{i}"
            )
            
            # Text
            text_color = "#000000" if i == self.selected_index else "#00ff00"
            self.create_text(
                self.padding + 8, y_offset + self.item_height // 2,
                text=item, anchor="w", fill=text_color, font=self.item_font,
                tags=f"item_{i}"
            )
            
            y_offset += self.item_height + self.padding
        
        # Update scroll region
        self.configure(scrollregion=(0, 0, self.winfo_width(), y_offset))
    
    def _get_item_at_y(self, y: int) -> Optional[int]:
        """Get item index at Y coordinate.
        
        Args:
            y: Y coordinate
            
        Returns:
            Item index or None
        """
        y_adjusted = y + self.canvasy(0)
        index = int(y_adjusted // (self.item_height + self.padding))
        
        if 0 <= index < len(self.items):
            return index
        return None
    
    def _on_click(self, event) -> None:
        """Handle mouse click."""
        index = self._get_item_at_y(event.y)
        if index is not None:
            self.selected_index = index
            self.drag_start_index = index
            self._render()
            
            if self.selection_callback:
                self.selection_callback(index, self.items[index])
    
    def _on_drag(self, event) -> None:
        """Handle mouse drag."""
        if self.drag_start_index is None:
            return
        
        target_index = self._get_item_at_y(event.y)
        if target_index is not None and target_index != self.drag_start_index:
            # Reorder items
            item = self.items.pop(self.drag_start_index)
            self.items.insert(target_index, item)
            self.drag_start_index = target_index
            self.selected_index = target_index
            self._render()
    
    def _on_release(self, event) -> None:
        """Handle mouse release."""
        if self.drag_start_index is not None and self.reorder_callback:
            self.reorder_callback(self.items.copy())
        self.drag_start_index = None
    
    def _on_mousewheel(self, event) -> None:
        """Handle mousewheel scroll."""
        self.yview_scroll(-1 * int(event.delta / 120), "units")
    
    def _on_hover(self, event) -> None:
        """Handle mouse hover."""
        index = self._get_item_at_y(event.y)
        if index is not None:
            self.configure(cursor="hand2")
        else:
            self.configure(cursor="")
