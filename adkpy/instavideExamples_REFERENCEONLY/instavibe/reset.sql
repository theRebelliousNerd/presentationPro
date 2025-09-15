
-- =============================================================================
-- Schema Reset for the Bitemporal Code Knowledge Graph
-- This script is idempotent and will completely reset the database.
-- =============================================================================

--
-- Drop Edges (depend on Nodes)
--
DROP TABLE IF EXISTS Edge_HasIssue;
DROP TABLE IF EXISTS Edge_DocumentsFeature;
DROP TABLE IF EXISTS Edge_ImplementsFeature;
DROP TABLE IF EXISTS Edge_Implements;
DROP TABLE IF EXISTS Edge_Imports;
DROP TABLE IF EXISTS Edge_Calls;

--
-- Drop Tables with Foreign Keys (depend on Nodes)
--
DROP TABLE IF EXISTS DocChunks;

--
-- Drop Interleaved Tables (depend on Nodes)
--
DROP TABLE IF EXISTS CodeIssues;
DROP TABLE IF EXISTS Documents;
DROP TABLE IF EXISTS Features;
DROP TABLE IF EXISTS Classes;
DROP TABLE IF EXISTS Functions;
DROP TABLE IF EXISTS Files;

--
-- Drop Base Node Table
--
DROP TABLE IF EXISTS Nodes;


-- =============================================================================
-- Create Tables
-- =============================================================================

--
-- Node Tables
--

-- The core table for all nodes in the graph. Each node has a unique ID and a type.
CREATE TABLE Nodes (
    node_id STRING(36) NOT NULL,
    node_type STRING(255) NOT NULL, -- e.g., 'File', 'Function', 'Class', 'Feature'
    created_at TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
) PRIMARY KEY (node_id);

-- Stores details for 'File' nodes.
CREATE TABLE Files (
    node_id STRING(36) NOT NULL,
    path STRING(MAX) NOT NULL,
) PRIMARY KEY (node_id),
INTERLEAVE IN PARENT Nodes ON DELETE CASCADE;

-- Stores details for 'Function' nodes.
CREATE TABLE Functions (
    node_id STRING(36) NOT NULL,
    name STRING(MAX) NOT NULL,
    signature STRING(MAX),
    summary STRING(MAX),
) PRIMARY KEY (node_id),
INTERLEAVE IN PARENT Nodes ON DELETE CASCADE;

-- Stores details for 'Class' nodes.
CREATE TABLE Classes (
    node_id STRING(36) NOT NULL,
    name STRING(MAX) NOT NULL,
) PRIMARY KEY (node_id),
INTERLEAVE IN PARENT Nodes ON DELETE CASCADE;

-- Stores details for 'Feature' nodes.
CREATE TABLE Features (
    node_id STRING(36) NOT NULL,
    name STRING(MAX) NOT NULL,
    dossier STRING(MAX), -- The detailed narrative description
) PRIMARY KEY (node_id),
INTERLEAVE IN PARENT Nodes ON DELETE CASCADE;

-- Stores details for documentation nodes.
CREATE TABLE Documents (
    node_id STRING(36) NOT NULL,
    doc_type STRING(255) NOT NULL, -- 'APIDocument', 'Tutorial', 'WebArticle'
    title STRING(MAX) NOT NULL,
    url STRING(MAX),
) PRIMARY KEY (node_id),
INTERLEAVE IN PARENT Nodes ON DELETE CASCADE;

-- Stores chunks of documents. The embedding itself is stored in Vertex AI Vector Search.
CREATE TABLE DocChunks (
    chunk_id STRING(36) NOT NULL,
    document_node_id STRING(36) NOT NULL,
    content STRING(MAX) NOT NULL,
    created_at TIMESTAMP NOT NULL OPTIONS (allow_commit_timestamp=true),
    CONSTRAINT Fk_DocChunks_Nodes FOREIGN KEY (document_node_id) REFERENCES Nodes (node_id),
) PRIMARY KEY (chunk_id);

-- Stores details for 'CodeIssue' nodes.
CREATE TABLE CodeIssues (
    node_id STRING(36) NOT NULL,
    issue_type STRING(255) NOT NULL, -- e.g., 'Broken', 'NeedsDependencies', 'NeedsGroundingData'
    description STRING(MAX),
) PRIMARY KEY (node_id),
INTERLEAVE IN PARENT Nodes ON DELETE CASCADE;

