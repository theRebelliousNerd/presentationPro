import os
from arango import ArangoClient

ARANGO_URL = os.environ.get("ARANGODB_URL", "http://arangodb:8529")
ARANGO_USER = os.environ.get("ARANGODB_USER", "root")
ARANGO_PASSWORD = os.environ.get("ARANGODB_PASSWORD", os.environ.get("ARANGO_ROOT_PASSWORD", "root"))
DB_NAME = os.environ.get("ARANGODB_DB", "presentpro")


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
    # Create ArangoSearch view for chunks if not exist
    view_name = "chunks_view"
    try:
        # Try to get the view, if it doesn't exist this will raise an exception
        db.view(view_name)
    except:
        # View doesn't exist, create it
        try:
            db.create_arangosearch_view(view_name, properties={
                "links": {
                    "chunks": {
                        "analyzers": ["text_en"],
                        "includeAllFields": True
                    }
                }
            })
        except:
            # View might already exist (race condition), ignore
            pass
    return view_name

