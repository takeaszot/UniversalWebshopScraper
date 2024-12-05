# UniversalWebshopScraper

**Author**: Jmask  
**Project**: Universal Web Scraping Framework  
**Startup Company**: [PlaceHolder]

## Getting Started

This section provides a step-by-step guide to set up and run the **UniversalWebshopScraper** project.

### Prerequisites

1. **Python 3.8 or higher**: Make sure you have Python installed. You can download it from [python.org](https://www.python.org/downloads/).
2. **Git**: Install Git to clone the repository. Download it from [git-scm.com](https://git-scm.com/downloads).

### Project Setup

For the organization setup process, please check out the [OrgSetup repository](https://github.com/Takeaszot/OrgSetup) for detailed steps and scripts.


## Project Overview

**UniversalWebshopScraper** is a flexible and efficient web scraping framework designed to extract product information from multiple online stores. The project utilizes modularized scripts for both single and multi-threaded scraping, enabling scalable data extraction from various e-commerce platforms. This README provides a comprehensive guide on the project structure, core modules, and usage.

---

## Folder Structure

```bash

Parent Directory/
│
├── Data/                           # External repository for storing all data
│   ├── scrapped_data/              # Folder inside the Data repository for storing scraped data
│   └── (other files)               # other data files 
│
└── UniversalWebshopScraper/
    ├── tests/                     # Folder for unit tests
    │
    ├── UniversalWebshopScraper/   # Main project directory
    │   ├── generalized_scraper/   # Generalized scraper module
    │   │   ├── AI_searcher/       # AI-based keyword expansion module
    │   │   │
    │   │   ├── checker/           # Module for validation and checking
    │   │   │
    │   │   ├── core/              # Core utilities and modules
    │   │   │   └── generalized_scraper.py # Main generalized scraper class and methods
    │   │   │
    │   │   ├── scraped_logs/      # Folder for storing scraping logs
    │   │   │
    │   │   └── scripts/           # Scripts for various scraping workflows
    │   │
    │   └── specific_scrapers/     # Specific scrapers for individual websites
    │
    └── README.md                  # Documentation for the project setup, structure, and usage

```

### Data Storage

The scraped data for this project is stored in a separate repository, not within the `UniversalWebshopScraper` directory.

#### Location of Data Repository

The data is stored in the following repository:  
[Data Repository](https://github.com/takeaszot/Data)

