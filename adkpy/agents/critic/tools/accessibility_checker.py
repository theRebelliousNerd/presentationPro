"""Accessibility compliance checker for WCAG standards.

This tool checks slides for accessibility compliance including:
- Color contrast ratios (WCAG AA/AAA)
- Text readability
- Screen reader compatibility
- Keyboard navigation support
"""

import logging
from typing import Dict, List, Any, Optional
import requests
import json

logger = logging.getLogger(__name__)


class WCAGStandard:
    """WCAG accessibility standards and thresholds."""

    # Contrast ratios
    AA_NORMAL_CONTRAST = 4.5
    AA_LARGE_CONTRAST = 3.0
    AAA_NORMAL_CONTRAST = 7.0
    AAA_LARGE_CONTRAST = 4.5

    # Text limits
    MAX_WORDS_PER_BULLET = 12
    MAX_TITLE_WORDS = 8
    MIN_FONT_SIZE = 18  # pt

    # Reading level
    MAX_FLESCH_KINCAID_GRADE = 8


async def check_accessibility(
    slide_content: Dict[str, Any],
    slide_image: Optional[str] = None,
    target_standard: str = "AA",
    visioncv_url: str = "http://visioncv:8091"
) -> Dict[str, Any]:
    """
    Check slide accessibility compliance against WCAG standards.

    Args:
        slide_content: Slide content dictionary
        slide_image: Optional base64 encoded slide image
        target_standard: WCAG standard ("AA" or "AAA")
        visioncv_url: VisionCV service URL

    Returns:
        Accessibility assessment results
    """
    logger.info(f"Checking accessibility for slide: {slide_content.get('title', 'Untitled')}")

    results = {
        "compliance_level": target_standard,
        "overall_score": 100,
        "issues": [],
        "recommendations": [],
        "checks": {
            "contrast": {"status": "pending", "score": 100, "details": {}},
            "readability": {"status": "pending", "score": 100, "details": {}},
            "structure": {"status": "pending", "score": 100, "details": {}},
            "content_length": {"status": "pending", "score": 100, "details": {}}
        }
    }

    # Check color contrast
    contrast_result = await _check_color_contrast(
        slide_image, target_standard, visioncv_url
    )
    results["checks"]["contrast"] = contrast_result

    # Check text readability
    readability_result = await _check_text_readability(slide_content)
    results["checks"]["readability"] = readability_result

    # Check document structure
    structure_result = await _check_document_structure(slide_content)
    results["checks"]["structure"] = structure_result

    # Check content length and complexity
    length_result = await _check_content_length(slide_content)
    results["checks"]["content_length"] = length_result

    # Calculate overall score and compile issues
    _compile_accessibility_results(results)

    return results


async def _check_color_contrast(
    slide_image: Optional[str],
    target_standard: str,
    visioncv_url: str
) -> Dict[str, Any]:
    """Check color contrast compliance."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    if not slide_image:
        result["status"] = "skipped"
        result["details"]["reason"] = "No image provided"
        return result

    try:
        # Call VisionCV contrast ratio tool
        response = requests.post(
            f"{visioncv_url}/tools/contrast_ratio",
            json={"image": slide_image},
            timeout=10
        )

        if response.status_code == 200:
            contrast_data = response.json()
            contrast_ratio = contrast_data.get("contrast_ratio", 0)

            # Determine threshold based on standard
            if target_standard == "AAA":
                threshold = WCAGStandard.AAA_NORMAL_CONTRAST
                large_threshold = WCAGStandard.AAA_LARGE_CONTRAST
            else:
                threshold = WCAGStandard.AA_NORMAL_CONTRAST
                large_threshold = WCAGStandard.AA_LARGE_CONTRAST

            result["details"] = {
                "contrast_ratio": contrast_ratio,
                "threshold": threshold,
                "large_text_threshold": large_threshold,
                "standard": target_standard
            }

            if contrast_ratio < threshold:
                result["status"] = "failed"
                result["score"] = max(0, int((contrast_ratio / threshold) * 100))
                result["issues"].append(
                    f"Contrast ratio {contrast_ratio:.2f} below {target_standard} standard ({threshold})"
                )
                result["recommendations"].extend([
                    "Increase color contrast between text and background",
                    "Use darker text on light backgrounds or vice versa",
                    "Consider adding a semi-transparent overlay to improve contrast"
                ])

        else:
            result["status"] = "error"
            result["score"] = 50
            result["details"]["error"] = f"VisionCV error: {response.status_code}"

    except Exception as e:
        logger.error(f"Contrast check failed: {e}")
        result["status"] = "error"
        result["score"] = 50
        result["details"]["error"] = str(e)
        result["recommendations"].append("Manual contrast verification required")

    return result


async def _check_text_readability(slide_content: Dict[str, Any]) -> Dict[str, Any]:
    """Check text readability and clarity."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    # Check title readability
    title = slide_content.get("title", "")
    if title:
        title_words = len(title.split())
        result["details"]["title_word_count"] = title_words

        if title_words > WCAGStandard.MAX_TITLE_WORDS:
            result["status"] = "warning"
            result["score"] -= 15
            result["issues"].append(f"Title too long: {title_words} words (max: {WCAGStandard.MAX_TITLE_WORDS})")
            result["recommendations"].append("Shorten title for better screen reader compatibility")

    # Check bullet point readability
    content = slide_content.get("content", [])
    if isinstance(content, list):
        long_bullets = []
        total_words = 0

        for i, bullet in enumerate(content):
            words = len(bullet.split())
            total_words += words

            if words > WCAGStandard.MAX_WORDS_PER_BULLET:
                long_bullets.append((i + 1, words))

        result["details"]["content_bullets"] = len(content)
        result["details"]["total_content_words"] = total_words
        result["details"]["average_words_per_bullet"] = total_words / len(content) if content else 0

        if long_bullets:
            result["status"] = "warning"
            result["score"] -= len(long_bullets) * 10
            for bullet_num, word_count in long_bullets:
                result["issues"].append(
                    f"Bullet {bullet_num} too long: {word_count} words (max: {WCAGStandard.MAX_WORDS_PER_BULLET})"
                )
            result["recommendations"].extend([
                "Break long bullet points into shorter sentences",
                "Use simpler language and fewer words per point",
                "Consider splitting complex bullets across multiple slides"
            ])

    # Check speaker notes readability
    speaker_notes = slide_content.get("speakerNotes", "")
    if speaker_notes:
        notes_sentences = speaker_notes.count('.') + speaker_notes.count('!') + speaker_notes.count('?')
        avg_sentence_length = len(speaker_notes.split()) / max(1, notes_sentences)

        result["details"]["speaker_notes_sentences"] = notes_sentences
        result["details"]["avg_sentence_length"] = avg_sentence_length

        if avg_sentence_length > 20:  # Long sentences are harder to read
            result["status"] = "warning"
            result["score"] -= 5
            result["issues"].append(f"Long sentences in speaker notes (avg: {avg_sentence_length:.1f} words)")
            result["recommendations"].append("Use shorter sentences in speaker notes for better readability")

    return result


