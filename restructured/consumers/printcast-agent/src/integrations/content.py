"""
Content fetching integration for PrintCast Agent.

Handles fetching content from various sources:
- GitHub Trending repositories
- RSS feeds
- News sources
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
import feedparser
from bs4 import BeautifulSoup
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ContentItem(BaseModel):
    """Represents a content item."""
    
    id: str
    source: str
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content_type: str = "text"


class ContentFetcher:
    """
    Fetches content from various sources for printing.
    
    Supports:
    - GitHub Trending repositories
    - RSS feeds
    - News APIs
    - Custom content sources
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize content fetcher.
        
        Args:
            config: Configuration including:
                - github_token: GitHub API token (optional)
                - rss_feeds: List of RSS feed URLs
                - news_api_key: News API key (optional)
                - cache_ttl: Cache TTL in seconds
        """
        self.config = config
        self.github_token = config.get("github_token")
        self.rss_feeds = config.get("rss_feeds", [
            "https://news.ycombinator.com/rss",
            "https://feeds.feedburner.com/TechCrunch/",
            "https://www.reddit.com/r/programming/.rss"
        ])
        self.news_api_key = config.get("news_api_key")
        self.cache_ttl = config.get("cache_ttl", 3600)
        
        self.client: Optional[httpx.AsyncClient] = None
        self.cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(
            "Content fetcher initialized",
            rss_feeds_count=len(self.rss_feeds),
            has_github_token=bool(self.github_token)
        )
    
    async def initialize(self):
        """Initialize HTTP client."""
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True
        )
    
    async def shutdown(self):
        """Cleanup resources."""
        if self.client:
            await self.client.aclose()
    
    async def get_available_content(self) -> Dict[str, Any]:
        """
        Get overview of available content sources.
        
        Returns:
            Dictionary of available content types and counts
        """
        return {
            "sources": {
                "github": {
                    "name": "GitHub Trending",
                    "available": True,
                    "languages": ["python", "javascript", "go", "rust", "java"]
                },
                "rss": {
                    "name": "RSS Feeds",
                    "available": True,
                    "feeds": len(self.rss_feeds)
                },
                "news": {
                    "name": "News Articles",
                    "available": bool(self.news_api_key)
                }
            }
        }
    
    async def fetch_github_trending(
        self,
        language: Optional[str] = None,
        since: str = "daily",
        limit: int = 10
    ) -> List[ContentItem]:
        """
        Fetch trending GitHub repositories.
        
        Args:
            language: Programming language filter
            since: Time range (daily, weekly, monthly)
            limit: Maximum number of repositories
        
        Returns:
            List of trending repositories
        """
        cache_key = f"github_{language}_{since}"
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if cached["expires"] > datetime.now():
                logger.debug("Using cached GitHub trending", key=cache_key)
                return cached["data"][:limit]
        
        try:
            # Scrape GitHub Trending page (no official API)
            url = "https://github.com/trending"
            params = {}
            if language:
                params["spoken_language_code"] = "en"
                url = f"{url}/{language}"
            if since:
                params["since"] = since
            
            if params:
                url = f"{url}?{urlencode(params)}"
            
            response = await self.client.get(url)
            
            if response.status_code != 200:
                logger.error(
                    "Failed to fetch GitHub trending",
                    status=response.status_code
                )
                return []
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            repos = []
            
            for article in soup.find_all("article", class_="Box-row", limit=limit):
                try:
                    # Extract repository info
                    h2 = article.find("h2", class_="h3")
                    if not h2:
                        continue
                    
                    repo_link = h2.find("a")
                    if not repo_link:
                        continue
                    
                    repo_path = repo_link.get("href", "").strip("/")
                    if not repo_path:
                        continue
                    
                    repo_name = repo_path.split("/")[-1]
                    owner = repo_path.split("/")[0] if "/" in repo_path else ""
                    
                    # Get description
                    desc_elem = article.find("p", class_="col-9")
                    description = desc_elem.text.strip() if desc_elem else ""
                    
                    # Get language
                    lang_elem = article.find("span", itemprop="programmingLanguage")
                    prog_language = lang_elem.text.strip() if lang_elem else ""
                    
                    # Get stars
                    stars_elem = article.find("svg", class_="octicon-star")
                    stars_text = "0"
                    if stars_elem and stars_elem.parent:
                        stars_text = stars_elem.parent.text.strip().replace(",", "")
                        # Extract just the number
                        stars_text = "".join(filter(str.isdigit, stars_text))
                    
                    # Get today's stars
                    today_stars = "0"
                    star_elem = article.find("span", class_="d-inline-block")
                    if star_elem:
                        star_text = star_elem.text.strip()
                        if "stars" in star_text:
                            today_stars = star_text.split()[0].replace(",", "")
                    
                    item = ContentItem(
                        id=f"gh_{repo_path.replace('/', '_')}",
                        source="github",
                        title=f"{owner}/{repo_name}",
                        description=description,
                        url=f"https://github.com/{repo_path}",
                        author=owner,
                        tags=[prog_language] if prog_language else [],
                        metadata={
                            "stars": int(stars_text) if stars_text.isdigit() else 0,
                            "today_stars": int(today_stars) if today_stars.isdigit() else 0,
                            "language": prog_language,
                            "repository": repo_name,
                            "owner": owner
                        },
                        content_type="repository"
                    )
                    
                    repos.append(item)
                    
                except Exception as e:
                    logger.warning(
                        "Failed to parse repository",
                        error=str(e)
                    )
                    continue
            
            # Cache results
            self.cache[cache_key] = {
                "data": repos,
                "expires": datetime.now() + timedelta(seconds=self.cache_ttl)
            }
            
            logger.info(
                "Fetched GitHub trending",
                count=len(repos),
                language=language,
                since=since
            )
            
            return repos[:limit]
            
        except Exception as e:
            logger.error("Failed to fetch GitHub trending", error=str(e))
            return []
    
    async def fetch_rss_feeds(
        self,
        feed_urls: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[ContentItem]:
        """
        Fetch content from RSS feeds.
        
        Args:
            feed_urls: Optional list of feed URLs (uses config if not provided)
            limit: Maximum number of items per feed
        
        Returns:
            List of RSS items
        """
        feeds = feed_urls or self.rss_feeds
        all_items = []
        
        async def fetch_feed(url: str) -> List[ContentItem]:
            """Fetch single RSS feed."""
            cache_key = f"rss_{url}"
            
            # Check cache
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                if cached["expires"] > datetime.now():
                    logger.debug("Using cached RSS feed", url=url)
                    return cached["data"]
            
            try:
                response = await self.client.get(url)
                if response.status_code != 200:
                    logger.warning(
                        "Failed to fetch RSS feed",
                        url=url,
                        status=response.status_code
                    )
                    return []
                
                # Parse feed
                feed = feedparser.parse(response.text)
                items = []
                
                for entry in feed.entries[:limit]:
                    # Parse published date
                    published = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published = datetime.fromtimestamp(
                            feedparser._mktime_tz(entry.published_parsed)
                        )
                    
                    # Extract tags
                    tags = []
                    if hasattr(entry, "tags"):
                        tags = [tag.term for tag in entry.tags]
                    
                    item = ContentItem(
                        id=f"rss_{hash(entry.get('id', entry.get('link', '')))}"[:20],
                        source=feed.feed.get("title", url),
                        title=entry.get("title", ""),
                        description=entry.get("summary", ""),
                        url=entry.get("link"),
                        author=entry.get("author"),
                        published_date=published,
                        tags=tags,
                        metadata={
                            "feed_title": feed.feed.get("title"),
                            "feed_url": url
                        },
                        content_type="article"
                    )
                    
                    items.append(item)
                
                # Cache results
                self.cache[cache_key] = {
                    "data": items,
                    "expires": datetime.now() + timedelta(seconds=self.cache_ttl)
                }
                
                logger.info(
                    "Fetched RSS feed",
                    url=url,
                    count=len(items)
                )
                
                return items
                
            except Exception as e:
                logger.error(
                    "Failed to fetch RSS feed",
                    url=url,
                    error=str(e)
                )
                return []
        
        # Fetch all feeds concurrently
        tasks = [fetch_feed(url) for url in feeds]
        results = await asyncio.gather(*tasks)
        
        # Combine and sort by date
        for items in results:
            all_items.extend(items)
        
        # Sort by published date (newest first)
        all_items.sort(
            key=lambda x: x.published_date or datetime.min,
            reverse=True
        )
        
        return all_items[:limit]
    
    async def fetch_news(
        self,
        query: Optional[str] = None,
        category: str = "technology",
        limit: int = 10
    ) -> List[ContentItem]:
        """
        Fetch news articles.
        
        Args:
            query: Search query
            category: News category
            limit: Maximum number of articles
        
        Returns:
            List of news articles
        """
        if not self.news_api_key:
            logger.warning("News API key not configured")
            return []
        
        cache_key = f"news_{query}_{category}"
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if cached["expires"] > datetime.now():
                logger.debug("Using cached news", key=cache_key)
                return cached["data"][:limit]
        
        try:
            # Use NewsAPI or similar service
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey": self.news_api_key,
                "category": category,
                "pageSize": limit
            }
            
            if query:
                params["q"] = query
            
            response = await self.client.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(
                    "Failed to fetch news",
                    status=response.status_code
                )
                return []
            
            data = response.json()
            items = []
            
            for article in data.get("articles", []):
                # Parse date
                published = None
                if article.get("publishedAt"):
                    published = datetime.fromisoformat(
                        article["publishedAt"].replace("Z", "+00:00")
                    )
                
                item = ContentItem(
                    id=f"news_{hash(article.get('url', ''))}",
                    source=article.get("source", {}).get("name", "News"),
                    title=article.get("title", ""),
                    description=article.get("description", ""),
                    url=article.get("url"),
                    author=article.get("author"),
                    published_date=published,
                    metadata={
                        "source_id": article.get("source", {}).get("id"),
                        "image_url": article.get("urlToImage")
                    },
                    content_type="news"
                )
                
                items.append(item)
            
            # Cache results
            self.cache[cache_key] = {
                "data": items,
                "expires": datetime.now() + timedelta(seconds=self.cache_ttl)
            }
            
            logger.info(
                "Fetched news articles",
                count=len(items),
                category=category
            )
            
            return items
            
        except Exception as e:
            logger.error("Failed to fetch news", error=str(e))
            return []
    
    async def search_content(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[ContentItem]:
        """
        Search across all content sources.
        
        Args:
            query: Search query
            sources: Optional list of sources to search
            limit: Maximum results
        
        Returns:
            Combined search results
        """
        sources = sources or ["github", "rss", "news"]
        all_results = []
        
        tasks = []
        if "github" in sources:
            # Search GitHub by using the query as language filter
            tasks.append(self.fetch_github_trending(language=query, limit=limit))
        
        if "rss" in sources:
            # RSS feeds don't support search, just fetch latest
            tasks.append(self.fetch_rss_feeds(limit=limit))
        
        if "news" in sources and self.news_api_key:
            tasks.append(self.fetch_news(query=query, limit=limit))
        
        results = await asyncio.gather(*tasks)
        
        for items in results:
            all_results.extend(items)
        
        # Filter by query in title/description
        query_lower = query.lower()
        filtered = []
        
        for item in all_results:
            if (query_lower in item.title.lower() or 
                (item.description and query_lower in item.description.lower())):
                filtered.append(item)
        
        return filtered[:limit]
    
    async def get_content_by_ids(
        self,
        content_ids: List[str]
    ) -> List[ContentItem]:
        """
        Get specific content items by ID.
        
        Args:
            content_ids: List of content IDs
        
        Returns:
            List of content items
        """
        items = []
        
        # Check all cache entries
        for cache_data in self.cache.values():
            if "data" in cache_data:
                for item in cache_data["data"]:
                    if item.id in content_ids:
                        items.append(item)
        
        return items
    
    def format_for_print(
        self,
        items: List[ContentItem],
        format: str = "text"
    ) -> str:
        """
        Format content items for printing.
        
        Args:
            items: Content items to format
            format: Output format (text, markdown, html)
        
        Returns:
            Formatted content
        """
        if format == "markdown":
            output = "# PrintCast Content Selection\n\n"
            output += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for item in items:
                output += f"## {item.title}\n\n"
                if item.author:
                    output += f"**Author:** {item.author}\n\n"
                if item.description:
                    output += f"{item.description}\n\n"
                if item.url:
                    output += f"**URL:** {item.url}\n\n"
                if item.tags:
                    output += f"**Tags:** {', '.join(item.tags)}\n\n"
                output += "---\n\n"
                
        elif format == "html":
            output = """<!DOCTYPE html>
<html>
<head>
    <title>PrintCast Content</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .item { margin-bottom: 30px; padding: 15px; border: 1px solid #ddd; }
        .meta { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>PrintCast Content Selection</h1>
    <p class="meta">Generated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
"""
            
            for item in items:
                output += f'<div class="item">\n'
                output += f'<h2>{item.title}</h2>\n'
                if item.author:
                    output += f'<p class="meta">Author: {item.author}</p>\n'
                if item.description:
                    output += f'<p>{item.description}</p>\n'
                if item.url:
                    output += f'<p><a href="{item.url}">{item.url}</a></p>\n'
                if item.tags:
                    output += f'<p class="meta">Tags: {", ".join(item.tags)}</p>\n'
                output += '</div>\n'
            
            output += "</body></html>"
            
        else:  # text format
            output = "PRINTCAST CONTENT SELECTION\n"
            output += "=" * 50 + "\n\n"
            output += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for i, item in enumerate(items, 1):
                output += f"{i}. {item.title}\n"
                if item.author:
                    output += f"   Author: {item.author}\n"
                if item.description:
                    output += f"   {item.description[:200]}...\n"
                if item.url:
                    output += f"   URL: {item.url}\n"
                output += "\n"
        
        return output