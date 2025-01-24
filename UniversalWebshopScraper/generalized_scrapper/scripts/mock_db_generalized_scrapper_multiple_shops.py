import os
import tempfile
import pandas as pd
from multiprocessing import Process, set_start_method
from UniversalWebshopScraper.generalized_scrapper.core.generalized_scrapper import GeneralizedScraper
import undetected_chromedriver as uc

# Pre-fetch undetected_chromedriver's executable to avoid parallel downloads
_ = uc.Chrome()
_.quit()

def run_scraper(site_info, categories_amazon_products):
    # Create a unique temporary directory for each Chrome instance
    temp_dir = tempfile.mkdtemp()
    print(f"[INFO] Created temporary directory for Chrome instance: {temp_dir}")

    # Initialize the scraper
    scraper = GeneralizedScraper(shopping_website=site_info["home_url"], user_data_dir=temp_dir)
    if not scraper.open_home_page(site_info["home_url"]):
        print(f"[ERROR] Failed to open home page for {site_info['name']}")
        return

    print(f"***** Starting search on {site_info['name']} *****")

    site_save_path = os.path.join('../scraped_data', site_info["name"].lower())
    os.makedirs(site_save_path, exist_ok=True)

    for category, products in categories_amazon_products.items():
        print(f"--- Searching category: {category} ---")
        for product in products:
            print(f"Searching for product: {product}")
            search_url = site_info["search_url_template"].format(
                base_url=site_info["home_url"], query=product.replace(" ", "+"), page_number="{page_number}"
            )

            scraper.open_search_url(search_url.format(page_number=1))
            scraper.scrape_all_products(scroll_based=True, url_template=search_url, page_number_supported=True)

        # Save scraped products to a CSV
        category_save_path = os.path.join(site_save_path, f"{category.replace(' ', '_')}.csv")
        df = pd.DataFrame(scraper.stored_products)
        df.to_csv(category_save_path, index=False)
        scraper.stored_products = []

    scraper.close_driver()
    print(f"***** Finished scraping for {site_info['name']} *****")

if __name__ == "__main__":
    set_start_method("spawn", force=True)

    shopping_sites = [
        {"name": "aliexpress", "home_url": "https://www.aliexpress.com", "search_url_template": '{base_url}/w/wholesale-{query}.html?page={{page_number}}'},
        {"name": "temu", "home_url": "https://www.temu.com", "search_url_template": "{base_url}/search_result.html?search_key={query}&search_method=user"},
        {"name": "ebay", "home_url": "https://www.ebay.com", "search_url_template": "{base_url}/sch/i.html?_nkw={query}&_pgn={{page_number}}"},
        {"name": "amazon", "home_url": "https://www.amazon.com", "search_url_template": "{base_url}/s?k={query}&page={page_number}"}
    ]
    from UniversalWebshopScraper.generalized_scrapper.core.product_categories import categories_products


    processes = []
    for site_info in shopping_sites:
        process = Process(target=run_scraper, args=(site_info, categories_products))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()

    print("***** All searches completed *****")
