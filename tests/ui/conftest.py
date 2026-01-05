"""Pytest fixtures for UI tests with mocked Tkinter components.

These fixtures enable GUI testing without requiring a display.
"""

import sys
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest


class MockTkWidget:
    """Base mock for Tkinter widgets."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._config: dict[str, Any] = {}
        self._children: list[Any] = []
        self._bindings: dict[str, list[Any]] = {}
        self._pack_info: dict[str, Any] = {}
        self._grid_info: dict[str, Any] = {}
        self._place_info: dict[str, Any] = {}
        # Store kwargs as config
        for key, value in kwargs.items():
            self._config[key] = value

    def __getitem__(self, key: str) -> Any:
        return self._config.get(key, "")

    def __setitem__(self, key: str, value: Any) -> None:
        self._config[key] = value

    def configure(self, **kwargs: Any) -> None:
        """Configure widget options."""
        self._config.update(kwargs)

    config = configure

    def cget(self, key: str) -> Any:
        """Get configuration option."""
        return self._config.get(key, "")

    def bind(self, event: str, func: Any, add: str = "") -> str:
        """Bind event to function."""
        if event not in self._bindings:
            self._bindings[event] = []
        self._bindings[event].append(func)
        return f"bind_{id(func)}"

    def unbind(self, event: str, funcid: str = "") -> None:
        """Unbind event."""
        if event in self._bindings:
            self._bindings[event] = []

    def pack(self, **kwargs: Any) -> None:
        """Pack widget."""
        self._pack_info = kwargs

    def pack_forget(self) -> None:
        """Remove from pack."""
        self._pack_info = {}

    def grid(self, **kwargs: Any) -> None:
        """Grid widget."""
        self._grid_info = kwargs

    def grid_forget(self) -> None:
        """Remove from grid."""
        self._grid_info = {}

    def place(self, **kwargs: Any) -> None:
        """Place widget."""
        self._place_info = kwargs

    def place_forget(self) -> None:
        """Remove from place."""
        self._place_info = {}

    def destroy(self) -> None:
        """Destroy widget."""
        self._children = []

    def winfo_children(self) -> list[Any]:
        """Get children."""
        return self._children

    def winfo_width(self) -> int:
        """Get width."""
        return self._config.get("width", 100)

    def winfo_height(self) -> int:
        """Get height."""
        return self._config.get("height", 100)

    def winfo_reqwidth(self) -> int:
        """Get requested width."""
        return self._config.get("width", 100)

    def winfo_reqheight(self) -> int:
        """Get requested height."""
        return self._config.get("height", 100)

    def winfo_exists(self) -> bool:
        """Check if widget exists."""
        return True

    def winfo_toplevel(self) -> "MockTkWidget":
        """Get toplevel window."""
        return self

    def winfo_screenwidth(self) -> int:
        """Get screen width."""
        return 1920

    def winfo_screenheight(self) -> int:
        """Get screen height."""
        return 1080

    def winfo_fpixels(self, value: str) -> float:
        """Convert to pixels."""
        if isinstance(value, str) and value.endswith("i"):
            return float(value[:-1]) * 72
        return float(value) if value else 0.0

    def update(self) -> None:
        """Update widget."""
        pass

    def update_idletasks(self) -> None:
        """Update idle tasks."""
        pass

    def after(self, ms: int, func: Any = None, *args: Any) -> str:
        """Schedule callback."""
        if func:
            func(*args)
        return f"after_{ms}"

    def after_cancel(self, id: str) -> None:
        """Cancel scheduled callback."""
        pass

    def focus_set(self) -> None:
        """Set focus."""
        pass

    def tk_focusNext(self) -> "MockTkWidget":
        """Get next focus widget."""
        return self

    def lift(self) -> None:
        """Raise window."""
        pass

    def lower(self) -> None:
        """Lower window."""
        pass


class MockTk(MockTkWidget):
    """Mock Tk root window."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._config["bg"] = "#ffffff"
        self.tk = Mock()
        self.tk.call = Mock(return_value="")
        self.tk.eval = Mock(return_value="")

    def title(self, title: str = "") -> str:
        """Set/get title."""
        if title:
            self._config["title"] = title
        return self._config.get("title", "")

    def geometry(self, geometry: str = "") -> str:
        """Set/get geometry."""
        if geometry:
            self._config["geometry"] = geometry
        return self._config.get("geometry", "800x600+0+0")

    def resizable(self, width: bool = True, height: bool = True) -> None:
        """Set resizable."""
        self._config["resizable"] = (width, height)

    def minsize(self, width: int = 0, height: int = 0) -> tuple[int, int]:
        """Set/get minimum size."""
        if width or height:
            self._config["minsize"] = (width, height)
        return self._config.get("minsize", (0, 0))

    def maxsize(self, width: int = 0, height: int = 0) -> tuple[int, int]:
        """Set/get maximum size."""
        if width or height:
            self._config["maxsize"] = (width, height)
        return self._config.get("maxsize", (0, 0))

    def protocol(self, name: str, func: Any = None) -> None:
        """Set protocol handler."""
        self._config[f"protocol_{name}"] = func

    def mainloop(self) -> None:
        """Start main loop (no-op in tests)."""
        pass

    def quit(self) -> None:
        """Quit main loop."""
        pass

    def withdraw(self) -> None:
        """Hide window."""
        self._config["visible"] = False

    def deiconify(self) -> None:
        """Show window."""
        self._config["visible"] = True

    def iconbitmap(self, bitmap: str = "") -> None:
        """Set icon."""
        self._config["icon"] = bitmap

    def state(self, state: str = "") -> str:
        """Set/get state."""
        if state:
            self._config["state"] = state
        return self._config.get("state", "normal")

    def attributes(self, *args: Any) -> Any:
        """Set/get attributes."""
        if len(args) == 1:
            return self._config.get(f"attr_{args[0]}", None)
        elif len(args) == 2:
            self._config[f"attr_{args[0]}"] = args[1]
        return None

    def option_add(self, pattern: str, value: Any, priority: int = 60) -> None:
        """Add option."""
        pass

    def eval(self, script: str) -> str:
        """Evaluate Tcl script."""
        return ""


