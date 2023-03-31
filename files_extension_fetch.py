import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm

# Check if a URL is valid
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

# Extract the page title from a BeautifulSoup object
def get_page_title(soup):
    title = soup.title.string
    return "".join(c for c in title if c.isalnum() or c.isspace())

# Download files with specified extensions from a given URL
def download_files(url, extensions):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    title = get_page_title(soup)
    
    # Create a directory named after the page title if it doesn't exist
    if not os.path.exists(title):
        os.makedirs(title)
    
    files_downloaded = 0
    
    # Iterate through all the links on the page
    for link in soup.find_all("a"):
        file_url = link.get("href")
        
        # Check if the file URL has one of the specified extensions
        if file_url and any(file_url.lower().endswith(ext) for ext in extensions):
            # Check if the file URL is a valid URL, otherwise join it with the base URL
            if is_valid_url(file_url):
                full_url = file_url
            else:
                full_url = urljoin(url, file_url)
            
            # Set the file name and path
            file_name = os.path.join(title, os.path.basename(file_url))
            
            # Download the file with a progress bar using the tqdm library
            with requests.get(full_url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get("content-length", 0))
                with open(file_name, "wb") as f:
                    for chunk in tqdm(r.iter_content(chunk_size=8192), total=total_size // 8192, unit="KB"):
                        f.write(chunk)
            
            files_downloaded += 1
            print(f"\nDownloaded: {file_name}")

    print(f"\nTotal files downloaded: {files_downloaded}")

# Entry point of the script
if __name__ == "__main__":
    # Check if there are enough command-line arguments
    if len(sys.argv) < 3:
        print("Usage: python files_extension_fetch.py <url> <extension1> <extension2> ...")
        sys.exit(1)

    # Get the URL and file extensions from the command-line arguments
    url = sys.argv[1]
    file_extensions = sys.argv[2:]
    download_files(url, file_extensions)
