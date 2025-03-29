import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Path to token and credentials files
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.json')

# OAuth2 scopes needed for Google Search Console
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

def get_service():
    """Get an authenticated service instance for Google Search Console API."""
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as token:
            creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)
    
    # If no valid credentials available, authenticate user
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    "credentials.json file not found. Please download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for future use
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    # Return the Search Console service
    return build('searchconsole', 'v1', credentials=creds)

def get_sites() -> List[Dict[str, Any]]:
    """Get a list of all sites in Google Search Console."""
    try:
        service = get_service()
        sites = service.sites().list().execute()
        
        return [
            {
                "url": site['siteUrl'],
                "permission_level": site.get('permissionLevel', 'UNKNOWN')
            }
            for site in sites.get('siteEntry', [])
        ]
    except Exception as e:
        return [{"error": str(e)}]

def get_search_performance(
    site_url: str,
    start_date: datetime,
    end_date: datetime,
    dimensions: List[str],
    filter_query: Optional[str] = None,
    filter_page: Optional[str] = None,
    filter_country: Optional[str] = None,
    filter_device: Optional[str] = None,
    row_limit: int = 1000
) -> Dict[str, Any]:
    """Get search performance data from Google Search Console."""
    try:
        service = get_service()
        
        # Build request body
        request_body = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
            'dimensions': dimensions,
            'rowLimit': row_limit,
            'dataState': 'ALL'  # Include all data (final and non-final)
        }
        
        # Add dimension filters if provided
        dimension_filter_groups = []
        
        if filter_query:
            dimension_filter_groups.append({
                'filters': [{
                    'dimension': 'query',
                    'operator': 'contains',
                    'expression': filter_query
                }]
            })
            
        if filter_page:
            dimension_filter_groups.append({
                'filters': [{
                    'dimension': 'page',
                    'operator': 'equals',
                    'expression': filter_page
                }]
            })
            
        if filter_country:
            dimension_filter_groups.append({
                'filters': [{
                    'dimension': 'country',
                    'operator': 'equals',
                    'expression': filter_country
                }]
            })
            
        if filter_device:
            dimension_filter_groups.append({
                'filters': [{
                    'dimension': 'device',
                    'operator': 'equals',
                    'expression': filter_device
                }]
            })
            
        if dimension_filter_groups:
            request_body['dimensionFilterGroups'] = dimension_filter_groups
        
        # Execute the request
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body=request_body
        ).execute()
        
        # Process and format the response
        rows = response.get('rows', [])
        formatted_rows = []
        
        for row in rows:
            formatted_row = {
                'clicks': row.get('clicks', 0),
                'impressions': row.get('impressions', 0),
                'ctr': row.get('ctr', 0),
                'position': row.get('position', 0)
            }
            
            # Add dimension values
            dimensions_values = row.get('keys', [])
            for i, dimension in enumerate(dimensions):
                if i < len(dimensions_values):
                    formatted_row[dimension] = dimensions_values[i]
            
            formatted_rows.append(formatted_row)
        
        return {
            'rows': formatted_rows,
            'total_rows': len(formatted_rows),
            'date_range': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'dimensions': dimensions
        }
    except Exception as e:
        return {'error': str(e)}

def inspect_url(site_url: str, page_url: str) -> Dict[str, Any]:
    """Inspect a specific URL in Google Search Console."""
    try:
        service = get_service()
        
        # Build request body
        request_body = {
            'inspectionUrl': page_url,
            'siteUrl': site_url
        }
        
        # Execute the request
        response = service.urlInspection().index().inspect(body=request_body).execute()
        
        # Extract the relevant information
        inspection_result = response.get('inspectionResult', {})
        index_status = inspection_result.get('indexStatusResult', {})
        mobile_usability = inspection_result.get('mobileUsabilityResult', {})
        rich_results = inspection_result.get('richResultsResult', {})
        
        return {
            'page_url': page_url,
            'inspection_state': inspection_result.get('inspectionResultState', 'UNKNOWN'),
            'index_status': {
                'verdict': index_status.get('verdict', 'UNKNOWN'),
                'coverage_state': index_status.get('coverageState', 'UNKNOWN'),
                'last_crawl': index_status.get('lastCrawlTime', 'UNKNOWN'),
                'page_fetch': index_status.get('pageFetchState', 'UNKNOWN'),
                'indexing_state': index_status.get('indexingState', 'UNKNOWN'),
                'robots_txt_state': index_status.get('robotsTxtState', 'UNKNOWN'),
                'canonical_url': index_status.get('googleCanonical', page_url)
            },
            'mobile_usability': {
                'verdict': mobile_usability.get('verdict', 'UNKNOWN'),
                'issues': mobile_usability.get('issues', [])
            },
            'rich_results': {
                'verdict': rich_results.get('verdict', 'UNKNOWN'),
                'detected_items': rich_results.get('detectedItems', [])
            },
            'raw_response': response  # Include full response for reference
        }
    except Exception as e:
        return {'error': str(e)}

