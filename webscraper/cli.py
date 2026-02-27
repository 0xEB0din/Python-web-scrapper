import sys
import argparse

from webscraper.utils import setup_logging


def build_parser():
    parser = argparse.ArgumentParser(
        prog="webscraper",
        description="Recursive web scraper with file download capabilities.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- crawl ---
    crawl_cmd = subparsers.add_parser(
        "crawl",
        help="Crawl a website recursively and download discovered files.",
    )
    crawl_cmd.add_argument("url", help="URL to start crawling from")
    crawl_cmd.add_argument(
        "--depth", type=int, default=2,
        help="How many levels deep to crawl (default: 2)",
    )
    crawl_cmd.add_argument(
        "--output-dir", "-o",
        help="Directory for downloads and results (default: derived from page title)",
    )
    crawl_cmd.add_argument(
        "--delay", type=float, default=0.5,
        help="Seconds to wait between requests (default: 0.5)",
    )
    crawl_cmd.add_argument(
        "--timeout", type=int, default=30,
        help="HTTP request timeout in seconds (default: 30)",
    )
    crawl_cmd.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show debug-level output",
    )

    # --- fetch ---
    fetch_cmd = subparsers.add_parser(
        "fetch",
        help="Download files with specific extensions from a single page.",
    )
    fetch_cmd.add_argument("url", help="Page URL to download files from")
    fetch_cmd.add_argument(
        "extensions", nargs="+",
        help="File extensions to match (e.g., .pdf .docx .xlsx)",
    )
    fetch_cmd.add_argument(
        "--output-dir", "-o",
        help="Directory for downloads (default: derived from page title)",
    )
    fetch_cmd.add_argument(
        "--timeout", type=int, default=30,
        help="HTTP request timeout in seconds (default: 30)",
    )
    fetch_cmd.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show debug-level output",
    )

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    setup_logging(verbose=args.verbose)

    if args.command == "crawl":
        # Lazy imports so --help stays fast
        from webscraper.crawler import Crawler

        crawler = Crawler(timeout=args.timeout, delay=args.delay)
        crawler.crawl(args.url, depth=args.depth, output_dir=args.output_dir)

    elif args.command == "fetch":
        from webscraper.downloader import FileDownloader

        downloader = FileDownloader(timeout=args.timeout)
        downloader.fetch_by_extension(
            args.url, args.extensions, output_dir=args.output_dir,
        )
