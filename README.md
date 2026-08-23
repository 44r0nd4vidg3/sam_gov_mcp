# Sam_MCP_Tool

<img width="1166" height="691" alt="Screenshot 2026-06-05 at 1 18 01 PM" src="https://github.com/user-attachments/assets/960d84de-72d4-48b0-b17b-fef77abc721f" />

## The official SAM.gov opportunities MCP server

https://open.gsa.gov/api/get-opportunities-public-api/

## Description

The SAM.gov Get Opportunities Public API (v2) is a synchronous service that provides comprehensive details on the latest active versions of published federal procurement opportunities.

## Repo Intent

To create an easy-to-use Model Context Protocol (MCP) server that enables natural language access to SAM.gov procurement opportunities through AI assistants like Claude.

## SAM.gov Opportunities MCP Server

This project implements a robust, modular Model Context Protocol (MCP) server in Python for the SAM.gov Get Opportunities Public API (v2). This server provides 100% coverage for searching and retrieving the latest federal procurement opportunities.

### Key Features

- ✅ **Modular Architecture**: Cleanly separated concerns with pluggable components
- ✅ **Full API Coverage**: Supports all SAM.gov search filters and parameters
- ✅ **Type-Safe**: Built with Pydantic for data validation
- ✅ **Async/Await**: Fully async implementation for high performance
- ✅ **Caching**: Optional in-memory caching for improved performance
- ✅ **Error Handling**: Comprehensive error handling with specific exception types
- ✅ **Well-Tested**: Extensive unit tests for all components
- ✅ **MCP Compatible**: Works with Claude, Cline, Cursor, and other MCP clients

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/44r0nd4vidg3/sam_gov_mcp.git
cd sam_gov_mcp

# Install the package
pip install -e .
```

### 2. Configuration

```bash
# Copy the environment template
cp .env.example .env

# Add your SAM.gov API Key to .env
# Get your key at: https://open.gsa.gov/api/get-opportunities-public-api/
SAM_API_KEY=your_actual_api_key_here
```

### 3. Run the Server

```bash
python -m sam_gov_mcp
```

### 4. Add to Claude Desktop

Edit `~/.config/Claude/claude_desktop_config.json`:

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

Restart Claude Desktop and the SAM.gov tools will be available!

## API Overview

The SAM.gov Get Opportunities API is a synchronous service that requires pagination. It provides details on active notices updated daily and archived notices updated weekly.

### Endpoints

- **Production**: https://api.sam.gov/opportunities/v2/search
- **Alpha (Testing)**: https://api-alpha.sam.gov/opportunities/v2/search

### Authentication

A public API Key is mandatory for all requests. You can generate this key in the Account Details page on SAM.gov (Production) or alpha.sam.gov (Alpha).

---

## Tool Implementation Details

### Mandatory Parameters

The following parameters must be included in every search request:

- **api_key**: Your public API key string.
- **postedFrom**: Start date for the search (Format: MM/dd/yyyy).
- **postedTo**: End date for the search (Format: MM/dd/yyyy).
  - *Constraint*: The date range between postedFrom and postedTo cannot exceed one year.

### Key Optional Filters

- **ptype** (Procurement Type): Supports codes such as u (Justification), o (Solicitation), a (Award Notice), k (Combined Synopsis/Solicitation), and more.
- **ncode**: NAICS Code (maximum of 6 digits).
- **status**: Filter by active, inactive, archived, cancelled, or deleted.
- **typeOfSetAside**: Use valid Set-Aside codes (e.g., SBA for Total Small Business, 8A for 8(a) Set-Aside, WOSB for Women-Owned Small Business).

### Pagination

- **limit**: Number of records per page. Max: 1000 (Default: 1).
- **offset**: Page index for results (Default: 0).

---

## Available MCP Tools

### search_opportunities

Search for federal procurement opportunities with flexible filtering.

**Example Usage:**
```
Find me all active solicitations posted between January 1 and March 31, 2024
```

**Parameters:**
- `posted_from` (required): Start date (MM/dd/yyyy)
- `posted_to` (required): End date (MM/dd/yyyy)
- `limit`: Records per page (1-1000)
- `offset`: Page offset for pagination
- `ptype`: Procurement type code
- `ncode`: NAICS code
- `status`: Status filter
- `type_of_set_aside`: Set-aside code
- `keyword`: Keyword search

### get_opportunity_details

Get detailed information about a specific opportunity (including contacts, attachments, awards).

**Parameters:**
- `opportunity_id`: The unique ID of the opportunity
- `solicitation_number`: The solicitation number

---

## Response Mapping

The server parses the following key data from the API's JSON response:

- **Metadata**: totalRecords, limit, and offset.
- **Opportunity Details**: title, solicitationNumber, postedDate, and description.
  - *Note*: The description field is a link; the api_key must be appended to this link to download the actual content.
- **Award Information**: Includes data.award.amount, data.award.date, and awardee details like name and ueiSAM.
- **Contacts & Links**: Point of Contact details (email, phone), resourceLinks for direct attachment downloads, and uiLink for the direct SAM.gov web interface.

---

## Error Handling

The server is designed to handle and surface the following HTTP response codes and scenarios:

- **400 (Bad Request)**: Triggered by invalid date formats, date ranges exceeding one year, or non-numeric limit/offset values.
- **404 (No Data Found)**: Returned when no opportunities match the search criteria.
- **Authentication Errors**: Handles cases where the api_key is missing or invalid.
- **500 (Internal Server Error)**: General API service failures.

---

## Project Structure

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

tests/                        # Comprehensive test suite
├── test_validators.py
├── test_api_client.py
├── test_response_mapper.py
└── test_cache.py

Configuration files:
├── pyproject.toml           # Project configuration
├── .env.example             # Environment template
├── .gitignore              # Git ignore rules
├── SETUP.md                # Detailed setup guide
└── README.md               # This file
```

