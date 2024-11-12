import tempfile
from multiprocessing import Process, Manager, Barrier, set_start_method, Queue
from UniversalWebshopScraper.generalized_scrapper.core.generalized_scrapper import GeneralizedScraper
import time
import os
import traceback


def worker_process(task_queue, status_queue, detected_image_urls, user_data_dir_template):
    """
    Worker process that initializes a persistent GeneralizedScraper instance and processes tasks from the task_queue.
    Communicates status back to the main process via the status_queue.

    Args:
        task_queue (multiprocessing.Queue): Queue from which the worker retrieves scraping tasks.
        status_queue (multiprocessing.Queue): Queue through which the worker sends status updates to the main process.
        detected_image_urls (multiprocessing.Manager.list): Shared list to store detected image URLs and prevent duplicates.
        user_data_dir_template (str): Template path for Chrome user data directories.
        worker_index (int): Unique index identifying the worker, used for consistent file naming.
    """
    worker_id = os.getpid()
    temp_dir = tempfile.mkdtemp(prefix=f"worker_{worker_id}_")
    print(f"[INFO] Worker {worker_id}: Created temporary directory for Chrome instance: {temp_dir}")

    try:
        # Initialize the scraper
        scraper = GeneralizedScraper(shopping_website="", user_data_dir=temp_dir)
        scraper.detected_image_urls = detected_image_urls

        # Signal that the worker is ready
        status_queue.put(('ready', worker_id))

        while True:
            task = task_queue.get()
            if task is None:
                # Sentinel received, terminate the worker
                print(f"[INFO] Worker {worker_id}: Received termination signal. Exiting.")
                break

            site_info, category, product_chunk = task
            try:
                site_name = site_info.get("name", "unknown_site")
                home_url = site_info.get("home_url", "")
                search_url_template = site_info.get("search_url_template", "")

                # Initialize the scraper with the current site's home URL if not already set
                if scraper.shopping_website != home_url:
                    scraper.shopping_website = home_url
                    if not scraper.open_home_page(home_url):
                        raise Exception(f"Failed to open home page for {site_name}")

                print(f"***** Worker {worker_id} processing category '{category}' on '{site_name}' *****")

                for product in product_chunk:
                    try:
                        print(f"Worker {worker_id}: Searching for product: {product}")
                        search_url = search_url_template.format(
                            base_url=home_url,
                            query=product.replace(" ", "+"),
                            page_number="{page_number}"
                        )

                        scraper.open_search_url(search_url.format(page_number=1))
                        scraper.scrape_all_products(scroll_based=False, url_template=search_url,
                                                    page_number_supported=True)
                        print(f"Worker {worker_id}: Scraped product: {product}")

                    except Exception as e:
                        print(f"[ERROR] Worker {worker_id}: Error scraping product '{product}': {e}")
                        traceback.print_exc()

                print(
                    f"Worker {worker_id}: Collected {len(scraper.stored_products)} products for category '{category}'")

                # Define CSV filename format with worker ID, site name, and category.
                csv_filename = f"batch_{worker_id}_{site_name}_{category.replace(' ', '_')}_products.csv"

                # Save the products collected by this worker to CSV.
                scraper.save_to_csv(save_path=csv_filename, category=category)
                print(f"Worker {worker_id}: Saved scraped data to '{csv_filename}'")

                # Signal task completion
                status_queue.put(('done', worker_id))

            except Exception as e:
                print(f"[ERROR] Worker {worker_id}: Failed to process category '{category}': {e}")
                traceback.print_exc()
                # Signal failure
                status_queue.put(('failed', worker_id))
                break  # Exit the worker on failure

    except Exception as e:
        print(f"[ERROR] Worker {worker_id}: Initialization failed: {e}")
        traceback.print_exc()
        # Signal failure
        status_queue.put(('failed', worker_id))

    finally:
        try:
            scraper.close_driver()
            print(f"[INFO] Worker {worker_id}: Closed Chrome driver.")
        except Exception as e:
            print(f"[WARNING] Worker {worker_id}: Error closing driver: {e}")
            traceback.print_exc()


