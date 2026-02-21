import asyncio
from pathlib import Path

import aiofiles
from pydantic import BaseModel, Field

from dot import config

from ..shared import shorten_path
from .base import BaseTool, ToolResult


class WriteParams(BaseModel):
    path: str = Field(description="Absolute path of the file to write to")
    content: str = Field(description="Content to be written to the file")


class WriteTool(BaseTool):
    name = "write"
    params = WriteParams
    description = (
        "Write content to a file. Creates the file if it doesn't exist, overwrites if it does. "
        "Automatically creates parent directories."
    )

    def format_call(self, params: WriteParams) -> str:
        accent = config.ui.colors.accent
        return f"[{accent}]{shorten_path(params.path)}[/{accent}]"

    async def execute(
        self, params: WriteParams, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:
        file_path = Path(params.path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_existed = file_path.exists()

        try:
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(params.content)
        except OSError as e:
            return ToolResult(success=False, display=f"[red]Failed to write: {e}[/red]")

        n_lines = params.content.count("\n") + 1
        short_path = shorten_path(str(file_path))
        diff_added = config.ui.colors.diff_added

        if file_existed:
            result = f"Overwrote {file_path} +{n_lines}"
            display = f"[dim]Overwrote {short_path}[/dim] [{diff_added}]+{n_lines}[/{diff_added}]"
        else:
            result = f"Created {file_path} +{n_lines}"
            display = f"[dim]Created {short_path}[/dim] [{diff_added}]+{n_lines}[/{diff_added}]"

        return ToolResult(success=True, result=result, display=display)
