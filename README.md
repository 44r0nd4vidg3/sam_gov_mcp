<h1>Sam_MCP_Tool</h1>
<h2>The offical sam.gov opportunities api documentation</h2>
https://open.gsa.gov/api/get-opportunities-public-api/
<h2>Description</h2>
<p>The SAM.gov Get Opportunities Public API (v2) is a synchronous service that provides comprehensive details on the latest active versions of published federal procurement opportunitie</p>
<h2>Repo Intent</h2>
<p>To create an easy interface for the api to natural language prompt.</p>
<h3>Goal</h3>
<p>To optimize your GitHub repository's documentation and provide a clear directive for building this MCP server, you should use a technical prompt that captures the specific constraints and data structures of the SAM.gov Get Opportunities Public API (v2).
GitHub Repository Prompt: SAM.gov Opportunities MCP Server
Objective: Develop a robust Model Context Protocol (MCP) server in Python that provides 100% coverage for the SAM.gov Get Opportunities Public API v2. The server must facilitate synchronous searching of the latest active versions of federal procurement opportunities.
Core Specifications:
Endpoints: Interface with the production environment (https://api.sam.gov/opportunities/v2/search) and provide a toggle for the Alpha testing environment (https://api-alpha.sam.gov/opportunities/v2/search).
Authentication: Every request must include a mandatory api_key string parameter, which users obtain from their SAM.gov Account Details page.
Mandatory Search Parameters: Implement strict validation for postedFrom and postedTo. These must be in MM/dd/yyyy format, and the date range cannot exceed one year.
Full Parameter Support: Provide tools for all v2 request parameters, including Procurement Type (ptype: u, p, a, r, s, o, g, k, i), Solicitation Number (solnum), NAICS Code (ncode), and Set-Aside Codes (e.g., SBA, 8A, HZC, WOSB).
Pagination & Limits: Handle synchronous pagination using limit (max 1,000, default 1) and offset (default 0).
Data Mapping & Response Handling:
Response Parsing: The server must parse the complex JSON response, extracting totalRecords, title, solicitationNumber, postedDate, and the description link (noting that the api_key must be appended to this link to download the actual description).
Nested Data: Ensure deep parsing for data.award (amount, date, awardee UEI), pointOfContact (email, phone, fullname), and resourceLinks for direct attachment downloads.
Error Management: Implement logic to handle and surface specific API error messages, such as 400 Bad Request (invalid date formats or ranges), 404 No Data Found, and authentication failures ("No api_key was supplied").
Robustness Requirements:
Include a pre-request validation layer to catch invalid date ranges or non-numeric limit/offset inputs before they reach the API.
Map all 18 valid Set-Aside values (from SBA to VSS) into an accessible constant or enum to ensure valid tool inputs.</p>
