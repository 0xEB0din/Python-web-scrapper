import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

def get_urls_from_page(url, error_file):
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        page_urls = set()

        body_element = soup.body
        for section in body_element.find_all('section'):
            for link in section.find_all('a', href=True):
                href = link.get('href').strip()
                decoded_href = unquote(href)
                full_url = urljoin(url, decoded_href)
                decoded_full_url = unquote(full_url)
                page_urls.add(decoded_full_url)

        return page_urls

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        error_file.write(f"Error: {e}\n")
        return set()

def main():
    start_url = 'https://example.com'
    
    with open('result_links.txt', 'w', encoding='utf-8') as output_file, \
         open('error_log.txt', 'w', encoding='utf-8') as error_file:

        all_urls = get_urls_from_page(start_url, error_file)

        for url in all_urls:
            output_file.write(f"URL: {url}\n")
            sub_urls = get_urls_from_page(url, error_file)
            for sub_url in sub_urls:
                output_file.write(f"  - {sub_url}\n")

if __name__ == '__main__':
    main()
