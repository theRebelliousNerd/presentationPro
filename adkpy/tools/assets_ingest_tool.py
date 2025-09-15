"""
AssetsIngestTool

Purpose
- Normalize, sanitize, and store uploaded assets for Graph RAG; generate lightweight text from simple file types when possible.

Notes
- This implementation purposefully avoids heavyweight dependencies. For local files, it extracts from .txt/.md only.
- PDF/DOCX/CSV extraction can be added later; callers may pass already-extracted text.
"""

from __future__ import annotations

import os
import csv
from typing import List, Optional, Tuple
from pydantic import BaseModel

from .arango_graph_rag_tool import ArangoGraphRAGTool, Asset, IngestResponse


class IngestAssetInput(BaseModel):
  presentationId: str
  name: str
  url: Optional[str] = None
  path: Optional[str] = None
  kind: Optional[str] = None
  text: Optional[str] = None


class IngestSummary(BaseModel):
  ok: bool
  docs: int
  chunks: int
  warnings: List[str] = []


class AssetsIngestTool:
  def __init__(self) -> None:
    self.graph = ArangoGraphRAGTool()

  def _extract_text_from_path(self, path: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (text, warning). Handles .txt/.md natively, optional PDF/DOCX/CSV."""
    try:
      if not path:
        return None, None
      if not os.path.exists(path):
        return None, f"Path not found: {path}"
      lower = path.lower()
      # TXT/MD
      if lower.endswith((".txt", ".md")):
        try:
          with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()
            return data, None
        except Exception as e:
          return None, f"Failed to read {path}: {e}"
      # CSV (simple join of cells)
      if lower.endswith(".csv"):
        try:
          rows = []
          with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
              rows.append(", ".join(cell.strip() for cell in row if cell is not None))
              if i >= 300:
                break
          text = "\n".join(rows)
          return text, None
        except Exception as e:
          return None, f"Failed to parse CSV {path}: {e}"
      # PDF via PyPDF2 (optional)
      if lower.endswith(".pdf"):
        try:
          from PyPDF2 import PdfReader  # type: ignore
          reader = PdfReader(path)
          out = []
          for i, page in enumerate(reader.pages):
            t = page.extract_text() or ""
            if t:
              out.append(t)
            if i >= 50:
              break
          text = "\n\n".join(out)
          return text, None
        except Exception as e:
          return None, f"PDF extraction unavailable or failed for {os.path.basename(path)}: {e}"
      # DOCX via docx2txt or python-docx (optional)
      if lower.endswith(".docx"):
        # Try docx2txt
        try:
          import docx2txt  # type: ignore
          text = docx2txt.process(path) or ""
          return text, None
        except Exception:
          # Fallback to python-docx
          try:
            from docx import Document  # type: ignore
            doc = Document(path)
            paras = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
            return "\n".join(paras), None
          except Exception as e:
            return None, f"DOCX extraction unavailable or failed for {os.path.basename(path)}: {e}"
      # Unsupported
      return None, None
    except Exception as e:
      return None, f"Unexpected error reading {path}: {e}"

  def ingest_assets(self, assets: List[IngestAssetInput]) -> IngestSummary:
    warnings: List[str] = []
    prepared: List[Asset] = []
    for a in assets:
      text = (a.text or "").strip()
      if not text and a.path:
        t, w = self._extract_text_from_path(a.path)
        if w:
          warnings.append(w)
        if t:
          text = t
      prepared.append(Asset(presentationId=a.presentationId, name=a.name, url=a.url, text=text, kind=a.kind))
    resp: IngestResponse = self.graph.ingest(prepared)
    return IngestSummary(ok=resp.ok, docs=resp.docs, chunks=resp.chunks, warnings=warnings)
