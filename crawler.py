import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import threading
import time

lock = threading.Lock()

def fetch_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_links(html, base_url):
    links = []
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            full_url = urljoin(base_url, link['href'])
            links.append(full_url)
    return links

def extract_pdf_links(html, base_url):
    pdf_links = []
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and href.endswith('.pdf'):
                full_url = urljoin(base_url, href)
                pdf_links.append(full_url)
    return pdf_links

def save_links_to_file(links, filename):
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory)
    try:
        with lock:  
            with open(filename, "a") as file:  
                for link in links:
                    file.write(link + "\n")
    except Exception as e:
        print(f"Error saving links to file: {e}")

def download_pdf(pdf_url, download_directory):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(pdf_url, headers=headers, stream=True)
        response.raise_for_status()
        
        pdf_name = pdf_url.split("/")[-1]
        pdf_path = os.path.join(download_directory, pdf_name)

        with open(pdf_path, "wb") as pdf_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    pdf_file.write(chunk)

        print(f"Downloaded: {pdf_name}")
    except requests.RequestException as e:
        print(f"Error downloading PDF {pdf_url}: {e}")

def crawl_and_extract_initial_links(start_url):
    html_content = fetch_page(start_url)
    if html_content:
        links = extract_links(html_content, start_url)
        save_links_to_file(links, "./Scrap_Results/links.txt")
    else:
        print("Could not fetch initial page content.")

def process_hash_links(links_chunk, pdf_filename, download_directory):
    for link in links_chunk:
        if "hash" in link:
            print(f"Thread {threading.current_thread().name}: Processing link with hash: {link}")
            html_content = fetch_page(link)
            if html_content:
                pdf_links = extract_pdf_links(html_content, link)
                if pdf_links:
                    print(f"Thread {threading.current_thread().name}: Found PDF links: {pdf_links}")
                    save_links_to_file(pdf_links, pdf_filename)
                    # Download PDFs
                    for pdf_link in pdf_links:
                        download_pdf(pdf_link, download_directory)
                else:
                    print(f"Thread {threading.current_thread().name}: No PDF links found on this page. Continuing to the next link.")
            else:
                print(f"Thread {threading.current_thread().name}: Could not fetch page content. Continuing to the next link.")
        else:
            print(f"Thread {threading.current_thread().name}: Skipping link (no hash): {link}")


if __name__ == "__main__":
    start_url = "https://papers.nips.cc/paper_files/paper/2023"
    start_time = time.time()

    crawl_and_extract_initial_links(start_url)

    links_file = "./Scrap_Results/links.txt"
    pdf_filename = "./Scrap_Results/pdf_links.txt"
    download_directory = "./Scrap_Results/PDFs"  

    if not os.path.exists(download_directory):
        os.makedirs(download_directory)

    try:
        with open(links_file, "r") as f:
            links = [line.strip() for line in f]
    except FileNotFoundError:
        print(f"Error: Links file '{links_file}' not found. Exiting.")
        exit()

    num_threads = min(2000, len(links)) 
    chunk_size = len(links) // num_threads
    link_chunks = [links[i:i + chunk_size] for i in range(0, len(links), chunk_size)]

    if len(links) % num_threads != 0:
        link_chunks[-1].extend(links[len(link_chunks) * chunk_size:])

    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=process_hash_links, args=(link_chunks[i], pdf_filename, download_directory), name=f"Thread-{i+1}")
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    total_time = end_time - start_time

    print(f"PDF link extraction and downloading complete.")
    print(f"Start time: {time.ctime(start_time)}")
    print(f"End time: {time.ctime(end_time)}")
    print(f"Total execution time: {total_time:.2f} seconds.")