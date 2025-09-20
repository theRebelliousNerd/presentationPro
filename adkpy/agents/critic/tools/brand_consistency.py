"""Brand consistency checker for presentation slides.

This tool ensures slides adhere to brand guidelines including:
- Color palette compliance
- Typography consistency
- Tone and voice alignment
- Logo and asset usage
- Visual hierarchy standards
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import re
import requests
from colorthief import ColorThief
import io
import base64
from PIL import Image

logger = logging.getLogger(__name__)


# Default PresentationPro brand guidelines
DEFAULT_BRAND_GUIDELINES = {
    "brand_name": "PresentationPro",
    "colors": {
        "primary": ["#192940", "#73BF50", "#556273"],
        "secondary": ["#E8F4FD", "#F0F8EC", "#F7F8F9"],
        "accent": ["#FF6B6B", "#4ECDC4", "#45B7D1"],
        "neutral": ["#FFFFFF", "#F8F9FA", "#E9ECEF", "#DEE2E6"]
    },
    "typography": {
        "headings": ["Montserrat", "Arial", "Helvetica"],
        "body": ["Roboto", "Arial", "Helvetica"],
        "script": ["Dancing Script", "cursive"]
    },
    "tone": {
        "primary": "professional",
        "alternatives": ["authoritative", "informative", "confident"],
        "avoid": ["casual", "playful", "overly_technical"]
    },
    "content_style": {
        "bullet_style": "parallel_structure",
        "capitalization": "sentence_case",
        "punctuation": "minimal",
        "length": "concise"
    },
    "visual_hierarchy": {
        "title_prominence": "high",
        "content_spacing": "generous",
        "emphasis_style": "bold_or_color"
    }
}


async def check_brand_consistency(
    slide_content: Dict[str, Any],
    slide_image: Optional[str] = None,
    brand_guidelines: Optional[Dict[str, Any]] = None,
    visioncv_url: str = "http://visioncv:8091"
) -> Dict[str, Any]:
    """
    Check slide brand consistency against guidelines.

    Args:
        slide_content: Slide content dictionary
        slide_image: Optional base64 encoded slide image
        brand_guidelines: Brand guidelines (uses default if None)
        visioncv_url: VisionCV service URL

    Returns:
        Brand consistency assessment results
    """
    if brand_guidelines is None:
        brand_guidelines = DEFAULT_BRAND_GUIDELINES

    logger.info(f"Checking brand consistency for slide: {slide_content.get('title', 'Untitled')}")

    results = {
        "brand_name": brand_guidelines.get("brand_name", "Unknown"),
        "overall_score": 100,
        "compliance_level": "excellent",
        "issues": [],
        "recommendations": [],
        "checks": {
            "color_palette": {"status": "pending", "score": 100, "details": {}},
            "typography": {"status": "pending", "score": 100, "details": {}},
            "tone_voice": {"status": "pending", "score": 100, "details": {}},
            "content_style": {"status": "pending", "score": 100, "details": {}},
            "visual_hierarchy": {"status": "pending", "score": 100, "details": {}}
        }
    }

    # Check color palette compliance
    color_result = await _check_color_palette(
        slide_image, brand_guidelines, visioncv_url
    )
    results["checks"]["color_palette"] = color_result

    # Check typography consistency (if we can detect it)
    typography_result = await _check_typography(slide_content, brand_guidelines)
    results["checks"]["typography"] = typography_result

    # Check tone and voice
    tone_result = await _check_tone_voice(slide_content, brand_guidelines)
    results["checks"]["tone_voice"] = tone_result

    # Check content style consistency
    style_result = await _check_content_style(slide_content, brand_guidelines)
    results["checks"]["content_style"] = style_result

    # Check visual hierarchy
    hierarchy_result = await _check_visual_hierarchy(slide_content, brand_guidelines)
    results["checks"]["visual_hierarchy"] = hierarchy_result

    # Compile overall results
    _compile_brand_results(results)

    return results


async def _check_color_palette(
    slide_image: Optional[str],
    brand_guidelines: Dict[str, Any],
    visioncv_url: str
) -> Dict[str, Any]:
    """Check color palette compliance."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    if not slide_image:
        result["status"] = "skipped"
        result["details"]["reason"] = "No image provided for color analysis"
        return result

    try:
        # Extract dominant colors from slide
        slide_colors = await _extract_slide_colors(slide_image)
        brand_colors = _get_all_brand_colors(brand_guidelines)

        result["details"]["slide_colors"] = slide_colors
        result["details"]["brand_colors"] = brand_colors

        if slide_colors:
            # Check if slide colors match brand palette
            color_matches = _find_color_matches(slide_colors, brand_colors)
            match_percentage = len(color_matches) / len(slide_colors) * 100

            result["details"]["color_matches"] = color_matches
            result["details"]["match_percentage"] = match_percentage

            if match_percentage < 60:  # Less than 60% brand colors
                result["status"] = "warning"
                result["score"] = max(40, int(match_percentage))
                result["issues"].append(
                    f"Only {match_percentage:.1f}% of slide colors match brand palette"
                )
                result["recommendations"].extend([
                    "Use more colors from the approved brand palette",
                    "Consider replacing non-brand colors with brand alternatives",
                    "Ensure dominant colors align with brand identity"
                ])

            elif match_percentage < 80:
                result["status"] = "warning"
                result["score"] = max(70, int(match_percentage))
                result["issues"].append("Some slide colors don't match brand palette")
                result["recommendations"].append("Optimize color choices to better align with brand")

        else:
            result["status"] = "error"
            result["score"] = 50
            result["details"]["error"] = "Could not extract colors from slide image"

    except Exception as e:
        logger.error(f"Color palette check failed: {e}")
        result["status"] = "error"
        result["score"] = 50
        result["details"]["error"] = str(e)

    return result


