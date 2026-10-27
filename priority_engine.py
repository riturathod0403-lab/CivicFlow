"""
CivicFlow - Priority Estimation Engine (priority_engine.py)
Estimates complaint urgency level (Low, Medium, High, Critical)
using risk-weighted semantic signals, public safety hazards, and impact factors.
"""

import re

CRITICAL_KEYWORDS = [
    "electrocution", "live wire", "exposed wire", "fire hazard", "burst", "bursting",
    "flooding street", "cave-in", "collapse", "dengue", "cholera", "epidemic", "biohazard",
    "dead body", "dead animal", "toxic", "chemical", "hospital", "ambulance", "falling into",
    "life threatening", "severe injury", "gas leak"
]

HIGH_KEYWORDS = [
    "deep crater", "accident", "overflowing", "damaged car", "heavy traffic", "blocked sewer",
    "completely dark", "dark stretch", "stagnant water", "missed 3 days", "foul smell",
    "school gate", "market", "no water for 24", "no water for 48", "broken pipe",
    "sewage water", "unauthorized dump", "burning trash", "hazard"
]

MEDIUM_KEYWORDS = [
    "leaking", "stray dog", "mosquitoes", "slow drain", "crack", "footpath",
    "encroachment", "dumping", "irregular", "dirty toilet", "flickering"
]

CATEGORY_BASE_WEIGHTS = {
    "water_supply": 2,
    "drainage": 2,
    "streetlights": 1,
    "potholes": 2,
    "garbage": 1,
    "sanitation": 2,
    "other": 0
}

def estimate_priority(text: str, category: str = "other") -> dict:
    """
    Estimates complaint priority: Low, Medium, High, Critical.
    Returns:
    {
        'priority': str,
        'score': int,
        'reasons': list[str]
    }
    """
    lower_text = text.lower()
    score = CATEGORY_BASE_WEIGHTS.get(category, 0)
    reasons = []

    # Check for Critical triggers
    matched_critical = [kw for kw in CRITICAL_KEYWORDS if re.search(r'\b' + re.escape(kw) + r'\b', lower_text)]
    if matched_critical:
        score += 8
        reasons.append(f"Public safety / emergency hazard detected: '{', '.join(matched_critical)}'")

    # Check for High triggers
    matched_high = [kw for kw in HIGH_KEYWORDS if re.search(r'\b' + re.escape(kw) + r'\b', lower_text)]
    if matched_high:
        score += 4
        reasons.append(f"High-impact civic disruption detected: '{', '.join(matched_high)}'")

    # Check for Medium triggers
    matched_medium = [kw for kw in MEDIUM_KEYWORDS if re.search(r'\b' + re.escape(kw) + r'\b', lower_text)]
    if matched_medium:
        score += 2
        reasons.append(f"Moderate civic disturbance keywords: '{', '.join(matched_medium)}'")

    # Length & Detail factor
    words = len(text.split())
    if words > 20:
        score += 1
        reasons.append("Detailed complaint submission with specific location context")

    if not reasons:
        reasons.append("Standard municipal service maintenance request")

    # Final mapping
    if score >= 9:
        priority = "Critical"
    elif score >= 5:
        priority = "High"
    elif score >= 2:
        priority = "Medium"
    else:
        priority = "Low"

    return {
        "priority": priority,
        "score": score,
        "reasons": reasons
    }
