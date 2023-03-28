# Python Web Scraper

This is a Python web scraper that fetches nested URLs up to two levels and grabs download URLs. The results are then sorted into three files:

1. `result_links.txt`: Contains the first-level scraping results.
2. `pdf_subpage_links.txt`: Contains all URLs that end with `.pdf` found in the second level.
3. `non_pdf_subpage_links.txt`: Contains all non-PDF URLs found in the second level.

## Usage

To use the web scraper, run the following command in your terminal or shell environment:

```bash
$ python fetch_urls.py https://example.com/
```
The argument passed to the script should be the URL of the website you want to scrape.


### Todo List
- [x] Use external files to store the URLs and errors.
- [x] Add a progress bar to show the scraping progress.
- [x] Display the results statistics after the scraping is done.
- [x] Modify the scraper to grab all links, not just PDFs.
- [x] Save the non-PDF links to a separate file.
- [x] Make the URL a command-line parameter instead of hard-coding it in the script.
- [ ] Add functionality to download the files from the URLs.
- [ ] Match the file names with the URLs to ensure correct downloading.
- [ ] Update the statistics after the download is complete.
- [ ] Flush the session.


