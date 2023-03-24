import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_urls_from_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        page_urls = set()

        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href.lower().endswith('.pdf'):
                full_url = urljoin(url, href)
                page_urls.add(full_url)

        return page_urls

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return set()

def main():
    start_url = 'https://example.com'  # Replace with the URL you want to start with
    all_urls = get_urls_from_page(start_url)

    for url in all_urls:
        print(f"URL: {url}")
        sub_urls = get_urls_from_page(url)
        for sub_url in sub_urls:
            print(f"  - {sub_url}")

if __name__ == '__main__':
    main()
