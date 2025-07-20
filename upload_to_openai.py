import os
import hashlib
import json
from openai import OpenAI
from tqdm import tqdm
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class OpenAIUploader:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.uploaded_files = []
        self.total_chunks = 0
        
    def calculate_file_hash(self, filepath):
        """Calculate MD5 hash of file content"""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def chunk_content(self, content, max_chunk_size=4000):
        """Split content into chunks based on headings and size"""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line)
            
            # If adding this line would exceed chunk size, save current chunk
            if current_size + line_size > max_chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        # Add the last chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
    
    def upload_file(self, filepath):
        """Upload a single file to OpenAI"""
        try:
            filename = os.path.basename(filepath)
            print(f"Uploading: {filename}")
            
            # Read file content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chunk the content
            chunks = self.chunk_content(content)
            print(f"  Split into {len(chunks)} chunks")
            
            # Upload file to OpenAI
            with open(filepath, 'rb') as f:
                file_obj = self.client.files.create(
                    file=f,
                    purpose='assistants'
                )
            
            self.uploaded_files.append({
                'file_id': file_obj.id,
                'filename': filename,
                'chunks': len(chunks),
                'size': len(content)
            })
            
            self.total_chunks += len(chunks)
            print(f"  Uploaded successfully (ID: {file_obj.id})")
            return file_obj.id
            
        except Exception as e:
            print(f"  Error uploading {filename}: {e}")
            return None
    
    def upload_directory(self, directory_path):
        """Upload all markdown files in directory"""
        print(f"Starting upload from: {directory_path}")
        
        # Get all .md files
        md_files = [f for f in os.listdir(directory_path) if f.endswith('.md')]
        print(f"Found {len(md_files)} markdown files")
        
        uploaded_count = 0
        
        for filename in tqdm(md_files, desc="Uploading files"):
            filepath = os.path.join(directory_path, filename)
            file_id = self.upload_file(filepath)
            
            if file_id:
                uploaded_count += 1
            
            # Be nice to the API
            time.sleep(0.5)
        
        return uploaded_count
    
    def get_upload_summary(self):
        """Get summary of uploaded files"""
        return {
            'total_files': len(self.uploaded_files),
            'total_chunks': self.total_chunks,
            'files': self.uploaded_files
        }

def main():
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Initialize uploader
    uploader = OpenAIUploader(api_key)
    
    # Upload files
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"Error: Directory '{data_dir}' not found")
        return
    
    uploaded_count = uploader.upload_directory(data_dir)
    
    # Print summary
    summary = uploader.get_upload_summary()
    print(f"\nUpload Summary:")
    print(f"  Files uploaded: {summary['total_files']}")
    print(f"  Total chunks: {summary['total_chunks']}")
    print(f"  Average chunks per file: {summary['total_chunks'] / summary['total_files']:.1f}")
    
    # Save summary to file
    with open('upload_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary saved to: upload_summary.json")
    

if __name__ == "__main__":
    main() 