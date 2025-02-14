from imports import *

# --- Configuration Settings ---
BASE_URL = "https://papers.nips.cc/"  # Base URL for NeurIPS papers
START_YEAR = 2023  # Start year for scraping
END_YEAR = 2023  # End year for scraping
MAX_PAPERS_PER_YEAR = 5  # Limit number of papers per year
OUTPUT_DIR = "MetaData_Results"  # Directory to store CSV metadata
RESULTS_DIR = "./Scrap_Results"  # Directory to store downloaded PDFs

# --- Utility Functions ---
def ensure_directory(path):
    """Ensure the specified directory exists, create if missing."""
    os.makedirs(path, exist_ok=True)


def fetch_page(url):
    """Fetch the HTML content of a given URL with error handling."""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def replace_illegal_chars(text):
    """Remove non-ASCII characters and trim whitespace."""
    if not text:
        return "N/A"
    return re.sub(r'[^\x20-\x7E]', '', text).strip()

# --- CSV Scraping Functions ---
def get_paper_links(year):
    """Retrieve paper links for a given year."""
    url = f"{BASE_URL}paper_files/paper/{year}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        print(f"Failed to fetch {year} page (Status: {response.status_code})")
        return []
    
    soup = BeautifulSoup(response.text, "html.parser")
    return [
        BASE_URL.rstrip("/") + link.get("href")
        for link in soup.find_all("a")
        if link.get("href") and link.get("href").startswith("/paper_files/paper/") and link.get("href").endswith(".html")
    ]


def scrape_year(year):
    """Scrape metadata of papers for a given year and save it in a CSV file."""
    print(f"Scraping papers for {year}...")
    paper_links = get_paper_links(year)
    if not paper_links:
        print(f"No papers found for {year}")
        return
    
    csv_file_path = os.path.join(OUTPUT_DIR, f"NeurIPS_{year}.csv")
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Sr. No", "Year", "Title", "Authors", "Abstract", "PDF Link"])
        
        sr_no = 1
        papers_scraped = 0  # Counter for papers scraped this year
        
        for paper_url in paper_links:
            if papers_scraped >= MAX_PAPERS_PER_YEAR:
                print(f"Reached maximum papers ({MAX_PAPERS_PER_YEAR}) for {year}.")
                break  # Stop after reaching limit
            
            response = requests.get(paper_url, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code != 200:
                print(f"Failed to fetch paper page: {paper_url} (Status: {response.status_code})")
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract metadata
            title_tag = soup.find("h4")
            title = replace_illegal_chars(title_tag.text) if title_tag else "Unknown Title"
            
            authors = "Unknown Authors"
            author_h4 = soup.find("h4", string="Authors")
            if author_h4:
                author_p = author_h4.find_next_sibling("p")
                if author_p:
                    authors = replace_illegal_chars(author_p.text)
            
            abstract = "No Abstract Found"
            abstract_h4 = soup.find("h4", string="Abstract")
            if abstract_h4:
                abstract_p = abstract_h4.find_next_sibling("p")
                if abstract_p:
                    abstract = replace_illegal_chars(abstract_p.text)
            
            pdf_link = next((BASE_URL.rstrip("/") + link.get("href") for link in soup.find_all("a") if "Paper" in link.text), None)
            
            if pdf_link:
                csv_writer.writerow([sr_no, year, title, authors, abstract, pdf_link])
                print(f"{year} | {sr_no}: {title} - Authors: {authors}")
                sr_no += 1
                papers_scraped += 1
            else:
                print(f"PDF link not found for {paper_url}")

# --- PDF Downloading Functions ---
def extract_pdf_links(html):
    """Extract PDF links from a given page."""
    pdf_links = []
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            if link['href'].endswith(".pdf"):
                pdf_links.append(urljoin(BASE_URL, link['href']))
    return pdf_links


def download_pdf(url, filepath, lock):
    """Download a PDF file with threading and locking."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        with open(filepath, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        with lock:
            print(f"Downloaded: {filepath}")
    except requests.RequestException as e:
        with lock:
            print(f"Error downloading {url}: {e}")


def process_paper(paper_name, paper_link, year_dir, lock):
    """Process each paper: extract and download its PDFs."""
    html = fetch_page(paper_link)
    if html:
        pdf_links = extract_pdf_links(html)
        threads = []
        for pdf_url in pdf_links:
            pdf_filename = os.path.join(year_dir, f"{paper_name}.pdf")
            thread = threading.Thread(target=download_pdf, args=(pdf_url, pdf_filename, lock))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()


def download_pdfs():
    """Main function to orchestrate PDF downloading."""
    ensure_directory(RESULTS_DIR)
    main_page_html = fetch_page(BASE_URL)
    
    lock = threading.Lock()
    # Iterate through years
    for year in range(START_YEAR, END_YEAR - 1, -1):
        year_dir = os.path.join(RESULTS_DIR, str(year))
        ensure_directory(year_dir)
        
        year_html = fetch_page(f"{BASE_URL}paper_files/paper/{year}")
        for paper_name, paper_link in extract_paper_links(year_html).items():
            process_paper(paper_name, paper_link, year_dir, lock)


def crawler_main():
    """Main function to execute CSV scraping and PDF downloading."""
    ensure_directory(OUTPUT_DIR)
    with Pool(processes=(END_YEAR - START_YEAR + 1)) as pool:
        pool.map(scrape_year, range(START_YEAR, END_YEAR - 1, -1))
    
    print("CSV scraping completed for all years!")
    download_pdfs()
    print("PDF downloading initiated!")
