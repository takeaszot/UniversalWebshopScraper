import cProfile
import pstats
import os

from UniversalWebshopScraper.generalized_scrapper.generalized_scrapper import GeneralizedScraper

def main():
    # Categories and products to search for
    categories_amazon_products = {
        "Electronics": [
            "Wireless Bluetooth Earbuds", "4K UHD Smart TV", "Noise-Cancelling Headphones"
        ],
        "Home & Kitchen": [
            "Memory Foam Mattress", "Air Fryer", "Electric Pressure Cooker"
        ]
    }

    home_url_amazon = "https://www.amazon.com"

    # Define the list of shopping websites and their search URL templates
    shopping_sites = [
        {
            "name": "Amazon",
            "home_url": home_url_amazon,
            "search_url_template": "{base_url}/s?k={query}&page={page_number}"
        }
    ]

    save_path = "./scraped_data"
    os.makedirs(save_path, exist_ok=True)

    for site_info in shopping_sites:
        site_name = site_info["name"].lower()
        scraper = GeneralizedScraper(shopping_website=site_info["home_url"])
        scraper.open_home_page(site_info["home_url"])
        print(f"***** Starting search on {site_name} *****")

        # Directory for the specific site
        site_save_path = os.path.join(save_path, site_name)
        os.makedirs(site_save_path, exist_ok=True)

        # Loop through each category and product
        for category, products in categories_amazon_products.items():
            print(f"--- Searching category: {category} ---")
            category_start_count = scraper.product_count

            # Directory for the specific category
            category_save_path = os.path.join(site_save_path, category.replace(" & ", "_").replace(" ", "_"))
            os.makedirs(category_save_path, exist_ok=True)

            for product in products:
                product_start_count = scraper.product_count
                print(f"Searching for product: {product}")
                search_url = site_info["search_url_template"].format(
                    base_url=home_url_amazon, query=product.replace(" ", "+"), page_number="{page_number}")

                scraper.open_search_url(search_url.format(page_number=1))
                scraper.scrape_all_products(scroll_based=True, url_template=search_url, page_number_supported=True)

            # Calculate the number of products scraped for this category
            category_product_count = scraper.product_count - category_start_count
            print(f"Found {category_product_count} new products in the category: {category}")

            # Save collected products to a CSV for this category
            csv_filename = os.path.join(category_save_path, f"{site_name}_{category}_scraped_products.csv")
            #scraper.save_to_csv(csv_filename)

        scraper.close_driver()
        print('*' * 69)

    print("***** All searches completed *****")

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    main()

    profiler.disable()

    # Save profiler results in a format suitable for Snakeviz
    profiler.dump_stats("profile_results.prof")
