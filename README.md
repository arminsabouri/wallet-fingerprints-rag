# Graph RAG

Graph-based Bitcoin wallet fingerprinting using code-graph-rag + Memgraph + Claude.

## How it works

1. **`graph`** — parses wallet source code, builds a Memgraph knowledge graph (functions, classes, call edges), and generates UniXcoder semantic embeddings stored locally via Qdrant.
2. **`agent-fingerprint`** — runs heuristic fingerprinting using claude-agent-sdk with the code-graph-rag MCP server.

## Requirements

- Python 3.12+
- Memgraph running (Docker)
- `ANTHROPIC_API_KEY` set in environment

## Setup

```bash
cd graph-rag
uv sync
```

Start Memgraph:

```bash
docker run -d \
  -p 7687:7687 -p 3000:3000 \
  memgraph/memgraph-mage:latest
```

## Usage

### Step 1: Build the graph

```bash
uv run python -m graph_rag graph \
  --repo-path /path/to/wallet \
  --project-name sparrow-1.8.0 \
  --exclude "tests/**" \
  --clean
```

This builds the Memgraph graph and generates semantic embeddings into `.qdrant_code_embeddings/` in the current directory.

Flags:

- `--repo-path`: path to the wallet source repository (required)
- `--project-name`: label stored in graph metadata
- `--clean`: wipe Memgraph before ingesting
- `--exclude`: glob patterns to skip (merged with `.cgrignore` if present)
- `--batch-size`: override ingest batch size

### Step 2: Run fingerprinting

```bash
uv run python -m graph_rag agent-fingerprint \
  --project-name sparrow-1.8.0 \
  --repo-path /path/to/wallet \
  --output sparrow-fingerprints.json \
  --pretty
```

Requires the code-graph-rag binary on PATH (or `--cgr-bin`). Use `--qdrant-path` to override the default Qdrant DB location.

Flags:

- `--project-name`: must match the name used during graph build (required)
- `--repo-path`: path to the wallet repository (required)
- `--output`: output JSON file (default: `fingerprints.json`)
- `--pretty`: indent the output JSON
- `--qdrant-path`: path to local Qdrant DB (overrides `QDRANT_DB_PATH` env var)
- `--model`: Claude model to use (default: `claude-sonnet-4-6`)
- `--cgr-bin`: path to code-graph-rag binary (auto-detected from PATH if omitted)
- `--concurrency`: max heuristics in parallel (default: 3)
- `--save-transcripts`: save full agent transcripts to `<output>.transcripts.json`

### Output format

```json
{
  "project_name": "sparrow-1.8.0",
  "fingerprints": {
    "tx_version": 2,
    "bip69_sorting": 0,
    "low_r_grinding": 1,
    "input_types": "P2PKH, P2WPKH, P2TR",
    ...
  }
}
```

Values are `1`/`0`/`-1` for binary heuristics, or a short string for text heuristics. `-1` means insufficient evidence in the code.
