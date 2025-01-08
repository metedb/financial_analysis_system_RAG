from langchain.tools import Tool
from typing import Dict, List, Optional
import httpx

NEWS_SEARCH_DESCRIPTION = """
Useful for searching news articles and content using semantic similarity.
Input should be a search query string and optionally specify top_k for number of results.
Use this when you need to find news articles related to a specific topic or query.
Format: 'query' or 'query|top_k' where top_k is optional number of results to return.
Example: "AI developments" or "AI developments|5" for top 5 results.
"""

class NewsSearchTool:
    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url
        
    def search(self, query_input: str) -> List[Dict]:
        """
        Execute semantic search for news articles.
        
        Args:
            query_input (str): The search query string, optionally with top_k parameter
                             Format: "query" or "query|top_k"
        
        Returns:
            List[Dict]: List of relevant news articles/chunks
            
        Raises:
            Exception: If the search service encounters an error
        """
        parts = query_input.split("|")
        query = parts[0].strip()
        top_k = int(parts[1]) if len(parts) > 1 else None
        
        with httpx.Client() as client:
            try:
                params = {"query": query}
                if top_k is not None:
                    params["top_k"] = top_k
                    
                response = client.get(
                    self.endpoint_url,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract results from response
                results = data.get("results", [])
                if not results:
                    return []
                    
                return results
                
            except httpx.RequestError as e:
                raise Exception(f"Search service error: {str(e)}")
            except httpx.HTTPStatusError as e:
                raise Exception(f"HTTP error: {str(e)}")
            except Exception as e:
                raise Exception(f"Unexpected error during search: {str(e)}")

def create_news_search_tool(endpoint_url: str) -> Tool:
    """
    Create a Langchain tool for news search.
    
    Args:
        endpoint_url (str): The endpoint URL for the search service
        
    Returns:
        Tool: Configured Langchain tool for news search
    """
    search_tool = NewsSearchTool(endpoint_url)
    
    return Tool(
        name="news_search",
        description=NEWS_SEARCH_DESCRIPTION,
        func=search_tool.search,
    )
