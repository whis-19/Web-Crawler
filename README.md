# Web Crawler

## Overview
This repository contains a Python-based web crawler designed to scrape metadata and download research papers from the NeurIPS conference website. The crawler collects paper titles, authors, abstracts, and PDF links and stores the data in CSV files. Additionally, it supports parallel downloading of PDFs using multithreading.

## Features
- **Scrape Research Papers**: Extracts metadata (title, authors, abstracts, and PDF links) for research papers from NeurIPS.
- **CSV Storage**: Saves scraped metadata into structured CSV files.
- **Multithreaded PDF Downloading**: Downloads PDFs concurrently for efficiency.
- **Configurable Parameters**: Allows customization of years, number of papers per year, and output directories.

## Installation
### Prerequisites
Ensure you have the following installed:
- Python 3.x
- Required Python libraries (install via `requirements.txt`)

### Setup
1. Clone the repository:
   ```sh
   git clone https://github.com/whis-19/Web-Crawler.git
   cd Web-Crawler
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage
### Running the Web Crawler
To scrape paper metadata and download PDFs, run:
```sh
python main.py
```

### Configuration
Modify the configuration variables in `main.py` to customize behavior:
- `START_YEAR` and `END_YEAR`: Define the range of years to scrape.
- `MAX_PAPERS_PER_YEAR`: Limit the number of papers per year.
- `OUTPUT_DIR`: Directory for storing CSV metadata.
- `RESULTS_DIR`: Directory for storing downloaded PDFs.

## Code Structure
- `main.py`: The entry point for running the web crawler.
- `scraper.py`: Contains functions for scraping metadata.
- `downloader.py`: Handles PDF downloads using multithreading.
- `utils.py`: Helper functions for URL fetching and file management.


## Contributing
Contributions are welcome! Feel free to open an issue or submit a pull request.

## Author
[whis-19](https://github.com/whis-19)

