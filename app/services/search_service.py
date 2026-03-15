"""
Web search service using DuckDuckGo (free, no API key required)
"""

import aiohttp
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from app.utils.logger import logger


class SearchService:
    """Web search service for internet searches"""
    
    def __init__(self):
        self.search_url = "https://html.duckduckgo.com/html/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using DuckDuckGo
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, snippet, and URL
        """
        try:
            logger.info(f"🔍 Searching web for: {query}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.search_url,
                    data={'q': query},
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response.raise_for_status()
                    html = await response.text()
            
            # Parse HTML results
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            
            # Find all result divs
            result_divs = soup.find_all('div', class_='result')
            
            for div in result_divs[:max_results]:
                try:
                    # Extract title and URL
                    title_tag = div.find('a', class_='result__a')
                    if not title_tag:
                        continue
                    
                    title = title_tag.get_text(strip=True)
                    url = title_tag.get('href', '')
                    
                    # Extract snippet
                    snippet_tag = div.find('a', class_='result__snippet')
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''
                    
                    if title and url:
                        results.append({
                            'title': title,
                            'url': url,
                            'snippet': snippet
                        })
                except Exception as e:
                    logger.warning(f"Error parsing search result: {e}")
                    continue
            
            logger.info(f"✅ Found {len(results)} search results")
            return results
        
        except Exception as e:
            logger.error(f"❌ Error searching web: {e}")
            raise Exception(f"Failed to search: {str(e)}")
    
    async def get_page_content(self, url: str, max_length: int = 2000) -> Optional[str]:
        """
        Fetch and extract main content from a webpage
        
        Args:
            url: URL to fetch
            max_length: Maximum content length
            
        Returns:
            Extracted text content or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        return None
                    
                    html = await response.text()
            
            # Parse and extract text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Truncate if too long
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
        
        except Exception as e:
            logger.warning(f"Error fetching page content: {e}")
            return None
    
    def format_search_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """
        Format search results as human-readable text
        
        Args:
            results: List of search results
            query: Original search query
            
        Returns:
            Formatted search results string
        """
        if not results:
            return f"No results found for '{query}'"
        
        formatted = f"Search results for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result['title']}\n"
            if result['snippet']:
                formatted += f"   {result['snippet']}\n"
            formatted += f"   URL: {result['url']}\n\n"
        
        return formatted
    
    async def search_and_summarize(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """
        Search and provide a summary of results
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            Dictionary with search results and summary
        """
        try:
            results = await self.search(query, max_results)
            
            if not results:
                return {
                    'success': False,
                    'message': f"No results found for '{query}'"
                }
            
            # Try to fetch content from top result for better context
            top_result_content = None
            if results:
                top_result_content = await self.get_page_content(results[0]['url'])
            
            summary_parts = []
            for result in results:
                summary_parts.append(f"• {result['title']}: {result['snippet']}")
            
            summary = "\n".join(summary_parts)
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'summary': summary,
                'top_content': top_result_content,
                'formatted': self.format_search_results(results, query)
            }
        
        except Exception as e:
            logger.error(f"Error in search and summarize: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to search for '{query}'"
            }
