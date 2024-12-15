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
import pycountry

from vectorproduct.translator import Translator


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
        self.color = WORKER_COLORS[worker_index % len(WORKER_COLORS)]

    def write(self, message):
        if message.strip():
            colored_prefix = f"{self.color}[WORKER {self.worker_index}]{Style.RESET_ALL}"
            formatted_message = f"{colored_prefix} {message.strip()}"
            self.log_func(formatted_message)

    def flush(self):
        pass


def setup_logging(worker_index, shop_name):
    """
    Set up a logger that logs to both a file and the console.
    Logs are stored in a subfolder for each shop inside the 'scraped_logs' folder in the project root.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_base_dir = os.path.join(project_root, "scraped_logs", shop_name)
    os.makedirs(logs_base_dir, exist_ok=True)

    log_file = os.path.join(logs_base_dir, f"worker_{worker_index}.log")

    logger = logging.getLogger(f"Worker-{worker_index}-{shop_name}")
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter("%(message)s")
    file_handler.setFormatter(file_formatter)

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
    Worker process that can detect language (if instructed) or scrape products.
    Tasks:
    - ("LANGUAGE_DETECTION", site_info): detect language from home page and return it
    - (site_info, category, product_list): normal scraping
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

            # Define the base path for saving data in the 'data' repository
            base_data_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../../Data/scrapped_data")
            )
            # print(f"Worker-{worker_index}: Base data path: {base_data_path}")
            os.makedirs(base_data_path, exist_ok=True)  # Ensure the directory exists

            while True:
                task = task_queue.get()
                if task is None:
                    print(f"Worker-{worker_index}: Received termination signal. Exiting.")
                    break

                if task[0] == "LANGUAGE_DETECTION":
                    # Task format: ("LANGUAGE_DETECTION", site_info)
                    _, site_info_task = task
                    home_url = site_info_task.get("home_url", "")
                    # Open homepage and detect language
                    scraper.shopping_website = home_url
                    scraper.open_home_page(home_url)
                    soup = scraper.extract_page_structure()
                    text = soup.get_text(separator=' ', strip=True)
                    # **Log the entire extracted text**
                    print(f"Extracted Text Sample: {text[:1000]}...")  # Logs first 1000 characters

                    lang = scraper.detect_language(text)
                    print(f"Detected language: {lang}")
                    status_queue.put(("lang_detected", worker_index, lang))

                else:
                    # Normal scraping task: (site_info, category, product_list)
                    site_info_task, category, product_list = task
                    site_name = site_info_task.get("name", "unknown_site")
                    home_url = site_info_task.get("home_url", "")
                    search_url_template = site_info_task.get("search_url_template", "")

                    if scraper.shopping_website != home_url:
                        scraper.shopping_website = home_url
                        if not scraper.open_home_page(home_url):
                            print(f"Failed to open home page for {site_name}")
                            status_queue.put(('failed', worker_index))
                            break

                    print(f"***** Worker-{worker_index} processing category '{category}' on '{site_name}' *****")

                    for product in product_list:
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

                            # Define the save path inside the 'data' repository
                            save_dir = os.path.join(base_data_path, f"{shop_name}", f"{category}")
                            os.makedirs(save_dir, exist_ok=True)
                            save_path = os.path.join(save_dir, f"{product}.csv")
                            scraper.scrape_all_products(scroll_based=True, url_template=search_url, page_number_supported=True, max_pages=3)
                            scraper.save_to_csv(save_path=save_path, category=category)
                            scraper.stored_products.clear()

                            print(f"Saved scraped data to: {save_path}")

                        except Exception as e:
                            print(f"Error scraping product '{product}': {e}")
                            traceback.print_exc()

                    status_queue.put(('done', worker_index))

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
    Manages worker processes, detects language, and then scrapes categories one by one.
    Before scraping each category, if translation is needed, it will translate that category's products.
    This avoids translating all categories upfront and only translates when required.
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

    # Wait for all workers to be ready
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

    # STEP 1: DETECT LANGUAGE using the first active worker
    detect_worker = sorted(active_workers)[0]
    print(f"[INFO] MainScraper: Using Worker-{detect_worker} to detect language.")

    # Send language detection task
    task_queue.put(("LANGUAGE_DETECTION", site_info))

    # Wait for language detection result
    language = None
    while True:
        msg = status_queue.get()
        if msg[0] == 'lang_detected':
            _, w_idx, lang = msg
            print(f"[INFO] MainScraper: Worker-{w_idx} detected site language: {lang}")
            language = lang
            break
        elif msg[0] == 'lang_failed':
            _, w_idx = msg
            print(f"[ERROR] MainScraper: Worker-{w_idx} failed to detect language.")
            return
        elif msg[0] == 'captcha':
            _, w_idx = msg
            print(f"[CAPTCHA] Worker-{w_idx} needs CAPTCHA resolution for language detection.")
            input("Resolve CAPTCHA and press Enter...")
            captcha_events[w_idx].set()

    if not language or language.lower() == 'unknown':
        print("[WARNING] Could not detect language. Defaulting to English search terms.")
        target_language = 'en'
    else:
        # Convert language name to ISO 639-1 code
        try:
            lang_obj = pycountry.languages.lookup(language)
            target_language = lang_obj.alpha_2
        except:
            print(f"[WARNING] Could not map language '{language}' to ISO code, defaulting to 'en'")
            target_language = 'en'

    print(f"[INFO] MainScraper: Detected language code: {target_language}")

    # Initialize translator only if needed
    if target_language != 'en':
        print(f"[INFO] MainScraper: Will translate search terms from 'en' to '{target_language}' when needed.")
        try:
            translator = Translator(source_lang='en', target_lang=target_language)
        except Exception as e:
            print(f"[ERROR] MainScraper: Translator initialization failed: {e}")
            traceback.print_exc()
            translator = None
    else:
        translator = None
        print("[INFO] MainScraper: No translation needed, target language is 'en'.")

    # STEP 3: Process each category one by one
    for category, products in categories_amazon_products.items():
        print(f"\n[INFO] MainScraper: Starting category: {category}")

        # Translate products for this category on-the-fly
        if translator:
            try:
                translated_products = [translator.translate(product) for product in products]
            except Exception as e:
                print(f"[ERROR] MainScraper: Translation for category '{category}' failed: {e}")
                traceback.print_exc()
                translated_products = products
        else:
            translated_products = products

        # Print translated words for the current category
        print("[INFO] MainScraper: Translated words for the current category:")
        for orig, trans in zip(products, translated_products):
            print(f"    '{orig}' -> '{trans}'")

        # Check if we still have active workers
        if not active_workers:
            print("[WARNING] No active workers left.")
            break

        # Distribute products among active workers
        product_chunks = [[] for _ in active_workers]
        for idx, product in enumerate(translated_products):
            worker_idx = idx % len(active_workers)
            worker_index = sorted(active_workers)[worker_idx]
            product_chunks[worker_index].append(product)

        for i, worker_index in enumerate(sorted(active_workers)):
            task = (site_info, category, product_chunks[i])
            task_queue.put(task)
            print(f"[INFO] MainScraper: Assigned {len(product_chunks[i])} products to Worker-{worker_index}")

        # Wait for all workers to finish the current category
        completed_workers = set()
        while len(completed_workers) < len(active_workers):
            msg = status_queue.get()
            status = msg[0]
            worker_index = msg[1]
            if status == 'done':
                print(f"[INFO] MainScraper: Worker-{worker_index} completed its task for category '{category}'.")
                completed_workers.add(worker_index)
            elif status == 'captcha':
                print(f"[CAPTCHA] MainScraper: Worker-{worker_index} requires CAPTCHA resolution.")
                input("Press Enter after resolving CAPTCHA...")
                captcha_events[worker_index].set()
            elif status == 'failed':
                print(f"[ERROR] MainScraper: Worker-{worker_index} failed on category '{category}'.")
                active_workers.discard(worker_index)
                completed_workers.add(worker_index)

        print(f"[INFO] MainScraper: Finished category: {category}")

    # STEP 4: Terminate Workers
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
    # from UniversalWebshopScraper.generalized_scrapper.checker.missing_products import categories_products

    n_workers = 1  # Number of workers to spawn

    # Loop through the shopping sites and start the scraper
    for site_info in shopping_sites:
        main_scraper(site_info, categories_products, n_workers=n_workers)

    print("***** All searches completed *****")