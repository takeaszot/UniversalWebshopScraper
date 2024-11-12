import tempfile
from multiprocessing import Process, Manager, Barrier, set_start_method
from UniversalWebshopScraper.generalized_scrapper.core.generalized_scrapper import GeneralizedScraper
import time


def run_scraper(site_info, category, products, detected_image_urls, user_data_dir, worker_id, n_workers, barrier):
    """
    Initializes and runs a scraper instance for a specific category on a specified website,
    distributing the scraping tasks across multiple workers. Each worker processes a chunk of
    products and saves the results to a CSV file, utilizing a shared list to avoid duplicate
    image URLs and a barrier to ensure all workers finish before the next steps.

    Args:
        site_info (dict): Contains details of the shopping site, including home and search URLs.
        category (str): The name of the category to scrape (e.g., "Electronics").
        products (list): A list of product names in the category to search for.
        detected_image_urls (list): A shared list across processes to store detected image URLs
                                    to prevent duplicates.
        user_data_dir (str): Directory path for the Chrome user data to manage separate sessions.
        worker_id (int): The unique ID of the worker process, used for chunking the product list
                         and file naming.
        n_workers (int): Total number of worker processes handling this task.
        barrier (Barrier): A threading barrier to synchronize worker processes upon task completion.

    Returns:
        None: The function completes and returns nothing, saving scraped data to a CSV file.

    Raises:
        Exception: Any issues with web navigation or scraping are handled and outputted to the console.
    """
    try:
        # Initialize the scraper for the specified site and set the shared image URLs list.
        scraper = GeneralizedScraper(shopping_website=site_info["home_url"], user_data_dir=user_data_dir)
        scraper.detected_image_urls = detected_image_urls

        # Verify homepage access and exit if unsuccessful.
        if not scraper.open_home_page(site_info["home_url"]):
            print(f"[ERROR] Worker {worker_id}: Failed to open home page for {site_info['name']}")
            return

        print(f"***** Worker {worker_id} started for category {category} on {site_info['name']} *****")

        # Divide the products evenly across workers; each worker processes a specific chunk.
        product_chunk = products[worker_id::n_workers]

        # Loop through each product in the worker’s assigned chunk.
        for product in product_chunk:
            print(f"Worker {worker_id} searching for product: {product}")
            # Construct search URL by replacing placeholders with the product name.
            search_url = site_info["search_url_template"].format(
                base_url=site_info["home_url"], query=product.replace(" ", "+"), page_number="{page_number}"
            )

            # Open the search URL (starting from page 1) and scrape all relevant product data.
            scraper.open_search_url(search_url.format(page_number=1))
            scraper.scrape_all_products(scroll_based=False, url_template=search_url, page_number_supported=True)

        print(f"Worker {worker_id} collected {len(scraper.stored_products)} products for category {category}")

        # Define CSV filename format with worker ID, site name, and category.
        csv_filename = f"batch_{worker_id}_{site_info['name']}_{category.replace(' ', '_')}_products.csv"

        # Save the products collected by this worker to CSV.
        scraper.save_to_csv(save_path=csv_filename, category=category)

    finally:
        # Ensure driver closes, and synchronization is met for all workers at the barrier.
        scraper.close_driver()
        barrier.wait()  # Wait for all workers before proceeding.


def main_scraper(site_info, categories_amazon_products, n_workers=2):
    """
    Main function to manage the distributed scraping process across multiple workers.
    Iterates over each product category, assigns workers to each category, and ensures
    that each worker process is synchronized using a barrier. All products in each category
    are evenly distributed across the specified number of workers.

    Args:
        site_info (dict): Dictionary containing information about the shopping site, including
                          the home URL and search URL template.
        categories_amazon_products (dict): Dictionary where keys are category names and values
                                           are lists of product names to search within each category.
        n_workers (int, optional): Number of worker processes to spawn per category. Defaults to 2.

    Returns:
        None: The function completes all categories in sequence, coordinating the worker processes
              and printing completion messages for each category.

    Raises:
        Exception: Any process-related errors are printed to the console.
    """
    # Use a shared list for image URLs across workers to prevent duplicate detections.
    manager = Manager()
    detected_image_urls = manager.list()

    # Iterate over each product category to be scraped.
    for category, products in categories_amazon_products.items():
        print(f"Starting category: {category}")

        # Create a barrier to synchronize all workers for this category.
        barrier = Barrier(n_workers)
        processes = []

        # Spawn worker processes to handle scraping for the current category.
        for i in range(n_workers):
            # Create a temporary directory to separate Chrome user data for each worker.
            temp_dir = tempfile.mkdtemp()
            print(f"[INFO] Created temporary directory for Chrome instance: {temp_dir}")

            # Initialize and start the worker process.
            process = Process(
                target=run_scraper,
                args=(site_info, category, products, detected_image_urls, temp_dir, i, n_workers, barrier)
            )
            processes.append(process)
            process.start()

            # Stagger process starts slightly to avoid simultaneous browser launch issues.
            time.sleep(4)

        # Wait for all processes to finish scraping the current category.
        for process in processes:
            process.join()

        print(f"Finished category: {category}, moving to the next.")


if __name__ == "__main__":
    set_start_method("spawn", force=True)

    shopping_sites = [
        {"name": "ebay", "home_url": "https://www.ebay.com",
         "search_url_template": "{base_url}/sch/i.html?_nkw={query}&_pgn={{page_number}}"}
    ]

    from UniversalWebshopScraper.generalized_scrapper.core.product_categories import categories_products

    # Define the list of categories you want to use
    selected_categories = [
    #    "Electronics",
    #    "Home & Kitchen",
        "Sports & Outdoors",
        "Toys & Games",
        "Health & Personal Care",
        "Automotive",
        "Beauty",
        "Garden & Outdoors",
        "Tools & Home Improvement",
        "Baby Products",
        "Pet Supplies",
        "Jewelry",
        "Appliances",
        "Furniture",
        "Musical Instruments",
        "Polish Random Products"
    ]

    # Filter categories_products based on selection
    selected_products = {cat: products for cat, products in categories_products.items() if cat in selected_categories}

    n_workers = 10  # Define the number of workers

    for site_info in shopping_sites:
        main_scraper(site_info, categories_products, n_workers=n_workers)

    print("***** All searches completed *****")
