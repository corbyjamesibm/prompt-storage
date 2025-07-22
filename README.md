# Prompt Store Application

This repository contains a skeleton implementation of a prompt storage service
with a Python backend powered by **FastAPI** and **Neo4j**, and a placeholder
directory for a Carbon Design System–based front‑end. It implements many of
the design decisions discussed in our earlier conversations:

* **Graph database storage:** Prompts and their metadata (source and tags) are
  stored in Neo4j. Using Neo4j allows you to model complex relationships and
  support advanced features like full‑text search【950625324955642†L392-L419】.
* **REST API:** A FastAPI backend (`backend/main.py`) exposes endpoints for
  creating prompts, retrieving them by ID, and performing full‑text search over
  prompt text. FastAPI automatically generates an OpenAPI specification and
  interactive documentation【519339884890229†L278-L297】.
* **Carbon Design System UI:** The `frontend/` directory is reserved for a
  React front‑end built with IBM’s Carbon components. Carbon offers component
  libraries for React, Angular, Vue, Svelte and Web Components【480330171635269†L55-L70】,
  and the React implementation (recommended here) provides a cohesive,
  enterprise‑ready look and feel.

## Backend (FastAPI + Neo4j)

The backend is contained in the `backend/` directory. To get up and running:

1. Ensure you have a Neo4j server running locally. The default connection URL
   is `bolt://localhost:7687`, with username `neo4j` and password `password`.
   You can override these by setting the `NEO4J_URI`, `NEO4J_USER` and
   `NEO4J_PASSWORD` environment variables before starting the application.
2. Install Python dependencies:

   ```bash
   python3 -m pip install -r backend/requirements.txt
   ```

3. Start the FastAPI application with Uvicorn:

   ```bash
   uvicorn backend.main:app --reload
   ```

   Once running, you can visit `http://localhost:8000/docs` to explore the
   automatically generated API documentation.

### API Endpoints

| Method | Path               | Description                                   |
|-------|--------------------|-----------------------------------------------|
| POST  | `/prompts`         | Create a new prompt (JSON body with `text`, optional `source` and `tags`). |
| GET   | `/prompts/{id}`    | Retrieve a prompt by ID.                      |
| GET   | `/prompts/search`  | Full‑text search over prompt text (query parameter `q`). |

## Front‑end Placeholder

The `frontend/` directory is intentionally empty in this skeleton. To build a
front‑end that uses IBM’s Carbon Design System:

1. Initialize a new React project inside `frontend/` using your preferred
   tooling (e.g. [Vite](https://vitejs.dev/), [Create React App](https://create-react-app.dev/), etc.).
2. Install Carbon’s React components and icons:

   ```bash
   npm install @carbon/react @carbon/icons-react
   ```

3. Build your UI using Carbon components. For example, you could create a
   prompt submission form with `TextInput` and `Button` components, and a
   searchable table of prompts using `DataTable`.
4. Configure your application to call the FastAPI endpoints for creating and
   searching prompts.

For details and component usage, see the Carbon Design System documentation
available at [carbondesignsystem.com](https://carbondesignsystem.com/)【480330171635269†L34-L38】.

## Next Steps

* **Implement chat transcript support:** When you want to support chat
  transcripts, extend the Neo4j model to include `User`, `Message` and
  `Conversation` nodes connected via `WROTE` and `PART_OF` relationships.
* **Full‑text indexing enhancements:** The current implementation uses Neo4j’s
  native full‑text index on `Prompt.text`. Consider adding additional
  indexes or ranking mechanisms for more nuanced search results.
* **MCP server:** For the full release, add a server layer that implements
  your chosen multi‑client protocol (MCP) on top of the API. This service
  can handle client authentication, message routing, and real‑time
  interactions while delegating storage to Neo4j via the existing API.

This skeleton should provide a solid foundation for building your prompt
storage system while leaving ample room for expansion as your requirements
evolve.
