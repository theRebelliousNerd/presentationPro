"""Critic tools exports."""

from .assets import compile_asset_snippets, CRITIC_TOOLS
from .visual_quality_gate import (
    VisualQualityGate,
    assess_visual_quality,
    apply_auto_fixes as apply_quality_fixes
)
from .accessibility_checker import check_accessibility, quick_accessibility_check
from .brand_consistency import check_brand_consistency, quick_brand_check
from .visual_clarity import check_visual_clarity, quick_clarity_check, apply_clarity_fixes
from .auto_fix import AutoFixEngine, apply_auto_fixes, quick_content_fixes

# Enhanced CRITIC_TOOLS with quality gate functions
QUALITY_GATE_TOOLS = [
    assess_visual_quality,
    check_accessibility,
    check_brand_consistency,
    check_visual_clarity,
    apply_auto_fixes,
    quick_content_fixes
]

# Combined tools for ADK integration
ENHANCED_CRITIC_TOOLS = CRITIC_TOOLS + QUALITY_GATE_TOOLS

__all__ = [
    "compile_asset_snippets",
    "CRITIC_TOOLS",
    "QUALITY_GATE_TOOLS",
    "ENHANCED_CRITIC_TOOLS",
    "VisualQualityGate",
    "assess_visual_quality",
    "check_accessibility",
    "check_brand_consistency",
    "check_visual_clarity",
    "apply_auto_fixes",
    "apply_quality_fixes",
    "apply_clarity_fixes",
    "quick_content_fixes",
    "quick_accessibility_check",
    "quick_brand_check",
    "quick_clarity_check",
    "AutoFixEngine"
]
