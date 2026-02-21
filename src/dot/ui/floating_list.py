"""
Floating list overlay for inline completion.

A reusable overlay component that renders below the input, showing
a paginated list with arrow indicator and counter. Used for:
- Slash commands (/)
- File path search (@)
- Session selection
- Any other searchable list
"""

from dataclasses import dataclass
from typing import TypeVar

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

from dot import config

T = TypeVar("T")


@dataclass
class ListItem[T]:
    value: T
    label: str
    description: str = ""

    def __hash__(self) -> int:
        return hash((self.label, self.description))


class FloatingList[T](Widget):
    """
    A floating overlay list with pagination and selection.

    Features:
    - Arrow indicator (→) for selected item
    - Position counter (x/total)
    - Window-based pagination (shows subset of items)
    - Keyboard navigation (up/down)
    - Hidden by default, show/hide controlled by parent

    The parent widget is responsible for:
    - Calling show(items) with filtered items
    - Calling hide() to dismiss
    - Calling move_up()/move_down() on key events
    - Reading selected_item when user confirms
    """

    DEFAULT_CSS = """
    FloatingList {
        height: auto;
        background: $surface;
        display: none;
        padding: 0 1;
    }

    FloatingList.-visible {
        display: block;
    }
    """

    # Reactive to trigger re-render
    _selected_index: reactive[int] = reactive(0, repaint=False)
    _visible: reactive[bool] = reactive(False, repaint=False)
    _render_key: reactive[int] = reactive(0)  # Force re-render

    def __init__(
        self,
        window_size: int = 5,
        label_width: int = 12,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._window_size = window_size
        self._min_label_width = label_width
        self._label_width = label_width
        self._items: list[ListItem[T]] = []

    @property
    def items(self) -> list[ListItem[T]]:
        return self._items

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @property
    def selected_item(self) -> ListItem[T] | None:
        if self._items and 0 <= self._selected_index < len(self._items):
            return self._items[self._selected_index]
        return None

    @property
    def is_visible(self) -> bool:
        return self._visible

    def _compute_label_width(self) -> int:
        if not self._items:
            return self._min_label_width
        max_len = max(len(item.label) for item in self._items)
        return max(self._min_label_width, min(max_len, 30))  # Cap at 30

    def show(self, items: list[ListItem[T]]) -> None:
        self._items = items
        self._selected_index = 0
        self._label_width = self._compute_label_width()
        self._visible = True
        self.add_class("-visible")
        self._render_key += 1
        # Force layout refresh to prevent visual artifacts in adjacent widgets
        if self.screen:
            self.screen.refresh(layout=True)

    def hide(self) -> None:
        self._visible = False
        self._items = []
        self._selected_index = 0
        self.remove_class("-visible")
        # Force layout refresh to prevent visual artifacts in adjacent widgets
        if self.screen:
            self.screen.refresh(layout=True)

    def update_items(self, items: list[ListItem[T]]) -> None:
        self._items = items
        self._label_width = self._compute_label_width()
        # Clamp selected index
        if self._selected_index >= len(items):
            self._selected_index = max(0, len(items) - 1)
        self._render_key += 1

    def move_up(self) -> None:
        if not self._items:
            return

        if self._selected_index > 0:
            self._selected_index -= 1
        else:
            self._selected_index = len(self._items) - 1
        self._render_key += 1

    def move_down(self) -> None:
        if not self._items:
            return

        if self._selected_index < len(self._items) - 1:
            self._selected_index += 1
        else:
            self._selected_index = 0
        self._render_key += 1

    def render(self) -> Text:
        _ = self._render_key  # Subscribe to changes

        if not self._items or not self._visible:
            return Text("")

        total = len(self._items)
        selected = self._selected_index

        # Calculate window
        half_window = self._window_size // 2
        start = max(0, selected - half_window)
        end = min(total, start + self._window_size)

        # Adjust start if we're near the end
        if end - start < self._window_size and start > 0:
            start = max(0, end - self._window_size)

        lines = []

        # Render visible items
        for i in range(start, end):
            item = self._items[i]
            is_selected = i == selected
            lines.append(self._render_row(item, is_selected))

        # Add counter row
        dim_color = config.ui.colors.dim
        counter = Text(f"  ({selected + 1}/{total})", style=dim_color)
        lines.append(counter)

        # Join with newlines
        result = Text()
        for i, line in enumerate(lines):
            if i > 0:
                result.append("\n")
            result.append_text(line)

        return result

    def _render_row(self, item: ListItem[T], is_selected: bool) -> Text:
        selected_color = config.ui.colors.selected
        dim_color = config.ui.colors.dim
        text = Text()

        # Arrow indicator
        if is_selected:
            text.append("→ ", style=f"bold {selected_color}")
        else:
            text.append("  ")

        # Label (padded to computed width for alignment)
        label = item.label.ljust(self._label_width)
        if is_selected:
            text.append(label, style=selected_color)
        else:
            text.append(label)

        # Description (if any)
        if item.description:
            text.append(" ")
            text.append(item.description, style=dim_color)

        return text

    def watch__visible(self, visible: bool) -> None:
        if visible:
            self.add_class("-visible")
        else:
            self.remove_class("-visible")
