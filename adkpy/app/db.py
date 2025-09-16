import os
from arango import ArangoClient
import logging

ARANGO_URL = os.environ.get("ARANGODB_URL", "http://arangodb:8529")
ARANGO_USER = os.environ.get("ARANGODB_USER", "root")
ARANGO_PASSWORD = os.environ.get("ARANGODB_PASSWORD", os.environ.get("ARANGO_ROOT_PASSWORD", "root"))
DB_NAME = os.environ.get("ARANGODB_DB", "presentpro")

logger = logging.getLogger(__name__)


def get_db():
    client = ArangoClient(hosts=ARANGO_URL)
    sys = client.db("_system", username=ARANGO_USER, password=ARANGO_PASSWORD)
    if not sys.has_database(DB_NAME):
        sys.create_database(DB_NAME)
    db = client.db(DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
    # collections
    if not db.has_collection("documents"):
        db.create_collection("documents")
    if not db.has_collection("chunks"):
        db.create_collection("chunks")
    if not db.has_collection("doc_edges"):
        db.create_collection("doc_edges", edge=True)
    return db


def ensure_view(db):
    """Ensure analyzers and ArangoSearch view exist and are configured.

    Returns the view name.
    """
    view_name = "chunks_view"

    # Ensure custom analyzers (best-effort; fall back to built-ins if creation fails)
    try:
        try:
            db.create_analyzer(
                name="norm_en",
                analyzer_type="norm",
                properties={"locale": "en.utf-8", "case": "lower", "accent": False},
                features=["frequency", "norm", "position"],
            )
            logger.info("Created analyzer 'norm_en'")
        except Exception:
            # Already exists or not supported
            pass
        try:
            db.create_analyzer(
                name="edge3",
                analyzer_type="ngram",
                properties={"min": 3, "max": 5, "preserveOriginal": True, "streamType": "utf8"},
                features=["frequency", "norm", "position"],
            )
            logger.info("Created analyzer 'edge3'")
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"Analyzer setup skipped: {e}")

    # Ensure view exists and is linked to fields with analyzers
    try:
        db.view(view_name)
    except Exception:
        try:
            db.create_arangosearch_view(
                view_name,
                properties={
                    "links": {
                        "chunks": {
                            "includeAllFields": False,
                            "fields": {
                                "text": {"analyzers": ["text_en", "norm_en"]},
                                "name": {"analyzers": ["norm_en", "text_en", "edge3"]},
                                "presentationId": {"analyzers": ["identity"]},
                                "docKey": {"analyzers": ["identity"]},
                            },
                        }
                    }
                },
            )
            logger.info("Created view 'chunks_view'")
        except Exception as e:
            logger.warning(f"Failed to create view '{view_name}': {e}")

    # Try to update properties (idempotent). Ignore failures (e.g., permissions).
    try:
        db.update_arangosearch_view(
            view_name,
            properties={
                "links": {
                    "chunks": {
                        "includeAllFields": False,
                        "fields": {
                            "text": {"analyzers": ["text_en", "norm_en"]},
                            "name": {"analyzers": ["norm_en", "text_en", "edge3"]},
                            "presentationId": {"analyzers": ["identity"]},
                            "docKey": {"analyzers": ["identity"]},
                        },
                    }
                }
            },
        )
        logger.info("Updated view 'chunks_view' properties")
    except Exception:
        pass

    return view_name
