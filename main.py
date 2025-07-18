
from scraper import fetch_articles, fetch_article_content, extract_content, save_markdown
import time
from tqdm import tqdm

def main():
    print("Starting article scraping...")
    
    # Fetch article list
    articles = fetch_articles(max_articles=40)
    print(f"Found {len(articles)} articles to process")
    
    successful = 0
    failed = 0
    
    for article in tqdm(articles, desc="Processing articles"):
        article_id = article["id"]
        title = article["title"]
        
        # Fetch article content using Zendesk API
        html_content = fetch_article_content(article_id, title)
        
        if html_content is None:
            failed += 1
            continue
        
        # Extract and convert to markdown
        content_md = extract_content(html_content)
        
        if not content_md:
            print(f"Empty content extracted: {title}")
            failed += 1
            continue
        
        # Save markdown file
        if save_markdown(title, content_md):
            successful += 1
        else:
            failed += 1
        
        # Be nice to the server
        time.sleep(0.5)
    
    print(f"\nScraping completed!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total: {len(articles)}")

if __name__ == "__main__":
    main()
