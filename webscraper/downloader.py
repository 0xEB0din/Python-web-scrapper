import os
import logging
from urllib.parse import unquote, urljoin

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from webscraper.utils import validate_url, safe_join, make_output_dir


logger = logging.getLogger(__name__)


class FileDownloader:
    """Handles file downloads with streaming, progress tracking, and content-type validation."""

    def __init__(self, session=None, timeout=30):
        self.session = session or requests.Session()
        self.timeout = timeout

    def download(self, url, output_dir, filename=None):
        """Stream-download a file into output_dir. Returns True on success."""
        try:
            resp = self.session.get(url, timeout=self.timeout, stream=True)
            resp.raise_for_status()

            if not filename:
                filename = self._resolve_filename(url, resp)

            file_path = safe_join(output_dir, filename)
            total_size = int(resp.headers.get("content-length", 0))

            with open(file_path, "wb") as f:
                with tqdm(total=total_size, unit="B", unit_scale=True,
                          desc=os.path.basename(file_path), leave=False) as pbar:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))

            logger.info("Downloaded: %s", os.path.basename(file_path))
            return True

        except requests.RequestException as e:
            logger.warning("Download failed (%s): %s", url, e)
            return False
        except ValueError as e:
            # Raised by safe_join when path traversal is detected
            logger.warning("Blocked unsafe download path: %s", e)
            return False

    def download_if_content_type(self, url, expected_type, output_dir):
        """
        Download only if the server reports a matching Content-Type.

        Sends a HEAD request first to avoid pulling down large files we don't want.
        This catches cases where URLs don't have file extensions but actually serve
        downloadable content (common with CMS platforms and redirect-based file serving).
        """
        try:
            head_resp = self.session.head(
                url, timeout=self.timeout, allow_redirects=True
            )
            content_type = head_resp.headers.get("content-type", "")

            # Use 'in' rather than '==' to handle parameters like
            # 'application/pdf; charset=utf-8'
            if expected_type in content_type:
                return self.download(url, output_dir)

        except requests.RequestException:
            logger.debug("Content-type check skipped (request failed): %s", url)

        return False

    def fetch_by_extension(self, page_url, extensions, output_dir=None):
        """Download all files from a single page whose URLs match the given extensions."""
        if not validate_url(page_url):
            logger.error("Invalid URL: %s", page_url)
            return

        try:
            resp = self.session.get(page_url, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error("Failed to fetch page: %s", e)
            return

        soup = BeautifulSoup(resp.content, "html.parser")

        # Derive output directory from page title
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        else:
            title = "downloads"
        output_path = output_dir or make_output_dir(title)

        downloaded = 0
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]
            if not any(href.lower().endswith(ext.lower()) for ext in extensions):
                continue

            full_url = href if validate_url(href) else urljoin(page_url, href)
            if self.download(full_url, output_path):
                downloaded += 1

        print(f"\nDownloaded {downloaded} file(s) matching: {', '.join(extensions)}")

    def _resolve_filename(self, url, response):
        """
        Determine a filename from the Content-Disposition header or URL path.

        Prefers the server-provided filename (Content-Disposition) when available,
        falls back to the last segment of the URL path.
        """
        disposition = response.headers.get("content-disposition", "")

        if "filename" in disposition:
            # Handle RFC 5987 extended notation: filename*=UTF-8''document.pdf
            if "filename*=" in disposition:
                name = disposition.split("filename*=")[-1].split("''")[-1]
            else:
                name = disposition.split("filename=")[-1].strip('" ')
            return unquote(name)

        # Fall back to URL path basename
        path = unquote(url.split("?")[0].split("#")[0])
        name = os.path.basename(path)
        return name if name else f"download_{hash(url) & 0xFFFFFFFF}"
