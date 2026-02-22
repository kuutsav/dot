import pytest

from kon.tools.write import WriteParams, WriteTool


@pytest.fixture
def write_tool():
    return WriteTool()


@pytest.fixture
def text_file(tmp_path):
    f = tmp_path / "index.py"
    return f


@pytest.mark.asyncio
async def test_write(write_tool, text_file):
    tool_result = await write_tool.execute(
        WriteParams(path=str(text_file), content="line1\nline2\nline3")
    )
    assert tool_result.success
    assert "Created" in tool_result.result
    assert "+3" in tool_result.result

    tool_result = await write_tool.execute(
        WriteParams(path=str(text_file), content="line1\nline2\nline3\nline4")
    )
    assert tool_result.success
    assert "Overwrote" in tool_result.result
    assert "+4" in tool_result.result
