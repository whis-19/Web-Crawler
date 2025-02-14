from imports import *
# --- Configuration for CSV Scraping ---
BASE_URL = "https://papers.nips.cc/"
START_YEAR = 2023
END_YEAR = 2023
MAX_PAPERS_PER_YEAR = 5  # Limit to 5 papers per year
OUTPUT_DIR = "MetaData_Results"

# --- Configuration for PDF Downloading ---
RESULTS_DIR = "./Scrap_Results"

# --- Utility Functions ---
def ensure_directory(path):
    os.makedirs(path, exist_ok=True)

def fetch_page(url):
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def replace_illegal_chars(text):
    if not text:
        return "N/A"
    return re.sub(r'[^\x20-\x7E]', '', text).strip()

# --- CSV Scraping Functions ---
def get_paper_links(year):
    url = f"{BASE_URL}paper_files/paper/{year}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
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
    print(f"Scraping papers for {year}...")

    paper_links = get_paper_links(year)
    if not paper_links:
        print(f"No papers found for {year}")
        return
    
    csv_file_path = os.path.join(OUTPUT_DIR, f"NeurIPS_{year}.csv")
    
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Write header row
        csv_writer.writerow(["Sr. No", "Year", "Title", "Authors", "Abstract", "PDF Link"])

        sr_no = 1
        papers_scraped = 0  # Counter for papers scraped this year

        for paper_url in paper_links:
            if papers_scraped >= MAX_PAPERS_PER_YEAR:
                print(f"Reached maximum papers ({MAX_PAPERS_PER_YEAR}) for {year}.")
                break  # Stop scraping after reaching the limit

            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(paper_url, headers=headers)
            if response.status_code != 200:
                print(f"Failed to fetch paper page: {paper_url} (Status: {response.status_code})")
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
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
def extract_year_links(html):
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
    pdf_links = []
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            if link['href'].endswith(".pdf"):
                pdf_links.append(urljoin(BASE_URL, link['href']))
    return pdf_links

def download_pdf(url, filepath, lock): # Add a lock
    try:
        response = requests.get(url, stream=True, timeout=10) # Add timeout
        response.raise_for_status()
        with open(filepath, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        with lock: # Acquire the lock before printing
            print(f"Downloaded: {filepath}")
    except requests.RequestException as e:
        with lock: # Acquire the lock even if there's an error
            print(f"Error downloading {url}: {e}")

def process_paper(paper_name, paper_link, year_dir, lock): # Add the lock
    html = fetch_page(paper_link)
    if html:
        pdf_links = extract_pdf_links(html)
        threads = [] # Store the threads
        for pdf_url in pdf_links:
            pdf_filename = os.path.join(year_dir, f"{paper_name}.pdf")
            thread = threading.Thread(target=download_pdf, args=(pdf_url, pdf_filename, lock)) # Pass the lock
            threads.append(thread) # Add thread to the list
            thread.start()
        for thread in threads: # Join all threads for this paper
            thread.join()

def download_pdfs():
    ensure_directory(RESULTS_DIR)
    main_page_html = fetch_page(BASE_URL)
    year_links = extract_year_links(main_page_html)
    
    for year, year_link in year_links.items():
        if int(year) < END_YEAR or int(year) > START_YEAR:
            continue
        
        year_dir = os.path.join(RESULTS_DIR, year)
        ensure_directory(year_dir)
        
        year_html = fetch_page(year_link)
        paper_links = extract_paper_links(year_html)
        
        limited_paper_links = dict(list(paper_links.items())[:MAX_PAPERS_PER_YEAR])

        lock = threading.Lock() # Create a lock for each year
        for paper_name, paper_link in limited_paper_links.items():
            process_paper(paper_name, paper_link, year_dir, lock)

def crawler_main():
    # --- CSV Scraping ---
    YEARS = list(range(START_YEAR, END_YEAR - 1, -1))  # Generate years in reverse order
    ensure_directory(OUTPUT_DIR)
    with Pool(processes=len(YEARS)) as pool:
        pool.map(scrape_year, YEARS)

    print("CSV scraping completed for all years!")

    # --- PDF Downloading ---
    download_pdfs()
    print("PDF downloading initiated in the background!")