class MockFrame(MockTkWidget):
    """Mock Frame widget."""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.master = master
        self._config.setdefault("bg", "#ffffff")
        if master and hasattr(master, "_children"):
            master._children.append(self)


class MockCanvas(MockTkWidget):
    """Mock Canvas widget."""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.master = master
        self._items: dict[int, dict[str, Any]] = {}
        self._item_counter = 0
        self._config.setdefault("bg", "#ffffff")
        if master and hasattr(master, "_children"):
            master._children.append(self)

    def create_rectangle(self, x1: float, y1: float, x2: float, y2: float, **kwargs: Any) -> int:
        """Create rectangle."""
        self._item_counter += 1
        self._items[self._item_counter] = {
            "type": "rectangle",
            "coords": (x1, y1, x2, y2),
            **kwargs,
        }
        return self._item_counter

    def create_oval(self, x1: float, y1: float, x2: float, y2: float, **kwargs: Any) -> int:
        """Create oval."""
        self._item_counter += 1
        self._items[self._item_counter] = {
            "type": "oval",
            "coords": (x1, y1, x2, y2),
            **kwargs,
        }
        return self._item_counter

    def create_line(self, *coords: float, **kwargs: Any) -> int:
        """Create line."""
        self._item_counter += 1
        self._items[self._item_counter] = {"type": "line", "coords": coords, **kwargs}
        return self._item_counter

    def create_text(self, x: float, y: float, **kwargs: Any) -> int:
        """Create text."""
        self._item_counter += 1
        self._items[self._item_counter] = {
            "type": "text",
            "coords": (x, y),
            **kwargs,
        }
        return self._item_counter

    def create_image(self, x: float, y: float, **kwargs: Any) -> int:
        """Create image."""
        self._item_counter += 1
        self._items[self._item_counter] = {
            "type": "image",
            "coords": (x, y),
            **kwargs,
        }
        return self._item_counter

    def coords(self, item: int, *coords: float) -> tuple[float, ...]:
        """Get/set coordinates."""
        if coords:
            if item in self._items:
                self._items[item]["coords"] = coords
            return ()
        return self._items.get(item, {}).get("coords", ())

    def itemconfigure(self, item: int, **kwargs: Any) -> None:
        """Configure item."""
        if item in self._items:
            self._items[item].update(kwargs)

    itemconfig = itemconfigure

    def delete(self, *items: Any) -> None:
        """Delete items."""
        for item in items:
            if item == "all":
                self._items.clear()
            elif item in self._items:
                del self._items[item]

    def move(self, item: int, dx: float, dy: float) -> None:
        """Move item."""
        if item in self._items:
            coords = list(self._items[item].get("coords", ()))
            if len(coords) >= 2:
                coords[0] += dx
                coords[1] += dy
                if len(coords) >= 4:
                    coords[2] += dx
                    coords[3] += dy
                self._items[item]["coords"] = tuple(coords)

    def tag_bind(self, tag: Any, event: str, func: Any, add: str = "") -> str:
        """Bind tag event."""
        return self.bind(f"{tag}_{event}", func, add)

    def find_all(self) -> tuple[int, ...]:
        """Find all items."""
        return tuple(self._items.keys())

    def find_withtag(self, tag: Any) -> tuple[int, ...]:
        """Find items with tag."""
        return tuple(k for k, v in self._items.items() if v.get("tags") == tag or tag == "all")

    def bbox(self, *items: Any) -> tuple[int, int, int, int] | None:
        """Get bounding box."""
        if not items:
            return None
        return (0, 0, 100, 100)

    def create_arc(self, x1: float, y1: float, x2: float, y2: float, **kwargs: Any) -> int:
        """Create arc."""
        self._item_counter += 1
        self._items[self._item_counter] = {
            "type": "arc",
            "coords": (x1, y1, x2, y2),
            **kwargs,
        }
        return self._item_counter


