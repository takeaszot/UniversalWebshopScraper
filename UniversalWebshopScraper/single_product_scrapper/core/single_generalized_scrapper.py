import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from vectorproduct.utils.time_decorators import time_it


class SingleProductGeneralizedScraper:
    def __init__(self, shopping_website, home_page):
        """
        :param shopping_website: Base domain or identifying string of the website (e.g. "https://www.ebay.com")
        :param home_page: The homepage URL to visit first (e.g. "https://www.ebay.com")
        """
        self.shopping_website = shopping_website
        self.home_page = home_page

        # Initialize the Selenium WebDriver (Chrome in this example)
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--headless")  # Uncomment to run headless
        self.driver = webdriver.Chrome(service=Service(), options=chrome_options)

    def _classify_leaf_node(self, tag):
        """
        Classify a leaf node into: 'image', 'title', 'description', or 'trash' (simple heuristics).
        Returns the string label.
        """
        # 1) Check if it's an <img> tag
        if tag.name == "img":
            return "image"

        # 2) Extract text content
        text_content = tag.get_text(strip=True)
        word_count = len(text_content.split())

        # 3) Check if it's a heading
        if tag.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            return "title"

        # 4) Heuristic for short text => maybe a 'title'
        if 1 <= word_count <= 10:
            return "title"

        # 5) Longer text => 'description'
        if word_count > 10:
            return "description"

        # 6) Otherwise => 'trash'
        return "trash"

    def _get_probability_distribution(self, label):
        """
        Return a probability distribution for each label in order:
        [prob_image, prob_title, prob_description, prob_trash]

        Here we do naive one-hot:
          - 1.0 for the predicted label, 0 for others.
        """
        if label == "image":
            return (1.0, 0.0, 0.0, 0.0)
        elif label == "title":
            return (0.0, 1.0, 0.0, 0.0)
        elif label == "description":
            return (0.0, 0.0, 1.0, 0.0)
        else:  # trash
            return (0.0, 0.0, 0.0, 1.0)

    def make_leaf_nodes_df(self, home_url, product_url):
        """
        1. Opens homepage
        2. Opens product page
        3. Identifies all leaf nodes
        4. Classifies them into ['image', 'title', 'description', 'trash']
        5. Returns a DataFrame with columns:
             - text_or_info
             - label
             - prob_image
             - prob_title
             - prob_description
             - prob_trash
        """
        # 1. Go to home page
        self.driver.get(home_url)
        time.sleep(2)  # small pause to let the page load

        # 2. Go to product page
        self.driver.get(product_url)
        time.sleep(2)  # let product page load

        # 3. Parse DOM with BeautifulSoup
        html_source = self.driver.page_source
        soup = BeautifulSoup(html_source, "html.parser")

        # 4. Identify leaf nodes
        all_tags = soup.find_all()
        records = []

        for tag in all_tags:
            child_tags = tag.find_all(recursive=False)
            if not child_tags:
                # It's a leaf node
                label = self._classify_leaf_node(tag)
                probs = self._get_probability_distribution(label)

                # For image tags, you might store src attribute
                if tag.name == "img":
                    content_str = tag.get("src", "").strip() or "No SRC"
                else:
                    content_str = tag.get_text(strip=True)

                record = {
                    "text_or_info": content_str,
                    "label": label,
                    "prob_image": probs[0],
                    "prob_title": probs[1],
                    "prob_description": probs[2],
                    "prob_trash": probs[3]
                }
                records.append(record)

        # 5. Convert to DataFrame
        df = pd.DataFrame(records)
        return df

    def scrape_comments_for_product(self, home_url, product_url):
        """
        1. Opens homepage
        2. Opens product URL
        3. Scrapes comments or reviews (placeholder logic).
           Actual selectors depend on each site's DOM.
        """
        # 1. Go to home page
        self.driver.get(home_url)
        time.sleep(2)

        # 2. Go to product page
        self.driver.get(product_url)
        time.sleep(2)

        # 3. Parse DOM
        html_source = self.driver.page_source
        soup = BeautifulSoup(html_source, "html.parser")

        # Example: Amazon's typical review text container
        comment_elements = soup.find_all("span", {"data-hook": "review-body"})
        comments = []
        for elem in comment_elements:
            text = elem.get_text(strip=True)
            if text:
                comments.append(text)

        if comments:
            print("Found the following comments on the product page:")
            for c in comments:
                print(" -", c)
        else:
            print("No comments found or no matching selectors for this site.")
        return comments

    def close_driver(self):
        """Close the Selenium WebDriver."""
        self.driver.quit()


