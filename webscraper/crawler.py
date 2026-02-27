import os
import time
import logging
from urllib.parse import urljoin, unquote

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import ftfy

from webscraper.downloader import FileDownloader
from webscraper.utils import validate_url, make_output_dir


logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (compatible; PythonWebScraper/1.0; "
    "+https://github.com/0xEB0din/Python-web-scrapper)"
)


class Crawler:
    """
    Recursive web crawler that extracts links at configurable depth
    and downloads discovered files.

    Separates the discovery phase (crawl + categorize URLs) from the
    download phase, making it straightforward to add dry-run mode,
    filters, or swap the download backend independently.
    """

    def __init__(self, timeout=30, delay=0.5):
        self.timeout = timeout
        self.delay = delay

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

        self.downloader = FileDownloader(session=self.session, timeout=timeout)

    def crawl(self, start_url, depth=2, output_dir=None):
        """
        Crawl from start_url to the specified depth, downloading PDFs
        found along the way.
        """
        if not validate_url(start_url):
            logger.error("Invalid URL: %s", start_url)
            return

        logger.info("Starting crawl: %s (depth=%d)", start_url, depth)

        try:
            soup = self._fetch_page(start_url)
        except requests.RequestException as e:
            logger.error("Failed to fetch start URL: %s", e)
            return

        page_title = self._get_page_title(soup)
        output_path = output_dir or make_output_dir(page_title)
        logger.info("Output: %s", output_path)

        # Depth 1: extract links from <section> elements on the start page
        level1_links = self._extract_links(soup, start_url, scope="section")
        logger.info("Found %d links at depth 1", len(level1_links))

        if depth < 2:
            self._save_results(output_path, level1_urls=level1_links)
            self._report(len(level1_links), 0, 0, 0)
            return

        # --- Discovery phase ---
        # Visit each level-1 link and collect all URLs found on those pages
        all_pdf_urls = set()
        all_non_pdf_urls = set()
        errors = []
        pages_crawled = 0

        for url in tqdm(level1_links, desc="Crawling pages", unit="page"):
            self._throttle()
            try:
                page = self._fetch_page(url)
                pdf_urls, non_pdf_urls = self._categorize_links(page, url)
                all_pdf_urls.update(pdf_urls)
                all_non_pdf_urls.update(non_pdf_urls)
                pages_crawled += 1
            except requests.RequestException as e:
                logger.warning("Skipping %s: %s", url, e)
                errors.append((url, str(e)))

        # --- Download phase ---
        downloaded = 0

        for pdf_url in tqdm(all_pdf_urls, desc="Downloading PDFs", unit="file"):
            self._throttle()
            if self.downloader.download(pdf_url, output_path):
                downloaded += 1

        # Content-type verification pass: some non-.pdf URLs actually serve PDF
        # content (common with CMS query-string file serving and redirects).
        # We use HEAD checks to avoid downloading unnecessarily.
        for url in tqdm(all_non_pdf_urls, desc="Checking non-PDF links", unit="url"):
            self._throttle()
            if self.downloader.download_if_content_type(
                url, "application/pdf", output_path
            ):
                downloaded += 1

        self._save_results(
            output_path, level1_links, all_pdf_urls, all_non_pdf_urls, errors
        )
        self._report(
            pages_crawled, len(all_pdf_urls), len(all_non_pdf_urls),
            downloaded, len(errors),
        )

    def _fetch_page(self, url):
        """Fetch a URL and return parsed HTML."""
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return BeautifulSoup(resp.text, "html.parser")

    def _extract_links(self, soup, base_url, scope=None):
        """
        Extract all anchor hrefs from the page.

        When scope is set (e.g., "section"), only links inside matching
        elements are collected. This lets us focus on content areas and
        skip navigation chrome at depth 1.
        """
        links = set()
        containers = soup.find_all(scope) if scope else [soup]

        for container in containers:
            for anchor in container.find_all("a", href=True):
                href = unquote(anchor["href"].strip())
                full_url = unquote(urljoin(base_url, href))
                links.add(full_url)

        return links

    def _categorize_links(self, soup, base_url):
        """Split page links into PDF and non-PDF sets based on URL extension."""
        pdf_urls = set()
        non_pdf_urls = set()

        for anchor in soup.find_all("a", href=True):
            href = unquote(anchor["href"].strip())
            full_url = unquote(urljoin(base_url, href))

            if full_url.lower().endswith(".pdf"):
                pdf_urls.add(full_url)
            else:
                non_pdf_urls.add(full_url)

        return pdf_urls, non_pdf_urls

    def _get_page_title(self, soup, fallback="scraped_output"):
        """Extract and normalize the page title for use as a directory name."""
        if soup.title and soup.title.string:
            return ftfy.fix_text(soup.title.string.strip())
        return fallback

    def _throttle(self):
        """Rate limiting between requests to avoid overwhelming target servers."""
        if self.delay > 0:
            time.sleep(self.delay)

    def _save_results(self, output_dir, level1_urls=None, pdf_urls=None,
                      non_pdf_urls=None, errors=None):
        """Write categorized URL lists to files inside the output directory."""
        if level1_urls:
            with open(os.path.join(output_dir, "result_links.txt"), "w",
                      encoding="utf-8") as f:
                for url in sorted(level1_urls):
                    f.write(url + "\n")

        if pdf_urls:
            with open(os.path.join(output_dir, "pdf_links.txt"), "w",
                      encoding="utf-8") as f:
                for url in sorted(pdf_urls):
                    f.write(url + "\n")

        if non_pdf_urls:
            with open(os.path.join(output_dir, "non_pdf_links.txt"), "w",
                      encoding="utf-8") as f:
                for url in sorted(non_pdf_urls):
                    f.write(url + "\n")

        if errors:
            with open(os.path.join(output_dir, "errors.log"), "w",
                      encoding="utf-8") as f:
                for url, err in errors:
                    f.write(f"{url} | {err}\n")

    @staticmethod
    def _report(pages, pdf_count, non_pdf_count, downloaded, error_count=0):
        """Print a summary of the crawl results."""
        print(f"\n{'─' * 42}")
        print(f"  Pages crawled:       {pages}")
        print(f"  PDF links found:     {pdf_count}")
        print(f"  Non-PDF links:       {non_pdf_count}")
        print(f"  Files downloaded:    {downloaded}")
        if error_count:
            print(f"  Errors:              {error_count}")
        print(f"{'─' * 42}")