--
-- Bitemporal Edge Tables
--

-- Edge: A function calling another function.
CREATE TABLE Edge_Calls (
    from_node_id STRING(36) NOT NULL, -- The calling function
    to_node_id STRING(36) NOT NULL,   -- The function being called
    valid_from_commit STRING(40) NOT NULL,
    valid_to_commit STRING(40),
    CONSTRAINT Fk_Calls_From FOREIGN KEY (from_node_id) REFERENCES Nodes (node_id),
    CONSTRAINT Fk_Calls_To FOREIGN KEY (to_node_id) REFERENCES Nodes (node_id),
) PRIMARY KEY (from_node_id, to_node_id, valid_from_commit);

-- Edge: A file importing another file.
CREATE TABLE Edge_Imports (
    from_node_id STRING(36) NOT NULL, -- The importing file
    to_node_id STRING(36) NOT NULL,   -- The file being imported
    valid_from_commit STRING(40) NOT NULL,
    valid_to_commit STRING(40),
    CONSTRAINT Fk_Imports_From FOREIGN KEY (from_node_id) REFERENCES Nodes (node_id),
    CONSTRAINT Fk_Imports_To FOREIGN KEY (to_node_id) REFERENCES Nodes (node_id),
) PRIMARY KEY (from_node_id, to_node_id, valid_from_commit);

-- Edge: A class implementing an interface (another class).
CREATE TABLE Edge_Implements (
    from_node_id STRING(36) NOT NULL, -- The class
    to_node_id STRING(36) NOT NULL,   -- The interface
    valid_from_commit STRING(40) NOT NULL,
    valid_to_commit STRING(40),
    CONSTRAINT Fk_Implements_From FOREIGN KEY (from_node_id) REFERENCES Nodes (node_id),
    CONSTRAINT Fk_Implements_To FOREIGN KEY (to_node_id) REFERENCES Nodes (node_id),
) PRIMARY KEY (from_node_id, to_node_id, valid_from_commit);

-- Edge: A code node (File, Function, Class) implementing a Feature.
CREATE TABLE Edge_ImplementsFeature (
    from_node_id STRING(36) NOT NULL, -- The code node
    to_node_id STRING(36) NOT NULL,   -- The feature node
    valid_from_commit STRING(40) NOT NULL,
    valid_to_commit STRING(40),
    CONSTRAINT Fk_ImplementsFeature_From FOREIGN KEY (from_node_id) REFERENCES Nodes (node_id),
    CONSTRAINT Fk_ImplementsFeature_To FOREIGN KEY (to_node_id) REFERENCES Nodes (node_id),
) PRIMARY KEY (from_node_id, to_node_id, valid_from_commit);

-- Edge: A document node documenting a Feature.
CREATE TABLE Edge_DocumentsFeature (
    from_node_id STRING(36) NOT NULL, -- The document node
    to_node_id STRING(36) NOT NULL,   -- The feature node
    valid_from_commit STRING(40) NOT NULL,
    valid_to_commit STRING(40),
    CONSTRAINT Fk_DocumentsFeature_From FOREIGN KEY (from_node_id) REFERENCES Nodes (node_id),
    CONSTRAINT Fk_DocumentsFeature_To FOREIGN KEY (to_node_id) REFERENCES Nodes (node_id),
) PRIMARY KEY (from_node_id, to_node_id, valid_from_commit);

-- Edge: A code node having a CodeIssue.
CREATE TABLE Edge_HasIssue (
    from_node_id STRING(36) NOT NULL, -- The code node
    to_node_id STRING(36) NOT NULL,   -- The issue node
    valid_from_commit STRING(40) NOT NULL,
    valid_to_commit STRING(40),
    CONSTRAINT Fk_HasIssue_From FOREIGN KEY (from_node_id) REFERENCES Nodes (node_id),
    CONSTRAINT Fk_HasIssue_To FOREIGN KEY (to_node_id) REFERENCES Nodes (node_id),
) PRIMARY KEY (from_node_id, to_node_id, valid_from_commit);
