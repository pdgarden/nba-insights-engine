"""Shared fuzzy string matching used by NER retrieval and the MCP search tools."""

from rapidfuzz import process as fuzz_process


def top_matches(query: str, choices: list[str], limit: int) -> list[tuple[str, float, int]]:
    """Return up to `limit` closest matches to `query` among `choices`, ranked by score (case-insensitive)."""
    return fuzz_process.extract(query, choices, limit=limit, processor=str.casefold)
