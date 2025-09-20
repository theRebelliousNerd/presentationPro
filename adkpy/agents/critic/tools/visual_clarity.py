"""Visual clarity checker for presentation slides.

This tool analyzes slides for visual clarity issues including:
- Image blur and sharpness
- Noise and artifacts
- Text readability
- Information density
- Visual balance and composition
"""

import logging
from typing import Dict, List, Any, Optional
import requests
import json
import base64
import io
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageStat

logger = logging.getLogger(__name__)


class ClarityThresholds:
    """Visual clarity thresholds and standards."""

    # Sharpness thresholds (0-100 scale)
    EXCELLENT_SHARPNESS = 80
    GOOD_SHARPNESS = 60
    ACCEPTABLE_SHARPNESS = 40

    # Noise thresholds (0-100 scale, lower is better)
    EXCELLENT_NOISE = 20
    GOOD_NOISE = 40
    ACCEPTABLE_NOISE = 60

    # Text density thresholds
    MAX_TOTAL_WORDS = 50
    MAX_BULLETS = 5
    MAX_WORDS_PER_BULLET = 12

    # Image quality thresholds
    MIN_CONTRAST = 50
    MIN_BRIGHTNESS = 30
    MAX_BRIGHTNESS = 230


async def check_visual_clarity(
    slide_content: Dict[str, Any],
    slide_image: Optional[str] = None,
    visioncv_url: str = "http://visioncv:8091"
) -> Dict[str, Any]:
    """
    Check slide visual clarity and readability.

    Args:
        slide_content: Slide content dictionary
        slide_image: Optional base64 encoded slide image
        visioncv_url: VisionCV service URL

    Returns:
        Visual clarity assessment results
    """
    logger.info(f"Checking visual clarity for slide: {slide_content.get('title', 'Untitled')}")

    results = {
        "overall_score": 100,
        "clarity_level": "excellent",
        "issues": [],
        "recommendations": [],
        "checks": {
            "image_sharpness": {"status": "pending", "score": 100, "details": {}},
            "noise_level": {"status": "pending", "score": 100, "details": {}},
            "text_density": {"status": "pending", "score": 100, "details": {}},
            "content_clarity": {"status": "pending", "score": 100, "details": {}},
            "visual_balance": {"status": "pending", "score": 100, "details": {}}
        }
    }

    # Check image sharpness
    sharpness_result = await _check_image_sharpness(slide_image, visioncv_url)
    results["checks"]["image_sharpness"] = sharpness_result

    # Check noise level
    noise_result = await _check_noise_level(slide_image, visioncv_url)
    results["checks"]["noise_level"] = noise_result

    # Check text density and readability
    density_result = await _check_text_density(slide_content)
    results["checks"]["text_density"] = density_result

    # Check content clarity
    content_result = await _check_content_clarity(slide_content)
    results["checks"]["content_clarity"] = content_result

    # Check visual balance
    balance_result = await _check_visual_balance(slide_content, slide_image)
    results["checks"]["visual_balance"] = balance_result

    # Compile overall results
    _compile_clarity_results(results)

    return results


