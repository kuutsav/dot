from dot.context import Context
from dot.loop import build_system_prompt


def test_system_prompt_includes_guidelines():
    prompt = build_system_prompt("/tmp", Context("/tmp"))

    assert "Use grep to search file contents" in prompt
    assert "Use find to search for files by name/glob" in prompt
    assert "Use read to view files" in prompt
    assert "Use edit for precise changes" in prompt
    assert "Use write only for new files or complete rewrites" in prompt
    assert "Use bash for terminal operations" in prompt


def test_system_prompt_includes_cwd():
    prompt = build_system_prompt("/test/dir", Context("/test/dir"))
    assert "/test/dir" in prompt
