import os
import pandas as pd
from tqdm import tqdm

from UniversalWebshopScraper.generalized_scrapper.core.generalized_scrapper import GeneralizedScraper

if __name__ == "__main__":
    # Categories and products to search for
    from UniversalWebshopScraper.generalized_scrapper.core.product_categories import categories_products

    home_url_amazon = "https://www.amazon.com"
    home_url_ebay = "https://www.ebay.com"

    # Define the list of shopping websites and their search URL templates
    shopping_sites = [
        {
            "name": "allegro",
            "home_url": "https://www.allegro.pl",
            "search_url_template": '{base_url}/listing?string={query}&p={{page_number}}'
        },
        '''{
            "name": "aliexpress",
            "home_url": "https://www.aliexpress.com",
            "search_url_template": '{base_url}/w/wholesale-{query}.html?page={{page_number}}'
        },
        

        {
            "name": "ebay",
            "home_url": home_url_ebay,
            "search_url_template": "{base_url}/sch/i.html?_nkw={query}&_pgn={{page_number}}"
        },
        {
            "name": "Amazon",
            "home_url": home_url_amazon,
            "search_url_template": "{base_url}/s?k={query}&page={page_number}"
        }'''
    ]

    save_path = "../scraped_data"
    os.makedirs(save_path, exist_ok=True)

    for site_info in shopping_sites:
        site_name = site_info["name"].lower()
        scraper = GeneralizedScraper(shopping_website=site_info["home_url"])
        scraper.open_home_page(site_info["home_url"])
        home_url = site_info["home_url"]
        print(f"***** Starting search on {site_name} *****")

        # Directory for the specific site
        site_save_path = os.path.join(save_path, site_name)
        os.makedirs(site_save_path, exist_ok=True)

        # Loop through each category and product
        for category, products in categories_products.items():
            print(f"--- Searching category: {category} ---")

            # Create a folder for the category
            category_safe_name = category.replace(" & ", "_").replace(" ", "_")
            category_save_path = os.path.join(site_save_path, category_safe_name)
            os.makedirs(category_save_path, exist_ok=True)

            for product in products:
                print(f"Searching for product: {product}")
                search_url = site_info["search_url_template"].format(
                    base_url=home_url, query=product.replace(" ", "+"), page_number="{page_number}")

                scraper.open_search_url(search_url.format(page_number=1))
                scraped_products = scraper.scrape_all_products(scroll_based=True, url_template=search_url,
                                                               page_number_supported=True)

                # Save each product immediately after it is scraped
                for product_data in scraped_products:
                    product_file = os.path.join(category_save_path, f"{product.replace(' ', '_')}.csv")

                    # Save to a CSV file
                    df = pd.DataFrame([product_data])

                    # Append to the CSV file or create it if it doesn't exist
                    if not os.path.exists(product_file):
                        df.to_csv(product_file, index=False)
                    else:
                        df.to_csv(product_file, mode='a', header=False, index=False)

            print(f"Finished searching for category: {category}")

        scraper.close_driver()
        print('*' * 69)

    print("***** All searches completed *****")