async def _check_image_sharpness(
    slide_image: Optional[str],
    visioncv_url: str
) -> Dict[str, Any]:
    """Check image sharpness and focus quality."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    if not slide_image:
        result["status"] = "skipped"
        result["details"]["reason"] = "No image provided for sharpness analysis"
        return result

    try:
        # Try VisionCV blur detection first
        sharpness_score = await _get_visioncv_sharpness(slide_image, visioncv_url)

        if sharpness_score is None:
            # Fallback to local analysis
            sharpness_score = await _analyze_local_sharpness(slide_image)

        result["details"]["sharpness_score"] = sharpness_score

        if sharpness_score >= ClarityThresholds.EXCELLENT_SHARPNESS:
            result["status"] = "excellent"
        elif sharpness_score >= ClarityThresholds.GOOD_SHARPNESS:
            result["status"] = "good"
        elif sharpness_score >= ClarityThresholds.ACCEPTABLE_SHARPNESS:
            result["status"] = "acceptable"
            result["score"] = 70
            result["issues"].append(f"Image sharpness below optimal ({sharpness_score:.1f})")
            result["recommendations"].append("Consider applying sharpening filter")
        else:
            result["status"] = "poor"
            result["score"] = max(20, int(sharpness_score))
            result["issues"].append(f"Image appears blurry (sharpness: {sharpness_score:.1f})")
            result["recommendations"].extend([
                "Apply image sharpening filter",
                "Use higher resolution source images",
                "Check image compression settings"
            ])

    except Exception as e:
        logger.error(f"Sharpness check failed: {e}")
        result["status"] = "error"
        result["score"] = 50
        result["details"]["error"] = str(e)

    return result


async def _check_noise_level(
    slide_image: Optional[str],
    visioncv_url: str
) -> Dict[str, Any]:
    """Check image noise and artifacts."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    if not slide_image:
        result["status"] = "skipped"
        result["details"]["reason"] = "No image provided for noise analysis"
        return result

    try:
        # Try VisionCV noise detection first
        noise_score = await _get_visioncv_noise(slide_image, visioncv_url)

        if noise_score is None:
            # Fallback to local analysis
            noise_score = await _analyze_local_noise(slide_image)

        result["details"]["noise_score"] = noise_score

        if noise_score <= ClarityThresholds.EXCELLENT_NOISE:
            result["status"] = "excellent"
        elif noise_score <= ClarityThresholds.GOOD_NOISE:
            result["status"] = "good"
        elif noise_score <= ClarityThresholds.ACCEPTABLE_NOISE:
            result["status"] = "acceptable"
            result["score"] = 70
            result["issues"].append(f"Moderate image noise detected ({noise_score:.1f})")
            result["recommendations"].append("Consider applying noise reduction")
        else:
            result["status"] = "poor"
            result["score"] = max(20, 100 - int(noise_score))
            result["issues"].append(f"High image noise detected ({noise_score:.1f})")
            result["recommendations"].extend([
                "Apply noise reduction filter",
                "Use higher quality source images",
                "Check image compression artifacts"
            ])

    except Exception as e:
        logger.error(f"Noise check failed: {e}")
        result["status"] = "error"
        result["score"] = 50
        result["details"]["error"] = str(e)

    return result


async def _check_text_density(slide_content: Dict[str, Any]) -> Dict[str, Any]:
    """Check text density and information overload."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    # Count words in different sections
    title_words = len(slide_content.get("title", "").split())
    content = slide_content.get("content", [])
    content_words = sum(len(bullet.split()) for bullet in content) if isinstance(content, list) else 0
    total_words = title_words + content_words

    result["details"]["title_words"] = title_words
    result["details"]["content_words"] = content_words
    result["details"]["total_words"] = total_words
    result["details"]["bullet_count"] = len(content) if isinstance(content, list) else 0

    # Check total word density
    if total_words > ClarityThresholds.MAX_TOTAL_WORDS:
        excess_words = total_words - ClarityThresholds.MAX_TOTAL_WORDS
        score_penalty = min(30, excess_words * 2)
        result["score"] -= score_penalty
        result["status"] = "warning" if score_penalty < 20 else "poor"
        result["issues"].append(f"High text density: {total_words} words (recommended: ≤{ClarityThresholds.MAX_TOTAL_WORDS})")
        result["recommendations"].extend([
            "Reduce text content for better readability",
            "Consider splitting content across multiple slides",
            "Use more visual elements to convey information"
        ])

    # Check bullet count
    if isinstance(content, list) and len(content) > ClarityThresholds.MAX_BULLETS:
        result["score"] -= 10
        result["status"] = "warning"
        result["issues"].append(f"Too many bullet points: {len(content)} (recommended: ≤{ClarityThresholds.MAX_BULLETS})")
        result["recommendations"].append("Limit bullet points to 3-5 key items")

    # Check individual bullet length
    if isinstance(content, list):
        long_bullets = []
        for i, bullet in enumerate(content):
            words = len(bullet.split())
            if words > ClarityThresholds.MAX_WORDS_PER_BULLET:
                long_bullets.append((i + 1, words))

        if long_bullets:
            result["score"] -= len(long_bullets) * 5
            result["status"] = "warning"
            for bullet_num, word_count in long_bullets:
                result["issues"].append(f"Bullet {bullet_num} too long: {word_count} words")
            result["recommendations"].append("Shorten bullet points for better clarity")

    return result


async def _check_content_clarity(slide_content: Dict[str, Any]) -> Dict[str, Any]:
    """Check content clarity and comprehension."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    # Check title clarity
    title = slide_content.get("title", "")
    if title:
        title_clarity = _analyze_title_clarity(title)
        result["details"]["title_clarity"] = title_clarity

        if title_clarity < 70:
            result["score"] -= 15
            result["status"] = "warning"
            result["issues"].append("Title could be clearer or more specific")
            result["recommendations"].append("Use more descriptive and specific title")

    # Check content clarity
    content = slide_content.get("content", [])
    if isinstance(content, list) and content:
        content_clarity = _analyze_content_clarity(content)
        result["details"]["content_clarity"] = content_clarity

        if content_clarity < 70:
            result["score"] -= 10
            result["status"] = "warning"
            result["issues"].append("Content could be clearer or more specific")
            result["recommendations"].extend([
                "Use more specific language",
                "Avoid jargon and complex terms",
                "Structure information more clearly"
            ])

    # Check speaker notes clarity
    speaker_notes = slide_content.get("speakerNotes", "")
    if speaker_notes:
        notes_clarity = _analyze_speaker_notes_clarity(speaker_notes)
        result["details"]["notes_clarity"] = notes_clarity

        if notes_clarity < 70:
            result["score"] -= 5
            result["status"] = "warning"
            result["issues"].append("Speaker notes could be clearer")
            result["recommendations"].append("Improve speaker notes clarity and detail")
    elif not speaker_notes and content:
        result["score"] -= 10
        result["status"] = "warning"
        result["issues"].append("Missing speaker notes reduces presenter clarity")
        result["recommendations"].append("Add detailed speaker notes for better presentation")

    return result