def get_coverage_issues(
    site_url: str,
    issue_filter: Optional[str] = None,
    start_date: datetime = None,
    end_date: datetime = None
) -> Dict[str, Any]:
    """Get index coverage issues from Google Search Console."""
    try:
        service = get_service()
        
        # Build request body for the Index Coverage report
        request_body = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
            'dimensions': ['issue'],
            'dataState': 'ALL'
        }
        
        if issue_filter:
            request_body['dimensionFilterGroups'] = [{
                'filters': [{
                    'dimension': 'issue',
                    'operator': 'equals',
                    'expression': issue_filter
                }]
            }]
        
        # Execute the request
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body=request_body
        ).execute()
        
        # Process and format the response
        rows = response.get('rows', [])
        formatted_issues = []
        
        for row in rows:
            issue_type = row.get('keys', ['UNKNOWN'])[0]
            
            # Get example URLs for this issue
            examples_request = {
                'dimensions': ['page'],
                'dimensionFilterGroups': [{
                    'filters': [{
                        'dimension': 'issue',
                        'operator': 'equals',
                        'expression': issue_type
                    }]
                }],
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'rowLimit': 10,
                'dataState': 'ALL'
            }
            
            examples_response = service.searchanalytics().query(
                siteUrl=site_url,
                body=examples_request
            ).execute()
            
            example_urls = [example.get('keys', [''])[0] for example in examples_response.get('rows', [])]
            
            formatted_issues.append({
                'issue_type': issue_type,
                'count': int(row.get('clicks', 0)),  # In coverage report, clicks represent count
                'example_urls': example_urls
            })
        
        return {
            'issues': formatted_issues,
            'total_issues': len(formatted_issues),
            'date_range': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }
        }
    except Exception as e:
        return {'error': str(e)}

def get_sitemaps(site_url: str) -> List[Dict[str, Any]]:
    """Get information about sitemaps in Google Search Console."""
    try:
        service = get_service()
        
        # Get list of sitemaps
        sitemaps_response = service.sitemaps().list(siteUrl=site_url).execute()
        
        formatted_sitemaps = []
        for sitemap in sitemaps_response.get('sitemap', []):
            # Get more detailed information about each sitemap
            sitemap_url = sitemap.get('path', '')
            
            if sitemap_url:
                try:
                    detail_response = service.sitemaps().get(
                        siteUrl=site_url,
                        feedpath=sitemap_url
                    ).execute()
                    
                    formatted_sitemaps.append({
                        'url': sitemap_url,
                        'status': detail_response.get('contents', [{}])[0].get('type', 'UNKNOWN'),
                        'last_downloaded': detail_response.get('lastDownloaded', 'UNKNOWN'),
                        'warnings': detail_response.get('warnings', 0),
                        'errors': detail_response.get('errors', 0),
                        'contents': [{
                            'type': content.get('type', 'UNKNOWN'),
                            'submitted': content.get('submitted', 0),
                            'indexed': content.get('indexed', 0)
                        } for content in detail_response.get('contents', [])]
                    })
                except:
                    # If detailed info fails, include basic info
                    formatted_sitemaps.append({
                        'url': sitemap_url,
                        'status': sitemap.get('lastSubmitted', 'UNKNOWN'),
                        'warnings': sitemap.get('warnings', 0),
                        'errors': sitemap.get('errors', 0)
                    })
        
        return formatted_sitemaps
    except Exception as e:
        return [{'error': str(e)}]

