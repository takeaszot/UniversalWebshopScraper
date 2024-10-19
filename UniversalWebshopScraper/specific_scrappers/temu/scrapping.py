import random
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import os
import requests
from PIL import Image
from io import BytesIO
import torch
import numpy as np
import time

TEMU_URL = "https://www.temu.com"


class TemuScraperSelenium:
    def __init__(self):
        self.driver = self.initialize_driver()

    def initialize_driver(self):
        options = uc.ChromeOptions()
        #options.add_argument(r"user-data-dir=C:\path\to\your\Chrome\User Data")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.98 Safari/537.36")
        options.add_argument('--disable-blink-features=AutomationControlled')
        driver = uc.Chrome(options=options)
        return driver

    def random_delay(self):
        time.sleep(random.uniform(5, 8))  # Delay to mimic human behavior more closely

    def is_window_open(self):
        try:
            return len(self.driver.window_handles) > 0
        except Exception:
            return False

    def scrape_product_details(self, product_url):
        scraped_data = {}

        # Add the product URL to the scraped data
        scraped_data['product_url'] = product_url

        # Wait for the page to load and the title to appear
        WebDriverWait(self.driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1')))
        time.sleep(5)  # Additional wait time for dynamic content

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Extract title
        title = soup.find('h1').text.strip() if soup.find('h1') else 'N/A'
        scraped_data['title'] = title

        # Extract price
        price_element = soup.find('div', {'id': 'goods_price'})
        price = price_element.text.strip() if price_element else 'N/A'
        scraped_data['price'] = price

        # Extract description (if available)
        description_element = soup.find('div', class_='js-description')
        description = description_element.text.strip() if description_element else 'N/A'
        scraped_data['description'] = description

        # Extract category (if available)
        # Looking for an <a> tag under the navigation structure containing the category
        category_element = soup.find('nav', class_='_2xXsvHwL').find('a') if soup.find('nav', class_='_2xXsvHwL') else None
        category = category_element.text.strip() if category_element else 'N/A'
        scraped_data['category'] = category

        # Extract main image URL
        main_image_element = soup.find('div', class_='_22_BWn2A')
        if main_image_element and 'background-image' in main_image_element['style']:
            # Extract the URL from the background-image style
            style_attribute = main_image_element['style']
            start = style_attribute.find("url('") + len("url('")
            end = style_attribute.find("')", start)
            main_image_url = style_attribute[start:end]
            print(f"Extracted main image URL: {main_image_url}")
            scraped_data['image_url'] = main_image_url
        else:
            scraped_data['image_url'] = 'N/A'

        # Extract additional images (if available)
        additional_images = []
        image_elements = soup.find_all('img', {'data-cui-image': '1'})
        for img_element in image_elements:
            img_url = img_element['src'] if img_element and 'src' in img_element.attrs else None
            if img_url:
                additional_images.append(img_url)

        scraped_data['additional_images'] = additional_images

        return scraped_data

    def open_home_page_and_navigate_to_product(self, product_url):
        try:
            home_url = "https://www.temu.com"
            self.driver.get(home_url)
            self.random_delay()

            # Navigate to the product URL
            self.driver.get(product_url)
            self.random_delay()
            return True
        except Exception as e:
            print(f"Failed to navigate to the product URL: {e}")
            return False

    def scrape_product_data_from_url(self, product_url):
        product_data = {}
        try:
            if not self.open_home_page_and_navigate_to_product(product_url):
                print("Failed to navigate to the product page.")
                return {}

            # Scrape the product details
            product_data = self.scrape_product_details(product_url)

        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            if self.is_window_open():
                self.driver.quit()

        return product_data

    def scrape_list(self, query):
        query = query.replace(" ", "+")
        scraped_products = []
        self.open_home_page_and_navigate_to_product(f"{TEMU_URL}/search_result.html?search_key={query}&search_method=user")
        #self.driver.get(f"{TEMU_URL}/search_result.html?search_key={query}&search_method=user")

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        for product in soup.find_all('div', class_="EKDT7a3v"):
            #print(product.find('div', class_avtive_="price"))
            try:
                title_tag = product.h2  # Check if title exists
                if title_tag:
                    title = title_tag.text.strip()  # Extract the product title
                else:
                    title = "No title available"

                image_tag = product.find('img')  # Check if image exists
                if image_tag and 'src' in image_tag.attrs:
                    image_url = image_tag['src']  # Extract the product image URL
                else:
                    image_url = "No image available"

                link_tag = product.find('a', href=True)  # Check if link exists
                if link_tag:
                    link = TEMU_URL + link_tag['href']  # Construct the product link
                else:
                    link = "No link available"

                # # Extract description (if available)
                # description_tag = product.find('span', class_='a-text-normal')
                # description = description_tag.text.strip() if description_tag else "No description available"
                
                price = product.find("div", attrs={"data-type":"price"}).text

                # Append the extracted details into a list
                scraped_products.append({
                    'title': title,
                    'description': None,
                    'image_url': image_url,
                    'link': link,
                    'price': price
                })

            except Exception as e:
                print(f"Error parsing product: {e}")

        return scraped_products


    def scrape_product_from_query(self, query):
        product_data = {}
        try:
            if not self.open_home_page_and_navigate_to_product(product_url):
                print("Failed to navigate to the product page.")
                return {}

            # Scrape the product details
            product_data = self.scrape_product_details(product_url)

        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            if self.is_window_open():
                self.driver.quit()

        return product_data

if __name__ == "__main__":
    product_url = "https://www.temu.com/pl/m%C4%99ska-swobodna--z-kapturem-i-kieszeniami-poliesterowa--bez-rozci%C4%85gliwo%C5%9Bci-jednolity--d%C5%82ugie-r%C4%99kawy-regularny-kr%C3%B3j-ciep%C5%82a--na-zewn%C4%85trz-z-wype%C5%82nieniem-z-w%C5%82%C3%B3kien-poliestrowych-i-tkan%C4%85-faktur%C4%85-g-601099687463528.html?top_gallery_url=https%3A%2F%2Fimg.kwcdn.com%2Fproduct%2Ffancy%2F84438c07-e192-4a07-b506-cc2479052a0e.jpg&spec_id=3002&spec_gallery_id=9501&refer_page_sn=10009&refer_source=0&freesia_scene=2&_oak_freesia_scene=2&_oak_rec_ext_1=OTUwMw&_oak_gallery_order=786112172%2C773597012%2C280441521%2C2039138199%2C1078071492&_oak_mp_inf=EOiU4uqm1ogBGiBkMjdmMzQ3NmNkZWE0MTZlYmQyMzViM2Y1OTliNzc0YiDP4rGKpzI%3D&spec_ids=3002%2C16084%2C15060%2C15067&search_key=kurtka&refer_page_el_sn=200049&refer_page_name=search_result&refer_page_id=10009_1728477687809_nx5l787z3o&_x_sessn_id=1i2kr5rx94"

    scraper = TemuScraperSelenium()
    # product_data = scraper.scrape_product_data_from_url(product_url)
    product_data = scraper.scrape_list("jacket")

    print(product_data)
