# SAM.gov Opportunities MCP Setup Guide

## Installation

### Prerequisites
- Python 3.8+
- pip
- A valid SAM.gov API Key

### Setup Steps

1. Install the package:

```bash
pip install -e .
```

2. Install dev dependencies:

```bash
pip install -e ".[dev]"
```

3. Create `.env` file:

```bash
cp .env.example .env
```

4. Add your SAM.gov API Key to `.env`:

```env
SAM_API_KEY=your_actual_api_key_here
```

## Running the Server

### Direct Execution

```bash
python -m sam_gov_mcp
```

### Claude Desktop Configuration

Add to `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sam-gov": {
      "command": "python",
      "args": ["-m", "sam_gov_mcp"]
    }
  }
}
```

### Cline/Cursor Configuration

Add to your MCP settings:

```json
{
  "mcpServers": {
    "sam-gov": {
      "command": "python",
      "args": ["-m", "sam_gov_mcp"]
    }
  }
}
```

## Available Tools

### search_opportunities

Search for federal procurement opportunities.

**Required Parameters:**
- `posted_from` (string): Start date in MM/dd/yyyy format
- `posted_to` (string): End date in MM/dd/yyyy format

**Optional Parameters:**
- `limit` (integer, 1-1000): Records per page (default: 10)
- `offset` (integer): Page offset (default: 0)
- `ptype` (string): Procurement type
  - `u` = Justification
  - `o` = Solicitation
  - `a` = Award Notice
  - `k` = Combined Synopsis/Solicitation
- `ncode` (string): NAICS code (1-6 digits)
- `status` (string): Status filter
  - `active`, `inactive`, `archived`, `cancelled`, `deleted`
- `type_of_set_aside` (string): Set-aside type
  - `SBA`, `8A`, `WOSB`, `HUBZONE`, `VOSB`, `SDVOSB`
- `keyword` (string): Keyword search term

**Example:**
```json
{
  "posted_from": "01/01/2024",
  "posted_to": "03/31/2024",
  "limit": 50,
  "ptype": "o",
  "status": "active"
}
```

### get_opportunity_details

Get detailed information about a specific opportunity.

**Parameters (one required):**
- `opportunity_id` (string): The opportunity ID
- `solicitation_number` (string): The solicitation number

## Configuration

Set via `.env` file:

```env
# SAM.gov API
SAM_API_KEY=your_api_key
SAM_ENVIRONMENT=production
SAM_TIMEOUT=30

# MCP Server
MCP_SERVER_DEBUG=False

# Cache
CACHE_ENABLED=False
CACHE_TTL=3600
CACHE_TYPE=memory
```

## Testing

Run all tests:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=sam_gov_mcp tests/
```

Run specific test suite:

```bash
pytest tests/test_validators.py -v
pytest tests/test_api_client.py -v
pytest tests/test_response_mapper.py -v
pytest tests/test_cache.py -v
```

## Architecture

```
sam_gov_mcp/
├── __init__.py              # Package initialization
├── __main__.py              # Entry point
├── config.py                # Configuration management
├── models.py                # Pydantic data models
├── errors.py                # Custom exceptions
├── api_client.py            # SAM.gov API client
├── response_mapper.py       # Response normalization
├── validators.py            # Parameter validation
├── cache.py                 # Caching layer
├── server.py                # MCP Server implementation
└── tools/                   # MCP Tools
    ├── __init__.py
    ├── base.py              # Base tool class
    ├── search.py            # Search opportunities tool
    └── details.py           # Get opportunity details tool
```

## Performance Tips

### Enable Caching

```env
CACHE_ENABLED=True
CACHE_TYPE=memory
CACHE_TTL=3600
```

This caches search results for 1 hour to improve performance for repeated queries.

## Troubleshooting

### Invalid API Key

```
AuthenticationError: Authentication failed: Invalid API key
```

Check your API key in `.env` file.

### Date Range Too Large

```
ValidationError: Date range cannot exceed 365 days
```

Use a date range of 1 year or less.

### Connection Timeout

Check internet connection and increase `SAM_TIMEOUT` in `.env`.

## License

MIT
