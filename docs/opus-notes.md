# Code Review Notes

Review of core loop, turn, and supporting layers. To be triaged later.

## Potential Bugs

### 1. Compaction sends full history to LLM when already over context window

**Location:** `loop.py:262`, `core/compaction.py:80`

When compaction triggers, `all_messages` (the full uncompacted history) is sent to the same provider for summarization. But compaction fires *because* we exceeded the context window — so the summarization request sends an even longer payload (all messages + summarization prompt). The LLM will likely reject it with a context length error.

The exception is caught and yields `CompactionEndEvent(aborted=True)`, but there's no retry, truncation, or fallback strategy. This is arguably the most significant issue.

**Possible fix:** Truncate the message history sent to the summarization call (e.g., keep first N and last M messages), or use a separate smaller model for summarization.

### 2. ToolCallDelta index ignored — latent multi-tool interleaving bug

**Location:** `turn.py:470-473`

```python
case ToolCallDelta(arguments_delta=delta):
    if current_tool_call:
        current_tool_call["arguments"] += delta
```

`ToolCallDelta` has an `index` field to correlate it back to a specific `ToolCallStart`, but the code always appends to `current_tool_call`. If a provider interleaves deltas for multiple concurrent tool calls (some OpenAI modes do this), deltas would be appended to the wrong tool call.

Fine for current Anthropic/OpenAI sequential streaming, but a correctness risk if any provider changes behavior.

### 3. Token counting in `_check_compaction` may double-count depending on provider

**Location:** `loop.py:250-255`, `core/compaction.py:53-64`

```python
tokens_before = (
    last_usage.input_tokens
    + last_usage.output_tokens
    + last_usage.cache_read_tokens
    + last_usage.cache_write_tokens
)
```

For Anthropic, `input_tokens` excludes cache-read tokens (reported separately), so this sum is correct. For OpenAI-compatible providers, the semantics may differ — `input_tokens` might already include cached tokens, leading to over-counting. Each provider needs to populate `Usage` consistently for this to be reliable.

### 4. Edit tool doesn't validate `old_string != new_string`

**Location:** `tools/edit.py`

The tool description says "must be different from old_string" but the implementation doesn't check. The edit silently succeeds as a no-op. The LLM might loop thinking it made a change.

## Performance

### 5. `_truncate_tail` uses `insert(0, ...)` in a loop

**Location:** `tools/bash.py:109`

```python
output_lines.insert(0, line)
```

O(n²) for large outputs. With `MAX_OUTPUT_LINES = 2000`, this is ~2M operations worst case. Could build in reverse and flip once, or use a deque.

## Design Observations

### 6. Compaction summarization doesn't pass `max_tokens`

**Location:** `core/compaction.py:82`, `core/handoff.py:44`

`generate_summary` and `generate_handoff_prompt` rely on the provider's default `max_tokens`, which might be low for summarizing a long conversation. Should probably pass an explicit higher limit.

### 7. No backoff on repeated compaction failures

If compaction fails (aborted), the next turn's `_check_compaction` will try again immediately with the same too-large context. No exponential backoff or circuit breaker.

### 8. `_get_tool_call_idle_timeout_seconds` has confusing zero/None semantics

**Location:** `turn.py:117-120`

```python
if timeout <= 0:
    return None
return timeout or _DEFAULT_TOOL_CALL_IDLE_TIMEOUT_SECONDS
```

Config value `0` disables timeout (returns `None`). Config value `None` uses the default via `or`. The double-check is slightly confusing — a single explicit check would be clearer.

## Test Coverage Gaps

- Compaction triggered during `Agent.run()` integration (overflow → compaction → continue/pause flow)
- Multi-tool-call ordering and interleaving
- `_await_approval` edge cases (future resolved before cancel, cancel before future, etc.)
- The `continue` mode synthetic user message injection after compaction
