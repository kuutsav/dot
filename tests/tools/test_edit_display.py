from kon import config
from kon.tools.edit import format_diff_display, truncate_diff_line


def test_truncate_diff_line_does_not_truncate_short_line() -> None:
    line = "+2 short line"
    assert truncate_diff_line(line, max_chars=90) == line


def test_truncate_diff_line_truncates_long_line_with_ellipsis() -> None:
    line = "+2 " + "x" * 200
    truncated = truncate_diff_line(line, max_chars=90)
    assert len(truncated) == 90
    assert truncated.endswith("...")


def test_format_diff_display_truncates_and_keeps_color_markup() -> None:
    long_added = "+2 " + "x" * 200
    long_removed = "-2 " + "y" * 200

    display = format_diff_display(f"{long_added}\n{long_removed}")
    lines = display.split("\n")

    added_color = config.ui.colors.diff_added
    removed_color = config.ui.colors.diff_removed

    assert len(lines) == 2
    assert lines[0].startswith(f"[{added_color}]")
    assert lines[0].endswith("...[/" + added_color + "]")
    assert lines[1].startswith(f"[{removed_color}]")
    assert lines[1].endswith("...[/" + removed_color + "]")
