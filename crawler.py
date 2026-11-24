import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re

class page_info:
    def __init__(self, url, facultyName, html):
        self.url = url
        self.facultyName = facultyName
        self.html = html

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

def fetchHtml(url):
    return requests.get(url)

def base(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def target_page(html):
    soup = BeautifulSoup(html.text, 'html.parser')
    faculty_tag = soup.find('div', class_='fac-info')
    if faculty_tag:
        return True
    else:
        return False

def extractFacultyName(html):
    soup = BeautifulSoup(html.text, 'html.parser')
    return soup.find('h1', class_='profheader').get_text()

def store_page(url, facultyName, html, pages):
    if not facultyName:
        return
    else:
        pages.append(page_info(url, facultyName, html))
    

def extractLinks(html, base):
    soup = BeautifulSoup(html.text, 'html.parser')
    a_tags = soup.find_all('a', href=True)
    links = []
    for tag in a_tags:
        link = tag.get('href')
        if not link or '#' in link:
            continue
        if bool(re.match(r'^(?![a-zA-Z][a-zA-Z0-9+.-]*:|//)', link)):
            link = urljoin(base, link)
        if link.startswith("http"):
            links.append(link)
    return links

# test
seed = "https://www.cpp.edu/engineering/ce/index.shtml"
pages = crawler(seed, 13)
for page in pages:
    print(page.url + '\t' + page.facultyName)