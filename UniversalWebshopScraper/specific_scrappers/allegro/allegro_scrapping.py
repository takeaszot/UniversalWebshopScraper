import random
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

GOOGLE_URL = "https://www.google.com"
ALLEGRO_URL = "https://www.allegro.pl"


class AllegroScraperSelenium:
    def __init__(self):
        self.driver = self.initialize_driver()

    def initialize_driver(self):
        options = uc.ChromeOptions()
        # Use your existing Chrome profile to load cookies and other settings
        user_data_dir = r"C:\Users\<YourUsername>\AppData\Local\Google\Chrome\User Data"  # Change to your actual path
        profile = "Profile 1"  # Change to the profile you want to use (e.g., "Default", "Profile 2")

        options.add_argument(f"user-data-dir={user_data_dir}")
        options.add_argument(f"profile-directory={profile}")
        options.add_argument('--disable-blink-features=AutomationControlled')
        driver = uc.Chrome(options=options)
        return driver

    def random_delay(self, min_seconds=6, max_seconds=12):
        time.sleep(random.uniform(min_seconds, max_seconds))  # Varying delay to mimic human behavior

    def is_window_open(self):
        try:
            return len(self.driver.window_handles) > 0
        except Exception:
            return False

    def open_google_home_page(self):
        try:
            self.driver.get(GOOGLE_URL)
            self.random_delay()
            return True
        except Exception as e:
            print(f"Failed to open Google homepage: {e}")
            return False

    def open_allegro_home_page(self):
        try:
            self.driver.get(ALLEGRO_URL)
            self.random_delay()
            return True
        except Exception as e:
            print(f"Failed to open Allegro homepage: {e}")
            return False

    def perform_search_on_allegro(self, query):
        try:
            # Locate the search bar and perform the search
            search_box = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "string"))
            )
            search_box.clear()
            search_box.send_keys(query)
            search_box.submit()  # Submit the search form

            self.random_delay()
            return True
        except Exception as e:
            print(f"Failed to perform the search on Allegro: {e}")
            return False

    def scrape_search_results(self):
        scraped_products = []

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Loop through each product card in the search results
        for product in soup.find_all('div', class_='mpof_ki myre_zn _9c44d_3AMmE'):
            try:
                title_tag = product.find('a', class_='_w7z6o')
                title = title_tag.text.strip() if title_tag else "No title available"

                image_tag = product.find('img')
                image_url = image_tag['src'] if image_tag and 'src' in image_tag.attrs else "No image available"

                link = title_tag['href'] if title_tag and 'href' in title_tag.attrs else "No link available"
                link = f"https://www.allegro.pl{link}" if link != "No link available" else link

                price_tag = product.find('span', class_='_1svub _lf05o')
                price = price_tag.text.strip() if price_tag else "No price available"

                # Append the extracted details into a list
                scraped_products.append({
                    'title': title,
                    'image_url': image_url,
                    'link': link,
                    'price': price
                })

            except Exception as e:
                print(f"Error parsing product: {e}")

        return scraped_products

    def scrape_list(self, query):
        # Open Google homepage first
        if not self.open_google_home_page():
            print("Failed to open Google homepage.")
            return []

        # Then open Allegro homepage
        if not self.open_allegro_home_page():
            print("Failed to open Allegro homepage.")
            return []

        # Perform the search on Allegro
        if not self.perform_search_on_allegro(query):
            print("Failed to search on Allegro.")
            return []

        # Scrape the search results
        product_data = self.scrape_search_results()

        # Close the browser after scraping
        if self.is_window_open():
            self.driver.quit()

        return product_data


if __name__ == "__main__":
    scraper = AllegroScraperSelenium()
    products = scraper.scrape_list("jacket")

    for product in products:
        print("Title:", product['title'])
        print("Price:", product['price'])
        print("Image URL:", product['image_url'])
        print("Product URL:", product['link'])
        print("-" * 69)
