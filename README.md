<h1>Sam_MCP_Tool</h1>
<h2>The offical sam.gov opportunities api documentation</h2>
https://open.gsa.gov/api/get-opportunities-public-api/
<h2>Description</h2>
<p>The SAM.gov Get Opportunities Public API (v2) is a synchronous service that provides comprehensive details on the latest active versions of published federal procurement opportunitie</p>
<h2>Repo Intent</h2>
<p>To create an easy interface for the api to natural language prompt.</p>
SAM.gov Opportunities MCP Server
This project implements a robust Model Context Protocol (MCP) server in Python for the SAM.gov Get Opportunities Public API (v2). This server provides 100% coverage for searching and retrieving the latest active versions of federal procurement opportunities.
API Overview
The SAM.gov Get Opportunities API is a synchronous service that requires pagination. It provides details on active notices updated daily and archived notices updated weekly.
Endpoints
Production: https://api.sam.gov/opportunities/v2/search
Alpha (Testing): https://api-alpha.sam.gov/opportunities/v2/search
Authentication
A public API Key is mandatory for all requests. You can generate this key in the Account Details page on SAM.gov (Production) or alpha.sam.gov (Alpha).

--------------------------------------------------------------------------------
Tool Implementation Details
Mandatory Parameters
The following parameters must be included in every search request:
api_key: Your public API key string.
postedFrom: Start date for the search (Format: MM/dd/yyyy).
postedTo: End date for the search (Format: MM/dd/yyyy).
Constraint: The date range between postedFrom and postedTo cannot exceed one year.
Key Optional Filters
ptype (Procurement Type): Supports codes such as u (Justification), o (Solicitation), a (Award Notice), k (Combined Synopsis/Solicitation), and more.
ncode: NAICS Code (maximum of 6 digits).
status: Filter by active, inactive, archived, cancelled, or deleted.
typeOfSetAside: Use valid Set-Aside codes (e.g., SBA for Total Small Business, 8A for 8(a) Set-Aside, WOSB for Women-Owned Small Business).
Pagination
limit: Number of records per page. Max: 1000 (Default: 1).
offset: Page index for results (Default: 0).

--------------------------------------------------------------------------------
Response Mapping
The server parses the following key data from the API's JSON response:
Metadata: totalRecords, limit, and offset.
Opportunity Details: title, solicitationNumber, postedDate, and description.
Note: The description field is a link; the api_key must be appended to this link to download the actual content.
Award Information: Includes data.award.amount, data.award.date, and awardee details like name and ueiSAM.
Contacts & Links: Point of Contact details (email, phone), resourceLinks for direct attachment downloads, and uiLink for the direct SAM.gov web interface.

--------------------------------------------------------------------------------
Error Handling
The server is designed to handle and surface the following HTTP response codes and scenarios:
400 (Bad Request): Triggered by invalid date formats, date ranges exceeding one year, or non-numeric limit/offset values.
404 (No Data Found): Returned when no opportunities match the search criteria.
Authentication Errors: Handles cases where the api_key is missing or invalid.
500 (Internal Server Error): General API service failures.
