# app/security.py

import re

# Regex patterns for SSNs and credit cards
SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b')
CREDIT_CARD_PATTERN = re.compile(r'\b(?:\d[ -]*?){13,16}\b')

# Standard prompt injection triggers
INJECTION_KEYWORDS = [
    "ignore all previous",
    "ignore the instructions",
    "ignore instructions",
    "bypass safety",
    "override safety",
    "auto-approve",
    "autoapprove",
    "force approval",
    "force approve",
    "bypass confirmation",
    "hijack agent",
    "system instructions",
    "you must approve",
    "do not ask for confirmation",
    "skip validation",
    "skip review"
]

def scrub_pii(text: str) -> tuple[str, list[str]]:
    """Scrubs SSNs and Credit Card numbers from the prompt.
    
    Returns the scrubbed prompt and a list of redacted categories.
    """
    redacted_categories = []
    
    # Scrub SSN
    if SSN_PATTERN.search(text):
        text = SSN_PATTERN.sub("[REDACTED_SSN]", text)
        redacted_categories.append("SSN")
        
    # Scrub Credit Card
    if CREDIT_CARD_PATTERN.search(text):
        text = CREDIT_CARD_PATTERN.sub("[REDACTED_CREDIT_CARD]", text)
        redacted_categories.append("CREDIT_CARD")
        
    return text, redacted_categories

def detect_prompt_injection(text: str) -> bool:
    """Detects if the user is trying to bypass rules or force auto-approval."""
    text_lower = text.lower()
    for keyword in INJECTION_KEYWORDS:
        if keyword in text_lower:
            return True
    return False