def submit_url_for_indexing(site_url: str, page_url: str) -> Dict[str, Any]:
    """Submit a URL for indexing via Google Search Console.
    
    Note: This API feature is not fully available through the public API,
    but this function will simulate the expected behavior.
    """
    try:
        # Inspect the URL first to check current status
        inspection_result = inspect_url(site_url, page_url)
        
        # Return a simulated response (actual API doesn't fully support this)
        return {
            'url': page_url,
            'site': site_url,
            'submission_status': 'SUBMITTED_FOR_INDEXING',
            'current_status': inspection_result.get('index_status', {}).get('verdict', 'UNKNOWN'),
            'message': 'URL submitted for indexing. It may take some time to process.',
            'note': 'This is a simulated response as the Google Search Console API does not fully support direct indexing requests.'
        }
    except Exception as e:
        return {'error': str(e)}

def check_indexing_status(site_url: str, page_url: str) -> Dict[str, Any]:
    """Check the indexing status of a URL."""
    try:
        # This just wraps the inspect_url function with a more focused response
        inspection_result = inspect_url(site_url, page_url)
        
        index_status = inspection_result.get('index_status', {})
        
        return {
            'url': page_url,
            'is_indexed': index_status.get('verdict') == 'PASS',
            'status': index_status.get('coverageState', 'UNKNOWN'),
            'last_crawl': index_status.get('lastCrawlTime', 'UNKNOWN'),
            'canonical_url': index_status.get('googleCanonical', page_url),
            'robots_txt_state': index_status.get('robotsTxtState', 'UNKNOWN'),
            'indexing_state': index_status.get('indexingState', 'UNKNOWN'),
            'page_fetch': index_status.get('pageFetchState', 'UNKNOWN')
        }
    except Exception as e:
        return {'error': str(e)}

def get_site_performance_summary(site_url: str, period_days: int = 28) -> Dict[str, Any]:
    """Get an overall performance summary for a site."""
    try:
        service = get_service()
        
        # Calculate date ranges
        end_date = datetime.now() - timedelta(days=1)
        start_date = end_date - timedelta(days=period_days)
        
        # Previous period for comparison
        previous_end_date = start_date - timedelta(days=1)
        previous_start_date = previous_end_date - timedelta(days=period_days)
        
        # Get current period data
        current_request = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
            'dimensions': ['date'],
            'rowLimit': period_days,
            'dataState': 'ALL'
        }
        
        current_response = service.searchanalytics().query(
            siteUrl=site_url,
            body=current_request
        ).execute()
        
        # Get previous period data
        previous_request = {
            'startDate': previous_start_date.strftime('%Y-%m-%d'),
            'endDate': previous_end_date.strftime('%Y-%m-%d'),
            'dimensions': ['date'],
            'rowLimit': period_days,
            'dataState': 'ALL'
        }
        
        previous_response = service.searchanalytics().query(
            siteUrl=site_url,
            body=previous_request
        ).execute()
        
        # Calculate totals for current period
        current_totals = {
            'clicks': sum(row.get('clicks', 0) for row in current_response.get('rows', [])),
            'impressions': sum(row.get('impressions', 0) for row in current_response.get('rows', [])),
            'ctr': sum(row.get('clicks', 0) for row in current_response.get('rows', [])) / 
                   sum(row.get('impressions', 0) for row in current_response.get('rows', []))
                   if sum(row.get('impressions', 0) for row in current_response.get('rows', [])) > 0 else 0,
            'position': sum(row.get('position', 0) * row.get('impressions', 0) 
                          for row in current_response.get('rows', [])) /
                       sum(row.get('impressions', 0) for row in current_response.get('rows', []))
                       if sum(row.get('impressions', 0) for row in current_response.get('rows', [])) > 0 else 0
        }
        
        # Calculate totals for previous period
        previous_totals = {
            'clicks': sum(row.get('clicks', 0) for row in previous_response.get('rows', [])),
            'impressions': sum(row.get('impressions', 0) for row in previous_response.get('rows', [])),
            'ctr': sum(row.get('clicks', 0) for row in previous_response.get('rows', [])) / 
                   sum(row.get('impressions', 0) for row in previous_response.get('rows', []))
                   if sum(row.get('impressions', 0) for row in previous_response.get('rows', [])) > 0 else 0,
            'position': sum(row.get('position', 0) * row.get('impressions', 0) 
                          for row in previous_response.get('rows', [])) /
                       sum(row.get('impressions', 0) for row in previous_response.get('rows', []))
                       if sum(row.get('impressions', 0) for row in previous_response.get('rows', [])) > 0 else 0
        }
        
        # Calculate changes
        changes = {
            'clicks_change': ((current_totals['clicks'] - previous_totals['clicks']) / 
                             previous_totals['clicks'] * 100) if previous_totals['clicks'] > 0 else 0,
            'impressions_change': ((current_totals['impressions'] - previous_totals['impressions']) / 
                                  previous_totals['impressions'] * 100) if previous_totals['impressions'] > 0 else 0,
            'ctr_change': ((current_totals['ctr'] - previous_totals['ctr']) / 
                          previous_totals['ctr'] * 100) if previous_totals['ctr'] > 0 else 0,
            'position_change': (previous_totals['position'] - current_totals['position'])
        }
        
        # Format daily data for charts
        daily_data = [
            {
                'date': row.get('keys', [''])[0],
                'clicks': row.get('clicks', 0),
                'impressions': row.get('impressions', 0),
                'ctr': row.get('ctr', 0),
                'position': row.get('position', 0)
            }
            for row in current_response.get('rows', [])
        ]
        
        return {
            'site_url': site_url,
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'days': period_days,
            'totals': current_totals,
            'previous_period': f"{previous_start_date.strftime('%Y-%m-%d')} to {previous_end_date.strftime('%Y-%m-%d')}",
            'previous_totals': previous_totals,
            'changes': changes,
            'daily_data': daily_data
        }
    except Exception as e:
        return {'error': str(e)}

