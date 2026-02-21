"""
Sanitize text content before sending to LLM APIs.

Lone Unicode surrogates (U+D800-U+DFFF) cause API errors with some providers.
This matches pi-mono's sanitizeSurrogates() behavior.
"""

import re

_SURROGATE_RE = re.compile(r"[\ud800-\udfff]")


def sanitize_surrogates(text: str) -> str:
    return _SURROGATE_RE.sub("\ufffd", text)
