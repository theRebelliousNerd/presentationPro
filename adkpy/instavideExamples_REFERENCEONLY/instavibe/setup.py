import os
import uuid
from google.cloud import spanner
from google.api_core import exceptions

# --- Configuration ---
INSTANCE_ID = os.environ.get("SPANNER_INSTANCE_ID", "instavibe-graph-instance")
DATABASE_ID = os.environ.get("SPANNER_DATABASE_ID", "graphdb")
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")

def create_database(instance, database_id):
    """Creates a new Spanner database, dropping it first if it exists."""
    db = instance.database(database_id)
    if db.exists():
        print(f"Database '{database_id}' already exists. Dropping it first.")
        db.drop()
    print(f"Creating database: {database_id}")
    operation = db.create()
    print("Waiting for database creation to complete...")
    operation.result(120) # Wait up to 120 seconds
    print("Database created successfully.")
    return db

def execute_ddl_from_file(database, ddl_file):
    """Executes a DDL script from a file on the given database."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ddl_path = os.path.join(script_dir, ddl_file)
    print(f"Reading DDL statements from {ddl_path}...")
    with open(ddl_path, 'r') as f:
        ddl_statements = f.read().split(';')
        ddl_statements = [s.strip() for s in ddl_statements if s.strip()]

    print(f"Executing {len(ddl_statements)} DDL statements...")
    for i, statement in enumerate(ddl_statements):
        print(f"  Executing statement {i+1}/{len(ddl_statements)}: {statement[:80]}...")
        try:
            operation = database.update_ddl([statement])
            operation.result(300) # Wait up to 5 minutes for each DDL statement
        except exceptions.GoogleAPICallError as e:
            print(f"    ERROR executing DDL: {e}")
            print("    Skipping statement and continuing...")
    print("Schema setup complete.")

def seed_initial_feature(database):
    """Seeds the database with the initial 'AI Developer Assistant' feature."""
    feature_id = str(uuid.uuid4())
    dossier_content = ("""
    This feature represents the AI Developer Assistant itself. Its purpose is to
    act as a personalized, codebase-aware AI that actively participates in the
    software development lifecycle. It is accessed via a CLI and leverages this
    very knowledge graph to understand, query, and modify the application's
    codebase and associated documentation.
    """).strip()

    print("Seeding initial feature...")
    with database.batch() as batch:
        # Insert into Nodes table
        batch.insert(
            table="Nodes",
            columns=["node_id", "node_type"],
            values=[(feature_id, "Feature")]
        )
        # Insert into Features table
        batch.insert(
            table="Features",
            columns=["node_id", "name", "dossier"],
            values=[(feature_id, "AI Developer Assistant", dossier_content)]
        )
    print(f"Successfully seeded Feature: AI Developer Assistant (ID: {feature_id})")

def main():
    """Main function to set up the database."""
    if not PROJECT_ID:
        print("Error: GOOGLE_CLOUD_PROJECT environment variable not set.")
        return

    print("--- Starting Database Setup ---")
    spanner_client = spanner.Client(project=PROJECT_ID)
    try:
        instance = spanner_client.instance(INSTANCE_ID)
        if not instance.exists():
            print(f"Error: Spanner instance '{INSTANCE_ID}' not found in project '{PROJECT_ID}'.")
            print("Please create the instance in the Google Cloud Console.")
            return

        # 1. Create (or re-create) the database
        db = create_database(instance, DATABASE_ID)

        # 2. Apply the schema from the reset.sql file
        execute_ddl_from_file(db, "reset.sql")

        # 3. Seed the database with initial data
        seed_initial_feature(db)

        print("--- Database setup finished successfully! ---")

    except exceptions.NotFound:
        print(f"Error: Spanner instance '{INSTANCE_ID}' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()