import random
import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import re
from sortedcontainers import SortedSet
import pandas as pd
import os
import cProfile
from line_profiler import profile
from collections import defaultdict

from UniversalWebshopScraper.generalized_scrapper.functions import detect_captcha_detector, normalize_price, normalize_url

"""


"""
# Define the patterns for detecting prices and currencies should work for all currencies and prices with or without commas
CURRENCY_PATTER = r"(\$|€|£|zł|PLN|USD|GBP|JPY|AUD)"
PRICE_PATTERN = r"(\d+(?:[.,]\d{3})*(?:[.,]\d\d))"
COST_PATTERN = f"{PRICE_PATTERN}\s*{CURRENCY_PATTER}|{CURRENCY_PATTER}\s*{PRICE_PATTERN}"

class GeneralizedScraper:
    """
    Initialize the GeneralizedScraper object with necessary attributes.

    Args:
        shopping_website (str): The URL of the shopping website.
    """
    def __init__(self, shopping_website=None):
        self.driver = self.initialize_driver()
        self.marked_blocks = set()  # Set to store marked blocks
        self.detected_products = set()  # Set to store detected products
        self.wrong_titles = set()  # Set to store detected titles
        self.detected_image_urls = SortedSet()  # Ordered set for image URLs
        self.parent_blocks = []  # change to set later, for now we use list to store all parent blocks to know how many we have
        self.shopping_website = shopping_website  # The URL of the shopping website
        self.product_count = 0  # Counter for the number of products detected
        self.stored_products = []  # List to store gathered products (dict format)

    def initialize_driver(self):
        """
        Initialize the Chrome driver with necessary options for avoiding CAPTCHA detection.

        Returns:
            driver: The initialized Chrome driver with customized options.
        """
        options = uc.ChromeOptions()
        user_data_dir = r"C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data"
        profile = "Profile 1"
        options.add_argument(f"user-data-dir={user_data_dir}")
        options.add_argument(f"profile-directory={profile}")
        options.add_argument('--disable-blink-features=AutomationControlled')
        driver = uc.Chrome(options=options)
        return driver

    def random_delay(self, min_seconds=1, max_seconds=2):
        """
        Mimic human-like random delay.

        Args:
            min_seconds (int): Minimum delay time in seconds.
            max_seconds (int): Maximum delay time in seconds.
        """
        time.sleep(random.uniform(min_seconds, max_seconds))

    def is_captcha_present(self, soup):
        """
        Detect if a CAPTCHA is present based on known CAPTCHA indicators in the HTML.

        Args:
            soup (BeautifulSoup): Parsed HTML of the page.

        Returns:
            bool: True if CAPTCHA is detected, False otherwise.
        """
        # TODO maybe this need to be improved
        # Define common CAPTCHA selectors
        captcha_selectors = [
            {'id': re.compile(r'captcha', re.I)},
            {'class': re.compile(r'captcha', re.I)},
            {'id': re.compile(r'recaptcha', re.I)},
            {'class': re.compile(r'recaptcha', re.I)},
            {'id': re.compile(r'g-recaptcha', re.I)},
            {'class': re.compile(r'g-recaptcha', re.I)},
            {'id': re.compile(r'h-captcha', re.I)},
            {'class': re.compile(r'h-captcha', re.I)},
            {'class': re.compile(r'arkose', re.I)},  # For Arkose Labs
            {'class': re.compile(r'cf-captcha', re.I)},  # For Cloudflare captchas
        ]

        # Check for elements matching the CAPTCHA selectors
        for selector in captcha_selectors:
            if soup.find(attrs=selector):
                print("CAPTCHA detected based on HTML attributes.")
                return True

        # Check for iframes that may contain CAPTCHA challenges
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if re.search(r'captcha|recaptcha|hcaptcha', src, re.I):
                print("CAPTCHA detected in an iframe.")
                return True

        # Optionally, check for CAPTCHA keywords in form actions or JavaScript
        forms = soup.find_all('form', action=True)
        for form in forms:
            if re.search(r'captcha', form['action'], re.I):
                print("CAPTCHA detected in form action.")
                return True

        scripts = soup.find_all('script', src=True)
        for script in scripts:
            if re.search(r'captcha', script['src'], re.I):
                print("CAPTCHA detected in script source.")
                return True

        # If none of the CAPTCHA indicators are found, assume no CAPTCHA is present
        return False

    def open_home_page(self, home_url):
        """
        Open the homepage and handle CAPTCHA if detected.

        Args:
            home_url (str): The URL of the homepage.

        Returns:
            bool: True if the page opened successfully, False otherwise.
        """
        try:
            self.driver.get(home_url)
            self.random_delay()
            soup = self.extract_page_structure()
            if self.is_captcha_present(soup):
                input("Resolve Captcha and click enter button")
            return True
        except Exception as e:
            print(f"Failed to navigate to the product URL: {e}")
            return False

    def open_search_url(self, search_url):
        """
        Open the search URL and handle CAPTCHA if detected.

        Args:
            search_url (str): The URL for the search page.

        Returns:
            bool: True if the page opened successfully, False otherwise.
        """
        try:
            self.driver.get(search_url.format(page_number=1))
            self.random_delay()
            soup = self.extract_page_structure()
            if self.is_captcha_present(soup):
                input("Resolve Captcha and click enter button")
            return True
        except Exception as e:
            print(f"Failed to navigate to the product URL: {e}")
            return

    def extract_page_structure(self):
        """
        Extract the page's HTML content using BeautifulSoup.

        Returns:
            BeautifulSoup: Parsed HTML content of the page.
        """
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        return soup

    def store_product(self, product_url, image_url, price, currency, title):
        """
        Store the product information in a list of dictionaries.

        Args:
            product_url (str): URL of the product.
            image_url (str): URL of the product image.
            price (str): Price of the product.
            currency (str): Currency of the product price.
            title (str): Title of the product.
        """
        self.stored_products.append({
            "Website": self.shopping_website,
            "Product URL": product_url,
            "Image URL": image_url,
            "Price": price,
            "Currency": currency,
            "Title": title
        })

    @profile
    def detect_product_blocks(self, soup):
        """
        Detect product blocks on the page by identifying the smallest subtrees with product information.

        Args:
            soup (BeautifulSoup): Parsed HTML of the page.
        """

        # Step 1: Identify all potential blocks that might contain product information.
        # We look for common HTML tags used to wrap products on e-commerce websites.
        blocks = soup.find_all(['div', 'li', 'article', 'span', 'ul'], recursive=True)

        # Step 2: Sort blocks by depth, with the deepest elements first.
        # Sorting by the number of parent elements allows us to process smaller, more specific blocks before larger containers.
        blocks.sort(key=lambda x: len(list(x.parents)), reverse=True)

        # how many block
        # print(f"Number of blocks: {len(blocks)}")

        # Step 3: Iterate through each block to identify and process those containing product data.
        for block in blocks:
            # Skip blocks that have already been processed to prevent redundant work.
            if id(block) in self.marked_blocks:
                continue

            # Step 4: Try to extract product information from the current block.
            # This includes URLs, images, price, and title. If any information is missing, we skip this block.
            product_info = self.extract_product_info(block)
            if not product_info:
                continue  # Skip block if product data is incomplete.

            # Unpack extracted information.
            product_urls, image_urls, price, title = product_info

            # Step 5: Mark the block and all of its child elements as processed.
            # This ensures we don't reprocess this block or its parents in future iterations.
            self.mark_and_block(block)

            # Step 6: Output basic information about detected products for debugging purposes.
            #print(f'number of product urls: {len(product_urls) if product_urls else 0}')
            #print(f'number of image urls: {len(image_urls) if image_urls else 0}')

            # Step 7: Extract the main product URL, image URL, price, and currency.
            # We assume the first URL and image in the list are the main ones for the product.
            product_url = product_urls[0]
            image_url = image_urls[0]
            price, currency = self._get_price_currency(price)

            # Step 8: Add each detected product URL and image URL to their respective sets.
            # This helps track which URLs have already been processed.
            for url in product_urls:
                self.detected_products.add(url)
            for url in image_urls:
                self.detected_image_urls.add(url)

            # Step 9: Store the product data in a list, ready for future saving to CSV or other storage.
            self.store_product(product_url, image_url, price, currency, title)

            # Step 10: Add a simplified version of the block’s structure to the parent_blocks set.
            # This is primarily for tracking and reporting purposes.
            self.parent_blocks.append(str(block).split('>')[0])

            # Step 11: Print detected product details for debugging and monitoring.
            # These prints help verify that scraping is working as intended.
            '''print(f"Detected parent block:\n{str(block).split('>')[0]}>")
            print("\n--- Detected Product Block ---")
            print(f"Website: {self.shopping_website}")
            print(f"Product URL: {product_url}")
            print(f"Image URL: {image_url}")
            print(f"Price: {price}")
            print(f"Currency: {currency}")
            print(f"Title: {title}")
            print('other urls:')

            # Print all product URLs detected in this block.
            print("All product URLs detected:")
            for url in product_urls:
                print(f"{url}\n")

            # Print all image URLs detected in this block.
            print("All image URLs detected:")
            for url in image_urls:
                print(f"{url}\n")

            print("--- End of Product Block ---\n")'''

            # Step 12: Increment the product count after successfully processing a product block.
            self.product_count += 1

    @profile
    def extract_product_info(self, block):
        """
        Extract product information from a block.

        Args:
            block (Tag): The HTML block to extract product information from.

        Returns:
            tuple: A tuple containing URLs, image URLs, price, and title, or None if any are missing.
        """
        price = self.find_price(block)

        if not price:
            return None

        product_urls = self.find_product_url(block)

        if not product_urls:
            return None

        image_urls = self.find_image_url(block)

        if not image_urls:
            return None

        title = self.find_title(block)

        if not title:
            return None

        return product_urls, image_urls, price, title

    @profile
    def find_product_url(self, block):
        """
        Find all product URLs inside a block.

        Args:
            block (Tag): The HTML block to search for product URLs.

        Returns:
            list: A list of unique product URLs not already detected, or None if empty.
        """
        product_urls = set()

        # Find all <a> tags and gather their URLs
        product_url_tags = block.find_all('a', href=True)
        for product_url_tag in product_url_tags:
            product_url = normalize_url(self.shopping_website, product_url_tag['href'])
            product_urls.add(product_url)

        # Remove already detected URLs
        unique_product_urls = [url for url in product_urls if url not in self.detected_products]

        # Return the first non-duplicate URL, if any
        if unique_product_urls:
            return unique_product_urls

        return None

    @profile
    def find_image_url(self, block):
        """
        Find all image URLs inside a block.

        Args:
            block (Tag): The HTML block to search for image URLs.

        Returns:
            list: A list of unique image URLs not already detected.
        """
        image_urls = set()

        # List of possible attributes for image sources in <img> and <source> tags
        source_attributes = [
            ('img', 'src'),
            ('img', 'srcset'),
            ('img', 'data-src'),
            ('img', 'data-srcset'),
            ('source', 'srcset')
        ]

        # Check each attribute in <img> and <source> tags
        for tag, attribute in source_attributes:
            for element in block.find_all(tag):
                if element.has_attr(attribute):
                    urls = element[attribute].split(',')
                    for url in urls:
                        if not url == '':
                            # Take the URL part only if srcset format, normalize it
                            normalized_url = normalize_url(self.shopping_website, url.split()[0])
                            if normalized_url:
                                image_urls.add(normalized_url)

        # Handle inline styles for background images in any tag with a style attribute
        for tag in block.find_all(True, style=True):
            style = tag['style']
            # Check for 'background-image' or 'background' URLs in inline styles
            match = re.search(r'background(?:-image)?:\s*url\((.*?)\)', style)
            if match:
                image_url = normalize_url(self.shopping_website, match.group(1))
                if image_url:
                    image_urls.add(image_url)

            # Optional: Check for URLs in 'content' style property (sometimes used)
            content_match = re.search(r'content:\s*url\((.*?)\)', style)
            if content_match:
                image_url = normalize_url(self.shopping_website, content_match.group(1))
                if image_url:
                    image_urls.add(image_url)

        # Remove already detected URLs
        unique_image_urls = [url for url in image_urls if url not in self.detected_image_urls]

        return unique_image_urls or []

    def _get_max_price(self, price_tags):
        """Get the maximum price from price_tags, assuming prices with STRIKETHROUGH have been filtered out.
        we get max price as sometimes there are small prices with number of rates!!! idk how to get this when we got full 'block' with only rates and without price

        Args:
            price_tags (list): List of price strings.

        Returns:
            str: The maximum price found in the price tags.
        """
        max_price_tag = price_tags[0]
        max_price = price_tags[0][0] if price_tags[0][0] else price_tags[0][3]
        max_price = float(normalize_price(max_price))

        for pt in price_tags:
            price = pt[0] if pt[0] else pt[3]
            price = float(normalize_price(price))  # Normalize each price before comparison

            if price > max_price:
                max_price_tag = pt
                max_price = price

        return max_price_tag

    def _get_price_currency(self, full_price):
        """
        Extract price and currency from a string.

        Args:
            full_price (str): The combined price and currency string.

        Returns:
            tuple: A tuple of price and currency.
        """
        price = re.findall(COST_PATTERN, full_price)
        return price[0][0] + price[0][3], price[0][1] + price[0][2]

    @profile
    def find_price(self, block):
        """
        Find price information in a block.

        Args:
            block (Tag): The HTML block to search for price information.

        Returns:
            str: The maximum price found, or None if no price is found.
        """
        # Get all text within the block in one call
        full_text = block.get_text(strip=True)

        # Apply the COST_PATTERN to the combined text
        price_pattern = re.compile(COST_PATTERN)
        price_tags = re.findall(price_pattern, full_text)

        if price_tags:
            max_price = self._get_max_price(price_tags)
            return "".join(max_price)

        return None

    @profile
    def find_title(self, block):
        """
        Find the most likely product title in a block, avoiding known "trash" strings.

        Args:
            block (Tag): The HTML block to search for the product title.

        Returns:
            str: The likely product title, or None if no valid title is found.
        """
        title_tags = block.find_all(['h1', 'h2', 'h3', 'span', 'a', 'div'])

        for tag in title_tags:
            if 'title' in tag.get('class', []) or 'name' in tag.get('class', []):
                text_content = tag.get_text(strip=True)
                # Check if content is valid and not in the detected "trash" titles
                if len(text_content) > 10 and text_content not in self.wrong_titles and \
                        not re.search(r'\d{1,2}[.,]\d{1,2}\s*[a-zA-Z]*', text_content):
                    return text_content

        # Fallback to the longest text if no specific title is found
        longest_text = max(block.stripped_strings, key=len, default="")
        if len(longest_text) > 10 and longest_text not in self.wrong_titles and \
                not re.search(r'\d{1,2}[.,]\d{1,2}\s*[a-zA-Z]*', longest_text):
            return longest_text

        return None

    @profile
    def mark_and_block(self, block):
        """
        Mark a block and its parent elements to avoid reprocessing.

        Args:
            block (Tag): The HTML block to mark as processed.
        """
        self.marked_blocks.add(id(block))
        for parent in block.parents:
            if id(parent) in self.marked_blocks:
                break
            self.marked_blocks.add(id(parent))

    def save_to_csv(self, save_path=None, category=None):
        """
        Save the stored products to a CSV file.

        Args:
            save_path (str): The file path to save the CSV file.
        """
        if self.stored_products:
            # Extract website name from the URL for folder naming
            website_name = self.shopping_website.replace("https://", "").replace("www.", "").split('.')[0]

            # Create directory for the specific website inside the 'scraped_data' folder
            save_dir = os.path.join('scraped_data', website_name, category)

            # Create the directory if it doesn't exist
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            # Create the full path for the CSV file
            csv_filename = f'{save_path}' if save_path else f'{website_name}_products.csv'
            save_path = os.path.join(save_dir, csv_filename)

            # Save the products to the CSV file
            df = pd.DataFrame(self.stored_products)
            df.to_csv(save_path, index=False)

            print(f"Saved {len(self.stored_products)} products to {save_path}")
        else:
            print("No products to save.")

    def close_driver(self):
        """
        Close the browser driver and print the count of detected products.
        """
        print("Closing the browser driver...")
        print(f"Detected {self.product_count} products.")
        if self.driver:
            self.driver.quit()

    def scroll_to_bottom(self, max_scrolls=10, scroll_pause_time=1):
        """
        Scroll down the page a set number of times to load more products.

        Args:
            max_scrolls (int): Maximum number of scrolls.
            scroll_pause_time (int): Pause time between scrolls in seconds.
        """

        last_height = self.driver.execute_script("return document.body.scrollHeight")

        for i in range(max_scrolls):
            # Scroll to the bottom of the page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.random_delay(scroll_pause_time, scroll_pause_time + 2)

            # Wait for new content to load
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            # Break if the page height hasn't changed, meaning no new content
            if new_height == last_height:
                break

            last_height = new_height

        # print(f"Scrolled {i + 1} times")

    # detect of not interesting blocks
    def trash_detection(self, soup):
        """
        Detect irrelevant strings by collecting duplicate strings across blocks on the first page.

        Args:
            soup (BeautifulSoup): Parsed HTML of the page.
        """
        # Dictionary to store counts of unique strings across blocks
        string_occurrences = defaultdict(int)

        # Loop through each block and count occurrences of each unique string across blocks
        blocks = soup.find_all(True)  # Find all tags to get strings from every block
        for block in blocks:
            block_strings = set()  # Track unique strings within each block

            for string in block.stripped_strings:
                # Filter short strings and avoid numbers that could indicate titles or product details
                if len(string) > 5 and not re.search(r'\d', string):
                    block_strings.add(string)

            # Count occurrences across all blocks
            for unique_string in block_strings:
                string_occurrences[unique_string] += 1

        # Define a threshold for what constitutes "trash" (e.g., appears in 3 or more blocks)
        threshold = 5
        self.wrong_titles = {string for string, count in string_occurrences.items() if count >= threshold}

        # Optional: Print out detected "trash" strings for debugging, each on a new line
        #print("Detected non-interesting (trash) titles:")
        #for title in self.wrong_titles:
        #    print(title)

    @profile
    def scrape_all_products(self, scroll_based=False, max_pages=20, max_scrolls=1, url_template=None,
                            page_number_supported=True):
        """
        Scrape all products using pagination and scrolling if enabled.

        Args:
            scroll_based (bool): Whether to use scrolling.
            max_pages (int): Maximum number of pages to scrape.
            max_scrolls (int): Maximum scrolls per page.
            url_template (str): Template URL with page number placeholder.
            page_number_supported (bool): Whether pagination is supported.
        """

        page_count = 1
        while page_count <= max_pages:
            print(f"Scraping page {page_count}")

            # Load the current page using pagination if supported
            if page_number_supported and url_template:
                search_url = url_template.format(page_number=page_count)
                self.driver.get(search_url)
                self.random_delay()

            # Scroll down the page if scroll_based is True
            if scroll_based:
                self.scroll_to_bottom(max_scrolls)  # Scroll down to load more products on the current page

            # Extract product blocks after scrolling
            soup = self.extract_page_structure()

            # we detect duplicated urls and titles to avoid trash that is duplicated (like 'promotion' or 'discount')
            if page_count == 1:
                self.trash_detection(soup)

            self.detect_product_blocks(soup)

            # how many marked blocks we have
            # print(f"Number of marked blocks: {len(self.marked_blocks)}")

            # clear marked blocks
            self.marked_blocks.clear()

            # Handle pagination if supported, otherwise just scroll and stop
            if page_number_supported:
                page_count += 1
            else:
                break  # Stop after scrolling if pagination is not supported

        # clear all trash titles after scraping all products on all pages
        self.wrong_titles.clear()


