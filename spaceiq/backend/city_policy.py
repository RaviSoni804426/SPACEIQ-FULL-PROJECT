from __future__ import annotations


BANGALORE_CANONICAL_CITY = "Bengaluru"
BANGALORE_CITY_ALIASES = frozenset(
    {
        "bangalore",
        "bangaluru",
        "bengalooru",
        "bengaluru",
        "blr",
    }
)
BANGALORE_QUERY_VALUES = (
    BANGALORE_CANONICAL_CITY,
    "Bangalore",
    "Bangaluru",
    "Bengalooru",
)


def normalize_bangalore_city(value: str | None) -> str:
    normalized = (value or "").strip().lower().replace(".", "")
    if normalized in BANGALORE_CITY_ALIASES:
        return BANGALORE_CANONICAL_CITY
    raise ValueError("SpaceIQ currently supports Bengaluru listings and partner requests only.")
