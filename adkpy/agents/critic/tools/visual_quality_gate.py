"""Visual Quality Gate Tool for presentation slides.

This tool provides comprehensive visual quality assessment including:
- Accessibility compliance (WCAG)
- Brand consistency checks
- Visual clarity assessment
- Automatic fix suggestions
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import requests
from PIL import Image, ImageFilter, ImageEnhance
import cv2
import numpy as np
from colorthief import ColorThief
import io
import base64

logger = logging.getLogger(__name__)


class QualityThreshold(Enum):
    """Quality threshold levels."""
    EXCELLENT = 90
    GOOD = 75
    ACCEPTABLE = 60
    POOR = 40


@dataclass
class QualityScore:
    """Quality assessment score."""
    category: str
    score: int  # 0-100
    threshold: QualityThreshold
    issues: List[str]
    fixes: List[str]
    details: Dict[str, Any]


@dataclass
class VisualQualityAssessment:
    """Complete visual quality assessment result."""
    overall_score: int
    accessibility_score: QualityScore
    brand_consistency_score: QualityScore
    visual_clarity_score: QualityScore
    auto_fixes_available: bool
    requires_manual_review: bool
    summary: str


class VisualQualityGate:
    """Visual quality gate for presentation slides."""

    def __init__(self, visioncv_base_url: str = "http://visioncv:8091"):
        """Initialize quality gate with VisionCV integration."""
        self.visioncv_url = visioncv_base_url
        self.wcag_contrast_threshold = 4.5  # WCAG AA standard

    async def assess_slide_quality(
        self,
        slide_content: Dict[str, Any],
        slide_image: Optional[str] = None,
        brand_guidelines: Optional[Dict[str, Any]] = None
    ) -> VisualQualityAssessment:
        """
        Perform comprehensive quality assessment on a slide.

        Args:
            slide_content: Slide content dict with title, content, etc.
            slide_image: Base64 encoded slide image or URL
            brand_guidelines: Brand guidelines configuration

        Returns:
            Complete visual quality assessment
        """
        logger.info(f"Assessing quality for slide: {slide_content.get('title', 'Untitled')}")

        # Run all quality checks in parallel
        accessibility_score = await self._check_accessibility(slide_content, slide_image)
        brand_score = await self._check_brand_consistency(slide_content, slide_image, brand_guidelines)
        clarity_score = await self._check_visual_clarity(slide_content, slide_image)

        # Calculate overall score (weighted average)
        overall_score = int(
            accessibility_score.score * 0.4 +
            brand_score.score * 0.3 +
            clarity_score.score * 0.3
        )

        # Determine if auto-fixes are available
        auto_fixes_available = any([
            accessibility_score.fixes,
            brand_score.fixes,
            clarity_score.fixes
        ])

        # Determine if manual review is required
        requires_manual_review = overall_score < QualityThreshold.ACCEPTABLE.value

        # Generate summary
        summary = self._generate_assessment_summary(
            overall_score, accessibility_score, brand_score, clarity_score
        )

        return VisualQualityAssessment(
            overall_score=overall_score,
            accessibility_score=accessibility_score,
            brand_consistency_score=brand_score,
            visual_clarity_score=clarity_score,
            auto_fixes_available=auto_fixes_available,
            requires_manual_review=requires_manual_review,
            summary=summary
        )

    async def _check_accessibility(
        self,
        slide_content: Dict[str, Any],
        slide_image: Optional[str]
    ) -> QualityScore:
        """Check WCAG accessibility compliance."""
        issues = []
        fixes = []
        details = {}
        score = 100  # Start with perfect score and deduct

        # Check text contrast if image is available
        if slide_image:
            try:
                contrast_ratio = await self._get_contrast_ratio(slide_image)
                details["contrast_ratio"] = contrast_ratio

                if contrast_ratio < self.wcag_contrast_threshold:
                    issues.append(f"Low contrast ratio: {contrast_ratio:.2f} (minimum: {self.wcag_contrast_threshold})")
                    fixes.append("Apply contrast overlay or adjust background color")
                    score -= 30

            except Exception as e:
                logger.warning(f"Failed to check contrast: {e}")
                issues.append("Could not verify contrast ratio")
                score -= 10

        # Check text readability
        content_items = slide_content.get("content", [])
        if isinstance(content_items, list):
            for item in content_items:
                if len(item.split()) > 15:  # Too many words per bullet
                    issues.append("Bullet points too long for accessibility")
                    fixes.append("Break long bullet points into shorter chunks")
                    score -= 10

        # Check title length
        title = slide_content.get("title", "")
        if len(title.split()) > 8:
            issues.append("Title too long for screen readers")
            fixes.append("Shorten title to 6-8 words maximum")
            score -= 10

        # Determine threshold
        if score >= QualityThreshold.EXCELLENT.value:
            threshold = QualityThreshold.EXCELLENT
        elif score >= QualityThreshold.GOOD.value:
            threshold = QualityThreshold.GOOD
        elif score >= QualityThreshold.ACCEPTABLE.value:
            threshold = QualityThreshold.ACCEPTABLE
        else:
            threshold = QualityThreshold.POOR

        return QualityScore(
            category="accessibility",
            score=max(0, score),
            threshold=threshold,
            issues=issues,
            fixes=fixes,
            details=details
        )

    async def _check_brand_consistency(
        self,
        slide_content: Dict[str, Any],
        slide_image: Optional[str],
        brand_guidelines: Optional[Dict[str, Any]]
    ) -> QualityScore:
        """Check brand consistency compliance."""
        issues = []
        fixes = []
        details = {}
        score = 100

        # If no brand guidelines provided, use basic checks
        if not brand_guidelines:
            brand_guidelines = {
                "primary_colors": ["#192940", "#73BF50", "#556273"],  # PresentationPro colors
                "fonts": ["Montserrat", "Roboto"],
                "tone": "professional"
            }

        # Check color consistency if image available
        if slide_image:
            try:
                dominant_colors = await self._extract_dominant_colors(slide_image)
                details["dominant_colors"] = dominant_colors

                brand_colors = brand_guidelines.get("primary_colors", [])
                if brand_colors and not self._colors_match_brand(dominant_colors, brand_colors):
                    issues.append("Slide colors don't match brand guidelines")
                    fixes.append("Apply brand color palette")
                    score -= 20

            except Exception as e:
                logger.warning(f"Failed to check brand colors: {e}")

        # Check tone consistency
        tone = slide_content.get("tone", "").lower()
        expected_tone = brand_guidelines.get("tone", "professional").lower()

        if tone and tone != expected_tone:
            issues.append(f"Tone mismatch: expected {expected_tone}, got {tone}")
            fixes.append(f"Adjust content tone to match {expected_tone} style")
            score -= 15

        # Check content style consistency
        content_items = slide_content.get("content", [])
        if isinstance(content_items, list) and len(content_items) > 1:
            # Check if all bullets start consistently (same case, punctuation)
            first_words = [item.split()[0] if item.split() else "" for item in content_items]
            if len(set(word[0].isupper() if word else False for word in first_words)) > 1:
                issues.append("Inconsistent bullet point capitalization")
                fixes.append("Standardize bullet point capitalization")
                score -= 10

        # Determine threshold
        if score >= QualityThreshold.EXCELLENT.value:
            threshold = QualityThreshold.EXCELLENT
        elif score >= QualityThreshold.GOOD.value:
            threshold = QualityThreshold.GOOD
        elif score >= QualityThreshold.ACCEPTABLE.value:
            threshold = QualityThreshold.ACCEPTABLE
        else:
            threshold = QualityThreshold.POOR

        return QualityScore(
            category="brand_consistency",
            score=max(0, score),
            threshold=threshold,
            issues=issues,
            fixes=fixes,
            details=details
        )

    async def _check_visual_clarity(
        self,
        slide_content: Dict[str, Any],
        slide_image: Optional[str]
    ) -> QualityScore:
        """Check visual clarity (blur, noise, readability)."""
        issues = []
        fixes = []
        details = {}
        score = 100

        if slide_image:
            try:
                # Check for blur
                blur_score = await self._detect_blur(slide_image)
                details["blur_score"] = blur_score

                if blur_score < 50:  # Threshold for acceptable sharpness
                    issues.append(f"Image appears blurry (sharpness: {blur_score})")
                    fixes.append("Apply image sharpening filter")
                    score -= 25

                # Check for noise
                noise_score = await self._detect_noise(slide_image)
                details["noise_score"] = noise_score

                if noise_score > 70:  # Threshold for acceptable noise
                    issues.append(f"High image noise detected (noise: {noise_score})")
                    fixes.append("Apply noise reduction filter")
                    score -= 20

            except Exception as e:
                logger.warning(f"Failed to check visual clarity: {e}")
                issues.append("Could not analyze image quality")
                score -= 10

        # Check text clarity and density
        content_items = slide_content.get("content", [])
        if isinstance(content_items, list):
            total_words = sum(len(item.split()) for item in content_items)
            if total_words > 40:  # Too much text on slide
                issues.append("Slide contains too much text")
                fixes.append("Reduce text density or split into multiple slides")
                score -= 20

        # Check speaker notes clarity
        speaker_notes = slide_content.get("speakerNotes", "")
        if speaker_notes and len(speaker_notes.split()) < 20:
            issues.append("Speaker notes too brief for presenter guidance")
            fixes.append("Expand speaker notes with more detail")
            score -= 10

        # Determine threshold
        if score >= QualityThreshold.EXCELLENT.value:
            threshold = QualityThreshold.EXCELLENT
        elif score >= QualityThreshold.GOOD.value:
            threshold = QualityThreshold.GOOD
        elif score >= QualityThreshold.ACCEPTABLE.value:
            threshold = QualityThreshold.ACCEPTABLE
        else:
            threshold = QualityThreshold.POOR

        return QualityScore(
            category="visual_clarity",
            score=max(0, score),
            threshold=threshold,
            issues=issues,
            fixes=fixes,
            details=details
        )

    async def _get_contrast_ratio(self, slide_image: str) -> float:
        """Get contrast ratio using VisionCV service."""
        try:
            response = requests.post(
                f"{self.visioncv_url}/tools/contrast_ratio",
                json={"image": slide_image},
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("contrast_ratio", 0.0)
        except Exception as e:
            logger.error(f"VisionCV contrast check failed: {e}")

        # Fallback: basic contrast estimation
        return await self._estimate_contrast_ratio(slide_image)

    async def _detect_blur(self, slide_image: str) -> float:
        """Detect blur in slide image using VisionCV service."""
        try:
            response = requests.post(
                f"{self.visioncv_url}/tools/blur_detection",
                json={"image": slide_image},
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("sharpness_score", 0.0)
        except Exception as e:
            logger.error(f"VisionCV blur detection failed: {e}")

        # Fallback: basic blur detection
        return await self._estimate_blur(slide_image)

    async def _detect_noise(self, slide_image: str) -> float:
        """Detect noise in slide image using VisionCV service."""
        try:
            response = requests.post(
                f"{self.visioncv_url}/tools/noise_detection",
                json={"image": slide_image},
                timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("noise_score", 0.0)
        except Exception as e:
            logger.error(f"VisionCV noise detection failed: {e}")

        # Fallback: return moderate noise score
        return 50.0

    async def _extract_dominant_colors(self, slide_image: str) -> List[str]:
        """Extract dominant colors from slide image."""
        try:
            # Decode base64 image
            if slide_image.startswith('data:'):
                slide_image = slide_image.split(',')[1]

            image_data = base64.b64decode(slide_image)
            image = Image.open(io.BytesIO(image_data))

            # Use ColorThief to get dominant colors
            color_thief = ColorThief(io.BytesIO(image_data))
            palette = color_thief.get_palette(color_count=5)

            # Convert RGB to hex
            hex_colors = [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in palette]
            return hex_colors

        except Exception as e:
            logger.error(f"Failed to extract colors: {e}")
            return []

    def _colors_match_brand(self, slide_colors: List[str], brand_colors: List[str]) -> bool:
        """Check if slide colors match brand guidelines."""
        if not slide_colors or not brand_colors:
            return True  # Can't validate without data

        # Convert hex colors to RGB for similarity comparison
        def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        def color_distance(c1: Tuple[int, int, int], c2: Tuple[int, int, int]) -> float:
            return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

        # Check if any slide color is similar to brand colors (threshold: 50)
        for slide_color in slide_colors[:3]:  # Check top 3 dominant colors
            try:
                slide_rgb = hex_to_rgb(slide_color)
                for brand_color in brand_colors:
                    brand_rgb = hex_to_rgb(brand_color)
                    if color_distance(slide_rgb, brand_rgb) < 50:
                        return True
            except ValueError:
                continue

        return False

    async def _estimate_contrast_ratio(self, slide_image: str) -> float:
        """Fallback contrast ratio estimation."""
        try:
            # Basic luminance difference calculation
            if slide_image.startswith('data:'):
                slide_image = slide_image.split(',')[1]

            image_data = base64.b64decode(slide_image)
            image = Image.open(io.BytesIO(image_data)).convert('L')  # Grayscale

            # Get histogram
            histogram = image.histogram()

            # Find darkest and lightest regions
            total_pixels = sum(histogram)
            dark_pixels = sum(histogram[:85])  # Dark third
            light_pixels = sum(histogram[170:])  # Light third

            # Estimate contrast ratio
            if dark_pixels > 0 and light_pixels > 0:
                ratio = (light_pixels / total_pixels) / (dark_pixels / total_pixels)
                return min(ratio, 21.0)  # Cap at WCAG maximum

            return 3.0  # Conservative estimate

        except Exception:
            return 3.0  # Conservative fallback

    async def _estimate_blur(self, slide_image: str) -> float:
        """Fallback blur estimation using Laplacian variance."""
        try:
            if slide_image.startswith('data:'):
                slide_image = slide_image.split(',')[1]

            image_data = base64.b64decode(slide_image)
            image = Image.open(io.BytesIO(image_data))

            # Convert PIL to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

            # Calculate Laplacian variance (sharpness measure)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

            # Normalize to 0-100 scale
            sharpness_score = min(laplacian_var / 10, 100)
            return sharpness_score

        except Exception:
            return 50.0  # Moderate sharpness estimate

    def _generate_assessment_summary(
        self,
        overall_score: int,
        accessibility_score: QualityScore,
        brand_score: QualityScore,
        clarity_score: QualityScore
    ) -> str:
        """Generate human-readable assessment summary."""
        if overall_score >= QualityThreshold.EXCELLENT.value:
            quality_level = "excellent"
        elif overall_score >= QualityThreshold.GOOD.value:
            quality_level = "good"
        elif overall_score >= QualityThreshold.ACCEPTABLE.value:
            quality_level = "acceptable"
        else:
            quality_level = "poor"

        issues_count = (
            len(accessibility_score.issues) +
            len(brand_score.issues) +
            len(clarity_score.issues)
        )

        fixes_count = (
            len(accessibility_score.fixes) +
            len(brand_score.fixes) +
            len(clarity_score.fixes)
        )

        summary = f"Slide quality is {quality_level} (score: {overall_score}/100). "

        if issues_count > 0:
            summary += f"Found {issues_count} issue(s). "

        if fixes_count > 0:
            summary += f"{fixes_count} automatic fix(es) available."
        else:
            summary += "No fixes required."

        return summary


# Tool function for ADK integration
async def assess_visual_quality(
    slide_content: Dict[str, Any],
    slide_image: Optional[str] = None,
    brand_guidelines: Optional[Dict[str, Any]] = None,
    visioncv_url: str = "http://visioncv:8091"
) -> Dict[str, Any]:
    """
    Assess visual quality of a presentation slide.

    Args:
        slide_content: Slide content dictionary
        slide_image: Optional base64 encoded slide image
        brand_guidelines: Optional brand guidelines configuration
        visioncv_url: VisionCV service URL

    Returns:
        Quality assessment results as dictionary
    """
    quality_gate = VisualQualityGate(visioncv_url)
    assessment = await quality_gate.assess_slide_quality(
        slide_content, slide_image, brand_guidelines
    )

    # Convert to dictionary for JSON serialization
    return {
        "overall_score": assessment.overall_score,
        "accessibility": {
            "score": assessment.accessibility_score.score,
            "threshold": assessment.accessibility_score.threshold.name,
            "issues": assessment.accessibility_score.issues,
            "fixes": assessment.accessibility_score.fixes,
            "details": assessment.accessibility_score.details
        },
        "brand_consistency": {
            "score": assessment.brand_consistency_score.score,
            "threshold": assessment.brand_consistency_score.threshold.name,
            "issues": assessment.brand_consistency_score.issues,
            "fixes": assessment.brand_consistency_score.fixes,
            "details": assessment.brand_consistency_score.details
        },
        "visual_clarity": {
            "score": assessment.visual_clarity_score.score,
            "threshold": assessment.visual_clarity_score.threshold.name,
            "issues": assessment.visual_clarity_score.issues,
            "fixes": assessment.visual_clarity_score.fixes,
            "details": assessment.visual_clarity_score.details
        },
        "auto_fixes_available": assessment.auto_fixes_available,
        "requires_manual_review": assessment.requires_manual_review,
        "summary": assessment.summary
    }


# Auto-fix functions
async def apply_auto_fixes(
    slide_content: Dict[str, Any],
    quality_assessment: Dict[str, Any],
    slide_image: Optional[str] = None
) -> Dict[str, Any]:
    """
    Apply automatic fixes based on quality assessment.

    Args:
        slide_content: Original slide content
        quality_assessment: Quality assessment results
        slide_image: Optional slide image for visual fixes

    Returns:
        Fixed slide content and metadata
    """
    fixed_content = slide_content.copy()
    applied_fixes = []

    # Apply accessibility fixes
    accessibility_fixes = quality_assessment.get("accessibility", {}).get("fixes", [])
    for fix in accessibility_fixes:
        if "shorten title" in fix.lower():
            title = fixed_content.get("title", "")
            if len(title.split()) > 6:
                words = title.split()[:6]
                fixed_content["title"] = " ".join(words)
                applied_fixes.append("Shortened title to 6 words")

        elif "break long bullet" in fix.lower():
            content = fixed_content.get("content", [])
            if isinstance(content, list):
                new_content = []
                for item in content:
                    if len(item.split()) > 12:
                        # Split long bullets at natural break points
                        words = item.split()
                        mid_point = len(words) // 2
                        new_content.extend([
                            " ".join(words[:mid_point]),
                            " ".join(words[mid_point:])
                        ])
                        applied_fixes.append(f"Split long bullet point: {item[:30]}...")
                    else:
                        new_content.append(item)
                fixed_content["content"] = new_content

    # Apply brand consistency fixes
    brand_fixes = quality_assessment.get("brand_consistency", {}).get("fixes", [])
    for fix in brand_fixes:
        if "standardize bullet" in fix.lower():
            content = fixed_content.get("content", [])
            if isinstance(content, list) and content:
                # Capitalize first word of each bullet
                fixed_content["content"] = [
                    item[0].upper() + item[1:] if item else item
                    for item in content
                ]
                applied_fixes.append("Standardized bullet point capitalization")

    # Apply clarity fixes
    clarity_fixes = quality_assessment.get("visual_clarity", {}).get("fixes", [])
    for fix in clarity_fixes:
        if "reduce text density" in fix.lower():
            content = fixed_content.get("content", [])
            if isinstance(content, list) and len(content) > 4:
                # Keep only the most important points
                fixed_content["content"] = content[:4]
                applied_fixes.append("Reduced bullet points to improve clarity")

        elif "expand speaker notes" in fix.lower():
            speaker_notes = fixed_content.get("speakerNotes", "")
            if len(speaker_notes.split()) < 20:
                # Add basic expansion
                title = fixed_content.get("title", "")
                expanded_notes = f"{speaker_notes} Elaborate on {title.lower()} by providing specific examples and context for the audience."
                fixed_content["speakerNotes"] = expanded_notes
                applied_fixes.append("Expanded speaker notes")

    return {
        "fixed_content": fixed_content,
        "applied_fixes": applied_fixes,
        "fix_count": len(applied_fixes)
    }


# Export for ADK tools integration
__all__ = [
    "VisualQualityGate",
    "VisualQualityAssessment",
    "QualityScore",
    "QualityThreshold",
    "assess_visual_quality",
    "apply_auto_fixes"
]