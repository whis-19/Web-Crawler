import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def fetch_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
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

def save_links_to_file(links, filename="./Scrap_Results/links.txt"):  
    directory = os.path.dirname(filename)  
    if not os.path.exists(directory):
        os.makedirs(directory)  

    with open(filename, "w") as file:
        for link in links:
            file.write(link + "\n")

if __name__ == "__main__":
    url = "https://papers.nips.cc/paper_files/paper/2023"
    html_content = fetch_page(url)
    links = extract_links(html_content, url)
    save_links_to_file(links)
    print(f"Extracted {len(links)} links and saved to links.txt")