def get_mobile_usability_issues(
    site_url: str,
    issue_filter: Optional[str] = None,
    start_date: datetime = None,
    end_date: datetime = None
) -> Dict[str, Any]:
    """Get mobile usability issues from Google Search Console."""
    try:
        service = get_service()
        
        # Build request body for the Mobile Usability report
        request_body = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
            'dimensions': ['issue'],
            'dataState': 'ALL'
        }
        
        if issue_filter:
            request_body['dimensionFilterGroups'] = [{
                'filters': [{
                    'dimension': 'issue',
                    'operator': 'equals',
                    'expression': issue_filter
                }]
            }]
        
        # Execute the request
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body=request_body
        ).execute()
        
        # Process and format the response
        rows = response.get('rows', [])
        formatted_issues = []
        
        for row in rows:
            issue_type = row.get('keys', ['UNKNOWN'])[0]
            
            # Get example URLs for this issue
            examples_request = {
                'dimensions': ['page'],
                'dimensionFilterGroups': [{
                    'filters': [{
                        'dimension': 'issue',
                        'operator': 'equals',
                        'expression': issue_type
                    }]
                }],
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'rowLimit': 10,
                'dataState': 'ALL'
            }
            
            examples_response = service.searchanalytics().query(
                siteUrl=site_url,
                body=examples_request
            ).execute()
            
            example_urls = [example.get('keys', [''])[0] for example in examples_response.get('rows', [])]
            
            formatted_issues.append({
                'issue_type': issue_type,
                'count': int(row.get('clicks', 0)),  # In this report, clicks represent count
                'example_urls': example_urls
            })
        
        return {
            'issues': formatted_issues,
            'total_issues': len(formatted_issues),
            'date_range': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }
        }
    except Exception as e:
        return {'error': str(e)}

def get_indexed_urls(
    site_url: str,
    filter_type: Optional[str] = None,
    start_date: datetime = None,
    end_date: datetime = None
) -> Dict[str, Any]:
    """Get a list of indexed URLs from Google Search Console.
    
    filter_type can be: ALL, INDEXED, NOT_INDEXED
    """
    try:
        service = get_service()
        
        # Build request body for the Index Coverage report to get pages
        request_body = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
            'dimensions': ['page'],
            'rowLimit': 1000,
            'dataState': 'ALL'
        }
        
        if filter_type and filter_type != 'ALL':
            # Add filter for indexed/non-indexed state
            request_body['dimensionFilterGroups'] = [{
                'filters': [{
                    'dimension': 'index_state',
                    'operator': 'equals',
                    'expression': 'INDEXED' if filter_type == 'INDEXED' else 'NOT_INDEXED'
                }]
            }]
        
        # Execute the request
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body=request_body
        ).execute()
        
        # Process and format the response
        rows = response.get('rows', [])
        urls = [row.get('keys', [''])[0] for row in rows]
        
        return {
            'urls': urls,
            'count': len(urls),
            'date_range': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            },
            'filter': filter_type or 'ALL'
        }
    except Exception as e:
        return {'error': str(e)}