def main_scraper(site_info, categories_amazon_products, n_workers=2):
    """
    Manages the distributed web scraping process by coordinating multiple worker processes.
    Initializes all workers upfront, handles initialization failures, assigns scraping tasks per category,
    and ensures synchronization after each category is processed.

    This function performs the following steps:
        1. Initializes a multiprocessing manager and shared data structures.
        2. Starts the specified number of worker processes.
        3. Monitors the initialization status of each worker.
        4. Assigns product scraping tasks to active workers for each category.
        5. Waits for all workers to complete their tasks for the current category.
        6. Handles worker failures by excluding failed workers from future tasks.
        7. Terminates all worker processes gracefully after all categories are processed.

    Args:
        site_info (dict): Dictionary containing information about the shopping site, including
                          'name', 'home_url', and 'search_url_template'.
        categories_amazon_products (dict): Dictionary where keys are category names and values
                                           are lists of product names to scrape within each category.
        n_workers (int, optional): Number of worker processes to spawn. Defaults to 2.

    Returns:
        None

    Raises:
        None: All exceptions are handled within the worker and main scraper functions.
    """
    print("[INFO] MainScraper: Starting main scraper.")
    manager = Manager()
    detected_image_urls = manager.list()

    task_queue = Queue()
    status_queue = Queue()

    workers = []
    active_workers = set()

    # Initialize all workers
    print(f"[INFO] MainScraper: Initializing {n_workers} workers.")
    for _ in range(n_workers):
        process = Process(
            target=worker_process,
            args=(task_queue, status_queue, detected_image_urls, None)
        )
        workers.append(process)
        process.start()
        # Small delay to stagger worker initialization
        time.sleep(5)

    # Monitor worker statuses
    for _ in range(n_workers):
        try:
            status, worker_id = status_queue.get(timeout=30)  # Wait up to 30 seconds for workers to respond
            if status == 'ready':
                active_workers.add(worker_id)
                print(f"[INFO] MainScraper: Worker {worker_id} is ready.")
            elif status == 'failed':
                print(f"[ERROR] MainScraper: Worker {worker_id} failed to initialize and will be excluded.")
        except:
            print("[ERROR] MainScraper: Timeout waiting for worker status. Exiting.")
            break

    if not active_workers:
        print("[CRITICAL] MainScraper: No workers are active. Exiting scraper.")
        return

    print(f"[INFO] MainScraper: Active workers: {active_workers}")

    # Iterate over each product category to be scraped.
    for category, products in categories_amazon_products.items():
        print(f"\n[INFO] MainScraper: Starting category: {category}")

        # Determine the number of active workers
        current_n_workers = len(active_workers)
        if current_n_workers == 0:
            print("[CRITICAL] MainScraper: No active workers remaining. Exiting scraper.")
            break

        # Divide the products evenly across active workers
        product_chunks = [[] for _ in range(current_n_workers)]
        for idx, product in enumerate(products):
            worker_idx = idx % current_n_workers
            product_chunks[worker_idx].append(product)

        # Assign each worker its chunk of products for the current category
        worker_ids = list(active_workers)
        for i, worker_id in enumerate(worker_ids):
            task = (site_info, category, product_chunks[i])
            task_queue.put(task)
            print(f"[INFO] MainScraper: Assigned {len(product_chunks[i])} products to Worker {worker_id}")

        # Wait for all workers to complete their tasks for this category
        completed_workers = set()
        while len(completed_workers) < current_n_workers:
            try:
                status, worker_id = status_queue.get(timeout=300)  # Wait up to 5 minutes per category
                if status == 'done':
                    print(f"[INFO] MainScraper: Worker {worker_id} completed category '{category}'.")
                    completed_workers.add(worker_id)
                elif status == 'failed':
                    print(f"[ERROR] MainScraper: Worker {worker_id} failed during processing.")
                    active_workers.discard(worker_id)
                    completed_workers.add(worker_id)
            except:
                print("[ERROR] MainScraper: Timeout waiting for workers to complete tasks.")
                break

        print(f"[INFO] MainScraper: Finished category: {category}, moving to the next.")

    # Terminate all workers
    print("[INFO] MainScraper: Terminating all workers.")
    for _ in workers:
        task_queue.put(None)  # Sentinel value to signal workers to terminate

    # Ensure all workers have terminated
    for process in workers:
        process.join()
        print(f"[INFO] MainScraper: Worker PID {process.pid} has terminated.")

    print("***** All searches completed *****")

if __name__ == "__main__":
    set_start_method("spawn", force=True)

    shopping_sites = [
        {
            "name": "ebay",
            "home_url": "https://www.ebay.com",
            "search_url_template": "{base_url}/sch/i.html?_nkw={query}&_pgn={{page_number}}"
        }
    ]

    from UniversalWebshopScraper.generalized_scrapper.core.product_categories import categories_products

    n_workers = 10  # Define the number of workers

    for site_info in shopping_sites:
        main_scraper(site_info, categories_products, n_workers=n_workers)