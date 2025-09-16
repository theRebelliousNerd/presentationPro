"""
Pydantic models for ArangoDB documents used by Graph RAG.

These models validate and normalize data for:
- documents: one row per uploaded asset per presentation
- chunks: paragraph-level text chunks belonging to a document
- doc_edges: edges from documents -> chunks

Note: These are not wired into the ingest/retrieve paths yet; they
exist to establish the contract and enable future validation.
"""

from typing import Literal, Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ArangoBase(BaseModel):
    """Common Arango document fields (optional)."""

    model_config = ConfigDict(populate_by_name=True)

    key: Optional[str] = Field(default=None, alias="_key")
    id: Optional[str] = Field(default=None, alias="_id")
    rev: Optional[str] = Field(default=None, alias="_rev")


class DocumentDoc(ArangoBase):
    """Top-level asset tracked per presentation.

    - presentationId: deck namespace
    - name: original file name (sanitized)
    - url: public URL (if any)
    - kind: 'image' | 'document' | 'other'
    """

    presentationId: str
    name: str
    url: Optional[str] = None
    kind: Literal["image", "document", "other"] = "document"

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        v = (v or "").strip()
        # keep alnum, dash, underscore, dot
        import re
        v = re.sub(r"[^\w\-.]+", "_", v)
        return v[:255] or "asset"


class ChunkDoc(ArangoBase):
    """Paragraph-level chunk of an asset for text search.

    - docKey: documents/_key to which this chunk belongs (not prefixed with collection)
    - name: asset file name
    - text: chunk content (trimmed)
    - url: optional pointer back to the source asset for UI linking
    """

    presentationId: str
    docKey: str
    name: str
    text: str
    url: Optional[str] = None
    embedding: Optional[List[float]] = None

    @field_validator("text")
    @classmethod
    def limit_text(cls, v: str) -> str:
        v = (v or "").strip()
        # enforce max payload size for search
        return v[:4000]


class DocEdge(BaseModel):
    """Edge from a document to a chunk.

    - _from: "documents/{docKey}"
    - _to: "chunks/{chunkKey}"
    - type: e.g., "has_chunk"
    """

    model_config = ConfigDict(populate_by_name=True)

    from_id: str = Field(alias="_from")
    to_id: str = Field(alias="_to")
    type: str = "has_chunk"
