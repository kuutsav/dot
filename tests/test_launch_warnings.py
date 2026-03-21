from kon.ui.app import Kon
from kon.ui.blocks import LaunchWarning


class _StubInputBox:
    def set_fd_path(self, path):
        self.path = path

    def set_commands(self, commands):
        self.commands = commands

    def focus(self) -> None:
        pass


def _make_app() -> Kon:
    return Kon(cwd=".")


def test_flush_launch_warnings_sends_to_chat(fake_chat) -> None:
    app = _make_app()

    app._add_launch_warning("Config fell back to defaults")
    app._add_launch_warning("Session file is invalid", severity="error")
    app._flush_launch_warnings(fake_chat)

    assert fake_chat.launch_warnings == [
        LaunchWarning(message="Config fell back to defaults", severity="warning"),
        LaunchWarning(message="Session file is invalid", severity="error"),
    ]


def test_on_mount_continue_recent_error_shows_launch_warning(fake_chat, monkeypatch) -> None:
    app = Kon(cwd=".", continue_recent=True)
    input_box = _StubInputBox()

    def _query_one(selector, cls=None):
        if selector == "#input-box":
            return input_box
        if selector == "#chat-log":
            return fake_chat
        raise AssertionError(f"Unexpected selector: {selector}")

    app.query_one = _query_one  # type: ignore[method-assign]

    def _run_worker(coro, **kwargs):
        coro.close()
        return None

    app.run_worker = _run_worker  # type: ignore[method-assign]

    def _fail_continue_recent(
        cwd, provider=None, model_id=None, thinking_level="medium", system_prompt=None
    ):
        raise ValueError("Invalid session file (no header): /tmp/bad.jsonl")

    monkeypatch.setattr("kon.ui.app.Session.continue_recent", _fail_continue_recent)

    app.on_mount()

    assert fake_chat.errors == []
    assert fake_chat.launch_warnings == [
        LaunchWarning(message="Invalid session file (no header): /tmp/bad.jsonl", severity="error")
    ]
