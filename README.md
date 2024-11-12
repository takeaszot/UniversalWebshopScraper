# UniversalWebshopScraper

**Author**: Jmask  
**Project**: Universal Web Scraping Framework  
**Startup Company**: [Startup Company Name]


## Project Overview

**UniversalWebshopScraper** is a flexible and efficient web scraping framework designed to extract product information from multiple online stores. The project utilizes modularized scripts for both single and multi-threaded scraping, enabling scalable data extraction from various e-commerce platforms. This README provides a comprehensive guide on the project structure, core modules, and usage.

---

## Folder Structure

```bash
UniversalWebshopScraper
│
├── .venv/                           # Virtual environment folder
├── scraped_data/                    # Folder to store scraped CSV files organized by category/website
├── tests/                           # Folder for unit tests (TBD)
│
├── UniversalWebshopScraper
│   ├── generalized_scraper           # Main scraping module
│   │
│   ├── AI_searcher/
│   │   └── AI_searcher.py             # Placeholder for future AI-based keyword expansion
│   │
│   ├── core/
│   │   ├── functions.py               # Utility functions for URL normalization and other helpers
│   │   ├── generalized_scraper.py     # Main generalized scraper class and methods
│   │   ├── product_categories.py      # Contains product categories and keywords for searching
│   │   └── trash_filtering.py         # Placeholder for filtering irrelevant content from results
│   │
│   ├── scripts/
│   │   ├── mock_db_generalized_scrapper.py         # Single-threaded scraper for one shop
│   │   ├── mock_db_generalized_scrapper_multiple_shops.py  # Multi-shop, one thread per shop scraper
│   │   └── turbo_generalized_scrapper_1_shop.py    # Multi-threaded, single shop high-speed scraper
│   │
│   └── scraped_data/                # Output directory for storing scraped data organized by website
│
├── specific_scrapers/               # Folder for any specific scrapers not covered by the generalized scraper
├── .gitignore                       # Git ignore file to exclude unnecessary files
├── README.md                        # Documentation for the project setup, structure, and usage
└── requirements.txt                 # Required Python packages for the project
