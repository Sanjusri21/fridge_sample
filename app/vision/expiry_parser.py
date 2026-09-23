"""
Expiry Date Parser.
Extracts and normalizes dates from OCR text or user queries.
Supports formats:
- EXP 14/09/2026
- EXP: 14-09-2026
- Expiry: 14/09/26
- Best Before: 14/09/2026
- BB 14/09/2026
- 2026-09-14
- 14.09.2026
- 14/09/2026
- 14-09-2026
"""

import re
from datetime import date, datetime
from typing import Optional, Tuple
from app.config.settings import logger


DATE_PATTERNS = [
    # YYYY-MM-DD or YYYY/MM/DD or YYYY.MM.DD
    (r"\b(20\d{2})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b", "%Y-%m-%d"),

    # DD-MM-YYYY or DD/MM/YYYY or DD.MM.YYYY
    (r"\b(0[1-9]|[12]\d|3[01])[-/.](0[1-9]|1[0-2])[-/.](20\d{2})\b", "%d-%m-%Y"),

    # DD-MM-YY or DD/MM/YY or DD.MM.YY (e.g. 14/09/26)
    (r"\b(0[1-9]|[12]\d|3[01])[-/.](0[1-9]|1[0-2])[-/.]([2-3]\d)\b", "%d-%m-%y"),
]

PREFIX_PATTERNS = [
    r"(?:exp(?:iry)?|bb|best\s*before|use\s*by|use\s*before)[\s:]*",
]


def parse_expiry_date(raw_text: str) -> Optional[date]:
    """
    Finds and parses an expiry date from raw text string.
    Returns datetime.date if successfully matched and parsed, or None.
    """
    if not raw_text:
        return None

    text = raw_text.strip()

    # Try searching after common expiry prefixes first
    for prefix in PREFIX_PATTERNS:
        match = re.search(prefix + r"([0-9\-\.\/]{6,10})", text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            parsed = _attempt_parse_candidate(candidate)
            if parsed:
                logger.info("Found date with prefix: '%s' -> %s", candidate, parsed)
                return parsed

    # Search for all standalone date patterns in text
    # 1. ISO format: YYYY-MM-DD
    iso_match = re.search(r"\b(20\d{2})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b", text)
    if iso_match:
        y, m, d = iso_match.group(1), iso_match.group(2), iso_match.group(3)
        try:
            return date(int(y), int(m), int(d))
        except ValueError:
            pass

    # 2. DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
    dmy_match = re.search(r"\b(0[1-9]|[12]\d|3[01])[-/.](0[1-9]|1[0-2])[-/.](20\d{2})\b", text)
    if dmy_match:
        d, m, y = dmy_match.group(1), dmy_match.group(2), dmy_match.group(3)
        try:
            return date(int(y), int(m), int(d))
        except ValueError:
            pass

    # 3. 2-digit year: DD/MM/YY
    dmy2_match = re.search(r"\b(0[1-9]|[12]\d|3[01])[-/.](0[1-9]|1[0-2])[-/.]([2-3]\d)\b", text)
    if dmy2_match:
        d, m, y = dmy2_match.group(1), dmy2_match.group(2), dmy2_match.group(3)
        full_year = 2000 + int(y)
        try:
            return date(full_year, int(m), int(d))
        except ValueError:
            pass

    return None


def _attempt_parse_candidate(candidate: str) -> Optional[date]:
    """Helper to parse a date candidate string across standard formats."""
    clean = candidate.replace("/", "-").replace(".", "-")
    # Formats to try
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%d-%m-%y"]
    for fmt in formats:
        try:
            dt = datetime.strptime(clean, fmt)
            return dt.date()
        except ValueError:
            continue
    return None
