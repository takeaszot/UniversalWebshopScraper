import tempfile
from multiprocessing import Process, Manager, set_start_method, Queue
from UniversalWebshopScraper.generalized_scrapper.core.generalized_scrapper import GeneralizedScraper
import time
import traceback
import sys
import logging
import os
from contextlib import contextmanager
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Define colors for workers
WORKER_COLORS = [Fore.RED, Fore.GREEN, Fore.BLUE, Fore.YELLOW, Fore.CYAN, Fore.MAGENTA]


class WorkerStreamLogger:
    """
    Custom stream logger to redirect prints and prepend [WORKER x] with color.
    """
    def __init__(self, worker_index, log_func):
        self.worker_index = worker_index
        self.log_func = log_func
        self.color = WORKER_COLORS[worker_index % len(WORKER_COLORS)]  # Assign a unique color

    def write(self, message):
        if message.strip():  # Avoid logging empty lines
            # Colorize only the prefix `[WORKER x]`
            colored_prefix = f"{self.color}[WORKER {self.worker_index}]{Style.RESET_ALL}"
            # Append the rest of the message in default (white) color
            formatted_message = f"{colored_prefix} {message.strip()}"
            self.log_func(formatted_message)

    def flush(self):
        pass  # No need to implement flush for our logging use case


def setup_logging(worker_index, shop_name):
    """
    Set up a logger that logs to both a file and the console.
    Logs are stored in a subfolder for each shop inside the 'scraped_logs' folder in the project root.
    """
    # Ensure logs are written to the root `scraped_logs` folder, not relative to the script
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Navigate to project root
    logs_base_dir = os.path.join(project_root, "scraped_logs", shop_name)
    os.makedirs(logs_base_dir, exist_ok=True)  # Ensure the directory exists

    log_file = os.path.join(logs_base_dir, f"worker_{worker_index}.log")

    # Create logger
    logger = logging.getLogger(f"Worker-{worker_index}-{shop_name}")
    logger.setLevel(logging.INFO)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter("%(message)s")
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

@contextmanager
def redirect_stdout_stderr(worker_index, log_func):
    """
    Context manager to redirect stdout and stderr to the custom WorkerStreamLogger.
    """
    worker_logger = WorkerStreamLogger(worker_index, log_func)
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = worker_logger
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr


def worker_process(task_queue, status_queue, detected_image_urls, worker_index, captcha_event, site_info):
    """
    Worker process that pauses on CAPTCHA and resumes when CAPTCHA is resolved.
    """
    shop_name = site_info.get("name", "unknown_shop")

    logger = setup_logging(worker_index, shop_name)

    def log_message(message):
        logger.info(message)

    with redirect_stdout_stderr(worker_index, log_message):
        print(f"Starting Worker-{worker_index} for shop '{shop_name}' and creating temporary directory.")
        temp_dir = tempfile.mkdtemp(prefix=f"worker_{worker_index}_")
        print(f"Created temporary directory for Chrome instance: {temp_dir}")

        scraper = None

        try:
            print(f"Initializing GeneralizedScraper.")
            scraper = GeneralizedScraper(shopping_website="", user_data_dir=temp_dir)
            scraper.detected_image_urls = detected_image_urls

            status_queue.put(('ready', worker_index))
            print(f"Worker-{worker_index}: Ready to receive tasks.")

            while True:
                task = task_queue.get()
                if task is None:
                    print(f"Worker-{worker_index}: Received termination signal. Exiting.")
                    break

                site_info, category, product_chunk = task
                try:
                    site_name = site_info.get("name", "unknown_site")
                    home_url = site_info.get("home_url", "")
                    search_url_template = site_info.get("search_url_template", "")

                    if scraper.shopping_website != home_url:
                        scraper.shopping_website = home_url
                        if not scraper.open_home_page(home_url):
                            raise Exception(f"Failed to open home page for {site_name}")

                    print(f"***** Worker-{worker_index} processing category '{category}' on '{site_name}' *****")

                    for product in product_chunk:
                        try:
                            print(f"Searching for product: {product}")
                            search_url = search_url_template.format(
                                base_url=home_url,
                                query=product.replace(" ", "+"),
                                page_number="{page_number}"
                            )

                            scraper.open_search_url(search_url.format(page_number=1))
                            soup = scraper.extract_page_structure()

                            if scraper.is_captcha_present(soup):
                                print(f"[CAPTCHA] CAPTCHA detected!")
                                status_queue.put(('captcha', worker_index))

                                print(f"[CAPTCHA] Worker-{worker_index} is waiting for CAPTCHA resolution.")
                                captcha_event.wait()
                                captcha_event.clear()

                                print(f"CAPTCHA resolved. Resuming task...")
                                continue

                            scraper.scrape_all_products(scroll_based=True, url_template=search_url, page_number_supported=True)
                            scraper.save_to_csv(save_path=f"{product}.csv", category=category)
                            scraper.stored_products.clear()

                        except Exception as e:
                            print(f"Error scraping product '{product}': {e}")
                            traceback.print_exc()

                    status_queue.put(('done', worker_index))

                except Exception as e:
                    print(f"Failed to process category '{category}': {e}")
                    traceback.print_exc()
                    status_queue.put(('failed', worker_index))
                    break

        finally:
            try:
                if scraper:
                    scraper.close_driver()
                    print(f"Closed Chrome driver.")
            except Exception as e:
                print(f"Error closing driver: {e}")
                traceback.print_exc()


