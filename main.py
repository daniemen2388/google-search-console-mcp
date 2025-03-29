from typing import List, Dict, Any, Optional, Tuple
from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
from gsc import (
    get_search_performance,
    get_indexed_urls,
    inspect_url,
    get_coverage_issues,
    get_sitemaps,
    submit_url_for_indexing,
    check_indexing_status,
    get_sites,
    get_site_performance_summary,
    get_mobile_usability_issues
)
import logging
import os
import sys # Import sys for stderr logging

# Configure logging to stderr so it doesn't interfere with stdio communication
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stderr)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("google-search-console")

@mcp.tool()
def list_sites() -> List[Dict[str, Any]]:
    """Get a list of all sites you have access to in Google Search Console.
    
    Returns:
        A list of site objects containing site URL and permission level.
    """
    return get_sites()

@mcp.tool()
def get_performance_data(
    site_url: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    dimensions: Optional[List[str]] = None,
    filter_query: Optional[str] = None,
    filter_page: Optional[str] = None,
    filter_country: Optional[str] = None,
    filter_device: Optional[str] = None,
    row_limit: int = 1000
) -> Dict[str, Any]:
    """Get search performance data from Google Search Console.
    
    Args:
        site_url: The site URL as registered in Google Search Console
        start_date: Start date for the data (defaults to 28 days ago)
        end_date: End date for the data (defaults to yesterday)
        dimensions: Data dimensions to include (query, page, country, device, date)
        filter_query: Filter results to this search query
        filter_page: Filter results to this page URL
        filter_country: Filter results to this country
        filter_device: Filter results to this device type (DESKTOP, MOBILE, TABLET)
        row_limit: Maximum number of rows to return
    
    Returns:
        Performance data including clicks, impressions, CTR, and position
    """
    # Default to last 28 days if dates not provided
    if not start_date:
        start_date = datetime.now() - timedelta(days=28)
    if not end_date:
        end_date = datetime.now() - timedelta(days=1)
        
    # Default dimensions if not provided
    if not dimensions:
        dimensions = ["query"]
        
    return get_search_performance(
        site_url=site_url,
        start_date=start_date,
        end_date=end_date,
        dimensions=dimensions,
        filter_query=filter_query,
        filter_page=filter_page,
        filter_country=filter_country,
        filter_device=filter_device,
        row_limit=row_limit
    )

@mcp.tool()
def get_url_inspection_result(site_url: str, page_url: str) -> Dict[str, Any]:
    """Inspect a specific URL in Google Search Console.
    
    Args:
        site_url: The site URL as registered in Google Search Console
        page_url: The specific page URL to inspect
    
    Returns:
        Inspection results including indexing status, mobile usability, and more
    """
    return inspect_url(site_url, page_url)

@mcp.tool()
def get_index_coverage(
    site_url: str,
    issue_filter: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Get index coverage issues from Google Search Console.
    
    Args:
        site_url: The site URL as registered in Google Search Console
        issue_filter: Filter by issue type (e.g., "SERVER_ERROR", "REDIRECT")
        start_date: Start date for the data (defaults to 90 days ago)
        end_date: End date for the data (defaults to yesterday)
    
    Returns:
        Coverage issues with counts and example URLs
    """
    if not start_date:
        start_date = datetime.now() - timedelta(days=90)
    if not end_date:
        end_date = datetime.now() - timedelta(days=1)
        
    return get_coverage_issues(
        site_url=site_url,
        issue_filter=issue_filter,
        start_date=start_date,
        end_date=end_date
    )

@mcp.tool()
def get_sitemap_data(site_url: str) -> List[Dict[str, Any]]:
    """Get information about sitemaps in Google Search Console.
    
    Args:
        site_url: The site URL as registered in Google Search Console
    
    Returns:
        List of sitemaps with status and stats
    """
    return get_sitemaps(site_url)

@mcp.tool()
def submit_url(site_url: str, page_url: str) -> Dict[str, Any]:
    """Submit a URL for indexing via Google Search Console.
    
    Args:
        site_url: The site URL as registered in Google Search Console
        page_url: The specific page URL to submit for indexing
    
    Returns:
        Submission status and details
    """
    return submit_url_for_indexing(site_url, page_url)

@mcp.tool()
def check_url_status(site_url: str, page_url: str) -> Dict[str, Any]:
    """Check the indexing status of a URL.
    
    Args:
        site_url: The site URL as registered in Google Search Console
        page_url: The specific page URL to check
    
    Returns:
        Current indexing status and details
    """
    return check_indexing_status(site_url, page_url)

@mcp.tool()
def get_site_summary(
    site_url: str,
    period_days: int = 28
) -> Dict[str, Any]:
    """Get an overall performance summary for a site.
    
    Args:
        site_url: The site URL as registered in Google Search Console
        period_days: Number of days to analyze (default 28)
    
    Returns:
        Summary data including total clicks, impressions, and trends
    """
    return get_site_performance_summary(site_url, period_days)

@mcp.tool()
def get_mobile_issues(
    site_url: str,
    issue_filter: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Get mobile usability issues from Google Search Console.
    
    Args:
        site_url: The site URL as registered in Google Search Console
        issue_filter: Filter by issue type (e.g., "CONTENT_TOO_WIDE", "CLICKABLE_ELEMENTS_TOO_CLOSE")
        start_date: Start date for the data (defaults to 90 days ago)
        end_date: End date for the data (defaults to yesterday)
    
    Returns:
        Mobile usability issues with counts and example URLs
    """
    if not start_date:
        start_date = datetime.now() - timedelta(days=90)
    if not end_date:
        end_date = datetime.now() - timedelta(days=1)
        
    return get_mobile_usability_issues(
        site_url=site_url,
        issue_filter=issue_filter,
        start_date=start_date,
        end_date=end_date
    )

def main():
    logger.info("Starting MCP server with stdio transport")
    # Run the server using stdio transport for communication with Claude Desktop
    mcp.run(transport='stdio')
    logger.info("MCP server stopped")

if __name__ == "__main__":
    main()