# Contributing

Thanks for your interest. Issues and pull requests are both welcome.

## Getting set up

```bash
git clone https://github.com/44r0nd4vidg3/sam_gov_mcp.git
cd sam_gov_mcp

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

Python 3.10 or newer. No API key is needed to develop or run the tests —
the HTTP layer is mocked.

## Before you open a PR

```bash
ruff check .                 # lint
pytest                       # full suite
python scripts/smoke_test.py # launches the server, completes a real handshake
```

All three must pass. CI runs the same checks on Python 3.10, 3.11, and 3.12,
plus a non-editable install, which catches packaging mistakes that an
editable install hides.

## What good looks like here

**Every change ships with a test.** The project once had a test suite that
could not be collected, and a server that had never been started. That is the
failure mode this repo is now built to prevent, so a change without a test
that would fail before it is a change we cannot verify.

**Tests stay offline.** Mock `httpx`; never call SAM.gov from a test. See
`tests/test_api_client.py` for the pattern.

**Errors are returned, not raised, across the MCP boundary.** A tool returns
`{"status": "error", "error_type": ..., "message": ...}` so the assistant can
explain what happened. Exceptions inside the package are fine and expected —
`errors.py` has the hierarchy.

**Never put a credential in tool output.** The API key belongs in requests,
not in anything a model or a log file will see. There is a regression test for
this in `tests/test_response_mapper.py`.

**Match the response-mapping style.** SAM.gov renames fields between notice
types. Read the current name first and fall back to older ones, so a schema
change degrades to a null field rather than an exception.

## Adding a tool

1. Add a module under `src/sam_gov_mcp/tools/`.
2. Subclass `BaseTool` and implement `name`, `description`, `input_schema`,
   and `execute`.
3. Export it from `tools/__init__.py`.
4. Register it in `MCPServer.tools`.
5. Add tests covering the happy path, a validation failure, and an API error.

Please avoid shipping a tool that returns a placeholder. An advertised tool
that apologises for not existing is worse than one tool that works.

## Commit messages

A short imperative subject, then a body explaining *why*, wrapped at 72
columns. If you are fixing a bug, say what the broken behaviour was — that
line is usually more useful to the next reader than the diff.

## Reporting a bug

Include the raw SAM.gov payload where relevant (with your API key removed),
what you expected, and what you got. Field-mapping issues in particular are
almost impossible to fix without the payload.

## Security

Please do not open a public issue for a security problem. Email the address in
`pyproject.toml` instead.