if __name__ == "__main__":
    # for speed testing use this command
    # PYTHONPATH=. kernprof -l -v UniversalWebshopScraper/generalized_scrapper/botleneck_testing/generalized_scrapper_2.py
    search_query = "tv"

    def run_new_method(scraper, search_url_template, base_url, csv_file_name, scroll_based=False, page_number_supported=True):
        """Run the new method with scrolling or pagination and save the results."""
        # first we need to open the home page to avoid captcha
        scraper.open_home_page(base_url)
        # next we open the search page and start scraping products
        scraper.open_search_url(search_url_template)
        # next we scrape all products with scrolling and pagination support if available, later on the first page we would learn parent blocks logic and then we would use it to scrape all products on other pages
        scraper.scrape_all_products(scroll_based=scroll_based, url_template=search_url_template, page_number_supported=page_number_supported)
        # just to check how many products we have scraped
        new_method_count = scraper.product_count
        # scraper.save_to_csv(csv_file_name)  # Save to the appropriate shop folder
        scraper.close_driver()
        return new_method_count

    ### Test Allegro (pagination-based) ###
    home_url_allegro = "https://www.allegro.pl"
    # Corrected URL template with double curly braces for page_number
    allegro_search_url_template = f'{home_url_allegro}/listing?string={search_query.replace(" ", "+")}&p={{page_number}}'

    scraper = GeneralizedScraper(shopping_website=home_url_allegro)
    new_allegro_count = run_new_method(scraper, allegro_search_url_template, home_url_allegro,
                                       'allegro_products_new.csv', scroll_based=True, page_number_supported=True)
    print(f"New Allegro product count: {new_allegro_count}")

    ### Test eBay (pagination-based) ###
    home_url_ebay = "https://www.ebay.com"
    ebay_search_url_template = "{base_url}/sch/i.html?_nkw={query}&_pgn={{page_number}}".format(
        base_url=home_url_ebay, query=search_query.replace(" ", "+"))

    scraper = GeneralizedScraper(shopping_website=home_url_ebay)
    new_ebay_count = run_new_method(scraper, ebay_search_url_template, home_url_ebay, 'ebay_products_new.csv', scroll_based=True, page_number_supported=True)
    print(f"New eBay product count: {new_ebay_count}")

    ### Test Aliexpress (scroll-based) ###
    home_url_aliexpress = "https://www.aliexpress.com"
    aliexpress_search_url_template = "{home_url}/w/wholesale-{query}.html?page={{page_number}}".format(home_url=home_url_aliexpress, query=search_query.replace(" ", "+"))

    scraper = GeneralizedScraper(shopping_website=home_url_aliexpress)
    new_aliexpress_count = run_new_method(scraper, aliexpress_search_url_template, home_url_aliexpress, 'aliexpress_products_new.csv', scroll_based=True, page_number_supported=True)
    print(f"New Aliexpress product count: {new_aliexpress_count}")

    ### Test Temu (scroll-based) ###
    home_url_temu = "https://www.temu.com"
    temu_search_url_template = "{base_url}/search_result.html?search_key={query}&search_method=user".format(
        base_url=home_url_temu, query=search_query.replace(" ", "+"))

    scraper = GeneralizedScraper(shopping_website=home_url_temu)
    new_temu_count = run_new_method(scraper, temu_search_url_template, home_url_temu, 'temu_products_new.csv', scroll_based=True, page_number_supported=False)
    print(f"New Temu product count: {new_temu_count}")

    ### Test Amazon (pagination-based) ###
    home_url_amazon = "https://www.amazon.com"
    amazon_search_url_template = "{base_url}/s?k={query}&page={{page_number}}".format(base_url=home_url_amazon, query=search_query.replace(" ", "+"))

    scraper = GeneralizedScraper(shopping_website=home_url_amazon)
    new_amazon_count = run_new_method(scraper, amazon_search_url_template, home_url_amazon, 'amazon_products_new.csv', scroll_based=True, page_number_supported=True)
    print(f"New Amazon product count: {new_amazon_count}")