"""
Path completion engine for tab completion.

Handles filesystem path completion with caching, tilde expansion,
and longest common prefix matching for multiple results.
"""

import os
import re


class PathComplete:
    """
    Async path completion with caching.

    Features:
    - Expands ~ and resolves relative paths
    - Caches directory listings for performance
    - Finds longest common prefix for multiple matches
    - Returns completion text and alternatives
    """

    def __init__(self) -> None:
        self._cache: dict[str, list[str]] = {}

    def clear_cache(self) -> None:
        self._cache.clear()

    async def __call__(self, cwd: str, path_fragment: str) -> tuple[str, list[str]]:
        """
        Complete a path fragment.

        Args:
            cwd: Current working directory for resolving relative paths
            path_fragment: The partial path to complete

        Returns:
            Tuple of (completion_text, alternatives)
            - completion_text: Text to append to complete the path (or longest common prefix)
            - alternatives: List of all matching paths (empty if unique match)
        """
        if not path_fragment:
            return "", []

        # Expand ~ to home directory
        if path_fragment.startswith("~"):
            expanded = os.path.expanduser(path_fragment)
        else:
            expanded = path_fragment

        # Resolve relative to cwd if not absolute
        base_path = os.path.join(cwd, expanded) if not os.path.isabs(expanded) else expanded

        # Normalize the path
        base_path = os.path.normpath(base_path)

        # Determine directory to list and prefix to match
        # Only list directory contents if path ends with / (explicit intent)
        # Otherwise, match the basename as a prefix in the parent directory
        ends_with_sep = path_fragment.endswith("/") or path_fragment.endswith(os.sep)
        is_home_only = path_fragment in ("~", "~/")
        is_dot_path = path_fragment in (".", "..")

        if ends_with_sep or is_home_only:
            # User wants to see directory contents
            if os.path.isdir(base_path):
                dir_to_list = base_path
                match_prefix = ""
            else:
                return "", []
        elif is_dot_path:
            # Special case: . or .. should complete to ./ or ../
            return "/", []
        else:
            # User is typing a name - match it in the parent directory
            dir_to_list = os.path.dirname(base_path)
            match_prefix = os.path.basename(base_path)
            if not dir_to_list:
                dir_to_list = cwd

        # Get directory listing (cached or fresh)
        entries = await self._list_directory(dir_to_list)
        if entries is None:
            return "", []

        # Filter entries by prefix
        matches = [e for e in entries if e.lower().startswith(match_prefix.lower())]

        if not matches:
            return "", []

        if len(matches) == 1:
            # Unique match - complete it
            match = matches[0]
            full_path = os.path.join(dir_to_list, match)

            # Add trailing separator for directories
            if os.path.isdir(full_path):
                match = match + os.sep

            # Calculate what to append
            completion = match[len(match_prefix) :]
            return completion, []

        # Multiple matches - find longest common prefix
        lcp = self._longest_common_prefix(matches)
        completion = lcp[len(match_prefix) :]

        # Build full display paths for alternatives
        alternatives = []
        for match in sorted(matches):
            full_path = os.path.join(dir_to_list, match)
            if os.path.isdir(full_path):
                alternatives.append(match + os.sep)
            else:
                alternatives.append(match)

        return completion, alternatives

    async def _list_directory(self, path: str) -> list[str] | None:
        """
        List directory contents (cached).

        Returns None if directory doesn't exist or can't be read.
        """
        if path in self._cache:
            return self._cache[path]

        try:
            entries = os.listdir(path)
            self._cache[path] = entries
            return entries
        except OSError:
            return None

    @staticmethod
    def extract_path_fragment(text: str) -> tuple[str, int]:
        """
        Extract the path fragment from text before cursor.

        Returns (path_fragment, start_column) or ("", -1) if no path found.
        """
        if not text:
            return "", -1

        # Handle quoted paths - look for an unclosed quote
        in_quote = False
        quote_char = None
        quote_start = -1

        for i, char in enumerate(text):
            if char in "\"'":
                if not in_quote:
                    in_quote = True
                    quote_char = char
                    quote_start = i
                elif char == quote_char:
                    in_quote = False
                    quote_char = None
                    quote_start = -1

        if in_quote and quote_start >= 0:
            # Return the content after the opening quote
            return text[quote_start + 1 :], quote_start

        # Not in a quote - find the last whitespace-separated token
        # that looks like a path
        # Match paths:
        # - Starting with ~ (home dir)
        # - Starting with ./ or ../ (relative)
        # - Starting with / (absolute)
        # - Containing / (like src/main.py)
        match = re.search(r"(~[^\s]*|\.\.?/[^\s]*|/[^\s]*|[^\s]*/[^\s]*)$", text)
        if match:
            return match.group(1), match.start()

        # Check if the last word could be a relative path (no slashes yet)
        # This allows completing "src" to "src/"
        words = text.split()
        if words:
            last_word = words[-1]
            start = text.rfind(last_word)
            # Only treat as path if it could be a valid path start
            if last_word and not last_word.startswith("-"):
                return last_word, start

        return "", -1

    @staticmethod
    def get_base_path(path_fragment: str) -> str:
        """
        Get the directory portion of a path fragment.

        For "src/dot/t" returns "src/dot/"
        For "src" returns ""
        """
        if os.sep in path_fragment:
            return path_fragment.rsplit(os.sep, 1)[0] + os.sep
        if "/" in path_fragment:  # Handle forward slash on all platforms
            return path_fragment.rsplit("/", 1)[0] + "/"
        return ""

    def _longest_common_prefix(self, strings: list[str]) -> str:
        """Find the longest common prefix of a list of strings (case-insensitive)."""
        if not strings:
            return ""
        if len(strings) == 1:
            return strings[0]

        # Use first string as reference
        first = strings[0]
        result = []

        for i, char in enumerate(first):
            # Check if all other strings have this character at position i
            char_lower = char.lower()
            for s in strings[1:]:
                if i >= len(s) or s[i].lower() != char_lower:
                    return "".join(result)
            result.append(char)

        return "".join(result)

    def invalidate(self, path: str) -> None:
        """Invalidate cache for a specific directory."""
        normalized = os.path.normpath(path)
        if normalized in self._cache:
            del self._cache[normalized]