class MockLabel(MockTkWidget):
    """Mock Label widget."""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.master = master
        self._config.setdefault("text", "")
        self._config.setdefault("bg", "#ffffff")
        if master and hasattr(master, "_children"):
            master._children.append(self)


class MockButton(MockTkWidget):
    """Mock Button widget."""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.master = master
        self._config.setdefault("text", "")
        self._config.setdefault("command", None)
        if master and hasattr(master, "_children"):
            master._children.append(self)

    def invoke(self) -> Any:
        """Invoke button command."""
        cmd = self._config.get("command")
        if callable(cmd):
            return cmd()
        return None


class MockEntry(MockTkWidget):
    """Mock Entry widget."""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.master = master
        self._text = ""
        if master and hasattr(master, "_children"):
            master._children.append(self)

    def get(self) -> str:
        """Get entry text."""
        return self._text

    def insert(self, index: Any, text: str) -> None:
        """Insert text."""
        if index == 0 or index == "0":
            self._text = text + self._text
        else:
            self._text += text

    def delete(self, start: Any, end: Any = None) -> None:
        """Delete text."""
        self._text = ""

    def icursor(self, index: Any) -> None:
        """Set cursor position."""
        pass

    def selection_range(self, start: Any, end: Any) -> None:
        """Select range."""
        pass


