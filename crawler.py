import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

lock = threading.Lock()
BASE_URL = "https://papers.nips.cc/"
RESULTS_DIR = "./Scrap_Results"

# Ensure base results directory exists
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

def fetch_page(url):
    """Fetch the HTML content of a given URL."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
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
                full_url = urljoin(BASE_URL, href)
                year_links[year] = full_url
    return year_links

def extract_paper_links(html, base_url):
    """Extract links to individual papers."""
    paper_links = []
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            full_url = urljoin(base_url, link['href'])
            paper_links.append(full_url)
    return paper_links

def save_links_to_file(links, filename):
    """Save extracted links to a text file."""
    try:
        with lock:
            with open(filename, "w") as file:
                for link in links:
                    file.write(link + "\n")
    except Exception as e:
        print(f"Error saving links to file: {e}")

def process_year_links(year_links):
    """Extract and save paper links for each year."""
    df = pd.DataFrame(columns=['Year', 'URL'])
    rows = []

    for year, url in year_links.items():
        year_folder = os.path.join(RESULTS_DIR, year)
        os.makedirs(year_folder, exist_ok=True)

        paper_html = fetch_page(url)
        paper_links = extract_paper_links(paper_html, url)

        paper_filename = os.path.join(year_folder, "paper_links.txt")
        save_links_to_file(paper_links, paper_filename)

        rows.append({'Year': year, 'URL': url})

    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    df.to_csv(os.path.join(RESULTS_DIR, "year_links.csv"), index=False)
    return df

def extract_pdf_links(html, base_url):
    """Extract PDF links from a paper's page."""
    pdf_links = []
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and href.endswith('.pdf'):
                full_url = urljoin(base_url, href)
                pdf_links.append(full_url)
    return pdf_links

def download_pdf(pdf_url, download_directory, paper_name):
    """Download a PDF file and save it with its paper name."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(pdf_url, headers=headers, stream=True)
        response.raise_for_status()

        pdf_name = f"{paper_name}.pdf"  
        pdf_path = os.path.join(download_directory, pdf_name)

        with open(pdf_path, "wb") as pdf_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    pdf_file.write(chunk)

        print(f"Downloaded: {pdf_name}")
    except requests.RequestException as e:
        print(f"Error downloading PDF {pdf_url}: {e}")

def process_paper_link(year, paper_link):
    """Process a single paper link: Extract and download PDFs."""
    year_folder = os.path.join(RESULTS_DIR, year)
    pdf_directory = os.path.join(year_folder, "PDFs")
    os.makedirs(pdf_directory, exist_ok=True)

    paper_name = paper_link.split("/")[-1].replace("-", "_")  
    html_content = fetch_page(paper_link)
    if html_content:
        pdf_links = extract_pdf_links(html_content, paper_link)

        with ThreadPoolExecutor(max_workers=50) as pdf_executor: 
            futures = [pdf_executor.submit(download_pdf, pdf_link, pdf_directory, paper_name) for pdf_link in pdf_links]

            for future in as_completed(futures):
                future.result()  

def process_papers_for_year(year, paper_links):
    """Process papers for a given year using a ThreadPoolExecutor."""
    with ThreadPoolExecutor(max_workers=2000) as paper_executor:
        futures = [paper_executor.submit(process_paper_link, year, paper_link) for paper_link in paper_links]

        for future in as_completed(futures):
            future.result()  

def main():
    start_time = time.time()
    print("Starting scraping...")

    main_page_html = fetch_page(BASE_URL)
    year_links = extract_year_links(main_page_html)
    df_years = process_year_links(year_links)

    with ThreadPoolExecutor(max_workers=10) as year_executor:  
        year_futures = []
        for _, row in df_years.iterrows():
            year = row['Year']
            paper_filename = os.path.join(RESULTS_DIR, year, "paper_links.txt")

            try:
                with open(paper_filename, "r") as f:
                    paper_links = [line.strip() for line in f]

                year_futures.append(year_executor.submit(process_papers_for_year, year, paper_links))
            except FileNotFoundError:
                print(f"Error: Paper links file '{paper_filename}' not found.")
                continue

        for future in as_completed(year_futures):
            future.result() 

    end_time = time.time()
    print(f"Scraping complete in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
