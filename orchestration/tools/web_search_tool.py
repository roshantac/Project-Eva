"""
Web search tool for EVA using DuckDuckGo
Provides personalized search results for user queries
"""

from typing import Dict, Any, List, Optional
from ddgs import DDGS
from utils.logger import get_logger
import warnings

logger = get_logger()

# Suppress DDGS impersonate warnings
warnings.filterwarnings('ignore', message='.*Impersonate.*')


class WebSearchTool:
    """Web search tool using DuckDuckGo"""
    
    def __init__(self, max_results: int = 8, timeout: int = 10):
        self.max_results = max_results
        self.timeout = timeout
        logger.info("Web search tool initialized (DuckDuckGo)")
    
    def search(
        self,
        query: str,
        max_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search the web using DuckDuckGo
        
        Args:
            query: Search query
            max_results: Maximum number of results (overrides default)
        
        Returns:
            Dict with search results
        """
        try:
            results_limit = max_results or self.max_results
            
            logger.tool_call("web_search", {
                "query": query,
                "max_results": results_limit
            })
            
            # Perform search using DuckDuckGo
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=results_limit))
            
            # Format results
            formatted_results = []
            for idx, result in enumerate(results, 1):
                formatted_results.append({
                    "position": idx,
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "url": result.get("href", ""),
                    "source": self._extract_domain(result.get("href", ""))
                })
            
            logger.info(f"Web search completed: {len(formatted_results)} results for '{query}'")
            
            return {
                "success": True,
                "query": query,
                "results": formatted_results,
                "count": len(formatted_results)
            }
        
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "results": [],
                "count": 0
            }
    
    def search_news(
        self,
        query: str,
        max_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for news articles
        
        Args:
            query: Search query
            max_results: Maximum number of results
        
        Returns:
            Dict with news results
        """
        try:
            results_limit = max_results or self.max_results
            
            logger.tool_call("web_search_news", {
                "query": query,
                "max_results": results_limit
            })
            
            # Perform news search
            with DDGS() as ddgs:
                results = list(ddgs.news(query, max_results=results_limit))
            
            # Format results
            formatted_results = []
            for idx, result in enumerate(results, 1):
                formatted_results.append({
                    "position": idx,
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "url": result.get("url", ""),
                    "source": result.get("source", ""),
                    "date": result.get("date", "")
                })
            
            logger.info(f"News search completed: {len(formatted_results)} results")
            
            return {
                "success": True,
                "query": query,
                "results": formatted_results,
                "count": len(formatted_results)
            }
        
        except Exception as e:
            logger.error(f"News search failed: {str(e)}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "results": [],
                "count": 0
            }
    
    def get_instant_answer(self, query: str) -> Dict[str, Any]:
        """
        Get instant answer for factual queries
        
        Args:
            query: Search query
        
        Returns:
            Dict with instant answer if available
        """
        try:
            logger.tool_call("get_instant_answer", {"query": query})
            
            with DDGS() as ddgs:
                answer = ddgs.answers(query)
            
            if answer:
                logger.info(f"Instant answer found for: {query}")
                return {
                    "success": True,
                    "query": query,
                    "answer": answer[0] if isinstance(answer, list) else answer,
                    "has_answer": True
                }
            else:
                return {
                    "success": True,
                    "query": query,
                    "answer": None,
                    "has_answer": False
                }
        
        except Exception as e:
            logger.error(f"Instant answer failed: {str(e)}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "has_answer": False
            }
    
    def format_results_for_llm(self, search_results: Dict[str, Any]) -> str:
        """
        Format search results for LLM consumption
        
        Args:
            search_results: Results from search() method
        
        Returns:
            Formatted string for LLM
        """
        if not search_results.get("success") or not search_results.get("results"):
            return "No search results found."
        
        formatted = f"Search Results for: {search_results['query']}\n\n"
        
        for result in search_results["results"]:
            formatted += f"{result['position']}. {result['title']}\n"
            formatted += f"   {result['snippet']}\n"
            formatted += f"   Source: {result.get('source', 'Unknown')}\n\n"
        
        return formatted
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "Unknown"


# Global instance
_web_search_instance: Optional[WebSearchTool] = None


def get_web_search_tool() -> WebSearchTool:
    """Get or create web search tool instance"""
    global _web_search_instance
    if _web_search_instance is None:
        _web_search_instance = WebSearchTool()
    return _web_search_instance

# Made with Bob