class MockListbox(MockTkWidget):
    """Mock Listbox widget."""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.master = master
        self._items: list[str] = []
        self._selection: list[int] = []
        if master and hasattr(master, "_children"):
            master._children.append(self)

    def insert(self, index: Any, *items: str) -> None:
        """Insert items."""
        if index == "end":
            self._items.extend(items)
        else:
            idx = int(index) if isinstance(index, str) else index
            for i, item in enumerate(items):
                self._items.insert(idx + i, item)

    def delete(self, start: Any, end: Any = None) -> None:
        """Delete items."""
        if start == 0 and end == "end":
            self._items.clear()
        elif end is None:
            idx = int(start) if isinstance(start, str) else start
            if 0 <= idx < len(self._items):
                del self._items[idx]
        else:
            start_idx = int(start) if isinstance(start, str) else start
            end_idx = len(self._items) if end == "end" else int(end) + 1
            del self._items[start_idx:end_idx]

    def get(self, start: Any, end: Any = None) -> str | tuple[str, ...]:
        """Get items."""
        if end is None:
            idx = int(start) if isinstance(start, str) else start
            return self._items[idx] if 0 <= idx < len(self._items) else ""
        start_idx = int(start) if isinstance(start, str) else start
        end_idx = len(self._items) if end == "end" else int(end) + 1
        return tuple(self._items[start_idx:end_idx])

    def curselection(self) -> tuple[int, ...]:
        """Get selection."""
        return tuple(self._selection)

    def selection_set(self, start: Any, end: Any = None) -> None:
        """Set selection."""
        idx = int(start) if isinstance(start, str) else start
        if idx not in self._selection:
            self._selection.append(idx)

    def selection_clear(self, start: Any, end: Any = None) -> None:
        """Clear selection."""
        if start == 0 and end == "end":
            self._selection.clear()
        else:
            idx = int(start) if isinstance(start, str) else start
            if idx in self._selection:
                self._selection.remove(idx)

    def size(self) -> int:
        """Get size."""
        return len(self._items)

    def see(self, index: Any) -> None:
        """Scroll to item."""
        pass


class MockScrollbar(MockTkWidget):
    """Mock Scrollbar widget."""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.master = master
        self._command = kwargs.get("command")
        if master and hasattr(master, "_children"):
            master._children.append(self)

    def set(self, first: float, last: float) -> None:
        """Set scrollbar position."""
        self._config["first"] = first
        self._config["last"] = last


class MockText(MockTkWidget):
    """Mock Text widget."""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.master = master
        self._content = ""
        if master and hasattr(master, "_children"):
            master._children.append(self)

    def get(self, start: str, end: str = "end") -> str:
        """Get text content."""
        return self._content

    def insert(self, index: str, text: str, *tags: str) -> None:
        """Insert text."""
        self._content += text

    def delete(self, start: str, end: str = "end") -> None:
        """Delete text."""
        self._content = ""

    def see(self, index: str) -> None:
        """Scroll to index."""
        pass

    def tag_add(self, tag: str, start: str, end: str = "") -> None:
        """Add tag."""
        pass

    def tag_config(self, tag: str, **kwargs: Any) -> None:
        """Configure tag."""
        pass

    def tag_remove(self, tag: str, start: str, end: str = "") -> None:
        """Remove tag."""
        pass


class MockMenu(MockTkWidget):
    """Mock Menu widget."""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.master = master
        self._entries: list[dict[str, Any]] = []
        if master and hasattr(master, "_children"):
            master._children.append(self)

    def add_command(self, **kwargs: Any) -> None:
        """Add command entry."""
        self._entries.append({"type": "command", **kwargs})

    def add_separator(self) -> None:
        """Add separator."""
        self._entries.append({"type": "separator"})

    def add_cascade(self, **kwargs: Any) -> None:
        """Add cascade menu."""
        self._entries.append({"type": "cascade", **kwargs})

    def add_checkbutton(self, **kwargs: Any) -> None:
        """Add checkbutton."""
        self._entries.append({"type": "checkbutton", **kwargs})

    def add_radiobutton(self, **kwargs: Any) -> None:
        """Add radiobutton."""
        self._entries.append({"type": "radiobutton", **kwargs})

    def delete(self, start: Any, end: Any = None) -> None:
        """Delete entries."""
        self._entries.clear()

    def entryconfigure(self, index: Any, **kwargs: Any) -> None:
        """Configure entry."""
        pass

    def post(self, x: int, y: int) -> None:
        """Show menu."""
        pass

    def unpost(self) -> None:
        """Hide menu."""
        pass


