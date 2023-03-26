import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from tqdm import tqdm
from termcolor import colored

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

def get_pdf_urls_from_page(url, error_file):
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        page_urls = set()

        for link in soup.find_all('a', href=True):
            href = link.get('href').strip()
            if not href.lower().endswith('.pdf'):
                continue
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
    start_url = 'https://www.riwaya.ga/riwayat_3alamiya.htm'

    with open('result_links.txt', 'w', encoding='utf-8') as output_file, \
            open('error_log.txt', 'w', encoding='utf-8') as error_file, \
            open('subpage_links.txt', 'w', encoding='utf-8') as subpage_file:

        all_urls = get_urls_from_page(start_url, error_file)

        total_urls = 0
        total_sub_urls = 0
        total_errors = 0

        for url in tqdm(all_urls, desc="Processing URLs", unit="url"):
            output_file.write(f"URL: {url}\n")
            pdf_urls = get_pdf_urls_from_page(url, error_file)
            total_sub_urls += len(pdf_urls)
            for pdf_url in pdf_urls:
                subpage_file.write(f"PDF URL: {pdf_url}\n")
            total_urls += 1

        with open('error_log.txt', 'r', encoding='utf-8') as error_file:
            total_errors = sum(1 for line in error_file if "Error:" in line)

        print(colored("\nProcessing completed!", "green"))
        print(colored(f"Total URLs processed: {total_urls}", "cyan"))
        print(colored(f"Total PDF URLs found: {total_sub_urls}", "cyan"))
        print(colored(f"Total errors encountered: {total_errors}", "red"))

if __name__ == '__main__':
    main()
