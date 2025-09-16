from arango import ArangoClient
from .db import get_db
import logging

logger = logging.getLogger(__name__)

DOCS = [
    'presentations','clarifications','outlines','slides','design_specs','speaker_notes','scripts','reviews','sessions',
    'messages','project_nodes','assets','agents'
]
EDGES = ['project_edges','content_edges','activity_edges']

def ensure_graph_schema():
    db = get_db()
    # Ensure doc/edge collections
    for name in DOCS:
        try:
            if not db.has_collection(name):
                db.create_collection(name)
                logger.info(f"Created collection: {name}")
        except Exception as e:
            logger.warning(f"Collection {name} ensure failed: {e}")
    for name in EDGES:
        try:
            if not db.has_collection(name):
                db.create_collection(name, edge=True)
                logger.info(f"Created edge collection: {name}")
        except Exception as e:
            logger.warning(f"Edge collection {name} ensure failed: {e}")

    # ProjectGraph
    try:
        if not db.has_graph('ProjectGraph'):
            g = db.create_graph('ProjectGraph')
            g.create_edge_definition(
                edge_collection='project_edges',
                from_vertex_collections=['presentations','project_nodes'],
                to_vertex_collections=['project_nodes','assets','messages']
            )
            logger.info('Created ProjectGraph')
        else:
            g = db.graph('ProjectGraph')
            edefs = [e['collection'] for e in g.edge_definitions()]
            if 'project_edges' not in edefs:
                g.create_edge_definition(
                    edge_collection='project_edges',
                    from_vertex_collections=['presentations','project_nodes'],
                    to_vertex_collections=['project_nodes','assets','messages']
                )
    except Exception as e:
        logger.warning(f"ProjectGraph ensure failed: {e}")

    # ContentGraph
    try:
        if not db.has_graph('ContentGraph'):
            g = db.create_graph('ContentGraph')
            g.create_edge_definition(
                edge_collection='content_edges',
                from_vertex_collections=['presentations','outlines','slides'],
                to_vertex_collections=['outlines','slides','design_specs','speaker_notes','reviews','scripts','assets']
            )
            logger.info('Created ContentGraph')
        else:
            g = db.graph('ContentGraph')
            edefs = [e['collection'] for e in g.edge_definitions()]
            if 'content_edges' not in edefs:
                g.create_edge_definition(
                    edge_collection='content_edges',
                    from_vertex_collections=['presentations','outlines','slides'],
                    to_vertex_collections=['outlines','slides','design_specs','speaker_notes','reviews','scripts','assets']
                )
    except Exception as e:
        logger.warning(f"ContentGraph ensure failed: {e}")

    # ActivityGraph
    try:
        if not db.has_graph('ActivityGraph'):
            g = db.create_graph('ActivityGraph')
            g.create_edge_definition(
                edge_collection='activity_edges',
                from_vertex_collections=['agents'],
                to_vertex_collections=['messages','design_specs','speaker_notes','reviews','scripts']
            )
            logger.info('Created ActivityGraph')
        else:
            g = db.graph('ActivityGraph')
            edefs = [e['collection'] for e in g.edge_definitions()]
            if 'activity_edges' not in edefs:
                g.create_edge_definition(
                    edge_collection='activity_edges',
                    from_vertex_collections=['agents'],
                    to_vertex_collections=['messages','design_specs','speaker_notes','reviews','scripts']
                )
    except Exception as e:
        logger.warning(f"ActivityGraph ensure failed: {e}")

    return True
