# SAM.gov Opportunities MCP Server

<img width="1166" height="691" alt="Screenshot" src="https://github.com/user-attachments/assets/960d84de-72d4-48b0-b17b-fef77abc721f" />

An unofficial [Model Context Protocol](https://modelcontextprotocol.io) server for the
[SAM.gov Get Opportunities Public API (v2)](https://open.gsa.gov/api/get-opportunities-public-api/),
so an AI assistant can search federal procurement opportunities in natural language.

> Not affiliated with, or endorsed by, GSA or SAM.gov.

## Status

Alpha. One tool is implemented and covered by tests: `search_opportunities`.
Response field mappings are written against the published v2 schema; if you
hit a field that comes back null, please open an issue with the raw payload.

## Which server should I run?

The repo contains two implementations. They do not run together — pick one.

| | `sam_gov_mcp/` (package) | `sam_server.py` (simple mode) |
|---|---|---|
| Structure | modular, typed, tested | one file, ~150 lines |
| Output | normalized JSON models | flat JSON list |
| Descriptions | returns the description URL | fetches and cleans description text |
| Caching | optional in-memory TTL cache | none |
| Config | `.env` or environment | `SAM_API_KEY` only |
| Recommended for | most users | quick local experiments |

`sam_gov_mcp/` is the canonical implementation. `sam_server.py` is kept
because its inline description fetching is genuinely useful; be aware that it
issues one extra API call per result (throttled to two at a time), so large
`limit` values are slow enough to hit client timeouts.

## Quick start

### 1. Install

```bash
git clone https://github.com/44r0nd4vidg3/sam_gov_mcp.git
cd sam_gov_mcp
pip install -e .
```

Requires Python 3.10 or newer.

### 2. Configure

```bash
cp .env.example .env
```

Then edit `.env` and set your key:

```env
SAM_API_KEY=your_actual_api_key_here
```

Get a key from your Account Details page on [SAM.gov](https://sam.gov)
(production) or alpha.sam.gov (testing). `.env` is gitignored — do not commit
a real key.

### 3. Run

```bash
sam-gov-mcp          # installed console script
python -m sam_gov_mcp # equivalent
```

The server speaks the stdio transport. Run directly it will simply wait for a
client on stdin, which is expected.

### 4. Add to Claude Desktop

Edit `claude_desktop_config.json`
(macOS: `~/Library/Application Support/Claude/`,
Linux: `~/.config/Claude/`):

```json
{
  "mcpServers": {
    "sam-gov": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["-m", "sam_gov_mcp"],
      "env": {
        "SAM_API_KEY": "your_actual_api_key_here"
      }
    }
  }
}
```

Use an absolute path to the interpreter of the environment you installed
into — Claude Desktop does not inherit your shell's `PATH` or virtualenv.
Restart Claude Desktop afterwards.

To run simple mode instead, point `args` at the script:
`"args": ["/absolute/path/to/sam_server.py"]`.

## Available tools

### `search_opportunities`

Search federal procurement opportunities.

| Parameter | Required | Description |
|---|---|---|
| `posted_from` | yes | Start date, `MM/dd/yyyy` |
| `posted_to` | yes | End date, `MM/dd/yyyy` |
| `limit` | no | Records per page, 1-1000 (default 10) |
| `offset` | no | Page offset (default 0) |
| `ptype` | no | Procurement type: `u`, `o`, `a`, `k`, `s`, `p` |
| `ncode` | no | NAICS code, 1-6 digits |
| `status` | no | `active`, `inactive`, `archived`, `cancelled`, `deleted` |
| `type_of_set_aside` | no | `SBA`, `8A`, `WOSB`, `HUBZONE`, `VOSB`, `SDVOSB` |
| `keyword` | no | Keyword search term |

The date range cannot exceed one year — a SAM.gov constraint, validated
before the request is sent.

Example prompts:

```
Find active solicitations posted between January 1 and March 31, 2024
Search 8(a) set-aside opportunities in NAICS 236115 from Q1 2024
Get the next page of results (limit 100, offset 100)
```

Results are returned as JSON:

```json
{
  "status": "success",
  "cached": false,
  "data": {
    "pagination": { "total_records": 42, "limit": 10, "offset": 0 },
    "opportunities": [
      {
        "id": "...",
        "title": "...",
        "solicitation_number": "...",
        "posted_date": "2024-01-02T00:00:00",
        "description": "https://api.sam.gov/.../description",
        "agency": "...",
        "ui_link": "https://sam.gov/opp/..."
      }
    ]
  }
}
```

`description` is a URL, not prose. Fetching it requires appending your API
key. The server deliberately does **not** do that: tool output is handed to a
language model and ends up in transcripts and logs, and a credential does not
belong there. Fetch it server-side if you need the text, or use simple mode,
which retrieves and cleans it before returning.

Errors are returned in the same envelope rather than raised, so the model
gets something it can act on:

```json
{
  "status": "error",
  "error_type": "validation_error",
  "message": "Date range cannot exceed 365 days. Your range: 730 days"
}
```

`error_type` is one of `validation_error`, `api_error`, or
`unexpected_error`. API failures map to typed exceptions internally:
401/403 → `AuthenticationError`, 400 → `BadRequestError`,
404 → `NotFoundError`, 429 → rate-limit `APIError`, 5xx → `ServerError`.
Transport failures and 5xx responses are retried with exponential backoff
(`SAM_MAX_RETRIES`, default 3).

## Configuration

All settings are read from the environment, or from `.env` in the working
directory.

| Variable | Default | Description |
|---|---|---|
| `SAM_API_KEY` | — | **Required.** SAM.gov public API key |
| `SAM_API_URL` | production search URL | Override the endpoint |
| `SAM_ENVIRONMENT` | `production` | `production` or `alpha` |
| `SAM_TIMEOUT` | `30` | Request timeout, seconds |
| `SAM_MAX_RETRIES` | `3` | Attempts for transport/5xx failures |
| `MCP_SERVER_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `MCP_SERVER_DEBUG` | `False` | Debug mode |
| `CACHE_ENABLED` | `False` | Enable in-memory caching |
| `CACHE_TTL` | `3600` | Cache lifetime, seconds |
| `CACHE_TYPE` | `memory` | `memory` or `none` |

There is no host or port setting: the stdio transport means the MCP client
launches the process and talks to it over a pipe.

With `CACHE_ENABLED=True`, identical searches within the TTL are served from
memory and the response carries `"cached": true`. The cache lives in the
server process and is lost on restart.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

CI runs the test suite and linter on Python 3.10, 3.11, and 3.12, and
separately asserts that the server can be constructed — the check that would
have caught the import and wiring failures fixed in 0.2.0.

## Project structure

```
sam_gov_mcp/
├── __init__.py          # Package initialization
├── __main__.py          # Entry point (stdio transport)
├── config.py            # Configuration (env + .env)
├── models.py            # Pydantic data models
├── errors.py            # Custom exceptions
├── api_client.py        # SAM.gov HTTP client
├── response_mapper.py   # Response normalization
├── validators.py        # Parameter validation
├── cache.py             # Caching layer
├── server.py            # MCP server
└── tools/
    ├── base.py          # Base tool class
    └── search.py        # search_opportunities

tests/
├── test_api_client.py
├── test_cache.py
├── test_response_mapper.py
├── test_search_tool.py
├── test_server.py
└── test_validators.py

sam_server.py            # Simple mode (single-file server)
```

## Adding a tool

1. Add a module under `sam_gov_mcp/tools/`.
2. Subclass `BaseTool` and implement `name`, `description`, `input_schema`,
   and `execute`.
3. Export it from `sam_gov_mcp/tools/__init__.py`.
4. Register it in `MCPServer.tools`.
5. Add tests.

```python
from sam_gov_mcp.tools.base import BaseTool


class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "What this tool does."

    @property
    def input_schema(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> dict:
        return {"status": "success", "data": {}}
```

## Troubleshooting

**Server shows no tools in Claude Desktop.** Run the command from your config
by hand — most failures are a wrong interpreter path or a missing
`SAM_API_KEY`. Errors go to stderr; Claude Desktop's MCP log captures them.

**`ValidationError: api_key Field required`.** No `SAM_API_KEY` in the
environment or in a `.env` in the working directory. Claude Desktop does not
run from your project directory, so prefer the config's `env` block.

**`Date range cannot exceed 365 days`.** A SAM.gov limit; narrow the range.

**Rate limited.** SAM.gov enforces per-key daily limits. Set
`CACHE_ENABLED=True` to avoid repeating identical searches.

## Roadmap

- Optional server-side description fetching in the package (simple mode does
  this today)
- A details tool, once it can return more than what search already provides
- Verification of response mappings against live payloads across notice types

## Contributing

Fork, branch, add tests, open a PR. CI must pass.

## License

MIT — see [LICENSE](LICENSE).
