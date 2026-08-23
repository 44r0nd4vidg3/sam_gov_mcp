# Setup Guide

Detailed setup for the SAM.gov Opportunities MCP Server. For a summary, see
the [README](README.md).

## Requirements

- Python 3.10 or newer
- A SAM.gov public API key

## Getting an API key

1. Sign in at [sam.gov](https://sam.gov) (or alpha.sam.gov for testing).
2. Open **Account Details**.
3. Request a public API key under **API Keys**.

Keys are per-account and rate limited per day. Treat one like a password.

## Installation

```bash
git clone https://github.com/44r0nd4vidg3/sam_gov_mcp.git
cd sam_gov_mcp

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e .
```

For development, install the test and lint extras instead:

```bash
pip install -e ".[dev]"
```

## Configuration

Copy the template and fill in your key:

```bash
cp .env.example .env
```

```env
SAM_API_KEY=your_actual_api_key_here
SAM_ENVIRONMENT=production
SAM_TIMEOUT=30
SAM_MAX_RETRIES=3

MCP_SERVER_LOG_LEVEL=INFO
MCP_SERVER_DEBUG=False

CACHE_ENABLED=False
CACHE_TTL=3600
CACHE_TYPE=memory
```

`.env` is gitignored. Environment variables take precedence over the file.

`.env` is read from the **current working directory**. An MCP client launches
the server from its own directory, so for client use set the key in the
client's `env` block rather than relying on `.env`.

## Verifying the install

```bash
python -c "from sam_gov_mcp.server import MCPServer; MCPServer(); print('ok')"
```

This constructs the server without connecting to SAM.gov. It fails fast if
the API key is missing or a dependency did not install.

Then start it:

```bash
sam-gov-mcp
```

It will wait silently for a client on stdin. That is correct behaviour;
`Ctrl-C` to exit.

## Connecting a client

### Claude Desktop

`claude_desktop_config.json` lives at:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sam-gov": {
      "command": "/absolute/path/to/sam_gov_mcp/.venv/bin/python",
      "args": ["-m", "sam_gov_mcp"],
      "env": {
        "SAM_API_KEY": "your_actual_api_key_here"
      }
    }
  }
}
```

Use absolute paths. Claude Desktop does not inherit your shell environment,
so `python` alone will usually resolve to the wrong interpreter. Restart the
app after editing.

### Other clients

Cline, Cursor, and Continue use the same shape: a `command`, `args`, and an
`env` block. Point them at the same interpreter.

## Running the tests

```bash
pytest
pytest --cov=sam_gov_mcp --cov-report=term-missing
pytest tests/test_search_tool.py -v
```

No network access or API key is needed; the HTTP client is mocked.

## Troubleshooting

**`ModuleNotFoundError: No module named 'sam_gov_mcp'`** — the client is
using a different interpreter than the one you installed into. Use an
absolute path to the venv's `python`.

**`ValidationError: api_key Field required`** — `SAM_API_KEY` is not set in
the process environment, and no `.env` was found in the working directory.

**Server starts but no tools appear** — check the client's MCP log. Logs go
to stderr; stdout is reserved for the JSON-RPC stream.

**`AuthenticationError: invalid or missing API key`** — the key was rejected.
Confirm it is the production key if `SAM_ENVIRONMENT=production`; production
and alpha keys are not interchangeable.

**Slow responses** — narrow the date range or lower `limit`. Set
`CACHE_ENABLED=True` to serve repeated searches from memory.