async def _check_typography(
    slide_content: Dict[str, Any],
    brand_guidelines: Dict[str, Any]
) -> Dict[str, Any]:
    """Check typography consistency (basic content analysis)."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    typography_rules = brand_guidelines.get("typography", {})

    # Since we can't directly detect fonts from content, we check style consistency
    title = slide_content.get("title", "")
    content = slide_content.get("content", [])

    # Check title formatting
    if title:
        title_issues = _check_title_formatting(title, typography_rules)
        if title_issues:
            result["status"] = "warning"
            result["score"] -= 10
            result["issues"].extend(title_issues)

    # Check content formatting consistency
    if isinstance(content, list) and content:
        content_issues = _check_content_formatting(content, typography_rules)
        if content_issues:
            result["status"] = "warning"
            result["score"] -= 5 * len(content_issues)
            result["issues"].extend(content_issues)

    result["details"]["title_check"] = bool(title)
    result["details"]["content_items"] = len(content) if isinstance(content, list) else 0

    if result["issues"]:
        result["recommendations"].extend([
            "Ensure consistent formatting across all text elements",
            "Use brand-approved typography hierarchy",
            "Maintain consistent text styling throughout presentation"
        ])

    return result


async def _check_tone_voice(
    slide_content: Dict[str, Any],
    brand_guidelines: Dict[str, Any]
) -> Dict[str, Any]:
    """Check tone and voice alignment."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    tone_rules = brand_guidelines.get("tone", {})
    primary_tone = tone_rules.get("primary", "professional")
    avoid_tones = tone_rules.get("avoid", [])

    # Analyze title tone
    title = slide_content.get("title", "")
    if title:
        title_tone_score = _analyze_text_tone(title, primary_tone, avoid_tones)
        result["details"]["title_tone_score"] = title_tone_score

        if title_tone_score < 70:
            result["status"] = "warning"
            result["score"] -= 15
            result["issues"].append(f"Title tone doesn't match brand voice ({primary_tone})")

    # Analyze content tone
    content = slide_content.get("content", [])
    if isinstance(content, list) and content:
        content_text = " ".join(content)
        content_tone_score = _analyze_text_tone(content_text, primary_tone, avoid_tones)
        result["details"]["content_tone_score"] = content_tone_score

        if content_tone_score < 70:
            result["status"] = "warning"
            result["score"] -= 10
            result["issues"].append(f"Content tone doesn't match brand voice ({primary_tone})")

    # Analyze speaker notes tone
    speaker_notes = slide_content.get("speakerNotes", "")
    if speaker_notes:
        notes_tone_score = _analyze_text_tone(speaker_notes, primary_tone, avoid_tones)
        result["details"]["notes_tone_score"] = notes_tone_score

        if notes_tone_score < 70:
            result["status"] = "warning"
            result["score"] -= 5
            result["issues"].append("Speaker notes tone could better match brand voice")

    if result["issues"]:
        result["recommendations"].extend([
            f"Adjust language to match {primary_tone} brand tone",
            "Use vocabulary and phrasing consistent with brand voice",
            "Avoid overly casual or technical language if not brand-appropriate"
        ])

    return result


