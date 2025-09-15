"""
ArangoGraphRAGTool

Purpose
- Provide agents with deck-scoped retrieval over uploaded documents using ArangoDB + ArangoSearch (BM25), no vectors.

Capabilities
- Ingest: persist documents and paragraph-level chunks; create edges; build/maintain ArangoSearch view.
- Retrieve: top-k chunks filtered by presentationId and query; return { name, text, url? }.

Implementation
- Thin wrapper around the FastAPI logic in adkpy/app using the same DB helpers and Pydantic models.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.db import get_db, ensure_view
from schemas.arango_models import DocumentDoc, ChunkDoc, DocEdge


class Asset(BaseModel):
  presentationId: str
  name: str
  url: Optional[str] = None
  text: Optional[str] = None
  kind: Optional[str] = None  # image|document|other (inferred if None)


class RetrievedChunk(BaseModel):
  name: str
  text: str
  url: Optional[str] = None


class IngestResponse(BaseModel):
  ok: bool = True
  docs: int = 0
  chunks: int = 0


class RetrieveResponse(BaseModel):
  chunks: List[RetrievedChunk] = Field(default_factory=list)


class ArangoGraphRAGTool:
  def __init__(self) -> None:
    self.db = get_db()
    ensure_view(self.db)

  def ingest(self, assets: List[Asset]) -> IngestResponse:
    """Persist assets and paragraph chunks; idempotent on re-ingest."""
    doc_col = self.db.collection("documents")
    chunk_col = self.db.collection("chunks")
    edge_col = self.db.collection("doc_edges")
    num_docs = 0
    num_chunks = 0
    for a in assets:
      kind = a.kind or ("image" if a.name.lower().endswith((".png",".jpg",".jpeg",".webp",".gif",".svg")) else "document")
      doc_key = f"{a.presentationId}:{a.name}"
      doc_model = DocumentDoc(
        key=doc_key,
        presentationId=a.presentationId,
        name=a.name,
        url=a.url,
        kind=kind,  # type: ignore[arg-type]
      )
      doc_payload = doc_model.model_dump(by_alias=True)
      if doc_col.has(doc_key):
        doc_col.update(doc_payload)
      else:
        doc_col.insert(doc_payload)
        num_docs += 1

      text = (a.text or "").strip()
      if text:
        paras = [p.strip() for p in text.replace("\r", "\n").split("\n\n") if p.strip()]
        for idx, p in enumerate(paras[:50]):
          chunk_key = f"{doc_key}:{idx}"
          chunk_model = ChunkDoc(
            key=chunk_key,
            presentationId=a.presentationId,
            docKey=doc_key,
            name=doc_model.name,
            text=p,
          )
          chunk_payload = chunk_model.model_dump(by_alias=True)
          if chunk_col.has(chunk_key):
            chunk_col.update(chunk_payload)
          else:
            chunk_col.insert(chunk_payload)
            num_chunks += 1
          edge_model = DocEdge(from_id=f"documents/{doc_key}", to_id=f"chunks/{chunk_key}")
          try:
            edge_col.insert(edge_model.model_dump(by_alias=True))
          except Exception:
            pass
    ensure_view(self.db)
    return IngestResponse(ok=True, docs=num_docs, chunks=num_chunks)

  def retrieve(self, presentation_id: str, query: str, limit: int = 5) -> RetrieveResponse:
    view = ensure_view(self.db)
    aql = f"""
    FOR d IN {view}
      SEARCH d.presentationId == @pid AND ANALYZER(d.text IN TOKENS(@q, 'text_en'), 'text_en')
      SORT BM25(d) DESC
      LIMIT @limit
      RETURN {{ name: d.name, text: d.text }}
    """
    cursor = self.db.aql.execute(aql, bind_vars={"pid": presentation_id, "q": query, "limit": limit})
    items = [RetrievedChunk(**row) for row in cursor]
    return RetrieveResponse(chunks=items)
