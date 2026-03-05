"""
scoring.py
Defines all audit criteria with weights/priorities, and the final score calculator.
"""

from typing import Dict, List

# ── Criteria registry ──────────────────────────────────────────────────────────
# weight: multiplier applied to the raw score when computing the weighted average
# priority: High / Medium / Low (informational label)
AUDIT_CRITERIA: Dict[str, dict] = {
    "structured_data": {
        "label": "Structured Data",
        "icon": "🏗️",
        "priority": "High",
        "weight": 3,
        "description": (
            "Checks for JSON-LD, Microdata, or RDFa schema markup. "
            "Validates type correctness and completeness of key schema types "
            "(Article, Product, Organisation, BreadcrumbList, FAQPage, etc.)."
        ),
    },
    "aria_accessibility": {
        "label": "ARIA & Accessibility",
        "icon": "♿",
        "priority": "High",
        "weight": 3,
        "description": (
            "Checks for ARIA roles, labels, landmarks, and alt text. "
            "Evaluates heading hierarchy, form labels, and focus management."
        ),
    },
    "content_structure": {
        "label": "Content Structure",
        "icon": "📄",
        "priority": "High",
        "weight": 3,
        "description": (
            "Evaluates heading hierarchy (H1-H6), paragraph structure, "
            "internal linking, semantic HTML5 elements (main, article, section, nav), "
            "and overall content organisation."
        ),
    },
    "meta_tags": {
        "label": "Meta Tags & Title",
        "icon": "🏷️",
        "priority": "High",
        "weight": 3,
        "description": (
            "Checks title tag, meta description, canonical URL, robots directives, "
            "Open Graph tags, and Twitter Card tags."
        ),
    },
    "llms_txt": {
        "label": "LLMs.txt",
        "icon": "🤖",
        "priority": "Medium",
        "weight": 2,
        "description": (
            "Checks whether the site has a /llms.txt file (or /llms-full.txt) "
            "as per the llmstxt.org specification, and evaluates its quality "
            "and completeness for AI-readability."
        ),
    },
    "page_speed_signals": {
        "label": "Page Speed Signals",
        "icon": "⚡",
        "priority": "Medium",
        "weight": 2,
        "description": (
            "Analyses render-blocking resources, image optimisation hints, "
            "lazy-loading attributes, and resource hints (preload, prefetch, preconnect)."
        ),
    },
    "internal_linking": {
        "label": "Internal Linking",
        "icon": "🔗",
        "priority": "Medium",
        "weight": 2,
        "description": (
            "Evaluates the quantity and quality of internal links, "
            "descriptive anchor text, and avoidance of generic link text."
        ),
    },
    "mobile_readiness": {
        "label": "Mobile Readiness",
        "icon": "📱",
        "priority": "Medium",
        "weight": 2,
        "description": (
            "Checks viewport meta tag, touch-target sizing hints in HTML, "
            "and absence of fixed-width layouts."
        ),
    },
    "security_headers": {
        "label": "Security & HTTPS",
        "icon": "🔒",
        "priority": "Low",
        "weight": 1,
        "description": (
            "Checks whether the URL uses HTTPS, presence of security-related "
            "meta tags, and CSP hints visible in HTML."
        ),
    },
    "social_sharing": {
        "label": "Social Sharing",
        "icon": "📣",
        "priority": "Low",
        "weight": 1,
        "description": (
            "Evaluates Open Graph completeness, Twitter Card tags, "
            "and share-friendly content structure."
        ),
    },
}


# ── Grade thresholds ───────────────────────────────────────────────────────────
GRADE_THRESHOLDS = [
    (90, "A+"),
    (80, "A"),
    (70, "B"),
    (60, "C"),
    (50, "D"),
    (0, "F"),
]


def get_grade(score: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def calculate_final_score(
    results: Dict[str, dict],
    active_criteria: List[str],
) -> dict:
    """
    Calculates weighted and raw average scores from per-criterion results.

    Returns a dict with:
        weighted_score  - 0-100 weighted by criterion weight
        raw_average     - 0-100 simple average
        grade           - letter grade
        breakdown       - per-criterion score + weight
    """
    if not results:
        return {"weighted_score": 0, "raw_average": 0, "grade": "F", "breakdown": {}}

    total_weight = 0
    weighted_sum = 0.0
    raw_sum = 0.0
    breakdown = {}

    for key in active_criteria:
        if key not in results:
            continue
        score = float(results[key].get("score", 0))
        weight = AUDIT_CRITERIA[key]["weight"]

        weighted_sum += score * weight
        total_weight += weight
        raw_sum += score

        breakdown[key] = {
            "score": score,
            "weight": weight,
            "contribution": score * weight,
        }

    n = len(breakdown)
    weighted_score = (weighted_sum / total_weight) if total_weight else 0
    raw_average = (raw_sum / n) if n else 0

    return {
        "weighted_score": round(weighted_score, 1),
        "raw_average": round(raw_average, 1),
        "grade": get_grade(weighted_score),
        "breakdown": breakdown,
    }
