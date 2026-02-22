#!/usr/bin/env python3

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kon.core.types import StreamDone, StreamError, TextPart, ThinkPart, UserMessage
from kon.llm import ProviderConfig, resolve_provider_api_type
from kon.llm.providers import OpenAIResponsesProvider


@dataclass
class ProbeResult:
    ok: bool
    error: str | None
    text_chunks: int
    thinking_chunks: int
    text_chars: int
    thinking_chars: int
    thinking_signatures: set[str]
    stop_reason: str | None
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int


async def _run_probe(
    *,
    provider_name: str,
    model: str,
    base_url: str,
    api_key: str | None,
    thinking_level: str,
    prompt: str,
    max_tokens: int,
) -> ProbeResult:
    api_type = resolve_provider_api_type(provider_name)

    config = ProviderConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        max_tokens=max_tokens,
        thinking_level=thinking_level,
    )

    if api_type.value == "openai-responses":
        provider = OpenAIResponsesProvider(config)
    else:
        from kon.llm import API_TYPE_TO_PROVIDER_CLASS

        provider_cls = API_TYPE_TO_PROVIDER_CLASS[api_type]
        provider = provider_cls(config)

    text_chunks = 0
    thinking_chunks = 0
    text_chars = 0
    thinking_chars = 0
    thinking_signatures: set[str] = set()
    stop_reason: str | None = None
    error: str | None = None

    stream = await provider.stream([UserMessage(content=prompt)])

    async for event in stream:
        if isinstance(event, TextPart):
            text_chunks += 1
            text_chars += len(event.text)
        elif isinstance(event, ThinkPart):
            thinking_chunks += 1
            thinking_chars += len(event.think)
            if event.signature:
                thinking_signatures.add(event.signature)
        elif isinstance(event, StreamDone):
            stop_reason = event.stop_reason.value
        elif isinstance(event, StreamError):
            error = event.error

    usage = stream.usage
    input_tokens = usage.input_tokens if usage else 0
    output_tokens = usage.output_tokens if usage else 0
    cache_read_tokens = usage.cache_read_tokens if usage else 0

    ok = error is None and text_chunks > 0

    return ProbeResult(
        ok=ok,
        error=error,
        text_chunks=text_chunks,
        thinking_chunks=thinking_chunks,
        text_chars=text_chars,
        thinking_chars=thinking_chars,
        thinking_signatures=thinking_signatures,
        stop_reason=stop_reason,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
    )


async def main() -> int:
    parser = argparse.ArgumentParser(description="Probe whether thinking blocks are streamed")
    parser.add_argument("--provider", default="openai", help="Provider name (e.g. openai)")
    parser.add_argument("--model", required=True, help="Model ID")
    parser.add_argument("--base-url", required=True, help="Base URL")
    parser.add_argument(
        "--api-key", help="API key (falls back to OPENAI_API_KEY then ZAI_API_KEY)"
    )
    parser.add_argument("--thinking-level", default="high", help="Thinking level")
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument(
        "--prompt",
        default=(
            "Solve this briefly: If a train leaves at 3:00 PM and travels 60 mph for 2.5 hours, "
            "what distance does it cover?"
        ),
    )
    parser.add_argument(
        "--require-thinking",
        action="store_true",
        help="Exit non-zero if no thinking chunks are observed",
    )
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("ZAI_API_KEY")

    print("Thinking probe")
    print(f"  provider:       {args.provider}")
    print(f"  model:          {args.model}")
    print(f"  base_url:       {args.base_url}")
    print(f"  thinking_level: {args.thinking_level}")

    resolved_api = resolve_provider_api_type(args.provider)
    if resolved_api.value == "openai-responses":
        provider_class_name = OpenAIResponsesProvider.__name__
    else:
        from kon.llm import API_TYPE_TO_PROVIDER_CLASS

        provider_class_name = API_TYPE_TO_PROVIDER_CLASS[resolved_api].__name__
    print(f"  api_type:       {resolved_api.value}")
    print(f"  provider_class: {provider_class_name}")

    try:
        result = await _run_probe(
            provider_name=args.provider,
            model=args.model,
            base_url=args.base_url,
            api_key=api_key,
            thinking_level=args.thinking_level,
            prompt=args.prompt,
            max_tokens=args.max_tokens,
        )
    except Exception as e:
        print(f"\nERROR: {e}")
        return 2

    print("\nResult")
    print(f"  ok:                 {result.ok}")
    print(f"  stop_reason:        {result.stop_reason}")
    print(f"  text_chunks:        {result.text_chunks}")
    print(f"  thinking_chunks:    {result.thinking_chunks}")
    print(f"  text_chars:         {result.text_chars}")
    print(f"  thinking_chars:     {result.thinking_chars}")
    signatures = sorted(result.thinking_signatures) if result.thinking_signatures else []
    print(f"  thinking_signatures:{signatures}")
    print(
        "  usage:              "
        f"{result.input_tokens} in / {result.output_tokens} out / "
        f"{result.cache_read_tokens} cached"
    )

    if result.error:
        print(f"\nStream error: {result.error}")
        return 2

    if args.require_thinking and result.thinking_chunks == 0:
        print("\nNo thinking chunks were observed.")
        return 1

    if result.thinking_chunks == 0:
        print("\nNo thinking chunks observed.")
        print("This usually means the upstream endpoint/model is not streaming reasoning fields.")
        print("(In kon UI, you can also toggle visibility with Ctrl+T.)")
    else:
        print("\nThinking chunks detected ✅")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
