import tempfile
from multiprocessing import Process, Manager, set_start_method, Queue
from UniversalWebshopScraper.generalized_scrapper.core.generalized_scrapper import GeneralizedScraper
import time
import traceback

def worker_process(task_queue, status_queue, detected_image_urls, worker_index):
    """
    Worker process that initializes a persistent GeneralizedScraper instance and processes tasks from the task_queue.
    Communicates status back to the main process via the status_queue.

    Args:
        task_queue (multiprocessing.Queue): Queue from which the worker retrieves scraping tasks.
        status_queue (multiprocessing.Queue): Queue through which the worker sends status updates to the main process.
        detected_image_urls (multiprocessing.Manager.list): Shared list to store detected image URLs and prevent duplicates.
        worker_index (int): Unique index identifying the worker, used for consistent file naming.
    """
    print(f"[INFO] Worker-{worker_index}: Starting and creating temporary directory.")
    temp_dir = tempfile.mkdtemp(prefix=f"worker_{worker_index}_")
    print(f"[INFO] Worker-{worker_index}: Created temporary directory for Chrome instance: {temp_dir}")

    scraper = None  # Initialize scraper to None to handle failures gracefully

    try:
        # Attempt to initialize the scraper
        print(f"[INFO] Worker-{worker_index}: Initializing GeneralizedScraper.")
        scraper = GeneralizedScraper(shopping_website="", user_data_dir=temp_dir)
        scraper.detected_image_urls = detected_image_urls

        # Signal readiness to the main process
        status_queue.put(('ready', worker_index))
        print(f"[INFO] Worker-{worker_index}: Ready to receive tasks.")

        while True:
            task = task_queue.get()
            if task is None:
                # Sentinel received, terminate the worker
                print(f"[INFO] Worker-{worker_index}: Received termination signal. Exiting.")
                break

            site_info, category, product_chunk = task
            try:
                site_name = site_info.get("name", "unknown_site")
                home_url = site_info.get("home_url", "")
                search_url_template = site_info.get("search_url_template", "")

                # If the scraper is set to a different site, reinitialize it
                if scraper.shopping_website != home_url:
                    scraper.shopping_website = home_url
                    if not scraper.open_home_page(home_url):
                        raise Exception(f"Failed to open home page for {site_name}")

                print(f"***** Worker-{worker_index} processing category '{category}' on '{site_name}' *****")

                for product in product_chunk:
                    try:
                        print(f"Worker-{worker_index}: Searching for product: {product}")
                        search_url = search_url_template.format(
                            base_url=home_url,
                            query=product.replace(" ", "+"),
                            page_number="{page_number}"
                        )

                        # Open the search URL and scrape all relevant product data
                        scraper.open_search_url(search_url.format(page_number=1))
                        scraper.scrape_all_products(scroll_based=False, url_template=search_url,
                                                    page_number_supported=True)
                        print(f"Worker-{worker_index}: Scraped product: {product}")

                    except Exception as e:
                        print(f"[ERROR] Worker-{worker_index}: Error scraping product '{product}': {e}")
                        traceback.print_exc()

                print(
                    f"Worker-{worker_index}: Collected {len(scraper.stored_products)} products for category '{category}'")

                # Define CSV filename format with worker ID, site name, and category.
                csv_filename = f"batch_{worker_index}_{site_info['name']}_{category.replace(' ', '_')}_products.csv"

                # Save the products collected by this worker to CSV.
                scraper.save_to_csv(save_path=csv_filename, category=category)

                # Clear stored data to prepare for the next category
                scraper.stored_products.clear()

                # Signal task completion to the main process
                status_queue.put(('done', worker_index))

            except Exception as e:
                print(f"[ERROR] Worker-{worker_index}: Failed to process category '{category}': {e}")
                traceback.print_exc()
                # Signal failure to the main process
                status_queue.put(('failed', worker_index))
                break  # Exit the worker on failure

    except Exception as e:
        print(f"[ERROR] Worker-{worker_index}: Initialization failed: {e}")
        traceback.print_exc()
        # Signal failure to the main process
        status_queue.put(('failed', worker_index))

    finally:
        try:
            if scraper:
                scraper.close_driver()
                print(f"[INFO] Worker-{worker_index}: Closed Chrome driver.")
        except Exception as e:
            print(f"[WARNING] Worker-{worker_index}: Error closing driver: {e}")
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

    # Initialize task and status queues for inter-process communication
    task_queue = Queue()
    status_queue = Queue()

    workers = []
    active_workers = set()

    # Step 1: Initialize all worker processes
    print(f"[INFO] MainScraper: Initializing {n_workers} workers.")
    for i in range(n_workers):
        process = Process(
            target=worker_process,
            args=(task_queue, status_queue, detected_image_urls, i)
        )
        workers.append(process)
        process.start()
        print(f"[INFO] MainScraper: Started Worker-{i} with PID {process.pid}")
        # Small delay to stagger worker initialization and prevent resource contention
        time.sleep(5)

    # Step 2: Monitor and collect the readiness status of each worker
    for i in range(n_workers):
        try:
            status, worker_index = status_queue.get(timeout=30)  # Wait up to 30 seconds for workers to respond
            if status == 'ready':
                active_workers.add(worker_index)
                print(f"[INFO] MainScraper: Worker-{worker_index} is ready.")
            elif status == 'failed':
                print(f"[ERROR] MainScraper: Worker-{worker_index} failed to initialize and will be excluded.")
        except:
            print("[ERROR] MainScraper: Timeout waiting for worker status. Exiting.")
            break

    if not active_workers:
        print("[CRITICAL] MainScraper: No workers are active. Exiting scraper.")
        return

    print(f"[INFO] MainScraper: Active workers: {sorted(active_workers)}")

    # Step 3: Iterate over each product category to be scraped
    for category, products in categories_amazon_products.items():
        print(f"\n[INFO] MainScraper: Starting category: {category}")

        # Update the number of active workers
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
        worker_indices = sorted(active_workers)  # Sorting for consistent assignment
        for i, worker_index in enumerate(worker_indices):
            task = (site_info, category, product_chunks[i])
            task_queue.put(task)
            print(f"[INFO] MainScraper: Assigned {len(product_chunks[i])} products to Worker-{worker_index}")

        # Step 4: Wait for all workers to complete their tasks for the current category
        completed_workers = set()
        while len(completed_workers) < current_n_workers:
            try:
                status, worker_index = status_queue.get()  # Remove the timeout parameter
                if status == 'done':
                    print(f"[INFO] MainScraper: Worker-{worker_index} completed category '{category}'.")
                    completed_workers.add(worker_index)
                elif status == 'failed':
                    print(f"[ERROR] MainScraper: Worker-{worker_index} failed during processing.")
                    active_workers.discard(worker_index)
                    completed_workers.add(worker_index)
            except Exception as e:
                print(f"[ERROR] MainScraper: Unexpected error: {e}")
                break

        print(f"[INFO] MainScraper: Finished category: {category}, moving to the next.")

    # Step 5: Terminate all worker processes gracefully
    print("[INFO] MainScraper: Terminating all workers.")
    for _ in workers:
        task_queue.put(None)  # Sentinel value to signal workers to terminate

    # Ensure all worker processes have terminated
    for process in workers:
        process.join()
        print(f"[INFO] MainScraper: Worker PID {process.pid} has terminated.")

    print("***** All searches completed *****")


if __name__ == "__main__":
    # Ensure that the multiprocessing start method is set to 'spawn' for compatibility
    set_start_method("spawn", force=True)

    shopping_sites = [
        {"name": "aliexpress",
         "home_url": "https://www.aliexpress.com",
         "search_url_template": '{base_url}/w/wholesale-{query}.html?page={{page_number}}'},
    ]

    from UniversalWebshopScraper.generalized_scrapper.core.product_categories import categories_products

    n_workers = 4  # Define the number of workers

    for site_info in shopping_sites:
        main_scraper(site_info, categories_products, n_workers=n_workers)

    print("***** All searches completed *****")