# ================================================================
# EXAMPLE USAGE
# ================================================================
if __name__ == "__main__":
    print("eBay example:")
    scraper = SingleProductGeneralizedScraper(
        shopping_website="https://www.ebay.com",
        home_page="https://www.ebay.com"
    )

    home_url = "https://www.ebay.com"
    product_url = ("https://www.ebay.com/itm/387423894005?_trkparms=amclksrc%3DITM%26aid%3D1110013%26algo%3DHOMESPLICE.SIMRXI%26ao%3D1%26asc%3D20230918095141%26meid%3Da1a8c4dc4fda48ffb8f1a3dfc529fb65%26pid%3D101843%26rk%3D2%26rkt%3D23%26itm%3D387423894005%26pmt%3D1%26noa%3D0%26pg%3D4375194%26algv%3DSimRXIV2BaseWithHPPrerankerOptimizedFilteringRVICIIEmbeddingRecall%26brand%3DUnbranded&_trksid=p4375194.c101843.m3021&itmprp=cksum%3A387423894005a1a8c4dc4fda48ffb8f1a3dfc529fb65%7Cenc%3AAQAJAAABMPIUntTq2Gv6ns2UEoKw%252B6dEe2ar%252F1a0hFj0eXUL%252FQmvyFLcIe7Isl%252BBv6BPSbBg8bufZGKmIQY7seLe03p9IC4wJJRkmxMJ695EaIrGN%252FtVWXWnkurL0JSc41%252Br4oqA0%252FOaFA1yc8hdOUbZ6Bt4T04%252BjBVySvxf8jbLaU%252BQuTHgtJZQI7S4QwvHptZ5Z6EXxttWppFvCETEstY9736BRCOgfEgFVEucrZWMCiUCSt7PI7ms8iVp7mGsU4Dwlr4rxZxhFGnn5GRveqc8aDIjPtCwoxTnYoBtPnbpL%252F%252Bic70COgPHdqVNsc0phwRdngdmE79JyG5Tm3qgRiUexp1gsUloCa2yrBItKgIOFYVOC9cQri4M3Ei%252BLzB%252FWX8NzK18Eetv2pkvBbd%252BDstRayVPaRg%253D%7Campid%3APL_CLK%7Cclp%3A4375194&itmmeta=01JGKG8TQ1992WA3K6XRRD61P4&_trkparms=parentrq%3A2704695c1940a626cd9fe5d3ffffd74a%7Cpageci%3A2fe2e456-c906-11ef-9a78-2e2a4490a4fb%7Ciid%3A1%7Cvlpname%3Avlp_homepage")  # example product

    # Create a DataFrame of leaf nodes with classification
    df_ebay = scraper.make_leaf_nodes_df(home_url, product_url)
    print(df_ebay.head(20))  # show first 20 rows
    print("\nNumber of rows in df:", len(df_ebay))

    # Optionally scrape comments
    scraper.scrape_comments_for_product(home_url, product_url)
    scraper.close_driver()

    print("\nAmazon example:")
    scraper = SingleProductGeneralizedScraper(
        shopping_website="https://www.amazon.com",
        home_page="https://www.amazon.com"
    )

    home_url = "https://www.amazon.com"
    product_url = ("https://www.amazon.com/AmazonBasics-Extra-Thick-Exercise-Carrying/dp/B01LP0U5X0/?_encoding=UTF8&pd_rd_w=kEPhA&content-id=amzn1.sym.9929d3ab-edb7-4ef5-a232-26d90f828fa5&pf_rd_p=9929d3ab-edb7-4ef5-a232-26d90f828fa5&pf_rd_r=B4BFFWFE0Z18GNTAJB5G&pd_rd_wg=UPiln&pd_rd_r=e771d60f-1763-4ae6-adea-227cce6d5f98&ref_=pd_hp_d_btf_crs_zg_bs_3375251&th=1")

    # Create a DataFrame of leaf nodes with classification
    df_amazon = scraper.make_leaf_nodes_df(home_url, product_url)
    print(df_amazon.head(20))  # show first 20 rows
    print("\nNumber of rows in df:", len(df_amazon))

    # Optionally scrape comments
    scraper.scrape_comments_for_product(home_url, product_url)
    scraper.close_driver()