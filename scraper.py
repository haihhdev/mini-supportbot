
import os
import requests
import time
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from slugify import slugify

def fetch_articles(max_articles=40):
    """Fetch articles from Zendesk API with proper headers"""
    articles = []
    page = 1
    
    # Add browser-like headers to avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    
    while len(articles) < max_articles:
        try:
            url = f"https://support.optisigns.com/api/v2/help_center/articles.json?page={page}&per_page=40"
            print(f"Fetching page {page}...")
            
            resp = requests.get(url, headers=headers, timeout=10)
            print(f"Page {page} status: {resp.status_code}")
            
            if resp.status_code != 200:
                print(f"Failed to fetch page {page}: {resp.status_code}")
                break
                
            data = resp.json()
            page_articles = data.get("articles", [])
            print(f"Found {len(page_articles)} articles on page {page}")
            
            if not page_articles:
                print("No more articles found")
                break
                
            articles.extend(page_articles)
            
            if not data.get("next_page"):
                print("No next page available")
                break
                
            page += 1
            time.sleep(1)  
            
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break
    
    print(f"Total articles fetched: {len(articles)}")
    return articles[:max_articles]

def fetch_article_content(article_id, title):
    """Fetch article content directly from Zendesk API"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }
    
    try:
        # Use Zendesk API to get article content directly
        url = f"https://support.optisigns.com/api/v2/help_center/articles/{article_id}.json"
        print(f"Fetching content for article {article_id}: {title}")
        
        resp = requests.get(url, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            data = resp.json()
            article = data.get("article", {})
            body = article.get("body", "")
            
            if body:
                print(f"Successfully fetched content for: {title}")
                return body
            else:
                print(f"No body content found for: {title}")
                return None
        else:
            print(f"HTTP {resp.status_code} for article {article_id}: {title}")
            return None
            
    except Exception as e:
        print(f"Error fetching article {article_id}: {e}")
        return None

def extract_content(html: str) -> str:
    """Extract and clean content from HTML"""
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove navigation and unwanted elements
        for tag in soup.select("nav, header, footer, .related-articles, .breadcrumbs, .article-meta, .article-footer"):
            tag.decompose()
        
        # Try different selectors for article content
        content_selectors = [
            "div.article-body",
            "div.article-content", 
            "div.content",
            "article",
            "main"
        ]
        
        content = None
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                print(f"Found content with selector: {selector}")
                break
        
        if not content:
            # If no specific selector found, use the whole body
            content = soup
        
        # Convert to markdown
        markdown = md(str(content), heading_style="ATX")
        return markdown.strip()
        
    except Exception as e:
        print(f"Error extracting content: {e}")
        return ""

def save_markdown(title: str, content: str, output_dir="data"):
    """Save content as markdown file"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{slugify(title)}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(content)
        
        print(f"Saved: {filename}")
        return True
        
    except Exception as e:
        print(f"Error saving {title}: {e}")
        return False
