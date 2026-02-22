from rich.style import Style
from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Label, Static

from kon import config

from .formatting import format_markdown


class ThinkingBlock(Static):
    """Uses plain text during streaming for performance, renders markdown on finalize."""

    ALLOW_SELECT = True
    can_focus = False

    def __init__(self, content: str = "", finalized: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self._content = content
        self._finalized = finalized
        self._label: Label | None = None
        self.add_class("thinking-block")

    def compose(self) -> ComposeResult:
        if self._finalized and self._content:
            yield Label(format_markdown(self._content), id="thinking-content", markup=False)
        else:
            yield Label(self._content, id="thinking-content", markup=False)

    @property
    def label(self) -> Label:
        if self._label is None:
            self._label = self.query_one("#thinking-content", Label)
        return self._label

    async def append(self, text: str) -> None:
        self._content += text
        self.label.update(self._content)

    def finalize(self) -> None:
        if self._content and not self._finalized:
            self._finalized = True
            self.call_after_refresh(self._do_finalize)

    def _do_finalize(self) -> None:
        if self._content:
            self.label.update(format_markdown(self._content))

    def set_content(self, text: str) -> None:
        self._content = text
        self._finalized = True
        self.label.update(format_markdown(self._content))


class ContentBlock(Static):
    # TODO: Consider switching to Textual's Markdown widget + MarkdownStream.write() for
    # incremental rendering during streaming. This would eliminate the visual reflow when
    # finalize() converts plain text to markdown. The tradeoff: our custom Rich-based
    # formatting (CustomMarkdown with LeftJustifiedHeading, PlainListItem, PlainCodeBlock)
    # is incompatible with Textual's Markdown pipeline, so we'd need to reimplement those
    # customizations using Textual's theming/CSS system. See toad and mistral-vibe for
    # reference implementations using MarkdownStream.

    ALLOW_SELECT = True
    can_focus = False

    def __init__(self, content: str = "", finalized: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self._content = content
        self._finalized = finalized
        self._label: Label | None = None
        self.add_class("content-block")

    def compose(self) -> ComposeResult:
        # If created with content (loading history), render markdown immediately
        if self._finalized and self._content:
            yield Label(format_markdown(self._content), id="content-text", markup=False)
        else:
            yield Label(self._content, id="content-text", markup=False)

    @property
    def label(self) -> Label:
        if self._label is None:
            self._label = self.query_one("#content-text", Label)
        return self._label

    async def append(self, text: str) -> None:
        self._content += text
        self.label.update(self._content)

    def finalize(self) -> None:
        if self._content and not self._finalized:
            self._finalized = True
            # Use call_after_refresh to batch the update
            self.call_after_refresh(self._do_finalize)

    def _do_finalize(self) -> None:
        if self._content:
            self.label.update(format_markdown(self._content))

    def set_content(self, text: str) -> None:
        self._content = text
        self._finalized = True
        self.label.update(format_markdown(self._content))


class ToolBlock(Static):
    """
    Format:
    TOOL_NAME call_msg
    truncated output
    """

    ALLOW_SELECT = True
    can_focus = False
    MAX_HEADER_LINES = 2

    def __init__(self, name: str = "", call_msg: str | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._name = name
        self._call_msg = call_msg
        self._result: str | None = None
        self._success: bool | None = None
        self.add_class("tool-block")
        self._set_state(None)

    def compose(self) -> ComposeResult:
        yield Label(self._format_header(), id="tool-header")
        yield Label(self._format_pending_output(), id="tool-output")

    def _format_header(self) -> Text:
        result = Text()
        formatted_name = " ".join(word.capitalize() for word in self._name.split("_"))
        result.append(formatted_name, style="bold")
        if self._call_msg:
            result.append(" ")
            result.append_text(self._format_call_msg())
        return result

    def _format_call_msg(self) -> Text:
        if not self._call_msg:
            return Text()
        lines = self._call_msg.split("\n")
        if len(lines) > self.MAX_HEADER_LINES:
            display_msg = "\n".join(lines[: self.MAX_HEADER_LINES])
            display_msg += f"\n... ({len(lines) - self.MAX_HEADER_LINES} more lines)"
            return self._render_markup_safe(display_msg)
        return self._render_markup_safe(self._call_msg)

    def _format_pending_output(self) -> Text:
        dim_color = config.ui.colors.dim
        return Text("...", style=dim_color)

    def _render_markup_safe(self, content: str) -> Text:
        try:
            text = Text.from_markup(content)
        except Exception:
            return Text(content)

        for span in text.spans:
            style = span.style
            if isinstance(style, str):
                try:
                    Style.parse(style)
                except Exception:
                    return Text(content)

        return text

    def _set_state(self, success: bool | None) -> None:
        self.remove_class("-pending", "-success", "-error")
        if success is None:
            self.add_class("-pending")
        elif success:
            self.add_class("-success")
        else:
            self.add_class("-error")

    def update_call_msg(self, call_msg: str) -> None:
        self._call_msg = call_msg
        self.query_one("#tool-header", Label).update(self._format_header())

    def set_result(self, content: str, success: bool, markup: bool = True) -> None:
        self._result = content
        self._success = success
        self._set_state(success)

        # Parse Rich markup for colored output (tools control their own truncation/styling)
        rendered = self._render_markup_safe(content) if markup else Text(content)
        self.query_one("#tool-output", Label).update(rendered)
        self.query_one("#tool-header", Label).update(self._format_header())


class UserBlock(Static):
    ALLOW_SELECT = True
    can_focus = False

    def __init__(self, content: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._content = content
        self.add_class("user-block")

    def compose(self) -> ComposeResult:
        text = Text()
        text.append("> ", style="bold")
        text.append(self._content)
        yield Label(text)
