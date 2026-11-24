import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re

class page_info:
    def __init__(self, url, facultyName, html):
        self.url = url
        self.facultyName = facultyName
        self.html = html

#-------------------------------------------------------------------------
# FUNCTION: crawler
# SPECIFICATION: starts from seed and crawls until num_targets faculty
#                pages are reached
# RETURNS: a list of page_info, where each page is a faculty page
#-------------------------------------------------------------------------
def crawler(seed, num_targets):
    targets_found = 0
    frontier = [seed]
    seen = set()
    seen.add(seed)
    pages = []
    while frontier:
        url = frontier.pop(0)
        print(url)
        html = fetchHtml(url)
        if target_page(html):
            facultyName = extractFacultyName(html)
            targets_found += 1
        else:
            facultyName = None
        store_page(url, facultyName, html, pages)
        if targets_found == num_targets:
            frontier.clear()
        else:
            links = extractLinks(html, base(url))
            for link in links:
                if link not in seen:
                    seen.add(link)
                    frontier.append(link)
    return pages

#-------------------------------------------------------------------------
# FUNCTION: fetchHtml
# SPECIFICATION: finds html content based on page url
# RETURNS: the html content of the page
#-------------------------------------------------------------------------
def fetchHtml(url):
    return requests.get(url)

#-------------------------------------------------------------------------
# FUNCTION: base
# SPECIFICATION: finds the base address of a url
# RETURNS: the base address
#-------------------------------------------------------------------------
def base(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

#-------------------------------------------------------------------------
# FUNCTION: target_page
# SPECIFICATION: uses html info to determine if the page is a default
#                faculty page
# RETURNS: true if its a faculty page, false otherwise
#-------------------------------------------------------------------------
def target_page(html):
    soup = BeautifulSoup(html.text, 'html.parser')
    faculty_tag = soup.find('div', class_='fac-info')
    if faculty_tag:
        return True
    else:
        return False

#-------------------------------------------------------------------------
# FUNCTION: extractFacultyName
# SPECIFICATION: finds the professor's name from a faculty page
# RETURNS: the name of the professor
#-------------------------------------------------------------------------
def extractFacultyName(html):
    soup = BeautifulSoup(html.text, 'html.parser')
    return soup.find('h1', class_='profheader').get_text()

#-------------------------------------------------------------------------
# FUNCTION: store_page
# SPECIFICATION: adds a page_entry to the list pages if that page is one
#                of the fauculty targets
#-------------------------------------------------------------------------
def store_page(url, facultyName, html, pages):
    if not facultyName:
        return
    else:
        pages.append(page_info(url, facultyName, html))

#-------------------------------------------------------------------------
# FUNCTION: extractLinks
# SPECIFICATION: finds and resolves all links on a page
# RETURNS: a list of links from the page
#-------------------------------------------------------------------------
def extractLinks(html, base):
    soup = BeautifulSoup(html.text, 'html.parser')
    a_tags = soup.find_all('a', href=True)
    links = []
    for tag in a_tags:
        link = tag.get('href')
        # skip over '#' links and empty hrefs
        if not link or '#' in link:
            continue
        # check if link is relative
        if bool(re.match(r'^(?![a-zA-Z][a-zA-Z0-9+.-]*:|//)', link)):
            # prepend the base url to the relative link
            link = urljoin(base, link)
        # filter out links that are not http (excludes links like "mailto:broncofamily@cpp.edu")
        if link.startswith("http"):
            links.append(link)
    return links