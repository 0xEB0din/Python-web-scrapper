# Python web Scrapper

A web scrapper to fetch nested urls (two levels) and graps download URLs, the result is sorted in thre files:
1. result_links.txt => the first level scrapping results
2. pdf_subpage.links.txt => 
3. non_pdf_subpage_links.txt => 

### Usage:
```bash
$ python fetch_urls.py https://example.com/
```

### Todo List
- [x] External files to grap the urls and errors
- [x] Progress Bar
- [x] Results stats
- [x] Grap all links, not only PDFs
- [x] Add the non-PDFs to another file
- [x] Extract the URL to be a CLI parameter
- [ ] Download the files from URLS
- [ ] Match the file names with the URLs
- [ ] Update the stats after the download