def main_scraper(site_info, categories_amazon_products, n_workers=2):
    """
    Manages worker processes and handles CAPTCHA resolution.
    """
    print("[INFO] MainScraper: Starting main scraper.")
    manager = Manager()
    detected_image_urls = manager.list()

    task_queue = Queue()
    status_queue = Queue()
    captcha_events = {i: manager.Event() for i in range(n_workers)}

    workers = []
    active_workers = set()

    print(f"[INFO] MainScraper: Initializing {n_workers} workers.")
    for i in range(n_workers):
        process = Process(
            target=worker_process,
            args=(task_queue, status_queue, detected_image_urls, i, captcha_events[i], site_info)
        )
        workers.append(process)
        process.start()
        time.sleep(2)

    for i in range(n_workers):
        try:
            status, worker_index = status_queue.get(timeout=30)
            if status == 'ready':
                active_workers.add(worker_index)
                print(f"[INFO] MainScraper: Worker-{worker_index} is ready.")
        except:
            print("[ERROR] MainScraper: Timeout waiting for worker status. Exiting.")
            break

    if not active_workers:
        print("[CRITICAL] MainScraper: No workers are active. Exiting scraper.")
        return

    print(f"[INFO] MainScraper: Active workers: {sorted(active_workers)}")

    for category, products in categories_amazon_products.items():
        print(f"\n[INFO] MainScraper: Starting category: {category}")
        product_chunks = [[] for _ in active_workers]

        for idx, product in enumerate(products):
            worker_idx = idx % len(active_workers)
            product_chunks[worker_idx].append(product)

        for i, worker_index in enumerate(sorted(active_workers)):
            task = (site_info, category, product_chunks[i])
            task_queue.put(task)
            print(f"[INFO] MainScraper: Assigned {len(product_chunks[i])} products to Worker-{worker_index}")

        completed_workers = set()
        while len(completed_workers) < len(active_workers):
            status, worker_index = status_queue.get()

            if status == 'done':
                print(f"[INFO] MainScraper: Worker-{worker_index} completed its task.")
                completed_workers.add(worker_index)
            elif status == 'captcha':
                print(f"[CAPTCHA] MainScraper: Worker-{worker_index} requires CAPTCHA resolution.")
                print(f"Resolve CAPTCHA for Worker-{worker_index} and press Enter to continue.")
                input("Press Enter to continue...")
                captcha_events[worker_index].set()
            elif status == 'failed':
                print(f"[ERROR] MainScraper: Worker-{worker_index} failed.")
                active_workers.discard(worker_index)
                completed_workers.add(worker_index)

        print(f"[INFO] MainScraper: Finished category: {category}")

    print("[INFO] MainScraper: Terminating all workers.")
    for _ in workers:
        task_queue.put(None)

    for process in workers:
        process.join()
        print(f"[INFO] MainScraper: Worker PID {process.pid} has terminated.")

    print("***** All searches completed *****")


if __name__ == "__main__":
    # Set the start method to "spawn" for compatibility with Windows
    set_start_method("spawn", force=True)

    # Define shopping sites to scrape
    shopping_sites = [
        {"name": "aliexpress",
         "home_url": "https://www.aliexpress.com",
         "search_url_template": '{base_url}/w/wholesale-{query}.html?page={{page_number}}'},
    ]

    # Import the product categories for scraping
    from UniversalWebshopScraper.generalized_scrapper.core.product_categories import categories_products

    n_workers = 12  # Number of workers to spawn

    # Loop through the shopping sites and start the scraper
    for site_info in shopping_sites:
        main_scraper(site_info, categories_products, n_workers=n_workers)

    print("***** All searches completed *****")