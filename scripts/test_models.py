#!/usr/bin/env python3
"""
Test all supported models across providers and thinking configurations.

Tests:
- Text response generation
- Thinking/reasoning blocks (when enabled)
- All thinking levels per model

Usage:
    python scripts/test_models.py
    python scripts/test_models.py --model claude-sonnet-4.5
    python scripts/test_models.py --thinking-level medium
    python scripts/test_models.py --provider github-copilot
"""

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kon.core.types import Message, StreamDone, StreamError, TextPart, ThinkPart, UserMessage
from kon.llm import (
    ApiType,
    CopilotAnthropicProvider,
    CopilotProvider,
    CopilotResponsesProvider,
    OpenAICodexResponsesProvider,
    OpenAICompletionsProvider,
    OpenAIResponsesProvider,
    ProviderConfig,
    get_all_models,
    is_copilot_logged_in,
    is_openai_logged_in,
)
from kon.llm.base import BaseProvider
from kon.llm.models import Model


@dataclass
class TestResult:
    model_id: str
    provider: str
    api_type: str
    thinking_level: str
    success: bool
    has_text: bool
    has_thinking: bool
    text_preview: str
    thinking_preview: str
    error: str | None
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int


def _get_provider_for_model(model: Model, thinking_level: str) -> BaseProvider | None:
    config = ProviderConfig(
        api_key="",
        base_url=model.base_url,
        model=model.id,
        max_tokens=4096,
        thinking_level=thinking_level,
    )

    if model.api == ApiType.ANTHROPIC_COPILOT:
        if not is_copilot_logged_in():
            return None
        return CopilotAnthropicProvider(config)

    elif model.api == ApiType.GITHUB_COPILOT_RESPONSES:
        if not is_copilot_logged_in():
            return None
        return CopilotResponsesProvider(config)

    elif model.api == ApiType.OPENAI_RESPONSES:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        config.api_key = api_key
        return OpenAIResponsesProvider(config)

    elif model.api == ApiType.GITHUB_COPILOT:
        if not is_copilot_logged_in():
            return None
        return CopilotProvider(config)

    elif model.api == ApiType.OPENAI_CODEX_RESPONSES:
        if not is_openai_logged_in():
            return None
        return OpenAICodexResponsesProvider(config)

    elif model.api == ApiType.OPENAI_COMPLETIONS:
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ZAI_API_KEY")
        if not api_key:
            return None
        config.api_key = api_key
        return OpenAICompletionsProvider(config)

    return None


async def _test_model(
    model: Model, thinking_level: str, prompt: str = "What is 2 + 2? Answer briefly."
) -> TestResult:
    provider = _get_provider_for_model(model, thinking_level)

    if not provider:
        return TestResult(
            model_id=model.id,
            provider=model.provider,
            api_type=model.api.value,
            thinking_level=thinking_level,
            success=False,
            has_text=False,
            has_thinking=False,
            text_preview="",
            thinking_preview="",
            error="No provider available (missing auth/keys)",
            input_tokens=0,
            output_tokens=0,
            cache_read_tokens=0,
        )

    messages: list[Message] = [UserMessage(content=prompt)]

    text_parts: list[str] = []
    thinking_parts: list[str] = []
    error: str | None = None
    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0

    try:
        stream = await provider.stream(messages)

        async for event in stream:
            if isinstance(event, TextPart):
                text_parts.append(event.text)
            elif isinstance(event, ThinkPart):
                thinking_parts.append(event.think)
            elif isinstance(event, StreamError):
                error = event.error
            elif isinstance(event, StreamDone):
                pass

        if stream.usage:
            input_tokens = stream.usage.input_tokens
            output_tokens = stream.usage.output_tokens
            cache_read_tokens = stream.usage.cache_read_tokens

    except Exception as e:
        error = str(e)

    full_text = "".join(text_parts)
    full_thinking = "".join(thinking_parts)

    text_preview = full_text[:100] + "..." if len(full_text) > 100 else full_text
    think_preview = full_thinking[:100] + "..." if len(full_thinking) > 100 else full_thinking

    return TestResult(
        model_id=model.id,
        provider=model.provider,
        api_type=model.api.value,
        thinking_level=thinking_level,
        success=error is None and len(full_text) > 0,
        has_text=len(full_text) > 0,
        has_thinking=len(full_thinking) > 0,
        text_preview=text_preview,
        thinking_preview=think_preview,
        error=error,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
    )


