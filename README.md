# WebScraper

A Python-based recursive web scraper that crawls websites at configurable depth, extracts and categorizes URLs, and downloads discovered files. Built with clean separation of concerns, safe file handling, and rate-limited requests.

## Why This Exists

I needed to bulk-download documents (PDFs, datasets, lecture slides) from hierarchically organized websites — the kind where files are buried two or three clicks deep across dozens of subpages. Existing tools were either overkill for the job (Scrapy's learning curve for a download task) or too limited (wget doesn't categorize by file type or verify content types). This sits in the middle: focused, configurable, and easy to extend.

## What It Does

- **Recursive crawling** at configurable depth — extracts links from each page level, scoped by HTML element
- **File type detection** using both URL extension and HTTP Content-Type headers, catching mislinked or extension-less resources
- **Organized output** — downloads go into named directories, URLs are written to categorized result files
- **Extension-based fetching** — single-page mode to grab all files matching specific extensions
- **Rate limiting** — configurable inter-request delay to avoid hammering target servers
- **Safe file handling** — filenames sanitized against path traversal, writes constrained to the output directory

## Architecture

```
webscraper/
├── __init__.py          # Package metadata
├── __main__.py          # Entry point (python -m webscraper)
├── cli.py               # Argument parsing, command routing
├── crawler.py           # Recursive crawling engine
├── downloader.py        # File downloads with streaming + validation
└── utils.py             # URL validation, path sanitization, logging
```

The scraper separates **discovery** from **download**: the crawler first visits all pages and collects URLs into deduplicated, categorized sets (PDF vs. non-PDF), then the downloader handles the file I/O phase. This clean split makes it easy to add a `--dry-run` mode, apply download filters, or swap the download backend without touching crawl logic.

**Key design decisions:**

- `requests.Session` for connection pooling and consistent headers across the crawl
- Downloads are streamed via `iter_content` to handle large files without loading them into memory
- Filenames are sanitized against path traversal before any disk write — defense-in-depth against malicious URLs or Content-Disposition headers
- HEAD requests for content-type checks before committing to full downloads
- Lazy imports in the CLI layer so `--help` responds instantly without loading the full dependency tree

## Installation

```bash
git clone https://github.com/0xEB0din/Python-web-scrapper.git
cd Python-web-scrapper
pip install -r requirements.txt
```

Requires Python 3.7+.

## Usage

### Recursive Crawl

Crawl a website and download all discovered PDFs:

```bash
python -m webscraper crawl https://example.com/resources/
```

With options:

```bash
python -m webscraper crawl https://example.com/docs/ \
    --depth 3 \
    --output-dir ./downloads \
    --delay 1.0 \
    --verbose
```

### Fetch by Extension

Download all files matching specific extensions from a single page:

```bash
python -m webscraper fetch https://example.com/datasets/ .csv .xlsx .json
```

### Command Reference

```
crawl <url>
  --depth N          Levels of recursion (default: 2)
  --output-dir DIR   Where to save output (default: derived from page title)
  --delay SECS       Wait between requests (default: 0.5)
  --timeout SECS     HTTP timeout per request (default: 30)
  -v, --verbose      Debug-level logging

fetch <url> <ext> [ext ...]
  --output-dir DIR   Where to save output (default: derived from page title)
  --timeout SECS     HTTP timeout per request (default: 30)
  -v, --verbose      Debug-level logging
```

## Output

The `crawl` command produces a directory containing:

```
<output_dir>/
├── result_links.txt     # Level-1 URLs from the start page
├── pdf_links.txt        # PDF URLs found at deeper levels
├── non_pdf_links.txt    # Non-PDF URLs found at deeper levels
├── errors.log           # Failed requests with context
└── *.pdf                # Downloaded files
```

## Security Considerations

This tool makes outbound HTTP requests and writes files to disk — both operations carry risk when inputs are untrusted.

**Implemented:**

- **Path traversal prevention** — downloaded filenames are stripped of directory components and sanitized; `safe_join()` verifies the resolved path stays within the output directory, blocking escape attempts via `../../` sequences or crafted Content-Disposition headers
- **Request timeouts** — all HTTP calls enforce a configurable timeout to prevent indefinite hangs from unresponsive servers
- **Input validation** — URLs are validated for scheme (HTTP/HTTPS only) and network location before any request is made
- **Rate limiting** — configurable inter-request delay reduces impact on target infrastructure
- **Content-Type verification** — files are checked by MIME type, not just URL extension, so extension spoofing doesn't bypass classification
- **Connection pooling via Session** — avoids leaking connections across the crawl

**Not yet implemented** (see [Roadmap](#roadmap)):

- SSRF protections — blocking requests to RFC 1918 private ranges (10.x, 172.16.x, 192.168.x), link-local (169.254.x), and loopback addresses
- Download size limits to guard against disk exhaustion
- URL allowlist/blocklist for scoping crawls to trusted domains
- robots.txt parsing and compliance
- TLS certificate verification controls

## Limitations & Tradeoffs

| Area | Current Behavior | Tradeoff |
|------|-----------------|----------|
| **Concurrency** | Single-threaded, synchronous | Easier to reason about and rate-limit, but slower on large sites |
| **JS rendering** | Static HTML only | No browser dependency, but SPAs and dynamically loaded content are invisible |
| **Crawl scope** | `<section>` tags at depth 1, all `<a>` tags deeper | Reduces noise from nav/footer links, but may miss content outside `<section>` |
| **Authentication** | Not supported | Keeps the tool simple, but can't scrape pages behind login walls |
| **State** | In-memory only | No external dependencies, but interrupted crawls can't be resumed |
| **Deduplication** | Per-run URL sets | Prevents duplicate downloads within a run, but no memory across sessions |

## Roadmap

**Planned Features**

- [ ] Configurable CSS selectors for link extraction (currently hardcoded to `<section>` at depth 1)
- [ ] `--dry-run` flag to preview discovered URLs without downloading
- [ ] Export results in structured formats (JSON, CSV) for pipeline integration
- [ ] Persistent crawl state for resuming interrupted sessions
- [ ] Custom HTTP headers and cookie support for authenticated scraping
- [ ] Configurable download file types (not just PDFs) in crawl mode

**Security Enhancements**

- [ ] SSRF protection — validate resolved IPs against private/reserved ranges before connecting
- [ ] robots.txt parsing with opt-in enforcement
- [ ] Per-file and per-session download size caps
- [ ] Domain allowlist/blocklist via config file
- [ ] TLS certificate pinning options
- [ ] Request header rotation to reduce fingerprinting

**Architecture**

- [ ] Async I/O with `aiohttp` for concurrent crawling and downloads
- [ ] Plugin system for custom content parsers (PDF metadata extraction, etc.)
- [ ] SQLite-backed crawl history for cross-run deduplication
- [ ] Docker image for sandboxed execution
- [ ] Test suite with mocked HTTP fixtures
- [ ] CI pipeline with linting and dependency scanning

## Dependencies

| Package | Purpose |
|---------|---------|
| [requests](https://docs.python-requests.org/) | HTTP client with session support |
| [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing and link extraction |
| [tqdm](https://github.com/tqdm/tqdm) | Download and crawl progress bars |
| [ftfy](https://github.com/rspeer/python-ftfy) | Unicode text normalization for page titles |

## License

MIT
