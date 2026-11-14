import re
from typing import Tuple

# Common prompt injection signatures targeting recipient LLMs
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior)\s+directives?",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"system\s*override",
    r"output\s+(all\s+)?(api|secret|private)\s+keys?",
    r"reveal\s+(your\s+)?system\s+prompt",
    r"jailbreak",
    r"dan\s+mode"
]

compiled_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

def sanitize_and_check_guardrails(title: str, content: str) -> Tuple[bool, str]:
    """
    Scans incoming post text for indirect prompt injection or adversarial attacks.
    Returns (is_safe: bool, reason: str).
    """
    combined = f"{title} {content}"

    for pattern in compiled_patterns:
        match = pattern.search(combined)
        if match:
            matched_phrase = match.group(0)
            return False, f"Prompt injection vector detected: '{matched_phrase}'"

    return True, "Passed security guardrails"
