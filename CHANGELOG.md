# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-08-23

The 0.1.0 package could not start. This release makes it run, and adds the
tests and CI that would have caught that.

### Fixed

- **The package would not import.** `server.py` and `__main__.py` imported
  `sam_gov_mcp.cache`, which was not in the repository. Every entry point and
  all three test modules failed with `ModuleNotFoundError`. The module is now
  implemented.
- **The server could not be constructed.** `MCPServer` passed
  `cache_manager=` to its tools, but `BaseTool.__init__` did not accept it.
- **The server never served.** `start()` logged a message and returned
  without opening a transport, then the entry point logged "started
  successfully" and slept in a loop. It now runs the stdio transport.
- **`.env` was ignored.** `env_file` was declared only on `AppConfig`, so the
  nested `SamApiConfig` never read it and `SAM_API_KEY` in `.env` raised
  "Field required" — the documented setup path could not work.
- **Every valid `ptype` was rejected.** `validate_procurement_type`
  upper-cased its input and compared it against a lower-case set.
- **Packaging dropped a subpackage.** `packages` listed only `sam_gov_mcp`,
  so a non-editable install failed on `sam_gov_mcp.tools`. `pydantic-settings`
  was imported but never declared as a dependency.
- **Response fields did not match the API.** Contacts are `fullName`, the
  agency is `fullParentPathName`, the identifier is `noticeId`, and awardee
  details nest under `award.awardee`. All silently produced nulls.
- **Error bodies masked errors.** `_handle_response` called `.json()` inside
  each error branch, so an HTML error page turned a 500 into a JSON decode
  error.
- **Logs went to stdout,** which carries the JSON-RPC stream. They now go to
  stderr.

### Security

- The API key is no longer appended to the `description` URL in tool output,
  where it reached model context, transcripts, and logs.
- `.gitignore` had been emptied, leaving `.env` one `git add .` away from
  being committed. Restored.

### Added

- `cache.py`: async cache abstraction, in-memory TTL backend, and a manager
  with stable key construction — wired into the search tool, so
  `CACHE_ENABLED` finally does something.
- Retries with exponential backoff for transport failures and 5xx responses,
  honouring `SAM_MAX_RETRIES`.
- `scripts/smoke_test.py`: launches the server as a real MCP client, completes
  the handshake, and makes a tool call.
- CI on Python 3.10, 3.11, and 3.12, including a non-editable install.
- 55 tests, including suites for the cache, the search tool, and server
  construction.
- `LICENSE`, `CONTRIBUTING.md`, this changelog, and a `sam-gov-mcp` console
  script.

### Changed

- Moved to a `src/` layout with setuptools package discovery, so packaging
  mistakes cannot hide behind the source tree on `sys.path`.
- The single-file server moved to `examples/simple_server.py`, gained a
  request timeout, and returns JSON instead of a Python repr.
- Minimum Python is now 3.10, matching what `mcp` and `pydantic-settings`
  actually require. The 3.8 and 3.9 classifiers were never accurate.
- Dropped the unused `host` and `port` settings; a stdio server has no socket.
- Rewrote the README and setup guide to describe what ships.

### Removed

- `get_opportunity_details`, which returned a placeholder message while the
  README advertised it as returning contacts, attachments, and awards.
- `main.py`, a leftover `print("Hello from sam-gov!")` scaffold.

## [0.1.0]

Initial release.
