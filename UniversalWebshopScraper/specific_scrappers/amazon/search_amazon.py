"""[module summary]"""

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

AMAZON_URL = "https://www.amazon.com"

# Initialize random User-Agent generator
ua = UserAgent()

# Initialize Selenium WebDriver (remove headless mode for debugging)
options = webdriver.ChromeOptions()
options.add_argument(f"user-agent={ua.random}")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-extensions")
options.add_argument("--disable-infobars")

# Path to the ChromeDriver executable (ensure it's installed and accessible)
driver = webdriver.Chrome(options=options)

# Function to generate search query from text description + image (optional enhancement)
def generate_search_query(text_description, image):
    """
    Generates a search query by combining a text description and (optionally) information from an image.
    """
    # For now, we rely ONLY on the text description.
    # We can enhance the query with some basic features extracted from the image.
    # Future extension: use an image classifier to get high-level categories to enhance the query.
    # For simplicity, for now I will use just the text description as the query.
    return text_description

# Amazon Scraper Class using Selenium
class AmazonScraperSelenium:
    def __init__(self, query, num_products=5):
        self.query = query.replace(' ', '+')
        self.base_url = f"{AMAZON_URL}/s?k={self.query}"
        self.num_products = num_products  # Number of products to scrape

    # Get products from Amazon query page
    def scrape_products(self, query: str="", page: int=1):
        if len(query) == 0:
            query = self.query

        query = query.replace(" ", "+")
        scraped_products = []
        try:
            driver.get(f"{AMAZON_URL}/s?k={query}&p={page}")

            # Wait until product search results are loaded
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]'))
            )
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            product_count = 0

            # Iterate through search results and extract product details
            for product in soup.find_all('div', {'data-component-type': 's-search-result'}):
                if product_count >= self.num_products:
                    break  # Stop when we've reached the desired number of products

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
                        link = AMAZON_URL + link_tag['href']  # Construct the product link
                    else:
                        link = "No link available"

                    # Extract description (if available)
                    description_tag = product.find('span', class_='a-text-normal')
                    description = description_tag.text.strip() if description_tag else "No description available"

                    price = product.find("span","a-price")
                    if price:
                        price = price.find("span","a-offscreen").text
                    else:
                        price = 0

                    # Append the extracted details into a list
                    scraped_products.append({
                        'title': title,
                        'description': description,
                        'image_url': image_url,
                        'link': link,
                        'price': price
                    })
                    product_count += 1

                except Exception as e:
                    print(f"Error parsing product: {e}")

        except Exception as e:
            print(f"Error scraping Amazon: {e}")
            return []
        print(f"Scraped {len(scraped_products)} products.")
        return scraped_products

    # Get products from all pages
    def _scrape_products_all(self, query: str=""):
        query = query.replace(" ", "+")
        scraped_products = []
        try:
            driver.get(f"{AMAZON_URL}/s?k={query}&p=1")
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]'))
            )
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            last_page = soup.find('span', "s-pagination-item s-pagination-disabled")
            last_page = int(last_page.text)
            
        except Exception as e:
            print(f"Error parsing product: {e}\n {driver.page_source}")
            return []

        for i in range(1, last_page+1):
                scraped_products += self.scrape_products(query, i)
        return scraped_products
    
    # 
    def scrape_products_all(self, query: str | list[str] = ""):
        if type(query) == str:
            return self._scrape_products_all(query)
        
        scraped_products = []
        for q in query:
            scraped_products += self._scrape_products_all(q)
        return scraped_products


    

# TODO: move it to separate file 
if __name__ == "__main__":
    # Input: Specify the number of products to scrape
    num_products_to_scrape = 5  # You can modify this value to scrape more or fewer products

    # create text to search
    local_image_path = r"C:\dropshipping\archive\test_product\testowy_produkt.jpg"
    query_image = Image.open(local_image_path)
    query_description = "Feral Duck Cartoon Printed Men's Round Neck T-Shirt With Comfy Short Sleeves Design, Perfect For Summer Everyday Life & Outdoor Vacation"

    # simple approach for now
    text_to_search = generate_search_query("Feral Duck Cartoon T-Shirt", None)

    # Perform the search with Selenium
    scraper = AmazonScraperSelenium(text_to_search, num_products=num_products_to_scrape)
    scraped_products = scraper.scrape_products()

    # Check if any products were scraped
    if not scraped_products:
        print("No products were scraped from Amazon. Exiting.")
    else:
        print(f"Scraped {len(scraped_products)} products.")

        # Display the scraped products
        for product in scraped_products:
            print(f"Title: {product['title']}")
            print(f"Description: {product['description']}")
            print(f"Image URL: {product['image_url']}")
            print(f"Link: {product['link']}")
            print("-" * 80)

    # now lets order and check similarity to provided product

    # Ensure you have these imports from your existing functions
    from models import CLIPModel, SimilaritySearch, display_single_product

    # Initialize CLIP model
    clip_model = CLIPModel()

    # Scraped products from Amazon (assuming you already have this data from your scraper)
    scraped_products = scraper.scrape_products()

    # Check if any products were scraped
    if not scraped_products:
        print("No products were scraped from Amazon. Exiting.")
        exit()

    # Step 1: Create embeddings for scraped products
    product_embeddings = []
    for product in scraped_products:
        try:
            # Download product image
            response = requests.get(product['image_url'])
            img = Image.open(BytesIO(response.content))

            # Encode image and text using CLIP
            image_embedding = clip_model.encode_image(img)
            text_embedding = clip_model.encode_text(product['description'])  # Use description for the text embedding

            # Combine image and text embeddings
            combined_embedding = np.hstack((image_embedding, text_embedding))
            product_embeddings.append(combined_embedding)

        except Exception as e:
            print(f"Error processing product: {product['title']} - {e}")

    # Convert embeddings to a NumPy array for FAISS
    product_embeddings = np.vstack(product_embeddings)

    # Step 2: Initialize the FAISS similarity search engine with the embeddings
    search = SimilaritySearch(product_embeddings)

    # Step 3: Load the local query image
    local_image_path = r"C:\dropshipping\archive\test_product\testowy_produkt.jpg"
    query_image = Image.open(local_image_path)
    query_description = "Feral Duck Cartoon Printed Men's Round Neck T-Shirt With Comfy Short Sleeves Design, Perfect For Summer Everyday Life & Outdoor Vacation"

    # Step 4: Create query embeddings (local image and description)
    query_image_embedding = clip_model.encode_image(query_image)
    query_text_embedding = clip_model.encode_text(query_description)

    # Combine the query image and text embeddings
    query_embedding = np.hstack((query_image_embedding, query_text_embedding))

    # Step 5: Perform similarity search
    top_k = 5  # Set the number of top similar products you want to display
    indices, similarity_scores = search.find_similar_items(query_image, query_description, clip_model, top_k=top_k)

    # Step 6: Display the top similar scraped products
    print(f"Showing top {top_k} similar products:")
    for idx, score in zip(indices[0], similarity_scores[0]):
        similar_product = scraped_products[idx]
        print(f"Product: {similar_product['title']}")
        print(f"Description: {similar_product['description']}")
        print(f"Image URL: {similar_product['image_url']}")
        print(f"Link: {similar_product['link']}")
        print(f"Similarity Score: {score:.2f}")
        print("-" * 80)

        # Optionally, display the product image and details visually
        display_single_product(similar_product['image_url'], similar_product['title'], score)

    # Quit the browser session
    driver.quit()