async def _check_visual_balance(
    slide_content: Dict[str, Any],
    slide_image: Optional[str]
) -> Dict[str, Any]:
    """Check visual balance and composition."""
    result = {
        "status": "passed",
        "score": 100,
        "details": {},
        "issues": [],
        "recommendations": []
    }

    # Check content balance
    title = slide_content.get("title", "")
    content = slide_content.get("content", [])
    image_prompt = slide_content.get("imagePrompt", "")

    result["details"]["has_title"] = bool(title)
    result["details"]["has_content"] = bool(content)
    result["details"]["has_image"] = bool(image_prompt)

    # Check for missing elements
    if not title:
        result["score"] -= 20
        result["status"] = "warning"
        result["issues"].append("Missing title affects visual hierarchy")
        result["recommendations"].append("Add descriptive title for better visual balance")

    if not content and not image_prompt:
        result["score"] -= 30
        result["status"] = "poor"
        result["issues"].append("Slide lacks both content and visuals")
        result["recommendations"].append("Add content or visual elements")

    # Check content distribution
    if isinstance(content, list):
        if len(content) == 1:
            result["score"] -= 5
            result["issues"].append("Single bullet point may look unbalanced")
            result["recommendations"].append("Consider expanding to 2-3 points or using different format")

    # Analyze image if available
    if slide_image:
        try:
            image_balance = await _analyze_image_balance(slide_image)
            result["details"]["image_balance"] = image_balance

            if image_balance < 70:
                result["score"] -= 10
                result["status"] = "warning"
                result["issues"].append("Image composition could be better balanced")
                result["recommendations"].append("Consider adjusting image composition or layout")

        except Exception as e:
            logger.warning(f"Image balance analysis failed: {e}")

    return result


# Helper functions for VisionCV integration