def _print_result(result: TestResult) -> None:
    status = "✅" if result.success else "❌"
    thinking_status = "🧠" if result.has_thinking else "  "

    line = (
        f"{status} {thinking_status} {result.model_id:20} "
        f"[{result.api_type:18}] thinking={result.thinking_level:8}"
    )
    print(line, end="")

    if result.error:
        print(f"  ERROR: {result.error[:50]}")
    else:
        tokens_info = f"tokens: {result.input_tokens}→{result.output_tokens}"
        if result.cache_read_tokens > 0:
            tokens_info += f" (cache: {result.cache_read_tokens})"
        print(f"  {tokens_info}")

        if result.text_preview:
            preview = result.text_preview.replace("\n", " ")[:60]
            print(f"         Text: {preview}")
        if result.has_thinking:
            preview = result.thinking_preview.replace("\n", " ")[:60]
            print(f"         Think: {preview}")


def _print_auth_status() -> None:
    print("Auth Status:")
    copilot = "✅ logged in" if is_copilot_logged_in() else "❌ not logged in"
    print(f"  GitHub Copilot: {copilot}")
    openai_codex = "✅ logged in" if is_openai_logged_in() else "❌ not logged in"
    print(f"  OpenAI Codex: {openai_codex}")
    openai = "✅ set" if os.environ.get("OPENAI_API_KEY") else "❌ not set"
    print(f"  OPENAI_API_KEY: {openai}")
    zai = "✅ set" if os.environ.get("ZAI_API_KEY") else "❌ not set"
    print(f"  ZAI_API_KEY (fallback): {zai}")
    print()


def _print_summary(results: list[TestResult]) -> None:
    print("=" * 80)
    print("Summary")
    print("=" * 80)

    total = len(results)
    passed = sum(1 for r in results if r.success)
    with_thinking = sum(1 for r in results if r.has_thinking)

    print(f"Total tests: {total}")
    print(f"Passed: {passed} ({100 * passed // total if total else 0}%)")
    print(f"With thinking: {with_thinking}")

    # Group by provider
    providers = {}
    for r in results:
        if r.provider not in providers:
            providers[r.provider] = {"total": 0, "passed": 0}
        providers[r.provider]["total"] += 1
        if r.success:
            providers[r.provider]["passed"] += 1

    print()
    print("By Provider:")
    for provider, stats in sorted(providers.items()):
        pct = 100 * stats["passed"] // stats["total"] if stats["total"] else 0
        print(f"  {provider}: {stats['passed']}/{stats['total']} ({pct}%)")

    # Group by API type
    api_types = {}
    for r in results:
        if r.api_type not in api_types:
            api_types[r.api_type] = {"total": 0, "passed": 0}
        api_types[r.api_type]["total"] += 1
        if r.success:
            api_types[r.api_type]["passed"] += 1

    print()
    print("By API Type:")
    for api_type, stats in sorted(api_types.items()):
        pct = 100 * stats["passed"] // stats["total"] if stats["total"] else 0
        print(f"  {api_type}: {stats['passed']}/{stats['total']} ({pct}%)")

    failed = [r for r in results if not r.success]
    if failed:
        print()
        print("Failed tests:")
        for r in failed:
            print(f"  - {r.model_id} (thinking={r.thinking_level}): {r.error}")


async def main():
    parser = argparse.ArgumentParser(description="Test all supported models")
    parser.add_argument("--model", "-m", help="Test specific model only")
    parser.add_argument("--thinking-level", "-t", help="Test specific thinking level")
    parser.add_argument("--provider", "-p", help="Test specific provider only")
    parser.add_argument("--prompt", default="What is 2 + 2? Answer briefly.", help="Test prompt")
    args = parser.parse_args()

    models = get_all_models()

    if args.model:
        models = [m for m in models if m.id == args.model]
        if not models:
            print(f"Model '{args.model}' not found")
            return

    if args.provider:
        models = [m for m in models if m.provider == args.provider]
        if not models:
            print(f"No models found for provider '{args.provider}'")
            return

    print("=" * 80)
    print("Model Testing")
    print("=" * 80)
    print()

    _print_auth_status()

    print(f"Testing {len(models)} model(s)")
    print(f'Prompt: "{args.prompt}"')
    print()

    results: list[TestResult] = []

    for model in models:
        print(f"--- {model.id} ({model.provider} / {model.api.value}) ---")

        # Get thinking levels for this model
        provider = _get_provider_for_model(model, "none")
        thinking_levels = provider.thinking_levels if provider else ["none"]

        # Filter to specific level if requested
        if args.thinking_level:
            if args.thinking_level in thinking_levels:
                thinking_levels = [args.thinking_level]
            else:
                print(f"  Thinking level '{args.thinking_level}' not supported")
                continue

        for level in thinking_levels:
            result = await _test_model(model, level, args.prompt)
            results.append(result)
            _print_result(result)

        print()

    _print_summary(results)


if __name__ == "__main__":
    asyncio.run(main())
