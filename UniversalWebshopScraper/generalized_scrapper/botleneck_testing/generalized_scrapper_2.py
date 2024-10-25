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

from UniversalWebshopScraper.generalized_scrapper.functions import detect_captcha_detector, normalize_price, normalize_url

"""


"""

CURRENCY_PATTER = r"(\$|€|£|zł|PLN|USD|GBP|JPY|AUD)"
PRICE_PATTERN = r"(\d+(?:[.,]\d{3})*(?:[.,]\d\d))"
COST_PATTERN = f"{PRICE_PATTERN}\s*{CURRENCY_PATTER}|{CURRENCY_PATTER}\s*{PRICE_PATTERN}"

class GeneralizedScraper:
    def __init__(self, shopping_website=None):
        self.driver = self.initialize_driver()
        self.marked_blocks = set()
        self.detected_products = set()  # Set to store detected products
        self.detected_image_urls = SortedSet()  # Ordered set for image URLs
        self.parent_blocks = set()
        self.shopping_website = shopping_website
        self.product_count = 0
        self.stored_products = []  # List to store gathered products (dict format)

    def initialize_driver(self):
        options = uc.ChromeOptions()
        user_data_dir = r"C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data"
        profile = "Profile 1"
        options.add_argument(f"user-data-dir={user_data_dir}")
        options.add_argument(f"profile-directory={profile}")
        options.add_argument('--disable-blink-features=AutomationControlled')
        driver = uc.Chrome(options=options)
        return driver

    def random_delay(self, min_seconds=1, max_seconds=1):
        """Mimic human-like random delay"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def is_captcha_present(self, soup):
        """Detect if a CAPTCHA is present based on known CAPTCHA indicators in the HTML."""
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
        """Open the homepage and navigate to the search URL"""
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
        """Open the search URL and resolve CAPTCHA if detected."""
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
        """Extract the page's HTML content using BeautifulSoup"""
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        return soup

    def store_product(self, product_url, image_url, price, currency, title):
        """Store the product information in a list of dictionaries."""
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
        """Detect product blocks by finding the smallest subtrees that fulfill the requirements,
        skipping elements that are inside STRIKETHROUGH class."""
        blocks = soup.find_all(['div', 'li', 'article', 'span', 'ul'], recursive=True)
        blocks.sort(key=lambda x: len(list(x.parents)), reverse=True)

        for block in blocks:
            if block in self.marked_blocks:
                continue  # Skip already processed blocks

            if self.is_valid_product_block(block):
                self.mark_block_and_children(block)
                product_urls, image_urls, price, title = self.extract_product_info(block)

                print(f'number of product urls: {len(product_urls) if product_urls else 0}')
                print(f'number of image urls: {len(image_urls) if image_urls else 0}')

                product_url = product_urls[0]
                image_url = image_urls[0]

                price, currency = self._get_price_currency(price)

                # Add all found product URLs to the detected_products set
                for product_url in product_urls:
                    self.detected_products.add(product_url)

                # Add all found image URLs to the detected_image_urls set
                for image_url in image_urls:
                    self.detected_image_urls.add(image_url)

                self.store_product(product_url, image_url, price, currency, title)
                self.parent_blocks.add(str(block).split('>')[0])

                # just print the highest-level tag
                print(f"Detected parent block:\n{str(block).split('>')[0]}>")
                print("\n--- Detected Product Block ---")
                print(f"Website: {self.shopping_website}")
                print(f"Product URL: {product_url}")
                print(f"Image URL: {image_url}")
                print(f"Price: {price}")
                print(f"Currency: {currency}")
                print(f"Title: {title}")
                print('other urls:')

                # Print all product URLs detected in this block
                if product_urls:
                    print("All product URLs detected:")
                    for url in product_urls:
                        print(f"{url}\n")
                else:
                    print("All product URLs detected: None\n")

                # Print all image URLs detected in this block
                if image_urls:
                    print("All image URLs detected:")
                    for url in image_urls:
                        print(f"{url}\n")
                else:
                    print("All image URLs detected: None\n")

                print("--- End of Product Block ---\n")

                self.product_count += 1


    def filter_strikethrough_prices(self, block, price):
        """Filter out any price that is inside an element with the STRIKETHROUGH class."""
        if block.find(class_='STRIKETHROUGH'):
            return None  # Skip if it's a strikethrough price
        return price

    def is_valid_product_block(self, block):
        """Check if a block contains all necessary information (product URL, image URL, and price)."""
        if not self.find_product_url(block):  # Check if a product URL exists
            return False
        if not self.find_image_url(block):  # Check if an image URL exists
            return False
        if not self.find_price(block):  # Check if a price exists
            return False
        if not self.find_title(block):
            return False
        return True

    def extract_product_info(self, block):  # we are doing this 2 times!!! TODO
        """Extract the product URL, image URL, price, and title from a block."""
        product_url = self.find_product_url(block)
        image_url = self.find_image_url(block)
        price = self.find_price(block)
        title = self.find_title(block)
        return product_url, image_url, price, title

    @profile
    def find_product_url(self, block):
        """Find all product URLs inside a block and return the first non-duplicate one."""
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
        """Find all image URLs inside a block (either img tag or inline style)."""
        image_urls = set()

        # Find all <img> tags and gather their URLs
        img_tags = block.find_all('img', src=True)
        for img_tag in img_tags:
            image_url = normalize_url(self.shopping_website, img_tag['src'])
            if image_url:  # Ensure no None values are added
                image_urls.add(image_url)

        # Check for inline styles with 'background-image' and extract the URLs
        style = block.get('style')
        if style and 'background-image' in style:
            match = re.search(r'url\((.*?)\)', style)
            if match:
                image_url = normalize_url(self.shopping_website, match.group(1))
                if image_url:  # Ensure no None values are added
                    image_urls.add(image_url)

        # Remove already detected URLs
        unique_image_urls = [url for url in image_urls if url not in self.detected_image_urls]

        return unique_image_urls or []

    def _get_max_price(self, price_tags):
        """Get the maximum price from price_tags, assuming prices with STRIKETHROUGH have been filtered out."""
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
        price = re.findall(COST_PATTERN, full_price)
        return price[0][0] + price[0][3], price[0][1] + price[0][2]

    def find_price(self, block):
        """Look for price information in the block, including cases with multi-span prices,
           and skip prices inside elements with the 'STRIKETHROUGH' class."""
        # Find all span elements within the block
        price_spans = block.find_all('span', recursive=True)
        full_text = ""

        for span in price_spans: # todo check if this works
            # Skip any price inside an element with a 'STRIKETHROUGH' class
            if span.find_parent(class_='STRIKETHROUGH'):
                continue

            text = span.get_text(strip=True)
            full_text += text  # Combine all text content from spans into a single string

        # Now apply your COST_PATTERN to the combined text
        price_pattern = re.compile(COST_PATTERN)
        price_tags = re.findall(price_pattern, full_text)

        if price_tags:
            max_price = self._get_max_price(price_tags)
            return "".join(max_price)

        return None

    def find_title(self, block):
        """Look for a string that is likely the product title."""
        title_tags = block.find_all(['h1', 'h2', 'h3', 'span', 'a', 'div'])

        for tag in title_tags:
            if 'title' in tag.get('class', []) or 'name' in tag.get('class', []):
                text_content = tag.get_text(strip=True)
                if len(text_content) > 10 and not re.search(r'\d{1,2}[.,]\d{1,2}\s*[a-zA-Z]*', text_content):
                    return text_content

        longest_text = max(block.stripped_strings, key=len, default="")
        if len(longest_text) > 10 and not re.search(r'\d{1,2}[.,]\d{1,2}\s*[a-zA-Z]*', longest_text):
            return longest_text

        return None

    def mark_block_and_children(self, block):
        """Mark the block and all its children as processed."""
        self.marked_blocks.add(block)
        for parent in block.parents:
            if parent not in self.marked_blocks:
                self.marked_blocks.add(parent)
        for child in block.find_all(recursive=True):  # can remove this TODO check
            if child not in self.marked_blocks:
                self.marked_blocks.add(child)

    def save_to_csv(self, save_path=None):
        """Save the stored products to a CSV file inside a directory for each e-commerce website."""
        if self.stored_products:
            # Extract website name from the URL for folder naming
            website_name = self.shopping_website.replace("https://", "").replace("www.", "").split('.')[0]

            # Create directory for the specific website inside the 'scraped_data' folder
            save_dir = os.path.join('scraped_data', website_name)

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
        """Close the browser driver"""
        print("Closing the browser driver...")
        print(f"Detected {self.product_count} products.")
        if self.driver:
            self.driver.quit()

    def scroll_to_bottom(self, max_scrolls=10, scroll_pause_time=1):
        """Scroll down the page a set number of times to load more products."""

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

        print(f"Scrolled {i + 1} times")

    @profile
    def scrape_all_products(self, scroll_based=False, max_pages=3, max_scrolls=1, url_template=None,
                            page_number_supported=True):
        """Scrape all products using scrolling and pagination together when both are True."""

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
            self.detect_product_blocks(soup)

            # clear marked blocks
            self.marked_blocks.clear()

            # Handle pagination if supported, otherwise just scroll and stop
            if page_number_supported:
                page_count += 1
            else:
                break  # Stop after scrolling if pagination is not supported

        # print all patent blocks
        print('parent blocks:')
        for block in self.parent_blocks:
            print(block)

if __name__ == "__main__":
    search_query = "tv"

    def run_new_method(scraper, search_url_template, base_url, csv_file_name, scroll_based=False, page_number_supported=True):
        """Run the new method with scrolling or pagination and save the results."""
        scraper.open_home_page(base_url)
        scraper.open_search_url(search_url_template)
        scraper.scrape_all_products(scroll_based=scroll_based, url_template=search_url_template, page_number_supported=page_number_supported)
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