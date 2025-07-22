"""
FastAPI application for storing and searching prompts in a Neo4j graph.

This module exposes a small REST API that allows clients to create prompts,
fetch individual prompts by ID, and perform simple full‑text searches over
stored prompt text. Prompts are stored as nodes in a Neo4j database,
optionally connected to tag nodes via `HAS_TAG` relationships. A full‑text
index on the `text` property enables efficient search without requiring
additional services.

Environment variables control the connection to Neo4j:

- `NEO4J_URI`: URI of the Neo4j bolt endpoint (defaults to
  `bolt://localhost:7687`)
- `NEO4J_USER`: database username (defaults to `neo4j`)
- `NEO4J_PASSWORD`: database password (defaults to `password`)

Example usage::

    uvicorn backend.main:app --reload

Then use a tool like `curl` or Postman to interact with the API:

    curl -X POST http://localhost:8000/prompts -H 'Content-Type: application/json' \
      -d '{"text": "Write a story about a robot", "source": "user", "tags": ["story","robot"]}'

    curl http://localhost:8000/prompts/<prompt_id>

    curl http://localhost:8000/prompts/search?q=robot

"""

from __future__ import annotations

import os
import uuid
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from neo4j import GraphDatabase
from pydantic import BaseModel


class PromptCreate(BaseModel):
    """Schema for creating a prompt via the API."""

    text: str
    source: Optional[str] = None
    tags: Optional[List[str]] = None



def get_driver() -> GraphDatabase.driver:
    """Create a Neo4j driver using environment variables for configuration.

    This function can be modified if your deployment uses different
    authentication mechanisms or connection protocols. The driver is
    intentionally created outside of FastAPI dependency injection to
    simplify example usage. In production you may want to manage driver
    lifecycle separately.
    """
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(user, password))



driver = get_driver()



app = FastAPI(
    title="Prompt Store API",
    description=(
        "An example service that stores prompts in a Neo4j graph and allows "
        "clients to create, retrieve and search prompts."
    ),
    version="0.1.0",
)



@app.on_event("shutdown")
def close_driver() -> None:
    """Ensure the Neo4j driver is closed when FastAPI shuts down."""
    if driver:
        driver.close()



def _create_prompt(tx, prompt_id: str, text: str, source: Optional[str], tags: List[str]):
    """Cypher transaction function to create a Prompt node and optional tags."""
    # Build the Cypher statement. The FOREACH construct is used to iterate
    # through the tag list and either create or merge tag nodes. Relationships
    # are created between the prompt and each tag.
    query = (
        "CREATE (p:Prompt {id: $id, text: $text, source: $source})\n"
        "FOREACH (tag IN $tags | MERGE (t:Tag {name: tag}) MERGE (p)-[:HAS_TAG]->(t))\n"
        "RETURN p.id AS id"
    )
    result = tx.run(query, id=prompt_id, text=text, source=source, tags=tags)
    record = result.single()
    return record["id"] if record else None



def _get_prompt(tx, prompt_id: str):
    """Fetch a prompt and its tags by ID."""
    query = (
        "MATCH (p:Prompt {id: $id}) "
        "OPTIONAL MATCH (p)-[:HAS_TAG]->(t:Tag) "
        "RETURN p, collect(t.name) AS tags"
    )
    record = tx.run(query, id=prompt_id).single()
    if record:
        p = record["p"]
        return {
            "id": p["id"],
            "text": p["text"],
            "source": p.get("source"),
            "tags": record["tags"],
        }
    return None



def _search_prompts(tx, query_string: str):
    """Search prompts by text using a full‑text index. Returns a list of matches."""
    # Ensure full‑text index exists. This will run every time search is called but
    # has no effect if the index already exists. You can move this to an
    # initialization step in production.
    tx.run(
        "CREATE FULLTEXT INDEX promptTextIndex IF NOT EXISTS FOR (p:Prompt) ON EACH [p.text]"
    )
    search_query = (
        "CALL db.index.fulltext.queryNodes('promptTextIndex', $q) "
        "YIELD node, score "
        "RETURN node.id AS id, node.text AS text, node.source AS source, score "
        "ORDER BY score DESC LIMIT 10"
    )
    result = tx.run(search_query, q=query_string)
    return [
        {
            "id": record["id"],
            "text": record["text"],
            "source": record["source"],
            "score": record["score"],
        }
        for record in result
    ]



@app.post("/prompts", summary="Create a new prompt")
async def create_prompt(prompt: PromptCreate):
    """Create a prompt in Neo4j and return its identifier."""
    prompt_id = str(uuid.uuid4())
    tags = prompt.tags or []
    with driver.session() as session:
        created_id = session.write_transaction(
            _create_prompt, prompt_id, prompt.text, prompt.source, tags
        )
    return {"id": created_id}



@app.get("/prompts/{prompt_id}", summary="Get prompt details by ID")
async def get_prompt(prompt_id: str):
    """Retrieve a prompt and its tags by ID."""
    with driver.session() as session:
        prompt = session.read_transaction(_get_prompt, prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt



@app.get("/prompts/search", summary="Search prompts by text")
async def search_prompts(q: str = Query(..., description="Search query")):
    """Search prompts by text using the full‑text index."""
    with driver.session() as session:
        results = session.read_transaction(_search_prompts, q)
    return results