async def _get_visioncv_sharpness(slide_image: str, visioncv_url: str) -> Optional[float]:
    """Get sharpness score from VisionCV service."""
    try:
        response = requests.post(
            f"{visioncv_url}/tools/blur_detection",
            json={"image": slide_image},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            return result.get("sharpness_score", None)
    except Exception as e:
        logger.warning(f"VisionCV sharpness check failed: {e}")
    return None


async def _get_visioncv_noise(slide_image: str, visioncv_url: str) -> Optional[float]:
    """Get noise score from VisionCV service."""
    try:
        response = requests.post(
            f"{visioncv_url}/tools/noise_detection",
            json={"image": slide_image},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            return result.get("noise_score", None)
    except Exception as e:
        logger.warning(f"VisionCV noise check failed: {e}")
    return None


# Local analysis fallbacks

async def _analyze_local_sharpness(slide_image: str) -> float:
    """Analyze image sharpness locally using Laplacian variance."""
    try:
        # Decode base64 image
        if slide_image.startswith('data:'):
            slide_image = slide_image.split(',')[1]

        image_data = base64.b64decode(slide_image)
        image = Image.open(io.BytesIO(image_data))

        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # Calculate Laplacian variance (sharpness measure)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Normalize to 0-100 scale
        sharpness_score = min(laplacian_var / 10, 100)
        return sharpness_score

    except Exception as e:
        logger.error(f"Local sharpness analysis failed: {e}")
        return 50.0


async def _analyze_local_noise(slide_image: str) -> float:
    """Analyze image noise locally."""
    try:
        # Decode base64 image
        if slide_image.startswith('data:'):
            slide_image = slide_image.split(',')[1]

        image_data = base64.b64decode(slide_image)
        image = Image.open(io.BytesIO(image_data))

        # Convert to grayscale for noise analysis
        gray_image = image.convert('L')

        # Calculate image statistics
        stat = ImageStat.Stat(gray_image)

        # Use standard deviation as noise indicator
        # Higher std dev typically indicates more noise
        noise_score = min(stat.stddev[0] / 2.55, 100)  # Normalize to 0-100

        return noise_score

    except Exception as e:
        logger.error(f"Local noise analysis failed: {e}")
        return 30.0  # Conservative noise estimate


async def _analyze_image_balance(slide_image: str) -> float:
    """Analyze image visual balance and composition."""
    try:
        # Decode base64 image
        if slide_image.startswith('data:'):
            slide_image = slide_image.split(',')[1]

        image_data = base64.b64decode(slide_image)
        image = Image.open(io.BytesIO(image_data))

        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

        # Calculate image moments for balance analysis
        moments = cv2.moments(gray)

        if moments['m00'] != 0:
            # Calculate centroid
            cx = int(moments['m10'] / moments['m00'])
            cy = int(moments['m01'] / moments['m00'])

            # Calculate how close centroid is to image center
            h, w = gray.shape
            center_x, center_y = w // 2, h // 2

            # Distance from center (normalized)
            distance = ((cx - center_x) ** 2 + (cy - center_y) ** 2) ** 0.5
            max_distance = (w ** 2 + h ** 2) ** 0.5 / 2

            balance_score = 100 - (distance / max_distance * 100)
            return max(0, balance_score)

        return 50.0  # Neutral balance if can't calculate

    except Exception as e:
        logger.error(f"Image balance analysis failed: {e}")
        return 70.0  # Assume reasonable balance


# Content analysis helpers

def _analyze_title_clarity(title: str) -> float:
    """Analyze title clarity and specificity."""
    if not title:
        return 0

    score = 100

    # Check for vague words
    vague_words = ["things", "stuff", "various", "some", "many", "overview", "introduction"]
    for word in vague_words:
        if word.lower() in title.lower():
            score -= 15

    # Check for specificity indicators
    specific_indicators = ["how", "what", "why", "when", "specific", "key", "top", "best"]
    for indicator in specific_indicators:
        if indicator.lower() in title.lower():
            score += 10

    # Penalize very short or very long titles
    words = len(title.split())
    if words < 2:
        score -= 20
    elif words > 8:
        score -= 10

    return max(0, min(100, score))


def _analyze_content_clarity(content: List[str]) -> float:
    """Analyze content clarity and specificity."""
    if not content:
        return 100

    total_score = 0

    for bullet in content:
        bullet_score = 100

        # Check for vague language
        vague_phrases = ["and more", "etc", "various", "some", "many", "things", "stuff"]
        for phrase in vague_phrases:
            if phrase.lower() in bullet.lower():
                bullet_score -= 20

        # Check for specific language
        specific_indicators = ["exactly", "specifically", "precisely", "clearly", "direct"]
        for indicator in specific_indicators:
            if indicator.lower() in bullet.lower():
                bullet_score += 10

        # Check for action verbs (clarity indicator)
        action_verbs = ["create", "develop", "implement", "analyze", "design", "build", "improve"]
        words = bullet.lower().split()
        if any(verb in words for verb in action_verbs):
            bullet_score += 5

        total_score += bullet_score

    return total_score / len(content)


def _analyze_speaker_notes_clarity(speaker_notes: str) -> float:
    """Analyze speaker notes clarity and usefulness."""
    if not speaker_notes:
        return 0

    score = 100

    # Check length adequacy
    words = len(speaker_notes.split())
    if words < 10:
        score -= 30
    elif words < 20:
        score -= 15

    # Check for specific guidance
    guidance_indicators = ["explain", "emphasize", "elaborate", "example", "demonstrate"]
    for indicator in guidance_indicators:
        if indicator.lower() in speaker_notes.lower():
            score += 10

    # Check for vague content
    if "..." in speaker_notes or "etc" in speaker_notes.lower():
        score -= 15

    return max(0, min(100, score))


def _compile_clarity_results(results: Dict[str, Any]) -> None:
    """Compile overall clarity results."""
    checks = results["checks"]

    # Calculate weighted overall score
    weights = {
        "image_sharpness": 0.25,
        "noise_level": 0.20,
        "text_density": 0.25,
        "content_clarity": 0.20,
        "visual_balance": 0.10
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

    # Set clarity level
    if results["overall_score"] >= 90:
        results["clarity_level"] = "excellent"
    elif results["overall_score"] >= 75:
        results["clarity_level"] = "good"
    elif results["overall_score"] >= 60:
        results["clarity_level"] = "acceptable"
    else:
        results["clarity_level"] = "needs_improvement"


# Quick clarity check function
async def quick_clarity_check(slide_content: Dict[str, Any]) -> bool:
    """
    Quick boolean check for basic clarity compliance.

    Returns:
        True if slide meets basic clarity requirements
    """
    try:
        result = await check_visual_clarity(slide_content)
        return result["overall_score"] >= 60
    except Exception:
        return False


# Auto-fix function for clarity issues
async def apply_clarity_fixes(slide_content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply automatic fixes for clarity issues.

    Args:
        slide_content: Original slide content

    Returns:
        Fixed slide content with applied changes
    """
    fixed_content = slide_content.copy()
    applied_fixes = []

    # Fix text density issues
    content = fixed_content.get("content", [])
    if isinstance(content, list):
        # Limit to max bullets
        if len(content) > ClarityThresholds.MAX_BULLETS:
            fixed_content["content"] = content[:ClarityThresholds.MAX_BULLETS]
            applied_fixes.append(f"Reduced bullets from {len(content)} to {ClarityThresholds.MAX_BULLETS}")

        # Shorten long bullets
        new_content = []
        for bullet in fixed_content.get("content", []):
            if len(bullet.split()) > ClarityThresholds.MAX_WORDS_PER_BULLET:
                words = bullet.split()[:ClarityThresholds.MAX_WORDS_PER_BULLET]
                new_content.append(" ".join(words))
                applied_fixes.append(f"Shortened bullet: {bullet[:30]}...")
            else:
                new_content.append(bullet)
        fixed_content["content"] = new_content

    # Fix title clarity
    title = fixed_content.get("title", "")
    if title:
        # Remove vague words
        vague_words = ["things", "stuff", "various", "overview"]
        title_words = title.split()
        filtered_words = [word for word in title_words if word.lower() not in vague_words]

        if len(filtered_words) != len(title_words):
            fixed_content["title"] = " ".join(filtered_words)
            applied_fixes.append("Removed vague words from title")

    # Add speaker notes if missing
    if not fixed_content.get("speakerNotes") and content:
        title = fixed_content.get("title", "")
        auto_notes = f"Present {title.lower()} by covering each key point systematically. Provide examples and context for audience understanding."
        fixed_content["speakerNotes"] = auto_notes
        applied_fixes.append("Added basic speaker notes")

    return {
        "fixed_content": fixed_content,
        "applied_fixes": applied_fixes,
        "fix_count": len(applied_fixes)
    }


# Export for tool integration
__all__ = [
    "check_visual_clarity",
    "quick_clarity_check",
    "apply_clarity_fixes",
    "ClarityThresholds"
]