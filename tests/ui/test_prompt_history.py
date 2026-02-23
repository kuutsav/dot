from __future__ import annotations

import json

import pytest

from kon.ui import prompt_history as ph
from kon.ui.prompt_history import MAX_HISTORY_ENTRIES, PromptHistory


@pytest.fixture(autouse=True)
def _isolate_history(tmp_path, monkeypatch):
    history_file = tmp_path / "prompt-history.jsonl"
    monkeypatch.setattr(ph, "_history_path", lambda: history_file)
    return history_file


def test_append_and_navigate():
    h = PromptHistory()
    h.append("hello")
    h.append("world")

    assert h.navigate(-1, "") == "world"
    assert h.navigate(-1, "world") == "hello"
    assert h.navigate(1, "hello") == "world"
    assert h.navigate(1, "world") == ""


def test_navigate_empty():
    h = PromptHistory()
    assert h.navigate(-1, "") is None


def test_navigate_preserves_draft():
    h = PromptHistory()
    h.append("old")

    result = h.navigate(-1, "my draft")
    assert result == "old"
    result = h.navigate(1, "old")
    assert result == "my draft"


def test_navigate_bounds():
    h = PromptHistory()
    h.append("only")

    assert h.navigate(-1, "") == "only"
    assert h.navigate(-1, "only") is None
    h._reset_index()
    assert h.navigate(1, "") is None


def test_dedup_consecutive():
    h = PromptHistory()
    h.append("same")
    h.append("same")
    assert len(h._entries) == 1


def test_persistence(tmp_path):
    h1 = PromptHistory()
    h1.append("first")
    h1.append("second")

    h2 = PromptHistory()
    assert h2._entries == ["first", "second"]


def test_max_entries_trim(tmp_path):
    h = PromptHistory()
    for i in range(MAX_HISTORY_ENTRIES + 10):
        h.append(f"entry-{i}")

    assert len(h._entries) == MAX_HISTORY_ENTRIES
    assert h._entries[0] == "entry-10"
    assert h._entries[-1] == f"entry-{MAX_HISTORY_ENTRIES + 9}"

    h2 = PromptHistory()
    assert len(h2._entries) == MAX_HISTORY_ENTRIES


def test_corrupt_lines_ignored(tmp_path):
    path = ph._history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps("good")
        + "\n"
        + "not valid json\n"
        + json.dumps(42)
        + "\n"
        + json.dumps("also good")
        + "\n",
        encoding="utf-8",
    )

    h = PromptHistory()
    assert h._entries == ["good", "also good"]
