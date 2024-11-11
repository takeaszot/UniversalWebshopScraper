import os
import tempfile
import pandas as pd
from multiprocessing import Process
from UniversalWebshopScraper.generalized_scrapper.generalized_scrapper import GeneralizedScraper

def run_scraper(site_info, categories_amazon_products):
    # Create a unique temporary directory for each Chrome instance
    temp_dir = tempfile.mkdtemp()

    # Initialize the scraper
    scraper = GeneralizedScraper(shopping_website=site_info["home_url"], user_data_dir=temp_dir)
    scraper.open_home_page(site_info["home_url"])

    home_url = site_info["home_url"]
    print(f"***** Starting search on {site_info['name']} *****")

    site_save_path = os.path.join('./scraped_data', site_info["name"].lower())
    os.makedirs(site_save_path, exist_ok=True)

    for category, products in categories_amazon_products.items():
        print(f"--- Searching category: {category} ---")
        for product in products:
            print(f"Searching for product: {product}")
            search_url = site_info["search_url_template"].format(
                base_url=home_url, query=product.replace(" ", "+"), page_number="{page_number}"
            )

            scraper.open_search_url(search_url.format(page_number=1))
            scraper.scrape_all_products(scroll_based=True, url_template=search_url, page_number_supported=False)

        # Save scraped products to a CSV
        category_save_path = os.path.join(site_save_path, f"{category.replace(' ', '_')}.csv")
        df = pd.DataFrame(scraper.stored_products)
        df.to_csv(category_save_path, index=False)
        scraper.stored_products = []

    scraper.close_driver()
    print(f"***** Finished scraping for {site_info['name']} *****")

if __name__ == "__main__":
    shopping_sites = [
        {"name": "temu", "home_url": "https://www.temu.com", "search_url_template": "{base_url}/search_result.html?search_key={query}&search_method=user"},
        {"name": "ebay", "home_url": "https://www.ebay.com", "search_url_template": "{base_url}/sch/i.html?_nkw={query}&_pgn={{page_number}}"},
        {"name": "amazon", "home_url": "https://www.amazon.com", "search_url_template": "{base_url}/s?k={query}&page={page_number}"}
    ]

    categories_amazon_products = {
        "electronics": ["tv", "smartphone", "laptop"],
        "home_appliances": ["vacuum cleaner", "microwave", "blender"]
    }

    # Create a process for each scraper
    processes = []
    for site_info in shopping_sites:
        process = Process(target=run_scraper, args=(site_info, categories_amazon_products))
        processes.append(process)
        process.start()

    # Wait for all processes to complete
    for process in processes:
        process.join()

    print("***** All searches completed *****")
