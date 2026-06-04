import os
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize the MCP Server
mcp = FastMCP("SAM-Gov-API")

# The Base URL for the SAM.gov API
BASE_URL = "https://api.sam.gov/opportunities/v2/search"

from datetime import datetime, timedelta

@mcp.tool()
async def search_opportunities(
    q: str = None, 
    limit: int = 10, 
    posted_from: str = None,
    posted_to: str = None,
    ncode: str = None,
    title: str = None
) -> str:
    """
    Search for government contract opportunities on SAM.gov.
    
    Args:
        q: Optional keyword to filter results locally (e.g. 'website', 'mobile').
        limit: Number of results to return (max 1000).
        posted_from: Starting date in MM/dd/yyyy or YYYY-MM-DD format (defaults to 30 days ago).
        posted_to: Ending date in MM/dd/yyyy or YYYY-MM-DD format (defaults to today).
        ncode: NAICS code filter (e.g. '541511' for Custom Computer Programming Services).
        title: Search term specifically within the opportunity title.
    """
    api_key = os.getenv("SAM_API_KEY")
    if not api_key:
        return "Error: SAM_API_KEY environment variable not set."

    # Parse and format dates to MM/dd/yyyy
    def format_date(d_str: str, default_date: datetime) -> str:
        if not d_str:
            return default_date.strftime("%m/%d/%Y")
        # Try YYYY-MM-DD
        try:
            return datetime.strptime(d_str, "%Y-%m-%d").strftime("%m/%d/%Y")
        except ValueError:
            pass
        # Try MM/dd/yyyy
        try:
            datetime.strptime(d_str, "%m/%d/%Y")
            return d_str
        except ValueError:
            pass
        return default_date.strftime("%m/%d/%Y")

    today = datetime.now()
    thirty_days_ago = today - timedelta(days=30)
    
    formatted_from = format_date(posted_from, thirty_days_ago)
    formatted_to = format_date(posted_to, today)

    params = {
        "api_key": api_key,
        "limit": limit,
        "postedFrom": formatted_from,
        "postedTo": formatted_to
    }
    if ncode:
        params["ncode"] = ncode
    if title:
        params["title"] = title

    import re
    import html
    import asyncio

    # Clean HTML helper
    def clean_html(text: str) -> str:
        if not text:
            return ""
        text = re.sub(r'<[^>]*>', '', text)
        text = html.unescape(text)
        return re.sub(r'\s+', ' ', text).strip()

    # Semaphore to limit concurrency (max 2 concurrent requests)
    sem = asyncio.Semaphore(2)

    # Fetch description helper
    async def fetch_description(client: httpx.AsyncClient, notice_id: str) -> str:
        if not notice_id:
            return "No description available."
        async with sem:
            try:
                # Add a 0.3-second delay between requests to prevent burst limits
                await asyncio.sleep(0.3)
                params = {"api_key": api_key, "noticeid": notice_id}
                resp = await client.get("https://api.sam.gov/prod/opportunities/v1/noticedesc", params=params)
                if resp.status_code == 200:
                    desc = resp.json().get("description", "")
                    cleaned = clean_html(desc)
                    return cleaned[:400] + "..." if len(cleaned) > 400 else cleaned
                elif resp.status_code == 429:
                    return "Rate limited while fetching description."
            except Exception:
                pass
            return "Description unavailable."

    async with httpx.AsyncClient() as client:
        response = await client.get(BASE_URL, params=params)
        
        if response.status_code != 200:
            return f"Error: API returned status {response.status_code}"
            
        data = response.json()
        opportunities = data.get("opportunitiesData", [])
        
        # Concurrently fetch descriptions with throttling
        tasks = [
            fetch_description(client, o.get("noticeId"))
            for o in opportunities
        ]
        descriptions = await asyncio.gather(*tasks)
        
        results = []
        for o, desc in zip(opportunities, descriptions):
            # Extract primary POC
            poc_info = "None listed"
            pocs = o.get("pointOfContact", [])
            if pocs:
                primary_poc = next((p for p in pocs if p.get("type") == "primary"), pocs[0])
                name = primary_poc.get("fullName") or "Unknown"
                email = primary_poc.get("email") or ""
                phone = primary_poc.get("phone") or ""
                poc_info = f"{name} ({email})"
                if phone:
                    poc_info += f" - Phone: {phone}"
            
            # Local search query filtering
            match = True
            if q:
                q_lower = q.lower()
                t_match = q_lower in (o.get("title") or "").lower()
                d_match = q_lower in desc.lower()
                s_match = q_lower in (o.get("solicitationNumber") or "").lower()
                match = t_match or d_match or s_match
                
            if match:
                results.append({
                    "title": o.get("title"),
                    "solicitation": o.get("solicitationNumber"),
                    "postedDate": o.get("postedDate"),
                    "url": o.get("uiLink"),
                    "description": desc,
                    "poc": poc_info
                })
            
        return str(results)

if __name__ == "__main__":
    mcp.run()