#!/usr/bin/env python
"""
ADK Modernization Script - Updates llm.py to fix prompt formatting issues
"""

import os
import shutil
from datetime import datetime

# Read the current llm.py
llm_path = "app/llm.py"
backup_path = f"app/llm.py.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Create backup
shutil.copy(llm_path, backup_path)
print(f"Created backup at {backup_path}")

# New modernized llm.py content
new_content = '''"""
ADK-Compatible LLM Module

This module provides a modernized interface to Google's Gemini API following ADK patterns.
It handles prompt formatting, model name normalization, and token usage tracking.
"""

import os
import time
from typing import Any, Dict, List, Optional, Union, Tuple
import google.generativeai as genai
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
GOOGLE_API_KEY = os.environ.get("GOOGLE_GENAI_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    logger.warning("GOOGLE_GENAI_API_KEY not set - LLM calls will fail")


def estimate_tokens(text: str) -> int:
    """Estimate token count for text (rough approximation)."""
    return max(1, round(len(text or "") / 4))


def normalize_model_name(model: str) -> str:
    """Normalize model names to Gemini API format."""
    if model and model.startswith("googleai/"):
        return model[9:]  # Remove "googleai/" prefix
    # Handle common aliases
    model_aliases = {
        "gemini-2-flash": "gemini-2.5-flash",
        "gemini-flash": "gemini-2.5-flash",
        "gemini-pro": "gemini-2.5-pro",
    }
    return model_aliases.get(model, model)


def format_prompt_parts(prompt_parts: Union[str, List, Dict]) -> List[str]:
    """
    Convert various prompt formats to Gemini-compatible format.

    Handles:
    - Simple strings
    - Lists of strings
    - Lists of dicts with 'text' key
    - Lists of dicts with 'role' and 'content' keys (chat format)
    """
    if isinstance(prompt_parts, str):
        return [prompt_parts]

    if isinstance(prompt_parts, list):
        formatted_parts = []
        for part in prompt_parts:
            if isinstance(part, str):
                formatted_parts.append(part)
            elif isinstance(part, dict):
                # Handle chat-style format (THIS IS THE KEY FIX)
                if 'role' in part and 'content' in part:
                    # Convert role/content to simple text
                    content = part.get('content', '')
                    formatted_parts.append(content)
                elif 'text' in part:
                    formatted_parts.append(part['text'])
                elif 'parts' in part:
                    # Content object format
                    parts = part['parts']
                    if isinstance(parts, list):
                        formatted_parts.extend([str(p) for p in parts])
                    else:
                        formatted_parts.append(str(parts))
                else:
                    # Try to convert to string
                    formatted_parts.append(str(part))
            else:
                formatted_parts.append(str(part))
        return formatted_parts

    # Single dict
    if isinstance(prompt_parts, dict):
        if 'parts' in prompt_parts:
            parts = prompt_parts['parts']
            if isinstance(parts, list):
                return [str(p) for p in parts]
            return [str(parts)]
        elif 'text' in prompt_parts:
            return [prompt_parts['text']]
        elif 'role' in prompt_parts and 'content' in prompt_parts:
            return [prompt_parts['content']]

    # Fallback: convert to string
    return [str(prompt_parts)]


def call_text_model(
    model: str,
    prompt_parts: Union[str, List, Dict],
    temperature: float = 0.7,
    max_output_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    top_k: Optional[int] = None
) -> Tuple[str, Dict[str, Any], int]:
    """
    Call Gemini text model with ADK-compatible interface.

    Args:
        model: Model name (e.g., "googleai/gemini-2.5-flash" or "gemini-2.5-flash")
        prompt_parts: Prompt in various formats (string, list, or dict)
        temperature: Sampling temperature (0.0 to 1.0)
        max_output_tokens: Maximum tokens to generate
        top_p: Nucleus sampling parameter
        top_k: Top-k sampling parameter

    Returns:
        Tuple of (response_text, usage_dict, duration_ms)
    """
    start = time.time()

    # Normalize model name
    model = normalize_model_name(model)

    # Initialize usage tracking
    usage = {
        "model": model,
        "promptTokens": 0,
        "completionTokens": 0,
        "totalTokens": 0
    }

    text = ""

    try:
        # Format prompt parts for Gemini API (CRITICAL FIX)
        formatted_parts = format_prompt_parts(prompt_parts)

        # Log formatted prompt for debugging
        logger.debug(f"Formatted prompt parts: {formatted_parts[:100]}...")  # First 100 chars

        # Configure generation parameters
        generation_config = {
            "temperature": temperature,
        }
        if max_output_tokens:
            generation_config["max_output_tokens"] = max_output_tokens
        if top_p is not None:
            generation_config["top_p"] = top_p
        if top_k is not None:
            generation_config["top_k"] = top_k

        # Create model and generate content
        model_instance = genai.GenerativeModel(
            model_name=model,
            generation_config=generation_config
        )

        response = model_instance.generate_content(formatted_parts)
        duration_ms = int((time.time() - start) * 1000)

        # Extract text from response
        if response and response.text:
            text = response.text.strip()

        # Extract usage metadata
        if hasattr(response, 'usage_metadata'):
            um = response.usage_metadata
            usage["promptTokens"] = getattr(um, 'prompt_token_count', 0)
            usage["completionTokens"] = getattr(um, 'candidates_token_count', 0)
            usage["totalTokens"] = usage["promptTokens"] + usage["completionTokens"]

        # Fallback token estimation if metadata not available
        if not usage["promptTokens"] and not usage["completionTokens"]:
            prompt_text = "\\n".join([str(p) for p in formatted_parts])
            usage["promptTokens"] = estimate_tokens(prompt_text)
            usage["completionTokens"] = estimate_tokens(text)
            usage["totalTokens"] = usage["promptTokens"] + usage["completionTokens"]

        logger.debug(f"LLM call successful: model={model}, duration={duration_ms}ms, tokens={usage['totalTokens']}")

    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        error_msg = str(e)
        logger.error(f"LLM error for model {model}: {error_msg}")

        # Log but don't expose full error details
        print(f"LLM error: {error_msg}", flush=True)

        # Return empty response with error in usage
        usage["error"] = error_msg

    return text, usage, duration_ms


def analyze_screenshot_contrast(png_bytes: bytes) -> Optional[Dict[str, float]]:
    """Analyze contrast metrics for a screenshot."""
    try:
        from PIL import Image, ImageStat
        import io
        im = Image.open(io.BytesIO(png_bytes)).convert('L')
        stat = ImageStat.Stat(im)
        mean = stat.mean[0]
        # rough variance proxy
        var = stat.var[0]
        return {"mean": mean, "variance": var}
    except Exception as e:
        logger.error(f"Failed to analyze screenshot contrast: {e}")
        return None
'''

# Write the new content
with open(llm_path, 'w') as f:
    f.write(new_content)

print(f"Successfully modernized {llm_path}")
print("\nKey changes made:")
print("1. Added format_prompt_parts function to handle role/content dict format")
print("2. Enhanced error handling and logging")
print("3. Added type hints and documentation")
print("4. Fixed prompt formatting issue that was causing Gemini API errors")
print("\nPlease restart the ADK container to apply changes:")
print("docker compose restart adkpy")