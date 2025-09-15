# ADK/A2A

This directory contains the Python ADK agents, tools, and A2A protocol models used by the app’s orchestrator.

Structure
- agents/: Clarifier, Outline, SlideWriter, Critic, NotesPolisher, Design, ScriptWriter, Research
- tools/: ArangoGraphRAG, VisionContrast, WebSearch, Telemetry, AssetsIngest
- a2a/: message types, policies, orchestrator notes
- schemas/: slide and telemetry descriptions

Implementation Notes
- Agents are implemented as lightweight classes using the Gemini model via `adkpy/app/llm.py`.
- Tools are packaged with minimal dependencies (Arango Graph RAG, Vision contrast, Web search, Telemetry, Assets ingest).
- A2A messages and policies are defined with Pydantic models.

Optional extraction dependencies (not required)
- PDF: `PyPDF2` (preferred) or `pdfminer.six`
- DOCX: `docx2txt` (preferred) or `python-docx`
- CSV: uses Python stdlib `csv`
These enable richer text extraction in `AssetsIngestTool`. Without them, the tool still works for `.txt`/`.md` and pass-through text.

Web search
- Uses Bing when `BING_SEARCH_API_KEY` is set; falls back to DuckDuckGo HTML parsing.
- Simple caching is enabled by default (in-memory). To persist across runs, set `WEB_SEARCH_CACHE` to a JSON file path.

Next Steps
- Extend web search with richer sources and caching; wire pricing for cost telemetry.
- Add robust telemetry persistence and tracing.
- Harden ingestion and retrieval with richer chunking and sanitization.
