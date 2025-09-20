"""Auto-fix mechanisms for visual and content issues.

This tool provides automatic fixes for common presentation issues:
- Text content optimization
- Image enhancement and correction
- Accessibility improvements
- Brand compliance adjustments
- Visual clarity enhancements
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import base64
import io
import json
import requests
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class AutoFixEngine:
    """Engine for applying automatic fixes to presentation slides."""

    def __init__(self, visioncv_url: str = "http://visioncv:8091"):
        """Initialize auto-fix engine."""
        self.visioncv_url = visioncv_url

    async def apply_comprehensive_fixes(
        self,
        slide_content: Dict[str, Any],
        quality_assessment: Dict[str, Any],
        slide_image: Optional[str] = None,
        fix_threshold: int = 70
    ) -> Dict[str, Any]:
        """
        Apply comprehensive automatic fixes based on quality assessment.

        Args:
            slide_content: Original slide content
            quality_assessment: Quality assessment results
            slide_image: Optional slide image for visual fixes
            fix_threshold: Minimum score threshold to trigger fixes

        Returns:
            Fixed content and metadata
        """
        logger.info(f"Applying auto-fixes for slide: {slide_content.get('title', 'Untitled')}")

        fixed_content = slide_content.copy()
        applied_fixes = []
        fix_metadata = {
            "original_scores": {},
            "improved_scores": {},
            "fix_categories": []
        }

        # Extract scores from assessment
        overall_score = quality_assessment.get("overall_score", 100)
        accessibility_score = quality_assessment.get("accessibility", {}).get("score", 100)
        brand_score = quality_assessment.get("brand_consistency", {}).get("score", 100)
        clarity_score = quality_assessment.get("visual_clarity", {}).get("score", 100)

        fix_metadata["original_scores"] = {
            "overall": overall_score,
            "accessibility": accessibility_score,
            "brand": brand_score,
            "clarity": clarity_score
        }

        # Apply fixes based on categories and thresholds
        if accessibility_score < fix_threshold:
            accessibility_fixes = await self._apply_accessibility_fixes(
                fixed_content, quality_assessment.get("accessibility", {}), slide_image
            )
            fixed_content = accessibility_fixes["content"]
            applied_fixes.extend(accessibility_fixes["fixes"])
            fix_metadata["fix_categories"].append("accessibility")

        if brand_score < fix_threshold:
            brand_fixes = await self._apply_brand_fixes(
                fixed_content, quality_assessment.get("brand_consistency", {})
            )
            fixed_content = brand_fixes["content"]
            applied_fixes.extend(brand_fixes["fixes"])
            fix_metadata["fix_categories"].append("brand")

        if clarity_score < fix_threshold:
            clarity_fixes = await self._apply_clarity_fixes(
                fixed_content, quality_assessment.get("visual_clarity", {}), slide_image
            )
            fixed_content = clarity_fixes["content"]
            applied_fixes.extend(clarity_fixes["fixes"])
            if clarity_fixes.get("fixed_image"):
                slide_image = clarity_fixes["fixed_image"]
            fix_metadata["fix_categories"].append("clarity")

        # Apply general content optimization
        content_fixes = await self._apply_content_optimization(fixed_content)
        fixed_content = content_fixes["content"]
        applied_fixes.extend(content_fixes["fixes"])

        return {
            "fixed_content": fixed_content,
            "fixed_image": slide_image,
            "applied_fixes": applied_fixes,
            "fix_count": len(applied_fixes),
            "fix_metadata": fix_metadata,
            "improvement_summary": self._generate_improvement_summary(applied_fixes)
        }

    async def _apply_accessibility_fixes(
        self,
        slide_content: Dict[str, Any],
        accessibility_issues: Dict[str, Any],
        slide_image: Optional[str]
    ) -> Dict[str, Any]:
        """Apply accessibility-specific fixes."""
        fixed_content = slide_content.copy()
        fixes = []

        issues = accessibility_issues.get("issues", [])
        recommendations = accessibility_issues.get("fixes", [])

        # Fix title length issues
        title = fixed_content.get("title", "")
        if any("title too long" in issue.lower() for issue in issues):
            if len(title.split()) > 6:
                words = title.split()[:6]
                fixed_content["title"] = " ".join(words)
                fixes.append(f"Shortened title from {len(title.split())} to 6 words")

        # Fix bullet point length issues
        content = fixed_content.get("content", [])
        if isinstance(content, list):
            new_content = []
            for i, bullet in enumerate(content):
                if len(bullet.split()) > 12:
                    # Try to split at natural break points
                    words = bullet.split()
                    if len(words) > 15:
                        # Split into two bullets
                        mid_point = len(words) // 2
                        new_content.extend([
                            " ".join(words[:mid_point]),
                            " ".join(words[mid_point:])
                        ])
                        fixes.append(f"Split long bullet {i+1} into two parts")
                    else:
                        # Just truncate
                        new_content.append(" ".join(words[:12]))
                        fixes.append(f"Shortened bullet {i+1} to 12 words")
                else:
                    new_content.append(bullet)

            fixed_content["content"] = new_content

        # Apply contrast fixes to image if needed
        if slide_image and any("contrast" in issue.lower() for issue in issues):
            try:
                enhanced_image = await self._enhance_image_contrast(slide_image)
                if enhanced_image:
                    slide_image = enhanced_image
                    fixes.append("Enhanced image contrast for accessibility")
            except Exception as e:
                logger.warning(f"Failed to enhance image contrast: {e}")

        return {"content": fixed_content, "fixes": fixes, "fixed_image": slide_image}

    async def _apply_brand_fixes(
        self,
        slide_content: Dict[str, Any],
        brand_issues: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply brand consistency fixes."""
        fixed_content = slide_content.copy()
        fixes = []

        issues = brand_issues.get("issues", [])

        # Fix capitalization consistency
        if any("capitalization" in issue.lower() for issue in issues):
            content = fixed_content.get("content", [])
            if isinstance(content, list):
                # Standardize to sentence case
                fixed_content["content"] = [
                    bullet[0].upper() + bullet[1:] if bullet else bullet
                    for bullet in content
                ]
                fixes.append("Standardized bullet point capitalization")

        # Fix tone consistency
        if any("tone" in issue.lower() for issue in issues):
            # Apply professional tone adjustments
            title = fixed_content.get("title", "")
            if "awesome" in title.lower() or "cool" in title.lower():
                # Replace casual words with professional alternatives
                replacements = {
                    "awesome": "excellent",
                    "cool": "effective",
                    "stuff": "elements",
                    "things": "components"
                }
                for casual, professional in replacements.items():
                    title = title.replace(casual, professional)
                    title = title.replace(casual.title(), professional.title())

                fixed_content["title"] = title
                fixes.append("Adjusted title tone to match brand voice")

            # Apply same to content
            content = fixed_content.get("content", [])
            if isinstance(content, list):
                new_content = []
                for bullet in content:
                    new_bullet = bullet
                    for casual, professional in replacements.items():
                        new_bullet = new_bullet.replace(casual, professional)
                        new_bullet = new_bullet.replace(casual.title(), professional.title())
                    new_content.append(new_bullet)

                if new_content != content:
                    fixed_content["content"] = new_content
                    fixes.append("Adjusted content tone to match brand voice")

        # Fix parallel structure issues
        content = fixed_content.get("content", [])
        if isinstance(content, list) and len(content) > 1:
            if not self._has_parallel_structure(content):
                # Try to fix parallel structure
                fixed_bullets = self._fix_parallel_structure(content)
                if fixed_bullets != content:
                    fixed_content["content"] = fixed_bullets
                    fixes.append("Improved bullet point parallel structure")

        return {"content": fixed_content, "fixes": fixes}

    async def _apply_clarity_fixes(
        self,
        slide_content: Dict[str, Any],
        clarity_issues: Dict[str, Any],
        slide_image: Optional[str]
    ) -> Dict[str, Any]:
        """Apply visual clarity fixes."""
        fixed_content = slide_content.copy()
        fixes = []
        fixed_image = slide_image

        issues = clarity_issues.get("issues", [])

        # Fix text density issues
        if any("text density" in issue.lower() or "too much text" in issue.lower() for issue in issues):
            content = fixed_content.get("content", [])
            if isinstance(content, list) and len(content) > 4:
                # Keep only the most important points
                fixed_content["content"] = content[:4]
                fixes.append(f"Reduced bullet points from {len(content)} to 4 for clarity")

        # Fix missing speaker notes
        if any("speaker notes" in issue.lower() for issue in issues):
            speaker_notes = fixed_content.get("speakerNotes", "")
            if not speaker_notes or len(speaker_notes.split()) < 20:
                title = fixed_content.get("title", "")
                content = fixed_content.get("content", [])

                # Generate expanded speaker notes
                expanded_notes = self._generate_speaker_notes(title, content)
                fixed_content["speakerNotes"] = expanded_notes
                fixes.append("Expanded speaker notes for better presenter guidance")

        # Fix image clarity issues
        if slide_image:
            if any("blurry" in issue.lower() or "sharpness" in issue.lower() for issue in issues):
                try:
                    sharpened_image = await self._sharpen_image(slide_image)
                    if sharpened_image:
                        fixed_image = sharpened_image
                        fixes.append("Applied image sharpening filter")
                except Exception as e:
                    logger.warning(f"Failed to sharpen image: {e}")

            if any("noise" in issue.lower() for issue in issues):
                try:
                    denoised_image = await self._denoise_image(slide_image)
                    if denoised_image:
                        fixed_image = denoised_image
                        fixes.append("Applied noise reduction filter")
                except Exception as e:
                    logger.warning(f"Failed to denoise image: {e}")

        return {"content": fixed_content, "fixes": fixes, "fixed_image": fixed_image}

    async def _apply_content_optimization(
        self,
        slide_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply general content optimization."""
        fixed_content = slide_content.copy()
        fixes = []

        # Optimize title
        title = fixed_content.get("title", "")
        if title:
            optimized_title = self._optimize_title(title)
            if optimized_title != title:
                fixed_content["title"] = optimized_title
                fixes.append("Optimized title for clarity and impact")

        # Optimize bullet points
        content = fixed_content.get("content", [])
        if isinstance(content, list) and content:
            optimized_content = self._optimize_bullet_points(content)
            if optimized_content != content:
                fixed_content["content"] = optimized_content
                fixes.append("Optimized bullet points for better readability")

        # Enhance image prompt if present
        image_prompt = fixed_content.get("imagePrompt", "")
        if image_prompt:
            optimized_prompt = self._optimize_image_prompt(image_prompt, title, content)
            if optimized_prompt != image_prompt:
                fixed_content["imagePrompt"] = optimized_prompt
                fixes.append("Enhanced image prompt for better alignment")

        return {"content": fixed_content, "fixes": fixes}

    # Image processing methods

    async def _enhance_image_contrast(self, slide_image: str) -> Optional[str]:
        """Enhance image contrast for accessibility."""
        try:
            # Decode image
            if slide_image.startswith('data:'):
                slide_image = slide_image.split(',')[1]

            image_data = base64.b64decode(slide_image)
            image = Image.open(io.BytesIO(image_data))

            # Apply contrast enhancement
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(1.3)  # 30% contrast increase

            # Convert back to base64
            buffer = io.BytesIO()
            enhanced.save(buffer, format='PNG')
            enhanced_b64 = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{enhanced_b64}"

        except Exception as e:
            logger.error(f"Contrast enhancement failed: {e}")
            return None

    async def _sharpen_image(self, slide_image: str) -> Optional[str]:
        """Apply sharpening filter to image."""
        try:
            # Decode image
            if slide_image.startswith('data:'):
                slide_image = slide_image.split(',')[1]

            image_data = base64.b64decode(slide_image)
            image = Image.open(io.BytesIO(image_data))

            # Apply unsharp mask filter
            sharpened = image.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))

            # Convert back to base64
            buffer = io.BytesIO()
            sharpened.save(buffer, format='PNG')
            sharpened_b64 = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{sharpened_b64}"

        except Exception as e:
            logger.error(f"Image sharpening failed: {e}")
            return None

    async def _denoise_image(self, slide_image: str) -> Optional[str]:
        """Apply noise reduction to image."""
        try:
            # Decode image
            if slide_image.startswith('data:'):
                slide_image = slide_image.split(',')[1]

            image_data = base64.b64decode(slide_image)
            image = Image.open(io.BytesIO(image_data))

            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Apply Non-local Means Denoising
            denoised = cv2.fastNlMeansDenoisingColored(cv_image, None, 10, 10, 7, 21)

            # Convert back to PIL
            denoised_pil = Image.fromarray(cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB))

            # Convert to base64
            buffer = io.BytesIO()
            denoised_pil.save(buffer, format='PNG')
            denoised_b64 = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{denoised_b64}"

        except Exception as e:
            logger.error(f"Image denoising failed: {e}")
            return None

    # Content optimization methods

    def _optimize_title(self, title: str) -> str:
        """Optimize title for clarity and impact."""
        if not title:
            return title

        optimized = title

        # Remove filler words
        filler_words = ["the", "a", "an", "of", "for", "in", "on", "at", "to", "and"]
        words = optimized.split()

        # Only remove fillers if title is too long
        if len(words) > 6:
            filtered_words = []
            for i, word in enumerate(words):
                # Keep first and last words, and important words
                if i == 0 or i == len(words) - 1 or word.lower() not in filler_words:
                    filtered_words.append(word)

            if len(filtered_words) < len(words):
                optimized = " ".join(filtered_words)

        # Ensure proper capitalization
        optimized = optimized.title()

        return optimized

    def _optimize_bullet_points(self, content: List[str]) -> List[str]:
        """Optimize bullet points for readability."""
        optimized = []

        for bullet in content:
            opt_bullet = bullet

            # Remove redundant words
            redundant_phrases = ["in order to", "it is important to", "we need to", "make sure to"]
            for phrase in redundant_phrases:
                opt_bullet = opt_bullet.replace(phrase, "")

            # Simplify common verbose constructions
            simplifications = {
                "utilize": "use",
                "implement": "use",
                "facilitate": "help",
                "in order to": "to",
                "prior to": "before",
                "subsequent to": "after"
            }

            for verbose, simple in simplifications.items():
                opt_bullet = opt_bullet.replace(verbose, simple)
                opt_bullet = opt_bullet.replace(verbose.title(), simple.title())

            # Clean up extra spaces
            opt_bullet = " ".join(opt_bullet.split())

            # Ensure bullet starts with capital letter
            if opt_bullet and opt_bullet[0].islower():
                opt_bullet = opt_bullet[0].upper() + opt_bullet[1:]

            optimized.append(opt_bullet)

        return optimized

    def _optimize_image_prompt(self, image_prompt: str, title: str, content: List[str]) -> str:
        """Optimize image prompt for better alignment with content."""
        if not image_prompt:
            return image_prompt

        # Incorporate key terms from title and content
        key_terms = set()

        # Extract key terms from title
        if title:
            title_words = [word.lower() for word in title.split() if len(word) > 3]
            key_terms.update(title_words)

        # Extract key terms from content
        if isinstance(content, list):
            for bullet in content:
                bullet_words = [word.lower() for word in bullet.split() if len(word) > 4]
                key_terms.update(bullet_words[:2])  # Take first 2 key words per bullet

        # Enhance prompt with key terms if not already present
        prompt_lower = image_prompt.lower()
        missing_terms = [term for term in key_terms if term not in prompt_lower]

        if missing_terms:
            # Add 1-2 most relevant missing terms
            enhanced_prompt = f"{image_prompt}, featuring {', '.join(list(missing_terms)[:2])}"
            return enhanced_prompt

        return image_prompt

    def _generate_speaker_notes(self, title: str, content: List[str]) -> str:
        """Generate comprehensive speaker notes."""
        notes = []

        if title:
            notes.append(f"Begin by introducing {title.lower()}.")

        if isinstance(content, list) and content:
            notes.append("Cover the following key points systematically:")

            for i, bullet in enumerate(content, 1):
                # Extract first few words as the key concept
                key_concept = " ".join(bullet.split()[:3])
                notes.append(f"{i}. Elaborate on {key_concept.lower()}, providing specific examples and context.")

        notes.append("Conclude by summarizing the main takeaways and their importance to the audience.")

        return " ".join(notes)

    def _has_parallel_structure(self, content: List[str]) -> bool:
        """Check if bullets have parallel grammatical structure."""
        if len(content) < 2:
            return True

        # Simple heuristic: check if bullets start with similar forms
        first_words = [bullet.split()[0].lower() if bullet.split() else "" for bullet in content]

        # Check for verb consistency
        action_verbs = ["create", "develop", "implement", "manage", "analyze", "design", "build", "improve", "ensure", "provide"]
        verb_starts = sum(1 for word in first_words if word in action_verbs)

        # Check for noun consistency
        if verb_starts < len(first_words) * 0.7:
            # Check if they start with nouns/concepts consistently
            return len(set(word[0].isupper() for word in first_words if word)) <= 1

        return verb_starts >= len(first_words) * 0.7

    def _fix_parallel_structure(self, content: List[str]) -> List[str]:
        """Attempt to fix parallel structure in bullet points."""
        if len(content) < 2:
            return content

        # Determine the dominant pattern
        first_words = [bullet.split()[0].lower() if bullet.split() else "" for bullet in content]
        action_verbs = ["create", "develop", "implement", "manage", "analyze", "design", "build", "improve", "ensure", "provide"]

        verb_starts = sum(1 for word in first_words if word in action_verbs)

        # If most start with verbs, make all start with verbs
        if verb_starts >= len(content) * 0.5:
            fixed_content = []
            for bullet in content:
                if bullet.split() and bullet.split()[0].lower() not in action_verbs:
                    # Try to add an action verb
                    fixed_bullet = f"Implement {bullet.lower()}"
                    fixed_content.append(fixed_bullet)
                else:
                    fixed_content.append(bullet)
            return fixed_content

        # Otherwise, ensure consistent capitalization
        return [bullet[0].upper() + bullet[1:] if bullet else bullet for bullet in content]

    def _generate_improvement_summary(self, applied_fixes: List[str]) -> str:
        """Generate a summary of improvements made."""
        if not applied_fixes:
            return "No fixes were needed."

        fix_count = len(applied_fixes)
        categories = []

        if any("title" in fix.lower() for fix in applied_fixes):
            categories.append("title optimization")
        if any("bullet" in fix.lower() or "content" in fix.lower() for fix in applied_fixes):
            categories.append("content refinement")
        if any("image" in fix.lower() or "contrast" in fix.lower() for fix in applied_fixes):
            categories.append("visual enhancement")
        if any("notes" in fix.lower() for fix in applied_fixes):
            categories.append("speaker notes improvement")
        if any("tone" in fix.lower() or "brand" in fix.lower() for fix in applied_fixes):
            categories.append("brand alignment")

        category_text = ", ".join(categories) if categories else "various improvements"

        return f"Applied {fix_count} automatic fixes including {category_text}."


# Convenience functions for ADK integration

async def apply_auto_fixes(
    slide_content: Dict[str, Any],
    quality_assessment: Dict[str, Any],
    slide_image: Optional[str] = None,
    fix_threshold: int = 70,
    visioncv_url: str = "http://visioncv:8091"
) -> Dict[str, Any]:
    """
    Apply automatic fixes to slide content based on quality assessment.

    Args:
        slide_content: Original slide content
        quality_assessment: Quality assessment results
        slide_image: Optional slide image
        fix_threshold: Score threshold to trigger fixes
        visioncv_url: VisionCV service URL

    Returns:
        Fixed content and metadata
    """
    engine = AutoFixEngine(visioncv_url)
    return await engine.apply_comprehensive_fixes(
        slide_content, quality_assessment, slide_image, fix_threshold
    )


async def quick_content_fixes(slide_content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply quick content fixes without full quality assessment.

    Args:
        slide_content: Original slide content

    Returns:
        Fixed content with basic improvements
    """
    engine = AutoFixEngine()
    return await engine._apply_content_optimization(slide_content)


# Export for tool integration
__all__ = [
    "AutoFixEngine",
    "apply_auto_fixes",
    "quick_content_fixes"
]