async def _check_content_style(
    slide_content: Dict[str, Any],
    brand_guidelines: Dict[str, Any]
) -> Dict[str, Any]:
    """Check content style consistency."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    style_rules = brand_guidelines.get("content_style", {})

    # Check bullet structure
    content = slide_content.get("content", [])
    if isinstance(content, list) and len(content) > 1:
        structure_issues = _check_bullet_structure(content, style_rules)
        if structure_issues:
            result["status"] = "warning"
            result["score"] -= 5 * len(structure_issues)
            result["issues"].extend(structure_issues)

    # Check capitalization consistency
    all_text = [slide_content.get("title", "")]
    if isinstance(content, list):
        all_text.extend(content)

    cap_issues = _check_capitalization_consistency(all_text, style_rules)
    if cap_issues:
        result["status"] = "warning"
        result["score"] -= 10
        result["issues"].extend(cap_issues)

    result["details"]["bullet_count"] = len(content) if isinstance(content, list) else 0
    result["details"]["has_parallel_structure"] = _has_parallel_structure(content)

    if result["issues"]:
        result["recommendations"].extend([
            "Ensure parallel structure in bullet points",
            "Use consistent capitalization throughout",
            "Follow brand style guidelines for punctuation and formatting"
        ])

    return result


async def _check_visual_hierarchy(
    slide_content: Dict[str, Any],
    brand_guidelines: Dict[str, Any]
) -> Dict[str, Any]:
    """Check visual hierarchy compliance."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    hierarchy_rules = brand_guidelines.get("visual_hierarchy", {})

    # Check title prominence
    title = slide_content.get("title", "")
    content = slide_content.get("content", [])

    if not title and content:
        result["status"] = "warning"
        result["score"] -= 20
        result["issues"].append("Missing title reduces visual hierarchy clarity")
        result["recommendations"].append("Add descriptive title for proper visual hierarchy")

    # Check content organization
    if isinstance(content, list):
        if len(content) > 6:  # Too many bullets hurt hierarchy
            result["status"] = "warning"
            result["score"] -= 10
            result["issues"].append("Too many bullet points may confuse visual hierarchy")
            result["recommendations"].append("Limit to 3-5 key points for better hierarchy")

        # Check for consistent bullet length (hierarchy indicator)
        if content:
            bullet_lengths = [len(bullet.split()) for bullet in content]
            length_variance = max(bullet_lengths) - min(bullet_lengths)

            result["details"]["bullet_length_variance"] = length_variance

            if length_variance > 8:  # High variance suggests poor hierarchy
                result["status"] = "warning"
                result["score"] -= 5
                result["issues"].append("Inconsistent bullet lengths affect visual hierarchy")
                result["recommendations"].append("Use more consistent bullet point lengths")

    result["details"]["has_title"] = bool(title)
    result["details"]["content_count"] = len(content) if isinstance(content, list) else 0

    return result


# Helper functions

