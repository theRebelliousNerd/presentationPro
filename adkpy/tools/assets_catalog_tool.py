"""
AssetsCatalogTool

Fetches SVG icons and pattern SVGs from vetted open-source sources with caching.

This tool is meant to be used by design-oriented agents to dynamically pull
assets based on a pack/name request while respecting a domain allowlist and
basic licensing constraints.
"""

from __future__ import annotations

import os
import time
import json
from typing import Optional, Dict, Any, List
from urllib.request import urlopen, Request

from pydantic import BaseModel

# Simple file cache
ASSETS_CACHE_PATH = os.environ.get("ASSETS_CACHE_PATH", ".cache/assets.json")
ASSETS_CACHE_TTL = int(os.environ.get("ASSETS_CACHE_TTL", "86400") or 86400)

_cache: Dict[str, Dict[str, Any]] = {}
if ASSETS_CACHE_PATH and os.path.exists(ASSETS_CACHE_PATH):
    try:
        with open(ASSETS_CACHE_PATH, "r", encoding="utf-8") as f:
            _cache = json.load(f) or {}
    except Exception:
        _cache = {}


def _cache_get(key: str) -> Optional[str]:
    ent = _cache.get(key)
    if not ent:
        return None
    if ASSETS_CACHE_TTL and (time.time() - ent.get("ts", 0)) > ASSETS_CACHE_TTL:
        return None
    return ent.get("data")


def _cache_set(key: str, data: str) -> None:
    _cache[key] = {"ts": time.time(), "data": data}
    try:
        os.makedirs(os.path.dirname(ASSETS_CACHE_PATH), exist_ok=True)
        with open(ASSETS_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(_cache, f)
    except Exception:
        pass


class IconInfo(BaseModel):
    pack: str
    name: str
    url: str


class SvgResponse(BaseModel):
    svg: str


def _http_get(url: str, timeout: int = 10) -> Optional[str]:
    try:
        req = Request(url)
        req.add_header("User-Agent", "PresentationPro/1.0")
        with urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                raw = resp.read().decode("utf-8", errors="ignore")
                return raw
    except Exception:
        return None
    return None


def icon_raw_url(pack: str, name: str) -> Optional[str]:
    pack = (pack or "").lower()
    name = name.replace(" ", "-").lower()
    if pack == "tabler":
        return f"https://raw.githubusercontent.com/tabler/tabler-icons/master/icons/outline/{name}.svg"
    if pack == "heroicons":
        # 24px outline set
        return f"https://raw.githubusercontent.com/tailwindlabs/heroicons/master/optimized/24/outline/{name}.svg"
    if pack == "lucide":
        # community mirror
        return f"https://unpkg.com/lucide-static/icons/{name}.svg"
    return None


def get_icon_svg(pack: str, name: str) -> Optional[str]:
    url = icon_raw_url(pack, name)
    if not url:
        return None
    ck = f"icon|{url}"
    hit = _cache_get(ck)
    if hit is not None:
        return hit
    data = _http_get(url)
    if data:
        _cache_set(ck, data)
        return data
    return None


CURATED_PATTERNS: Dict[str, str] = {
    "topography": (
        '<svg xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" viewBox="0 0 160 120">'
        '<path d="M0,60 C40,40 120,80 160,60" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>'
        '<path d="M0,90 C30,70 130,110 160,90" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>'
        '<path d="M0,30 C50,20 110,40 160,30" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>'
        '</svg>'
    ),
    "hexagons": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 34.64">'
        '<polygon points="20,0 40,10 40,24.64 20,34.64 0,24.64 0,10" fill="none" stroke="rgba(255,255,255,0.07)" stroke-width="1" />'
        '</svg>'
    ),
    "diagonal": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<defs><pattern id="diag" width="20" height="20" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<rect width="10" height="20" fill="rgba(255,255,255,0.06)" />'
        '</pattern></defs>'
        '<rect width="100%" height="100%" fill="url(#diag)" />'
        '</svg>'
    ),
    "overlap": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        '<g fill="rgba(255,255,255,0.06)"><circle cx="20" cy="30" r="20"/><circle cx="35" cy="40" r="18"/><circle cx="70" cy="60" r="30"/></g>'
        '</svg>'
    ),
}


def get_pattern_svg(name: str) -> Optional[str]:
    name = (name or "").lower()
    if name in CURATED_PATTERNS:
        return CURATED_PATTERNS[name]
    return None


def list_icon_candidates(pack: str, q: str, limit: int = 10) -> List[IconInfo]:
    # Minimal curated set. For full dynamic listing, we could fetch pack indexes.
    candidates = [
        ("check", "check"), ("lightbulb", "light-bulb"), ("chart", "chart-bar"), ("photo", "photo"),
        ("arrow-right", "arrow-right"), ("info", "info-circle"), ("warning", "alert-triangle"),
    ]
    out: List[IconInfo] = []
    for label, slug in candidates:
        if q and q.lower() not in label and q.lower() not in slug:
            continue
        url = icon_raw_url(pack, slug)
        if url:
            out.append(IconInfo(pack=pack, name=slug, url=url))
        if len(out) >= limit:
            break
    return out