---

## Configuration

All configuration is managed through environment variables in the `.env` file:

```env
# SAM.gov API Configuration
SAM_API_KEY=your_public_api_key_here
SAM_API_URL=https://api.sam.gov/opportunities/v2/search
SAM_ENVIRONMENT=production    # or 'alpha'
SAM_TIMEOUT=30

# MCP Server Configuration
MCP_SERVER_PORT=8000
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_DEBUG=False

# Cache Configuration
CACHE_ENABLED=False
CACHE_TTL=3600
CACHE_TYPE=memory
```

---

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test Suites

```bash
# Validators
pytest tests/test_validators.py -v

# API Client
pytest tests/test_api_client.py -v

# Response Mapper
pytest tests/test_response_mapper.py -v

# Cache
pytest tests/test_cache.py -v
```

### Run with Coverage

```bash
pytest --cov=sam_gov_mcp --cov-report=html tests/
```

---

## Usage Examples

### In Claude Desktop

1. **Simple Search:**
   ```
   Find me all active solicitations posted between January 1 and March 31, 2024
   ```

2. **Filtered Search:**
   ```
   Search for 8(a) set-aside opportunities in NAICS code 236115 from Q1 2024
   ```

3. **Pagination:**
   ```
   Get the next page of results (limit 100, offset 100) for IT services
   ```

### Direct API Call Example

```python
import asyncio
from sam_gov_mcp.server import MCPServer
from sam_gov_mcp.config import AppConfig

async def main():
    config = AppConfig()
    server = MCPServer(config=config)
    
    # Call search tool directly
    result = await server.tools["search_opportunities"].execute(
        posted_from="01/01/2024",
        posted_to="03/31/2024",
        ptype="o",
        status="active",
        limit=50
    )
    
    print(result)

asyncio.run(main())
```

---

## Performance Optimization

### Enable Caching

```env
CACHE_ENABLED=True
CACHE_TYPE=memory
CACHE_TTL=3600
```

Caching search results for 1 hour significantly improves performance for repeated queries.

---

## Extending the Server

To add new tools:

1. Create a new file in `sam_gov_mcp/tools/`
2. Extend the `BaseTool` class
3. Implement required methods: `name`, `description`, `input_schema`, `execute`
4. Register in `MCPServer.tools` dictionary
5. Add tests in `tests/`

Example:

```python
from sam_gov_mcp.tools.base import BaseTool

class MyCustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_custom_tool"
    
    @property
    def description(self) -> str:
        return "My custom tool description"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                # Define your parameters
            },
            "required": ["param1"]
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        # Implement your logic
        return {"status": "success", "data": {}}
```

---

## Troubleshooting

### Invalid API Key
```
AuthenticationError: Authentication failed: Invalid API key
```
Check your API key in the `.env` file. Get a new one at https://open.gsa.gov/api/get-opportunities-public-api/

### Date Range Too Large
```
ValidationError: Date range cannot exceed 365 days
```
Use a date range of 1 year or less between `posted_from` and `posted_to`.

### Connection Timeout
Check your internet connection and increase `SAM_TIMEOUT` in `.env` file.

### Cache Issues
Set `CACHE_ENABLED=False` to temporarily disable caching while debugging.

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

## License

MIT License - See LICENSE file for details

---

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

For SAM.gov API documentation, visit: https://open.gsa.gov/api/get-opportunities-public-api/
