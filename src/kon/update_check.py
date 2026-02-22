import re

import aiohttp


def _base_version_tuple(version: str) -> tuple[int, ...]:
    match = re.match(r"^\s*v?(\d+(?:\.\d+)*)", version.strip().lower())
    if not match:
        return (0,)

    parts = [int(part) for part in match.group(1).split(".")]
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def _stage_key(version: str) -> tuple[int, int]:
    match = re.match(r"^\s*v?\d+(?:\.\d+)*(.*)$", version.strip().lower())
    rest = match.group(1) if match else ""

    stage_patterns: list[tuple[str, int]] = [
        (r"^[._-]?dev(\d*)", -2),
        (r"^[._-]?(?:a|alpha)(\d*)", -1),
        (r"^[._-]?(?:b|beta)(\d*)", 0),
        (r"^[._-]?rc(\d*)", 1),
        (r"^[._-]?post(\d*)", 3),
    ]

    for pattern, stage in stage_patterns:
        stage_match = re.match(pattern, rest)
        if stage_match:
            number = int(stage_match.group(1)) if stage_match.group(1) else 0
            return stage, number

    return 2, 0


def is_newer_version(current_version: str, latest_version: str) -> bool:
    current_key = (_base_version_tuple(current_version), *_stage_key(current_version))
    latest_key = (_base_version_tuple(latest_version), *_stage_key(latest_version))
    return latest_key > current_key


async def fetch_latest_pypi_version(package_name: str, timeout_seconds: float = 4.0) -> str | None:
    url = f"https://pypi.org/pypi/{package_name}/json"
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    try:
        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.get(url, headers={"User-Agent": "kon"}) as response,
        ):
            if response.status != 200:
                return None
            payload = await response.json(content_type=None)
    except Exception:
        return None

    info = payload.get("info") if isinstance(payload, dict) else None
    version = info.get("version") if isinstance(info, dict) else None
    return version if isinstance(version, str) and version.strip() else None


async def get_newer_pypi_version(package_name: str, current_version: str) -> str | None:
    latest_version = await fetch_latest_pypi_version(package_name)
    if latest_version is None:
        return None
    return latest_version if is_newer_version(current_version, latest_version) else None
