"""
ArangoGraphRAGTool

Provides presentation-scoped retrieval using ArangoDB. Paragraph chunks
are indexed with BM25 and hashed semantic embeddings to improve recall.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
import re
import math
import hashlib

from pydantic import BaseModel, Field

from app.db import get_db, ensure_view
from schemas.arango_models import DocumentDoc, ChunkDoc, DocEdge

EMBED_DIM = 64


def _compute_embedding(text: str) -> List[float]:
    """Produce a deterministic hashing-based embedding."""
    tokens = [t for t in re.findall(r"[A-Za-z0-9_]+", text.lower()) if t]
    if not tokens:
        return []
    vec = [0.0] * EMBED_DIM
    for token in tokens:
        digest = int(hashlib.sha1(token.encode("utf-8")).hexdigest(), 16)
        for dim in range(EMBED_DIM):
            bit = 1 if (digest >> dim) & 1 else -1
            vec[dim] += bit
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))


class Asset(BaseModel):
  presentationId: str
  name: str
  url: Optional[str] = None
  text: Optional[str] = None
  kind: Optional[str] = None


class RetrievedChunk(BaseModel):
  name: str
  text: str
  url: Optional[str] = None
  score: float = 0.0
  chunkKey: Optional[str] = None


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

  def _sanitize_key(self, value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_:.-]", "_", (value or "").strip())
    return (clean or "key")[:200]

  def _rerank(self, rows: List[Dict[str, Any]], query: str, limit: int) -> List[RetrievedChunk]:
    if not rows:
        return []
    bm_scores = [float(row.get("score", 0.0) or 0.0) for row in rows]
    max_bm = max(bm_scores) if bm_scores else 1.0
    query_vec = _compute_embedding(query)
    results: List[RetrievedChunk] = []
    for row, bm in zip(rows, bm_scores):
        embedding = row.get("embedding") or []
        cos = _cosine_similarity(query_vec, embedding) if query_vec and embedding else 0.0
        bm_norm = bm / max_bm if max_bm else 0.0
        combined = 0.5 * bm_norm + 0.5 * max(cos, 0.0)
        results.append(RetrievedChunk(
            name=row.get("name") or "",
            text=row.get("text") or "",
            url=row.get("url"),
            score=combined,
            chunkKey=row.get("key") or row.get("_key"),
        ))
    results.sort(key=lambda chunk: chunk.score, reverse=True)
    return results[:limit]

  def ingest(self, assets: List[Asset]) -> IngestResponse:
    doc_col = self.db.collection("documents")
    chunk_col = self.db.collection("chunks")
    edge_col = self.db.collection("doc_edges")
    num_docs = 0
    num_chunks = 0

    for asset in assets:
      kind = asset.kind or ("image" if asset.name.lower().endswith((".png",".jpg",".jpeg",".webp",".gif",".svg")) else "document")
      doc_key = f"{self._sanitize_key(asset.presentationId)}:{self._sanitize_key(asset.name)}"
      doc_model = DocumentDoc(
        key=doc_key,
        presentationId=asset.presentationId,
        name=asset.name,
        url=asset.url,
        kind=kind,  # type: ignore[arg-type]
      )
      payload = {k: v for k, v in doc_model.model_dump(by_alias=True).items() if v is not None}
      if doc_col.has(doc_key):
        doc_col.update(payload)
      else:
        doc_col.insert(payload)
        num_docs += 1

      text = (asset.text or "").strip()
      if not text:
        continue
      blocks = text.replace("\r", "\n").split("\n\n")
      paragraphs = [block.strip() for block in blocks if block.strip()]
      for idx, paragraph in enumerate(paragraphs[:50]):
        chunk_key = f"{doc_key}:{idx}"
        embedding = _compute_embedding(paragraph)
        chunk_doc = ChunkDoc(
          key=chunk_key,
          presentationId=asset.presentationId,
          docKey=doc_key,
          name=doc_model.name,
          text=paragraph,
          url=asset.url,
          embedding=embedding or None,
        )
        chunk_payload = {k: v for k, v in chunk_doc.model_dump(by_alias=True).items() if v is not None}
        if chunk_col.has(chunk_key):
          chunk_col.update(chunk_payload)
        else:
          chunk_col.insert(chunk_payload)
          num_chunks += 1
        edge = DocEdge(from_id=f"documents/{doc_key}", to_id=f"chunks/{chunk_key}")
        try:
          edge_col.insert(edge.model_dump(by_alias=True))
        except Exception:
          pass

    ensure_view(self.db)
    return IngestResponse(ok=True, docs=num_docs, chunks=num_chunks)

  def retrieve(self, presentation_id: str, query: str, limit: int = 5) -> RetrieveResponse:
    view = ensure_view(self.db)
    bind_vars = {"pid": presentation_id, "q": query, "limit": max(limit * 3, limit)}

    seeded: List[RetrievedChunk] = []
    advanced_aql = """
    FOR d IN {view}
      SEARCH d.presentationId == @pid AND MIN_MATCH(
        BOOST(ANALYZER(PHRASE(d.text, @q), 'text_en'), 1.3),
        ANALYZER(d.text IN TOKENS(@q, 'text_en'), 'text_en'),
        BOOST(ANALYZER(d.name IN TOKENS(@q, 'norm_en'), 'norm_en'), 1.5)
      , 1)
      SORT BM25(d) DESC, TFIDF(d) DESC
      LIMIT @limit
      LET source = DOCUMENT('chunks', d._key)
      RETURN {{
        "key": d._key,
        "name": source.name,
        "text": source.text,
        "url": source.url,
        "embedding": source.embedding,
        "score": BM25(d)
      }}
    """.format(view=view)

    try:
      rows = list(self.db.aql.execute(advanced_aql, bind_vars=bind_vars))
      seeded = self._rerank(rows, query, limit)
      if len(seeded) >= limit:
        return RetrieveResponse(chunks=seeded[:limit])
    except Exception:
      seeded = []

    simple_aql = """
    FOR d IN {view}
      SEARCH d.presentationId == @pid AND ANALYZER(d.text IN TOKENS(@q, 'text_en'), 'text_en')
      SORT BM25(d) DESC
      LIMIT @limit
      LET source = DOCUMENT('chunks', d._key)
      RETURN {{
        "key": d._key,
        "name": source.name,
        "text": source.text,
        "url": source.url,
        "embedding": source.embedding,
        "score": BM25(d)
      }}
    """.format(view=view)

    rows = list(self.db.aql.execute(simple_aql, bind_vars=bind_vars))
    ranked = self._rerank(rows, query, limit)

    if seeded:
      combined = {chunk.chunkKey or f"seed-{i}": chunk for i, chunk in enumerate(seeded)}
      for chunk in ranked:
        key = chunk.chunkKey or f"simple-{len(combined)}"
        if key in combined:
          if chunk.score > combined[key].score:
            combined[key] = chunk
        else:
          combined[key] = chunk
      ranked = sorted(combined.values(), key=lambda c: c.score, reverse=True)

    if len(ranked) < limit:
      seen = {chunk.chunkKey for chunk in ranked if chunk.chunkKey}
      extras = self._semantic_backfill(presentation_id, query, limit, seen)
      if extras:
        merged = ranked + extras
        merged.sort(key=lambda chunk: chunk.score, reverse=True)
        ranked = merged[:limit]

    return RetrieveResponse(chunks=ranked)

  def _semantic_backfill(self, presentation_id: str, query: str, limit: int, seen_keys: set[str]) -> List[RetrievedChunk]:
    query_vec = _compute_embedding(query)
    if not query_vec:
      return []
    try:
      rows = list(self.db.aql.execute(
        """
        FOR c IN chunks
          FILTER c.presentationId == @pid AND c.embedding != null
          LIMIT @limit
          RETURN {
            "key": c._key,
            "name": c.name,
            "text": c.text,
            "url": c.url,
            "embedding": c.embedding
          }
        """,
        bind_vars={"pid": presentation_id, "limit": max(limit * 8, limit)}
      ))
    except Exception:
      return []

    scored: List[RetrievedChunk] = []
    for row in rows:
      key = row.get("key") or row.get("_key")
      if key and key in seen_keys:
        continue
      embedding = row.get("embedding") or []
      cos = _cosine_similarity(query_vec, embedding)
      if cos <= 0:
        continue
      scored.append(RetrievedChunk(
        name=row.get("name") or "",
        text=row.get("text") or "",
        url=row.get("url"),
        score=float(cos),
        chunkKey=key,
      ))

    scored.sort(key=lambda chunk: chunk.score, reverse=True)
    # Only return enough to fill the requested limit when combined with existing matches
    remaining = max(0, limit - len(seen_keys))
    return scored[:remaining]
