#!/usr/bin/env python3
"""
OptiSigns Support Bot - Daily Scraper & Uploader
Main script for daily job deployment
"""

import os
import json
import hashlib
import time
from datetime import datetime
from dotenv import load_dotenv
from scraper import fetch_articles, fetch_article_content, extract_content, save_markdown
from upload_to_openai import OpenAIUploader

# Load environment variables
load_dotenv()

class DailyJob:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.uploader = OpenAIUploader(self.api_key)
        self.data_dir = "data"
        self.hash_file = "article_hashes.json"
        self.log_file = "job_log.json"
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
    
    def calculate_file_hash(self, filepath):
        """Calculate MD5 hash of file content"""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def load_article_hashes(self):
        """Load existing article hashes"""
        if os.path.exists(self.hash_file):
            with open(self.hash_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_article_hashes(self, hashes):
        """Save article hashes"""
        with open(self.hash_file, 'w') as f:
            json.dump(hashes, f, indent=2)
    
    def log_job_result(self, stats):
        """Log job execution results"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'stats': stats
        }
        
        # Load existing logs
        logs = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
        
        # Add new log entry
        logs.append(log_entry)
        
        # Keep only last 30 days of logs
        if len(logs) > 30:
            logs = logs[-30:]
        
        # Save logs
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def scrape_and_detect_changes(self, max_articles=40):
        """Scrape articles and detect changes"""
        print("Starting daily scrape...")
        
        # Load existing hashes
        existing_hashes = self.load_article_hashes()
        
        # Fetch articles from API
        articles = fetch_articles(max_articles=max_articles)
        print(f"📋 Found {len(articles)} articles to process")
        
        stats = {
            'total_articles': len(articles),
            'added': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0,
            'uploaded_files': []
        }
        
        for article in articles:
            article_id = article["id"]
            title = article["title"]
            filename = f"{title.lower().replace(' ', '-').replace('/', '-')}.md"
            filepath = os.path.join(self.data_dir, filename)
            
            try:
                # Fetch article content
                html_content = fetch_article_content(article_id, title)
                
                if html_content is None:
                    print(f"Failed to fetch content: {title}")
                    stats['failed'] += 1
                    continue
                
                # Convert to markdown
                content_md = extract_content(html_content)
                
                if not content_md:
                    print(f"Empty content: {title}")
                    stats['failed'] += 1
                    continue
                
                # Calculate new hash
                new_hash = hashlib.md5(content_md.encode()).hexdigest()
                
                # Check if file exists and hash changed
                if filename in existing_hashes:
                    if existing_hashes[filename] == new_hash:
                        print(f"Skipped (no changes): {title}")
                        stats['skipped'] += 1
                        continue
                    else:
                        print(f"Updated: {title}")
                        stats['updated'] += 1
                else:
                    print(f"Added: {title}")
                    stats['added'] += 1
                
                # Save markdown file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"# {title}\n\n")
                    f.write(content_md)
                
                # Update hash
                existing_hashes[filename] = new_hash
                stats['uploaded_files'].append(filename)
                
                # Be nice to the server
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing {title}: {e}")
                stats['failed'] += 1
        
        # Save updated hashes
        self.save_article_hashes(existing_hashes)
        
        return stats
    
    def upload_changes_to_openai(self, uploaded_files):
        """Upload changed files to OpenAI"""
        if not uploaded_files:
            print("No files to upload")
            return 0
        
        print(f"Uploading {len(uploaded_files)} files to OpenAI...")
        
        uploaded_count = 0
        for filename in uploaded_files:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                file_id = self.uploader.upload_file(filepath)
                if file_id:
                    uploaded_count += 1
                time.sleep(0.5)
        
        return uploaded_count
    
    def run(self):
        """Main job execution"""
        start_time = time.time()
        
        print("Starting OptiSigns Daily Job")
        print("=" * 50)
        print(f"Start time: {datetime.now().isoformat()}")
        
        try:
            # Step 1: Scrape and detect changes
            stats = self.scrape_and_detect_changes()
            
            # Step 2: Upload changes to OpenAI
            if stats['uploaded_files']:
                uploaded_count = self.upload_changes_to_openai(stats['uploaded_files'])
                stats['openai_uploaded'] = uploaded_count
            else:
                stats['openai_uploaded'] = 0
            
            # Step 3: Log results
            self.log_job_result(stats)
            
            # Step 4: Print summary
            end_time = time.time()
            duration = end_time - start_time
            
            print("\n" + "=" * 50)
            print("JOB SUMMARY")
            print("=" * 50)
            print(f"Duration: {duration:.2f} seconds")
            print(f"Total articles: {stats['total_articles']}")
            print(f"Added: {stats['added']}")
            print(f"Updated: {stats['updated']}")
            print(f"Skipped: {stats['skipped']}")
            print(f"Failed: {stats['failed']}")
            print(f"Uploaded to OpenAI: {stats['openai_uploaded']}")
            print(f"Log saved to: {self.log_file}")
            
            # Exit with success code
            return 0
            
        except Exception as e:
            print(f"Job failed: {e}")
            return 1

def main():
    """Entry point for the daily job"""
    try:
        job = DailyJob()
        exit_code = job.run()
        exit(exit_code)
    except Exception as e:
        print(f"Failed to initialize job: {e}")
        exit(1)

if __name__ == "__main__":
    main()
