import os
import sys
import requests
import unicodedata
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from tqdm import tqdm
from termcolor import colored
import ftfy


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


def download_pdf(url, folder_path, error_file):
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Extract filename from URL
        filename = os.path.basename(url)

        # Create full file path
        file_path = os.path.join(folder_path, filename)

        # Write file to disk
        with open(file_path, 'wb') as f:
            f.write(response.content)

        print(colored(f"PDF downloaded: {url}", "green"))

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        error_file.write(f"Error: {e}\n")

# New function to check and download PDFs
def check_and_download_pdfs(url, folder_path, error_file):
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        pdf_urls = set()
        for link in soup.find_all('a', href=True):
            href = link.get('href').strip()
            decoded_href = unquote(href)
            full_url = urljoin(url, decoded_href)
            decoded_full_url = unquote(full_url)

            if decoded_full_url.lower().endswith('.pdf'):
                pdf_urls.add(decoded_full_url)

        for pdf_url in pdf_urls:
            download_pdf(pdf_url, folder_path, error_file)

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        error_file.write(f"Error: {e}\n")


def main(start_url):
    with open('result_links.txt', 'w', encoding='utf-8') as output_file, \
            open('error_log.txt', 'w', encoding='utf-8') as error_file, \
            open('pdf_subpage_links.txt', 'w', encoding='utf-8') as pdf_subpage_file, \
            open('non_pdf_subpage_links.txt', 'w', encoding='utf-8') as non_pdf_subpage_file:

        all_urls = get_urls_from_page(start_url, error_file)

        # Create folder for PDF downloads
        response = requests.get(start_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        page_title = soup.title.string.strip()
        fixed_title = ftfy.fix_text(page_title)
        folder_name = fixed_title.replace(' ', '_')
        folder_path = os.path.join(os.getcwd(), folder_name)
        os.makedirs(folder_path, exist_ok=True)

        total_urls = 0
        total_pdf_sub_urls = 0
        total_non_pdf_sub_urls = 0
        total_errors = 0
        downloaded_files_count = 0

        for url in tqdm(all_urls, desc="Processing URLs", unit="url"):
            output_file.write(f"URL: {url}\n")
            pdf_urls, non_pdf_urls = get_subpage_urls(url, error_file)
            total_pdf_sub_urls += len(pdf_urls)
            total_non_pdf_sub_urls += len(non_pdf_urls)

            for pdf_url in pdf_urls:
                pdf_subpage_file.write(f"PDF URL: {pdf_url}\n")
                download_pdf(pdf_url, folder_path, error_file)
                downloaded_files_count += 1

            for non_pdf_url in non_pdf_urls:
                non_pdf_subpage_file.write(f"Non-PDF URL: {non_pdf_url}\n")

            # Check and download PDFs from non-PDF sub-URLs
            check_and_download_pdfs(non_pdf_url, folder_path, error_file)
            downloaded_files_count += len(pdf_urls)
            total_urls += 1

    with open('error_log.txt', 'r', encoding='utf-8') as error_file:
        total_errors = sum(1 for line in error_file if "Error:" in line)

    print(colored("\nProcessing completed!", "green"))
    print(colored(f"Total URLs processed: {total_urls}", "cyan"))
    print(colored(f"Total PDF sub-URLs found: {total_pdf_sub_urls}", "blue"))
    print(colored(f"Total non-PDF sub-URLs found: {total_non_pdf_sub_urls}", "yellow"))
    print(colored(f"Total files downloaded: {downloaded_files_count}", "cyan"))
    print(colored(f"Total errors encountered: {total_errors}", "red"))

    # Ask the user if they want to purge the result files
    purge_choice = input("\nDo you want to purge the result files? (y/n): ").lower()
    if purge_choice == 'y':
        os.remove('result_links.txt')
        os.remove('error_log.txt')
        os.remove('pdf_subpage_links.txt')
        os.remove('non_pdf_subpage_links.txt')
        print(colored("Result files purged successfully.", "green"))
    else:
        print(colored("Result files not purged.", "yellow"))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python script.py <start_url>")
        sys.exit(1)
    start_url = sys.argv[1]
    main(start_url)
