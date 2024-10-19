import random
import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import re
from sortedcontainers import SortedSet
import pandas as pd

from agents.generalized_scrapper.functions import detect_captcha_detector, normalize_price, normalize_url

# TODO add proper comments
# TODO move between pages and get the data from them

CURRENCY_PATTER = r"(\$|€|£|zł|PLN|USD|GBP|JPY|AUD)"
PRICE_PATTERN = r"(\d+(?:[.,]\d{3})*(?:[.,]\d\d))"
COST_PATTERN = f"{PRICE_PATTERN}\s*{CURRENCY_PATTER}|{CURRENCY_PATTER}\s*{PRICE_PATTERN}"

class GeneralizedScraper:
    def __init__(self, shopping_website=None):
        self.driver = self.initialize_driver()
        self.marked_blocks = []  # List to store already processed blocks
        self.detected_products = set()  # Set to store detected products
        self.detected_image_urls = SortedSet()  # Ordered set for image URLs
        self.shopping_website = shopping_website
        self.product_count = 0
        self.stored_products = []  # List to store gathered products (dict format)

    def initialize_driver(self):
        #TODO repair this
        options = uc.ChromeOptions()
        user_data_dir = r"C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data"
        profile = "Profile 1"
        options.add_argument(f"user-data-dir={user_data_dir}")
        options.add_argument(f"profile-directory={profile}")
        options.add_argument('--disable-blink-features=AutomationControlled')
        driver = uc.Chrome(options=options)
        return driver

    def random_delay(self, min_seconds=4, max_seconds=6):
        """Mimic human-like random delay"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def is_captcha_present(self, soup):
        """Detect if a CAPTCHA is present based on interaction blocking elements and structural clues."""
        price_tags = re.search(COST_PATTERN, soup.text)
        if price_tags:
            return False
        return True

    def open_home_page_and_navigate_to_product(self, home_url, search_url):
        """Step 2 and 3: Open the homepage and navigate to the search URL"""
        try:
            self.driver.get(home_url)
            self.random_delay()
            self.driver.get(search_url)
            self.random_delay()
            soup =  self.extract_page_structure()
            if self.is_captcha_present(soup):
                input("Resolve Captcha and click enter button")
            return True
        except Exception as e:
            print(f"Failed to navigate to the product URL: {e}")
            return False

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

    def detect_product_blocks(self, soup):
        """Detect product blocks by finding the smallest subtrees that fulfill the requirements,
        skipping elements that are inside STRIKETHROUGH class."""

        # Find all blocks in the soup
        blocks = soup.find_all(['div', 'li', 'article', 'span', 'ul'], recursive=True)
        blocks.sort(key=lambda x: len(list(x.parents)), reverse=True)

        for block in blocks:
            if block in self.marked_blocks:
                continue  # Skip already processed blocks

            if self.is_valid_product_block(block):
                self.mark_block_and_children(block)
                product_url, image_url, price, title = self.extract_product_info(block)

                # Skip STRIKETHROUGH elements only when extracting prices
                filtered_price = self.filter_strikethrough_prices(block, price)

                if filtered_price:  # Only process if there is a valid price
                    price, currency = self._get_price_currency(filtered_price)

                    # Ensure product uniqueness
                    if product_url in self.detected_products:
                        continue
                    self.detected_products.add(product_url)

                    # Avoid duplicate image URLs using ordered set
                    if image_url in self.detected_image_urls:
                        continue
                    self.detected_image_urls.add(image_url)  # Mark this image URL as processed

                    # if product_url had not / at start add it
                    if not product_url.startswith("http"):
                        # If the URL doesn't start with "/", add it
                        if not product_url.startswith("/"):
                            product_url = f"/{product_url}"

                        # Prepend the base URL (shopping website)
                        product_url = f"{self.shopping_website}{product_url}"

                    # Store product information
                    self.store_product(product_url, image_url, price, currency, title)

                    print("\n--- Detected Product Block ---")
                    print(f"Website: {self.shopping_website}")
                    print(f"Product URL: {product_url}")
                    print(f"Image URL: {image_url}")
                    print(f"Price: {price}")
                    print(f"Currency: {currency}")
                    print(f"Title: {title}")
                    print("--- End of Product Block ---\n")

                    self.product_count += 1

    def filter_strikethrough_prices(self, block, price):
        """Filter out any price that is inside an element with the STRIKETHROUGH class."""
        # Check if the price or parent elements have the 'STRIKETHROUGH' class
        if block.find(class_='STRIKETHROUGH'):
            return None  # Skip if it's a strikethrough price
        return price

    def is_valid_product_block(self, block):
        """Check if a block contains all necessary information (product URL, image URL, price, and title)."""
        product_url, image_url, price, title = self.extract_product_info(block)
        return all([product_url, image_url, price, title])

    def extract_product_info(self, block):
        """Extract the product URL, image URL, price, and title from a block."""
        product_url = self.find_product_url(block)
        image_url = self.find_image_url(block)
        price = self.find_price(block)
        title = self.find_title(block)
        return product_url, image_url, price, title

    def find_product_url(self, block):
        """Find the product URL inside a block."""
        product_url = block.find('a', href=True)
        if product_url:
            # Normalize the URL
            return normalize_url(self.shopping_website, product_url['href'])
        return None

    def find_image_url(self, block):
        """Find the image URL inside a block (either img tag or inline style)."""
        img_tag = block.find('img', src=True)
        if img_tag:
            # Normalize the image URL
            return normalize_url(self.shopping_website, img_tag['src'])

        # Check for background images in inline styles (span or div)
        style = block.get('style')
        if style and 'background-image' in style:
            match = re.search(r'url\((.*?)\)', style)
            if match:
                return normalize_url(self.shopping_website, match.group(1))

        return None

    def _get_max_price(self, price_tags):
        """Get the maximum price from price_tags, assuming prices with STRIKETHROUGH have been filtered out."""
        # TODO maybe we can do it even better

        # Start with the first valid price tag
        max_price_tag = price_tags[0]
        max_price = price_tags[0][0] if price_tags[0][0] else price_tags[0][3]

        # Normalize the first price
        max_price = float(normalize_price(max_price))

        # Iterate through the price tags and find the maximum price
        for pt in price_tags:
            price = pt[0] if pt[0] else pt[3]
            price = float(normalize_price(price))  # Normalize each price before comparison

            # Change comparison to find the maximum price
            if price > max_price:
                max_price_tag = pt
                max_price = price

        return max_price_tag

    def _get_price_currency(self, full_pirce):
        price = re.findall(COST_PATTERN, full_pirce)
        return price[0][0] + price[0][3], price[0][1] + price[0][2]

    def find_price(self, block):
        """Look for price information in the block (currency symbols like $, €, PLN, etc.)."""
        price_pattern = re.compile(COST_PATTERN)
        price_tags = re.findall(price_pattern, block.text)

        if price_tags:
            # Extract the correct price using the maximum price logic
            max_price = self._get_max_price(price_tags)
            return "".join(max_price)

        return None

    def find_title(self, block):
        """Look for a string that is likely the product title."""
        # TODO update this function to get the title from the block!
        # Prioritize semantic tags commonly used for titles
        title_tags = block.find_all(['h1', 'h2', 'h3', 'span', 'a', 'div'])

        for tag in title_tags:
            # Extract text and check for reasonable length and content
            if 'title' in tag.get('class', []) or 'name' in tag.get('class', []):
                text_content = tag.get_text(strip=True)
                if len(text_content) > 10 and not re.search(r'\d{1,2}[.,]\d{1,2}\s*[a-zA-Z]*', text_content):
                    return text_content

        # Fallback to extracting the longest text content
        longest_text = max(block.stripped_strings, key=len, default="")
        if len(longest_text) > 10 and not re.search(r'\d{1,2}[.,]\d{1,2}\s*[a-zA-Z]*', longest_text):
            return longest_text

        return None

    def mark_block_and_children(self, block):
        """Mark the block and all its children as processed."""
        self.marked_blocks.append(block)
        for parent in block.parents:
            if parent not in self.marked_blocks:
                self.marked_blocks.append(parent)
        for child in block.find_all(recursive=True):
            if child not in self.marked_blocks:
                self.marked_blocks.append(child)

    def save_to_csv(self, save_path):
        """Save the stored products to a CSV file."""
        if self.stored_products:
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


if __name__ == "__main__":
    search_query = "tv"

    ### Test Temu ###
    home_url_temu = "https://www.temu.com"
    scraper = GeneralizedScraper(shopping_website=home_url_temu)

    temu_search_url_template = "{base_url}/search_result.html?search_key={query}&search_method=user"
    scraper.open_home_page_and_navigate_to_product(home_url_temu,
                                                   temu_search_url_template.format(base_url=home_url_temu,
                                                                                   query=search_query.replace(" ",
                                                                                                              "+")))
    soup_temu = scraper.extract_page_structure()

    print('Temu:')
    scraper.detect_product_blocks(soup_temu)
    print(f"Detected {scraper.product_count} products.")
    scraper.close_driver()

    ### Test Amazon ###
    home_url_amazon = "https://www.amazon.com"
    scraper = GeneralizedScraper(shopping_website=home_url_amazon)

    amazon_search_url_template = "{base_url}/s?k={query}"
    scraper.open_home_page_and_navigate_to_product(home_url_amazon,
                                                   amazon_search_url_template.format(base_url=home_url_amazon,
                                                                                     query=search_query.replace(" ",
                                                                                                                "+")))
    soup_amazon = scraper.extract_page_structure()

    print('Amazon:')
    scraper.detect_product_blocks(soup_amazon)
    print(f"Detected {scraper.product_count} products.")
    scraper.close_driver()

    ### Test Allegro ###
    home_url_allegro = "https://www.allegro.pl"
    scraper = GeneralizedScraper(shopping_website=home_url_allegro)

    allegro_search_url_template = "{base_url}/listing?string={query}"
    scraper.open_home_page_and_navigate_to_product(home_url_allegro,
                                                   allegro_search_url_template.format(base_url=home_url_allegro,
                                                                                      query=search_query.replace(" ",
                                                                                                                 "+")))
    soup_allegro = scraper.extract_page_structure()

    print('Allegro:')
    scraper.detect_product_blocks(soup_allegro)
    print(f"Detected {scraper.product_count} products.")
    scraper.close_driver()

    ### Test eBay ###
    home_url_ebay = "https://www.ebay.com"
    scraper = GeneralizedScraper(shopping_website=home_url_ebay)

    ebay_search_url_template = "{base_url}/sch/i.html?_from=R40&_trksid=p4432023.m570.l1313&_nkw={query}&_sacat=0"
    scraper.open_home_page_and_navigate_to_product(home_url_ebay,
                                                   ebay_search_url_template.format(base_url=home_url_ebay,
                                                                                   query=search_query.replace(" ",
                                                                                                              "+")))
    soup_ebay = scraper.extract_page_structure()

    print('eBay:')
    scraper.detect_product_blocks(soup_ebay)
    print(f"Detected {scraper.product_count} products.")
    scraper.close_driver()

    # aliexpress
    # TODO repair this part
    home_url_aliexpress = "https://www.aliexpress.com"
    scraper = GeneralizedScraper(shopping_website=home_url_aliexpress)

    # https://www.aliexpress.us/w/wholesale-jacketd-men.html?spm=a2g0o.productlist.auto_suggest.2.41fb15faIlHSvj
    aliexpress_search_url_template = "{base_url}/w/wholesale-{query}.html?spm=a2g0o.productlist.auto_suggest.2.41fb15faIlHSvj"
    scraper.open_home_page_and_navigate_to_product(home_url_aliexpress,
                                                   aliexpress_search_url_template.format(base_url=home_url_aliexpress,
                                                                                   query=search_query.replace(" ",
                                                                                                              "-")))
    soup_aliexpress = scraper.extract_page_structure()

    print('Aliexpress:')
    scraper.detect_product_blocks(soup_aliexpress)
    print(f"Detected {scraper.product_count} products.")
    scraper.close_driver()

