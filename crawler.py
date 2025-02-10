import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import threading
import re

# The regex patterns were inspired by ChatGPT.  
# The "Web Scraping Crash Course" by FreeCodeCamp was extremely helpful.  
# The BeautifulSoup documentation provided valuable insights.

BASE_URL = "https://papers.nips.cc/"
RESULTS_DIR = "./Scrap_Results"

def ensure_directory(path):
    """Ensure the directory exists."""
    os.makedirs(path, exist_ok=True)

def fetch_page(url):
    """Fetch the HTML content of a given URL."""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_year_links(html):
    """Extract links for different years."""
    year_links = {}
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith("/paper_files/paper/"):
                year = href.split("/")[-1]
                year_links[year] = urljoin(BASE_URL, href)
    return year_links

def extract_paper_links(html):
    """Extract links to individual papers."""
    paper_links = {}
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith("/paper_files/paper/"):
                paper_name = link.text.strip().replace(' ', '_').replace('/', '_')
                paper_links[paper_name] = urljoin(BASE_URL, href)
    return paper_links

def extract_pdf_links(html):
    """Extract PDF links from a paper's page."""
    pdf_links = []
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            if link['href'].endswith(".pdf"):
                pdf_links.append(urljoin(BASE_URL, link['href']))
    return pdf_links

def download_pdf(url, filepath):
    """Download a PDF file."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filepath, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        print(f"Downloaded: {filepath}")
    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")

def process_paper(paper_name, paper_link, year_dir):
    """Process a single paper by extracting and downloading PDFs."""
    html = fetch_page(paper_link)
    if html:
        pdf_links = extract_pdf_links(html)
        for pdf_url in pdf_links:
            pdf_filename = os.path.join(year_dir, f"{paper_name}.pdf")
            threading.Thread(target=download_pdf, args=(pdf_url, pdf_filename)).start()

def main():
    ensure_directory(RESULTS_DIR)
    main_page_html = fetch_page(BASE_URL)
    year_links = extract_year_links(main_page_html)
    
    for year, year_link in year_links.items():
        year_dir = os.path.join(RESULTS_DIR, year)
        ensure_directory(year_dir)
        
        year_html = fetch_page(year_link)
        paper_links = extract_paper_links(year_html)
        
        for paper_name, paper_link in paper_links.items():
            process_paper(paper_name, paper_link, year_dir)
    
if __name__ == "__main__":
    main()
