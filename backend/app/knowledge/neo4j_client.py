import os
from neo4j import GraphDatabase

class Neo4jClient:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "test")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Verify connection on startup; if it fails we keep driver as None
            with self.driver.session() as session:
                session.run("RETURN 1")
        except Exception as e:
            # Log the issue and continue with driver set to None so the app can still run without Neo4j
            print(f"Warning: Unable to connect to Neo4j at {uri}: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()
        else:
            print("Neo4j driver was not initialized; nothing to close.")

    def create_publication(self, doc: dict):
        """Create or merge a Publication node from a document.
        Expected keys in doc: 'id', optional 'metadata.title' and 'metadata.abstract'.
        """
        if self.driver is None:
            # Neo4j not available; skip insertion but keep workflow alive
            print("Warning: Neo4j driver not initialized; skipping Publication node creation.")
            return
        title = doc.get('metadata', {}).get('title', '')
        abstract = doc.get('metadata', {}).get('abstract', '')
        cypher = (
            "MERGE (p:Publication {id: $id}) "
            "SET p.title = $title, p.abstract = $abstract"
        )
        params = {
            "id": doc.get('id'),
            "title": title,
            "abstract": abstract,
        }
        with self.driver.session() as session:
            session.run(cypher, params)

    def run_query(self, cypher: str, parameters: dict | None = None):
        """Execute an arbitrary Cypher query and return list of records.
        Returns a list of dictionaries (record data). Raises if driver not initialized.
        """
        if self.driver is None:
            raise Exception("Neo4j driver not initialized")
        with self.driver.session() as session:
            result = session.run(cypher, parameters or {})
            return [record.data() for record in result]

        """Create or merge a Publication node from a document.
        Expected keys in doc: 'id', optional 'metadata.title' and 'metadata.abstract'.
        """
        if self.driver is None:
            # Neo4j not available; skip insertion but keep workflow alive
            print("Warning: Neo4j driver not initialized; skipping Publication node creation.")
            return
        title = doc.get('metadata', {}).get('title', '')
        abstract = doc.get('metadata', {}).get('abstract', '')
        cypher = (
            "MERGE (p:Publication {id: $id}) "
            "SET p.title = $title, p.abstract = $abstract"
        )
        params = {
            "id": doc.get('id'),
            "title": title,
            "abstract": abstract,
        }
        with self.driver.session() as session:
            session.run(cypher, params)

        """Create or merge a Publication node from a document.
        Expected keys in doc: 'id', optional 'metadata.title' and 'metadata.abstract'.
        """
        if self.driver is None:
            # Neo4j not available; skip insertion but keep workflow alive
            print("Warning: Neo4j driver not initialized; skipping Publication node creation.")
            return
        title = doc.get('metadata', {}).get('title', '')
        abstract = doc.get('metadata', {}).get('abstract', '')
        cypher = (
            "MERGE (p:Publication {id: $id}) "
            "SET p.title = $title, p.abstract = $abstract"
        )
        params = {
            "id": doc.get('id'),
            "title": title,
            "abstract": abstract,
        }
        with self.driver.session() as session:
            session.run(cypher, params)