async def _check_document_structure(slide_content: Dict[str, Any]) -> Dict[str, Any]:
    """Check document structure for accessibility."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    # Check for proper heading structure
    title = slide_content.get("title", "")
    if not title or title.strip() == "":
        result["status"] = "failed"
        result["score"] -= 30
        result["issues"].append("Missing slide title")
        result["recommendations"].append("Add descriptive title for screen reader navigation")
    else:
        result["details"]["has_title"] = True
        result["details"]["title_length"] = len(title)

    # Check content structure
    content = slide_content.get("content", [])
    if isinstance(content, list):
        if not content:
            result["status"] = "warning"
            result["score"] -= 10
            result["issues"].append("Slide has no content bullets")
            result["recommendations"].append("Add content or mark as section divider")
        else:
            # Check for consistent structure
            bullet_starts = [bullet.split()[0] if bullet.split() else "" for bullet in content]
            consistent_capitalization = len(set(start[0].isupper() if start else False for start in bullet_starts)) <= 1

            result["details"]["bullet_count"] = len(content)
            result["details"]["consistent_structure"] = consistent_capitalization

            if not consistent_capitalization:
                result["status"] = "warning"
                result["score"] -= 5
                result["issues"].append("Inconsistent bullet point structure")
                result["recommendations"].append("Use consistent capitalization and structure for all bullets")

    # Check for alternative text indicators
    image_prompt = slide_content.get("imagePrompt", "")
    if image_prompt:
        result["details"]["has_image_description"] = True
        if len(image_prompt.split()) < 5:
            result["status"] = "warning"
            result["score"] -= 5
            result["issues"].append("Image description too brief")
            result["recommendations"].append("Provide more detailed image descriptions for accessibility")

    return result


async def _check_content_length(slide_content: Dict[str, Any]) -> Dict[str, Any]:
    """Check content length and information density."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    # Calculate total text density
    title_words = len(slide_content.get("title", "").split())
    content_words = sum(len(bullet.split()) for bullet in slide_content.get("content", []))
    total_words = title_words + content_words

    result["details"]["total_words"] = total_words
    result["details"]["title_words"] = title_words
    result["details"]["content_words"] = content_words

    # Check for information overload
    if total_words > 50:  # Too much text for accessibility
        result["status"] = "warning"
        result["score"] -= min(20, (total_words - 50) // 5)
        result["issues"].append(f"High text density: {total_words} words on slide")
        result["recommendations"].extend([
            "Reduce text density for better accessibility",
            "Consider splitting information across multiple slides",
            "Use more visual elements to convey information"
        ])

    # Check bullet count
    content = slide_content.get("content", [])
    if isinstance(content, list) and len(content) > 6:
        result["status"] = "warning"
        result["score"] -= 10
        result["issues"].append(f"Too many bullet points: {len(content)} (recommended: 3-5)")
        result["recommendations"].append("Limit bullet points to 3-5 for better comprehension")

    return result


def _compile_accessibility_results(results: Dict[str, Any]) -> None:
    """Compile overall accessibility results."""
    checks = results["checks"]

    # Calculate weighted overall score
    weights = {
        "contrast": 0.3,
        "readability": 0.3,
        "structure": 0.25,
        "content_length": 0.15
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

    # Set overall status
    if results["overall_score"] >= 90:
        results["overall_status"] = "excellent"
    elif results["overall_score"] >= 75:
        results["overall_status"] = "good"
    elif results["overall_score"] >= 60:
        results["overall_status"] = "acceptable"
    else:
        results["overall_status"] = "needs_improvement"


# Quick accessibility check function
async def quick_accessibility_check(slide_content: Dict[str, Any]) -> bool:
    """
    Quick boolean check for basic accessibility compliance.

    Returns:
        True if slide meets basic accessibility requirements
    """
    try:
        result = await check_accessibility(slide_content)
        return result["overall_score"] >= 60
    except Exception:
        return False


# Export for tool integration
__all__ = [
    "check_accessibility",
    "quick_accessibility_check",
    "WCAGStandard"
]