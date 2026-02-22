from kon.ui.input import InputBox


class _FakeTextArea:
    def __init__(self, text: str) -> None:
        self.text = text
        self.cleared = False

    def clear(self) -> None:
        self.text = ""
        self.cleared = True


class _TestableInputBox(InputBox):
    def __init__(self, text: str = "") -> None:
        super().__init__(cwd="/tmp")
        self._fake_textarea = _FakeTextArea(text)
        self.posted_messages: list[InputBox.Submitted] = []

    def query_one(self, *args, **kwargs):  # type: ignore[override]
        return self._fake_textarea

    def post_message(self, message: InputBox.Submitted):  # type: ignore[override]
        self.posted_messages.append(message)


def test_large_multiline_paste_collapses_and_expands() -> None:
    input_box = InputBox(cwd="/tmp")
    pasted = "\n".join(f"line {i}" for i in range(6))

    marker = input_box._transform_paste(pasted)

    assert marker == "[paste #1 +6 lines]"
    assert input_box._expand_paste_markers(marker) == pasted


def test_large_char_paste_collapses_and_expands() -> None:
    input_box = InputBox(cwd="/tmp")
    pasted = "x" * 501

    marker = input_box._transform_paste(pasted)

    assert marker == "[paste #1 501 chars]"
    assert input_box._expand_paste_markers(marker) == pasted


def test_threshold_boundaries_not_collapsed() -> None:
    input_box = InputBox(cwd="/tmp")

    five_lines = "\n".join(f"line {i}" for i in range(5))
    five_hundred_chars = "x" * 500

    assert input_box._transform_paste(five_lines) == five_lines
    assert input_box._transform_paste(five_hundred_chars) == five_hundred_chars


def test_submit_keeps_display_text_but_expands_query_text() -> None:
    pasted = "\n".join(f"line {i}" for i in range(6))
    display = "prefix [paste #1 +6 lines] suffix"
    input_box = _TestableInputBox(display)
    input_box._pastes[1] = pasted
    input_box._paste_counter = 1

    input_box._do_submit()

    assert len(input_box.posted_messages) == 1
    message = input_box.posted_messages[0]
    assert message.text == display
    assert message.query_text == f"prefix {pasted} suffix"
    assert input_box._fake_textarea.cleared is True
    assert input_box._pastes == {}
    assert input_box._paste_counter == 0
    assert input_box._history[-1] == f"prefix {pasted} suffix"
