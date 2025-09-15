"""
WebSearchTool

Provide curated, rate-limited web search with minimal dependencies.

Implementation notes
- Uses Bing Web Search API if BING_SEARCH_API_KEY is set (no extra deps) via urllib.
- Falls back to DuckDuckGo HTML scraping with a simple regex if no key.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pydantic import BaseModel

# Global cache/config so multiple instances share state in-process
_GLOBAL_CACHE: dict = {}
_GLOBAL_CACHE_ENABLED: bool = True
try:
  _GLOBAL_CACHE_TTL: int = int(os.environ.get("WEB_SEARCH_CACHE_TTL", "3600") or 3600)
except Exception:
  _GLOBAL_CACHE_TTL = 3600


class WebResult(BaseModel):
  title: str
  url: str
  snippet: str


class WebSearchTool:
  def __init__(self, *, allow_domains: Optional[List[str]] = None, cache: Optional[bool] = None, cache_ttl: Optional[int] = None, cache_path: Optional[str] = None) -> None:
    self.allow = [d.lower() for d in (allow_domains or [])]
    self._cache_enabled = (_GLOBAL_CACHE_ENABLED if cache is None else bool(cache))
    self._cache_ttl = max(0, int(_GLOBAL_CACHE_TTL if cache_ttl is None else int(cache_ttl)))
    self._cache: dict = _GLOBAL_CACHE
    self._cache_path = cache_path or os.environ.get("WEB_SEARCH_CACHE")
    if self._cache_path and os.path.exists(self._cache_path):
      try:
        with open(self._cache_path, "r", encoding="utf-8") as f:
          loaded = json.load(f)
          if isinstance(loaded, dict):
            self._cache.update(loaded)
      except Exception:
        pass

  def _allowed(self, url: str) -> bool:
    if not self.allow:
      return True
    from urllib.parse import urlparse
    host = (urlparse(url).hostname or "").lower()
    return any(host.endswith(d) for d in self.allow)

  def _cache_key(self, query: str, top_k: int) -> str:
    key = {
      "q": query,
      "k": int(top_k),
      "allow": self.allow,
    }
    try:
      return json.dumps(key, sort_keys=True)
    except Exception:
      return f"{query}|{top_k}|{','.join(self.allow)}"

  def _cache_get(self, key: str) -> Optional[List[WebResult]]:
    if not self._cache_enabled:
      return None
    now = time.time()
    entry = self._cache.get(key)
    if not entry:
      return None
    ts = entry.get("ts", 0)
    if self._cache_ttl and (now - ts) > self._cache_ttl:
      return None
    try:
      items = [WebResult(**x) for x in (entry.get("items") or [])]
      return items
    except Exception:
      return None

  def _cache_set(self, key: str, items: List[WebResult]) -> None:
    if not self._cache_enabled:
      return
    self._cache[key] = {"ts": time.time(), "items": [it.model_dump() for it in items]}
    if self._cache_path:
      try:
        os.makedirs(os.path.dirname(self._cache_path), exist_ok=True)
        with open(self._cache_path, "w", encoding="utf-8") as f:
          json.dump(self._cache, f)
      except Exception:
        pass

  def search(self, query: str, top_k: int = 5) -> List[WebResult]:
    # cache check
    ck = self._cache_key(query, top_k)
    cached = self._cache_get(ck)
    if cached is not None:
      return cached
    key = os.environ.get("BING_SEARCH_API_KEY")
    results: List[WebResult] = []
    if key:
      try:
        params = urlencode({"q": query, "count": min(max(top_k, 1), 10), "mkt": "en-US", "safeSearch": "Strict"})
        req = Request(f"https://api.bing.microsoft.com/v7.0/search?{params}")
        req.add_header("Ocp-Apim-Subscription-Key", key)
        with urlopen(req, timeout=10) as resp:
          data = json.loads(resp.read().decode("utf-8"))
        for it in (data.get("webPages", {}) or {}).get("value", [])[:top_k]:
          url = it.get("url", "")
          if url and self._allowed(url):
            results.append(WebResult(title=it.get("name", ""), url=url, snippet=it.get("snippet", "")))
        self._cache_set(ck, results)
        return results
      except Exception:
        # fall through to ddg
        pass
    # Fallback: DuckDuckGo HTML
    try:
      params = urlencode({"q": query, "s": "0"})
      req = Request(f"https://duckduckgo.com/html/?{params}")
      req.add_header("User-Agent", "Mozilla/5.0 (compatible; ADK/1.0)")
      with urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
      # Very rough parsing: anchor with class="result__a"; grab title and href
      anchors = re.findall(r"<a[^>]*class=\"result__a\"[^>]*href=\"(.*?)\"[^>]*>(.*?)</a>", html, flags=re.I|re.S)
      for href, title in anchors[:top_k*2]:
        # unescape HTML entities
        title_clean = re.sub(r"<.*?>", "", title)
        if href and self._allowed(href):
          results.append(WebResult(title=title_clean.strip(), url=href, snippet=""))
        if len(results) >= top_k:
          break
    except Exception:
      pass
    self._cache_set(ck, results)
    return results


def set_global_cache_config(*, ttl: Optional[int] = None, enabled: Optional[bool] = None) -> dict:
  global _GLOBAL_CACHE_TTL, _GLOBAL_CACHE_ENABLED
  if ttl is not None:
    try:
      _GLOBAL_CACHE_TTL = max(0, int(ttl))
    except Exception:
      pass
  if enabled is not None:
    _GLOBAL_CACHE_ENABLED = bool(enabled)
  return {"cacheTtl": _GLOBAL_CACHE_TTL, "enabled": _GLOBAL_CACHE_ENABLED}


def clear_global_cache(delete_file: bool = True, cache_path: Optional[str] = None) -> dict:
  global _GLOBAL_CACHE
  _GLOBAL_CACHE.clear()
  path = cache_path or os.environ.get("WEB_SEARCH_CACHE")
  if delete_file and path and os.path.exists(path):
    try:
      os.remove(path)
    except Exception:
      pass
  return {"ok": True}