class MockToplevel(MockTk):
    """Mock Toplevel window."""

    def __init__(self, master: Any = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.master = master
        if master and hasattr(master, "_children"):
            master._children.append(self)

    def transient(self, master: Any = None) -> None:
        """Set transient."""
        pass

    def grab_set(self) -> None:
        """Grab focus."""
        pass

    def grab_release(self) -> None:
        """Release grab."""
        pass

    def wait_window(self) -> None:
        """Wait for window to close."""
        pass


class MockPhotoImage:
    """Mock PhotoImage."""

    def __init__(self, **kwargs: Any) -> None:
        self._config = kwargs
        self._width = kwargs.get("width", 100)
        self._height = kwargs.get("height", 100)

    def width(self) -> int:
        """Get width."""
        return self._width

    def height(self) -> int:
        """Get height."""
        return self._height

    def blank(self) -> None:
        """Clear image."""
        pass

    def put(self, data: Any, to: tuple[int, int] = (0, 0)) -> None:
        """Put pixel data."""
        pass

    def get(self, x: int, y: int) -> tuple[int, int, int]:
        """Get pixel."""
        return (0, 0, 0)

    def subsample(self, x: int, y: int = 1) -> "MockPhotoImage":
        """Subsample image."""
        return MockPhotoImage(width=self._width // x, height=self._height // y)

    def zoom(self, x: int, y: int = 1) -> "MockPhotoImage":
        """Zoom image."""
        return MockPhotoImage(width=self._width * x, height=self._height * y)


class MockStringVar:
    """Mock StringVar."""

    def __init__(self, master: Any = None, value: str = "", name: str = "") -> None:
        self._value = value

    def get(self) -> str:
        """Get value."""
        return self._value

    def set(self, value: str) -> None:
        """Set value."""
        self._value = value

    def trace_add(self, mode: str, callback: Any) -> str:
        """Add trace."""
        return f"trace_{id(callback)}"

    def trace_remove(self, mode: str, cbname: str) -> None:
        """Remove trace."""
        pass


class MockIntVar:
    """Mock IntVar."""

    def __init__(self, master: Any = None, value: int = 0, name: str = "") -> None:
        self._value = value

    def get(self) -> int:
        """Get value."""
        return self._value

    def set(self, value: int) -> None:
        """Set value."""
        self._value = value


class MockBooleanVar:
    """Mock BooleanVar."""

    def __init__(self, master: Any = None, value: bool = False, name: str = "") -> None:
        self._value = value

    def get(self) -> bool:
        """Get value."""
        return self._value

    def set(self, value: bool) -> None:
        """Set value."""
        self._value = value


class MockDoubleVar:
    """Mock DoubleVar."""

    def __init__(self, master: Any = None, value: float = 0.0, name: str = "") -> None:
        self._value = value

    def get(self) -> float:
        """Get value."""
        return self._value

    def set(self, value: float) -> None:
        """Set value."""
        self._value = value


class MockFont:
    """Mock tkinter.font.Font."""

    def __init__(self, **kwargs: Any) -> None:
        self._config = kwargs
        self.family = kwargs.get("family", "TkDefaultFont")
        self.size = kwargs.get("size", 10)
        self.weight = kwargs.get("weight", "normal")
        self.slant = kwargs.get("slant", "roman")

    def actual(self, option: str = None) -> Any:
        """Get actual font properties."""
        props = {
            "family": self.family,
            "size": self.size,
            "weight": self.weight,
            "slant": self.slant,
        }
        if option:
            return props.get(option)
        return props

    def configure(self, **kwargs: Any) -> None:
        """Configure font."""
        self._config.update(kwargs)
        if "family" in kwargs:
            self.family = kwargs["family"]
        if "size" in kwargs:
            self.size = kwargs["size"]

    def measure(self, text: str) -> int:
        """Measure text width."""
        return len(text) * self.size

    def metrics(self, option: str = None) -> Any:
        """Get font metrics."""
        metrics = {"ascent": self.size, "descent": 3, "linespace": self.size + 3}
        if option:
            return metrics.get(option, 0)
        return metrics


class MockTkModule:
    """Mock tkinter module."""

    Tk = MockTk
    Frame = MockFrame
    Canvas = MockCanvas
    Label = MockLabel
    Button = MockButton
    Entry = MockEntry
    Listbox = MockListbox
    Scrollbar = MockScrollbar
    Text = MockText
    Menu = MockMenu
    Toplevel = MockToplevel
    PhotoImage = MockPhotoImage
    StringVar = MockStringVar
    IntVar = MockIntVar
    BooleanVar = MockBooleanVar
    DoubleVar = MockDoubleVar

    # Constants
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    CENTER = "center"
    BOTH = "both"
    X = "x"
    Y = "y"
    NONE = "none"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    RAISED = "raised"
    SUNKEN = "sunken"
    FLAT = "flat"
    GROOVE = "groove"
    RIDGE = "ridge"
    SOLID = "solid"
    DISABLED = "disabled"
    NORMAL = "normal"
    ACTIVE = "active"
    HIDDEN = "hidden"
    CASCADE = "cascade"
    CHECKBUTTON = "checkbutton"
    COMMAND = "command"
    RADIOBUTTON = "radiobutton"
    SEPARATOR = "separator"
    END = "end"
    INSERT = "insert"
    CURRENT = "current"
    ANCHOR = "anchor"
    ALL = "all"
    BROWSE = "browse"
    SINGLE = "single"
    MULTIPLE = "multiple"
    EXTENDED = "extended"
    NW = "nw"
    N = "n"
    NE = "ne"
    W = "w"
    E = "e"
    SW = "sw"
    S = "s"
    SE = "se"
    NS = "ns"
    EW = "ew"
    NSEW = "nsew"
    WORD = "word"
    CHAR = "char"
    UNITS = "units"
    PAGES = "pages"

    class font:
        """Mock tkinter.font submodule."""

        Font = MockFont

        @staticmethod
        def families() -> tuple[str, ...]:
            """Get available font families."""
            return ("TkDefaultFont", "Courier", "Helvetica", "Times")

        @staticmethod
        def nametofont(name: str) -> MockFont:
            """Get named font."""
            return MockFont(family=name)


class MockTtkModule:
    """Mock ttk module."""

    Frame = MockFrame
    Label = MockLabel
    Button = MockButton
    Entry = MockEntry
    Scrollbar = MockScrollbar
    Progressbar = MockTkWidget
    Notebook = MockTkWidget
    Treeview = MockTkWidget
    Combobox = MockEntry
    Scale = MockTkWidget
    Separator = MockTkWidget
    Sizegrip = MockTkWidget
    Style = MagicMock


@pytest.fixture
def mock_tk_root() -> MockTk:
    """Create mock Tk root window.

    Returns:
        Mock Tk root window
    """
    return MockTk()


@pytest.fixture
def mock_tk_frame(mock_tk_root: MockTk) -> MockFrame:
    """Create mock Frame widget.

    Args:
        mock_tk_root: Mock Tk root window

    Returns:
        Mock Frame widget
    """
    return MockFrame(mock_tk_root)


@pytest.fixture
def mock_tk_canvas(mock_tk_root: MockTk) -> MockCanvas:
    """Create mock Canvas widget.

    Args:
        mock_tk_root: Mock Tk root window

    Returns:
        Mock Canvas widget
    """
    return MockCanvas(mock_tk_root)


@pytest.fixture(autouse=True)
def mock_tkinter() -> MagicMock:
    """Automatically mock tkinter for all UI tests.

    This fixture patches tkinter and ttk modules with mock implementations
    that don't require a display.

    Returns:
        Mock tkinter module
    """
    mock_tk = MockTkModule()
    mock_ttk = MockTtkModule()

    with (
        patch.dict(sys.modules, {"tkinter": mock_tk, "tkinter.ttk": mock_ttk}),
        patch("tkinter.Tk", MockTk),
        patch("tkinter.Frame", MockFrame),
        patch("tkinter.Canvas", MockCanvas),
        patch("tkinter.Label", MockLabel),
        patch("tkinter.Button", MockButton),
        patch("tkinter.Entry", MockEntry),
        patch("tkinter.Listbox", MockListbox),
        patch("tkinter.Text", MockText),
        patch("tkinter.Menu", MockMenu),
        patch("tkinter.Toplevel", MockToplevel),
        patch("tkinter.PhotoImage", MockPhotoImage),
        patch("tkinter.StringVar", MockStringVar),
        patch("tkinter.IntVar", MockIntVar),
        patch("tkinter.BooleanVar", MockBooleanVar),
        patch("tkinter.DoubleVar", MockDoubleVar),
        patch("tkinter.font.Font", MockFont),
    ):
        yield mock_tk
