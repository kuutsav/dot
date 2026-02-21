from __future__ import annotations

from ...core.types import ImageContent, Message, ToolResultMessage, UserMessage


def infer_copilot_initiator(messages: list[Message]) -> str:
    """
    Copilot expects X-Initiator to indicate whether the request is user-initiated
    or agent-initiated (e.g. follow-up after assistant/tool messages).
    """
    if not messages:
        return "user"
    last = messages[-1]
    return "user" if isinstance(last, UserMessage) else "agent"


def has_copilot_vision_input(messages: list[Message]) -> bool:
    """Copilot requires Copilot-Vision-Request header when sending images."""
    for msg in messages:
        if (
            isinstance(msg, UserMessage)
            and not isinstance(msg.content, str)
            and any(isinstance(c, ImageContent) for c in msg.content)
        ):
            return True
        if isinstance(msg, ToolResultMessage) and any(
            isinstance(c, ImageContent) for c in msg.content
        ):
            return True
    return False


def build_copilot_dynamic_headers(messages: list[Message]) -> dict[str, str]:
    headers: dict[str, str] = {
        "X-Initiator": infer_copilot_initiator(messages),
        "Openai-Intent": "conversation-edits",
    }

    if has_copilot_vision_input(messages):
        headers["Copilot-Vision-Request"] = "true"

    return headers