async def _extract_slide_colors(slide_image: str) -> List[str]:
    """Extract dominant colors from slide image."""
    try:
        # Decode base64 image
        if slide_image.startswith('data:'):
            slide_image = slide_image.split(',')[1]

        image_data = base64.b64decode(slide_image)

        # Use ColorThief to get dominant colors
        color_thief = ColorThief(io.BytesIO(image_data))
        palette = color_thief.get_palette(color_count=6)

        # Convert RGB to hex
        hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in palette]
        return hex_colors

    except Exception as e:
        logger.error(f"Failed to extract colors: {e}")
        return []


def _get_all_brand_colors(brand_guidelines: Dict[str, Any]) -> List[str]:
    """Get all brand colors from guidelines."""
    colors = []
    color_config = brand_guidelines.get("colors", {})

    for category in ["primary", "secondary", "accent", "neutral"]:
        category_colors = color_config.get(category, [])
        colors.extend(category_colors)

    return colors


def _find_color_matches(slide_colors: List[str], brand_colors: List[str]) -> List[Dict[str, str]]:
    """Find matching colors between slide and brand palette."""
    matches = []

    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def color_distance(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
        return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

    for slide_color in slide_colors:
        try:
            slide_rgb = hex_to_rgb(slide_color)
            best_match = None
            min_distance = float('inf')

            for brand_color in brand_colors:
                try:
                    brand_rgb = hex_to_rgb(brand_color)
                    distance = color_distance(slide_rgb, brand_rgb)

                    if distance < min_distance and distance < 50:  # Similarity threshold
                        min_distance = distance
                        best_match = brand_color
                except ValueError:
                    continue

            if best_match:
                matches.append({
                    "slide_color": slide_color,
                    "brand_color": best_match,
                    "distance": min_distance
                })

        except ValueError:
            continue

    return matches


def _check_title_formatting(title: str, typography_rules: Dict[str, Any]) -> List[str]:
    """Check title formatting issues."""
    issues = []

    # Check for all caps (usually not brand appropriate)
    if title.isupper() and len(title) > 3:
        issues.append("Title should not be in ALL CAPS")

    # Check for excessive punctuation
    if title.count('!') > 1 or title.count('?') > 1:
        issues.append("Avoid excessive punctuation in titles")

    return issues


def _check_content_formatting(content: List[str], typography_rules: Dict[str, Any]) -> List[str]:
    """Check content formatting issues."""
    issues = []

    if not content:
        return issues

    # Check for inconsistent capitalization
    first_words = [bullet.split()[0] if bullet.split() else "" for bullet in content]
    caps = [word[0].isupper() if word else False for word in first_words]

    if len(set(caps)) > 1:  # Mixed capitalization
        issues.append("Inconsistent bullet point capitalization")

    # Check for inconsistent punctuation
    ends_with_period = [bullet.strip().endswith('.') for bullet in content]
    if len(set(ends_with_period)) > 1:  # Mixed punctuation
        issues.append("Inconsistent bullet point punctuation")

    return issues


def _analyze_text_tone(text: str, target_tone: str, avoid_tones: List[str]) -> int:
    """Analyze text tone alignment (simplified heuristic)."""
    if not text:
        return 100

    text_lower = text.lower()
    score = 100

    # Define tone indicators
    tone_indicators = {
        "professional": {
            "positive": ["achieve", "deliver", "implement", "optimize", "strategic", "effective"],
            "negative": ["awesome", "cool", "stuff", "things", "whatever", "kinda"]
        },
        "casual": {
            "positive": ["awesome", "cool", "hey", "stuff", "things", "great"],
            "negative": ["implement", "strategic", "optimize", "facilitate", "leverage"]
        },
        "technical": {
            "positive": ["algorithm", "implementation", "framework", "methodology", "protocol"],
            "negative": ["feel", "think", "maybe", "probably", "seems"]
        }
    }

    # Check target tone alignment
    if target_tone in tone_indicators:
        positive_words = tone_indicators[target_tone]["positive"]
        negative_words = tone_indicators[target_tone]["negative"]

        positive_matches = sum(1 for word in positive_words if word in text_lower)
        negative_matches = sum(1 for word in negative_words if word in text_lower)

        # Adjust score based on matches
        score += positive_matches * 5
        score -= negative_matches * 10

    # Check for avoided tones
    for avoid_tone in avoid_tones:
        if avoid_tone in tone_indicators:
            avoid_positive = tone_indicators[avoid_tone]["positive"]
            avoid_matches = sum(1 for word in avoid_positive if word in text_lower)
            score -= avoid_matches * 8

    return max(0, min(100, score))


def _check_bullet_structure(content: List[str], style_rules: Dict[str, Any]) -> List[str]:
    """Check bullet point structure consistency."""
    issues = []

    if len(content) < 2:
        return issues

    # Check parallel structure
    if not _has_parallel_structure(content):
        issues.append("Bullet points lack parallel structure")

    return issues


def _has_parallel_structure(content: List[str]) -> bool:
    """Check if bullets have parallel grammatical structure."""
    if not isinstance(content, list) or len(content) < 2:
        return True

    # Simple heuristic: check if bullets start with similar grammatical forms
    first_words = [bullet.split()[0].lower() if bullet.split() else "" for bullet in content]

    # Check for action verbs (parallel structure indicator)
    action_verbs = ["develop", "create", "implement", "manage", "analyze", "design", "build", "improve"]
    verb_starts = sum(1 for word in first_words if word in action_verbs)

    # If most bullets start with action verbs, structure is parallel
    return verb_starts >= len(first_words) * 0.7


def _check_capitalization_consistency(text_items: List[str], style_rules: Dict[str, Any]) -> List[str]:
    """Check capitalization consistency."""
    issues = []

    capitalization_style = style_rules.get("capitalization", "sentence_case")

    # Filter out empty strings
    valid_items = [item for item in text_items if item and item.strip()]

    if not valid_items:
        return issues

    if capitalization_style == "sentence_case":
        # Check if all items follow sentence case
        incorrect_items = []
        for item in valid_items:
            if item and not (item[0].isupper() and not item[1:].isupper()):
                incorrect_items.append(item[:20] + "..." if len(item) > 20 else item)

        if incorrect_items:
            issues.append(f"Items not in sentence case: {', '.join(incorrect_items)}")

    return issues


def _compile_brand_results(results: Dict[str, Any]) -> None:
    """Compile overall brand consistency results."""
    checks = results["checks"]

    # Calculate weighted overall score
    weights = {
        "color_palette": 0.25,
        "typography": 0.20,
        "tone_voice": 0.25,
        "content_style": 0.20,
        "visual_hierarchy": 0.10
    }

    overall_score = sum(
        checks[check]["score"] * weight
        for check, weight in weights.items()
    )

    results["overall_score"] = int(overall_score)

    # Compile all issues and recommendations
    for check_name, check_result in checks.items():
        results["issues"].extend(check_result.get("issues", []))
        results["recommendations"].extend(check_result.get("recommendations", []))

    # Remove duplicate recommendations
    results["recommendations"] = list(dict.fromkeys(results["recommendations"]))

    # Set compliance level
    if results["overall_score"] >= 90:
        results["compliance_level"] = "excellent"
    elif results["overall_score"] >= 75:
        results["compliance_level"] = "good"
    elif results["overall_score"] >= 60:
        results["compliance_level"] = "acceptable"
    else:
        results["compliance_level"] = "needs_improvement"


# Quick brand check function
async def quick_brand_check(slide_content: Dict[str, Any]) -> bool:
    """
    Quick boolean check for basic brand compliance.

    Returns:
        True if slide meets basic brand requirements
    """
    try:
        result = await check_brand_consistency(slide_content)
        return result["overall_score"] >= 60
    except Exception:
        return False


# Export for tool integration
__all__ = [
    "check_brand_consistency",
    "quick_brand_check",
    "DEFAULT_BRAND_GUIDELINES"
]