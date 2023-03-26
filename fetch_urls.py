import sys
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

def get_subpage_urls(url, error_file):
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        pdf_urls = set()
        non_pdf_urls = set()

        for link in soup.find_all('a', href=True):
            href = link.get('href').strip()
            decoded_href = unquote(href)
            full_url = urljoin(url, decoded_href)
            decoded_full_url = unquote(full_url)
            
            if decoded_full_url.lower().endswith('.pdf'):
                pdf_urls.add(decoded_full_url)
            else:
                non_pdf_urls.add(decoded_full_url)

        return pdf_urls, non_pdf_urls

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        error_file.write(f"Error: {e}\n")
        return set(), set()

def main(start_url):
    with open('result_links.txt', 'w', encoding='utf-8') as output_file, \
            open('error_log.txt', 'w', encoding='utf-8') as error_file, \
            open('pdf_subpage_links.txt', 'w', encoding='utf-8') as pdf_subpage_file, \
            open('non_pdf_subpage_links.txt', 'w', encoding='utf-8') as non_pdf_subpage_file:

        all_urls = get_urls_from_page(start_url, error_file)

        total_urls = 0
        total_pdf_sub_urls = 0
        total_non_pdf_sub_urls = 0
        total_errors = 0

        for url in tqdm(all_urls, desc="Processing URLs", unit="url"):
            output_file.write(f"URL: {url}\n")
            pdf_urls, non_pdf_urls = get_subpage_urls(url, error_file)
            total_pdf_sub_urls += len(pdf_urls)
            total_non_pdf_sub_urls += len(non_pdf_urls)
            for pdf_url in pdf_urls:
                pdf_subpage_file.write(f"PDF URL: {pdf_url}\n")
            for non_pdf_url in non_pdf_urls:
                non_pdf_subpage_file.write(f"Non-PDF URL: {non_pdf_url}\n")
            total_urls += 1

        with open('error_log.txt', 'r', encoding='utf-8') as error_file:
            total_errors = sum(1 for line in error_file if "Error:" in line)

        print(colored("\nProcessing completed!", "green"))
        print(colored(f"Total URLs processed: {total_urls}", "cyan"))
        print(colored(f"Total PDF sub-URLs found: {total_pdf_sub_urls}", "cyan"))
        print(colored(f"Total non-PDF sub-URLs found: {total_non_pdf_sub_urls}", "cyan"))
        print(colored(f"Total errors encountered: {total_errors}", "red"))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python script.py <start_url>")
        sys.exit(1)
    start_url = sys.argv[1]
    main(start_url)