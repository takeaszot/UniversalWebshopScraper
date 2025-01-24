import re
import json
import time
import random
import tempfile

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By

# Hugging Face Transformers for Zero-Shot Classification
from transformers import pipeline

########################################################################
# If you do not want to use a zero-shot approach, comment out or remove
# the lines that reference `self.zero_shot_classifier`.
########################################################################

class GeneralizedScraper:
    def __init__(
            self,
            shopping_website,
            home_page=None,
            user_data_dir=None,
            initialize_driver_func=None,
            offline_mode=False
    ):
        """
        Basic initialization of the scraper.
        """
        self.shopping_website = shopping_website
        self.home_page = home_page
        self.user_data_dir = user_data_dir
        self.initialize_driver_func = initialize_driver_func
        self.offline_mode = offline_mode

        self.product_count = 0
        self.stored_products = []

        # Only initialize the driver if not in offline mode
        if self.offline_mode:
            self.driver = None
        else:
            if self.initialize_driver_func:
                # If the user provides a custom driver initialization
                self.driver = self.initialize_driver_func(self)
            else:
                # Default driver initialization (undetected-chromedriver)
                self.driver = self.default_initialize_driver()

        # ------------------------------------------
        #  Zero-Shot Classification Pipeline (Hugging Face)
        # ------------------------------------------
        # Initialize once to avoid overhead on each call.
        # Model: facebook/bart-large-mnli (english).
        # For multi-language, you might try: joeddav/xlm-roberta-large-xnli
        try:
            self.zero_shot_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            print("Zero-shot classification model loaded successfully.")
        except Exception as e:
            print(f"Warning: Could not load zero-shot model: {e}")
            self.zero_shot_classifier = None

    def default_initialize_driver(self):
        """
        Sets up a Selenium WebDriver instance using undetected-chromedriver.
        """
        import undetected_chromedriver as uc

        options = uc.ChromeOptions()
        if self.user_data_dir:
            options.add_argument(f"user-data-dir={self.user_data_dir}")
        options.add_argument("--no-first-run")
        options.add_argument("--new-window")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")

        # Simulate foreground activity
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--force-device-scale-factor=1")

        # Example user agent
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/110.0.5481.178 Safari/537.36"
        )

        temp_data_path = tempfile.mkdtemp()
        driver = uc.Chrome(options=options, user_data_dir=temp_data_path)

        try:
            driver.set_window_position(0, 0)
            driver.set_window_size(1920, 1080)
        except Exception as e:
            print(f"Failed to set window position/size: {e}")

        return driver

    def extract_page_structure(self):
        """
        Return a BeautifulSoup object of the current page.
        """
        if not self.driver:
            return None
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        return soup

    def is_captcha_present(self, soup):
        """
        Very basic check for CAPTCHAs using known patterns.
        """
        if not soup:
            return False

        captcha_selectors = [
            {'id': re.compile(r'captcha', re.I)},
            {'class': re.compile(r'captcha', re.I)},
            {'id': re.compile(r'recaptcha', re.I)},
            {'class': re.compile(r'recaptcha', re.I)},
            {'id': re.compile(r'g-recaptcha', re.I)},
            {'class': re.compile(r'g-recaptcha', re.I)},
            {'id': re.compile(r'h-captcha', re.I)},
            {'class': re.compile(r'h-captcha', re.I)},
            {'class': re.compile(r'arkose', re.I)},
            {'class': re.compile(r'cf-captcha', re.I)},
            # Additional anti-bot systems
            {'id': re.compile(r'nocaptcha', re.I)},
            {'class': re.compile(r'baxia-punish', re.I)},
            {'id': re.compile(r'nc_\d+_nocaptcha', re.I)},
            {'class': re.compile(r'nc-container', re.I)},
        ]

        for sel in captcha_selectors:
            if soup.find(attrs=sel):
                print("CAPTCHA detected based on HTML attributes.")
                return True

        # iframes
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if re.search(r'captcha|recaptcha|hcaptcha', src, re.I):
                print("CAPTCHA detected in an iframe.")
                return True

        # form actions
        forms = soup.find_all('form', action=True)
        for form in forms:
            if re.search(r'captcha', form['action'], re.I):
                print("CAPTCHA detected in form action.")
                return True

        # script sources
        scripts = soup.find_all('script', src=True)
        for script in scripts:
            if re.search(r'captcha', script['src'], re.I):
                print("CAPTCHA detected in script source.")
                return True

        # textual indicators
        text_indicators = [
            "Please slide to verify",
            "unusual traffic",
            "Sorry, we have detected unusual traffic",
            "prove you're not a robot"
        ]
        body_text = soup.body.get_text(strip=True) if soup.body else ""
        for txt in text_indicators:
            if txt.lower() in body_text.lower():
                print(f"CAPTCHA detected based on text content: '{txt}'")
                return True

        return False

    def random_delay(self, min_seconds=2, max_seconds=4):
        """
        Random sleep to mimic human-like behavior.
        """
        time.sleep(random.uniform(min_seconds, max_seconds))

    def close_driver(self):
        """
        Close the browser and print product_count (if relevant).
        """
        print("Closing the browser driver...")
        print(f"Detected {self.product_count} products.")
        if self.driver:
            self.driver.quit()

    def open_home_page(self, home_url):
        """
        Navigate to homepage and handle possible CAPTCHAs.
        """
        if not self.driver:
            return False

        try:
            print(f"Navigating to homepage: {home_url}")
            self.driver.get(home_url)
            self.random_delay()

            soup = self.extract_page_structure()
            if self.is_captcha_present(soup):
                input("Please resolve the CAPTCHA in the browser, then press ENTER here...")

            return True
        except Exception as e:
            print(f"Failed to navigate to homepage: {e}")
            return False

    def incremental_scroll_with_html_check(self, max_scrolls=10, scroll_pause_time=1):
        """
        Scroll down in increments and check if new content loads.
        """
        if not self.driver:
            return

        last_page_source = self.driver.page_source
        for scroll in range(max_scrolls):
            self.driver.execute_script("window.scrollBy(0, 2400);")
            time.sleep(random.uniform(scroll_pause_time - 0.5, scroll_pause_time + 0.5))
            current_page_source = self.driver.page_source

            if current_page_source == last_page_source:
                print(f"Scroll {scroll + 1}: No additional HTML loaded. Stopping.")
                break
            else:
                print(f"Scroll {scroll + 1}: Additional HTML detected.")
            last_page_source = current_page_source

        print("Finished scrolling.")

    ################################################################
    #  SCRAPE COMMENTS FOR A SINGLE PRODUCT
    ################################################################
    def scrape_comments_for_product(self, home_url, product_url):
        """
        1. Open home page (handle CAPTCHA)
        2. Navigate to product page
        3. Scroll to load reviews
        4. Attempt JSON-LD extraction
        5. Fallback: zero-shot classification on raw text
        """
        # 1. Home page
        if not self.open_home_page(home_url):
            print("Could not open homepage. Aborting.")
            return

        # 2. Navigate to product
        try:
            print(f"\nNavigating to product page: {product_url}")
            self.driver.get(product_url)
            self.random_delay()
        except Exception as e:
            print(f"Failed to navigate to product URL: {e}")
            return

        # Check captcha on product page
        soup = self.extract_page_structure()
        if self.is_captcha_present(soup):
            input("Please resolve the CAPTCHA on the product page, then press ENTER here...")

        # 3. Scroll to (hopefully) load all reviews
        self.incremental_scroll_with_html_check(max_scrolls=10, scroll_pause_time=1)

        # 4. Extract reviews
        page_source = self.driver.page_source
        reviews = self._extract_reviews_from_jsonld(page_source)

        if not reviews:
            reviews = self._extract_reviews_from_text_with_zeroshot(page_source)

        # 5. Print results
        if reviews:
            print("\n--- Extracted Reviews ---")
            for i, r in enumerate(reviews, 1):
                print(f"{i}. {r}")
        else:
            print("No reviews/comments found on this page.")

    ################################################################
    #  JSON-LD EXTRACTION
    ################################################################
    def _extract_reviews_from_jsonld(self, html_content):
        """
        1. Find <script type="application/ld+json"> blocks
        2. Parse them for 'review' or 'reviews'
        3. Return a list of review texts
        """
        pattern = re.compile(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            re.DOTALL | re.IGNORECASE
        )
        blocks = pattern.findall(html_content)
        if not blocks:
            return []

        all_reviews = []
        for block in blocks:
            candidates = self._split_json_objects(block.strip())
            for c in candidates:
                try:
                    data = json.loads(c)
                    # Could be a dict or list
                    if isinstance(data, dict):
                        found = self._find_reviews_in_dict(data)
                        all_reviews.extend(found)
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                found = self._find_reviews_in_dict(item)
                                all_reviews.extend(found)
                except json.JSONDecodeError:
                    continue

        return all_reviews

    def _split_json_objects(self, content):
        """
        Some sites embed multiple JSON objects in one <script> block.
        Attempt naive splitting on '}{'.
        """
        content = content.strip()
        if content.startswith('{') or content.startswith('['):
            return [content]

        segments = content.split('}{')
        json_list = []
        for i, seg in enumerate(segments):
            if i == 0:
                json_list.append(seg + '}')
            elif i == len(segments) - 1:
                json_list.append('{' + seg)
            else:
                json_list.append('{' + seg + '}')
        return json_list

    def _find_reviews_in_dict(self, data):
        """
        Recursively locate 'review' or 'reviews' keys in JSON.
        """
        results = []
        for key, value in data.items():
            if key.lower() in ["review", "reviews"]:
                # Could be dict or list
                if isinstance(value, dict):
                    txt = self._extract_review_text(value)
                    if txt:
                        results.append(txt)
                elif isinstance(value, list):
                    for rv in value:
                        txt = self._extract_review_text(rv)
                        if txt:
                            results.append(txt)
            else:
                # Recurse
                if isinstance(value, dict):
                    results.extend(self._find_reviews_in_dict(value))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            results.extend(self._find_reviews_in_dict(item))
        return results

    def _extract_review_text(self, review_obj):
        """
        Common fields in JSON-LD for reviews:
          - 'reviewBody'
          - 'description'
          - 'reviewText'
        """
        possible_fields = ['reviewBody', 'description', 'reviewText']
        for field in possible_fields:
            if field in review_obj and isinstance(review_obj[field], str):
                return review_obj[field].strip()
        return None

    ################################################################
    #  ZERO-SHOT FALLBACK
    ################################################################

    def _extract_reviews_from_text_with_zeroshot(self, html_content):
        """
        1. Remove script/style
        2. Split text into paragraphs
        3. Filter obvious ad/promo text
        4. Use zero-shot classification to keep chunks that are likely "review"
        """
        # Quick remove script/style
        text_no_scripts = re.sub(r'<script.*?>.*?</script>', '', html_content, flags=re.DOTALL)
        text_no_scripts = re.sub(r'<style.*?>.*?</style>', '', text_no_scripts, flags=re.DOTALL)

        # Remove HTML tags
        text_plain = re.sub(r'<[^>]+>', ' ', text_no_scripts)
        text_plain = re.sub(r'\s+', ' ', text_plain).strip()

        # Split into paragraphs (or sentences).
        # Adjust as needed for your domain.
        # Dot-split can be too fine-grained, but let's keep it simple:
        paragraphs = re.split(r'[.!?]\s+', text_plain)

        # Filter out obvious spam/promo paragraphs
        skip_keywords = ["why you're seeing this ad", "promoted items", "advertiser:", "sponsored"]
        def is_ad_chunk(chunk: str) -> bool:
            lower = chunk.lower()
            return any(kw in lower for kw in skip_keywords)

        candidate_chunks = []
        for p in paragraphs:
            if len(p.strip()) < 30:
                # skip short lines
                continue
            if not is_ad_chunk(p):
                candidate_chunks.append(p.strip())

        if not self.zero_shot_classifier:
            # If for some reason model didn't load, just return candidate_chunks
            print("Warning: Zero-shot model not loaded; returning candidate chunks unfiltered.")
            return candidate_chunks

        final_reviews = []
        for chunk in candidate_chunks:
            # Apply zero-shot
            result = self.zero_shot_classifier(
                chunk,
                candidate_labels=["review", "not_review"],
                multi_label=False
            )
            # We assume 'labels' is sorted by highest confidence
            top_label = result['labels'][0]
            top_score = result['scores'][0]
            # Only keep if top_label is "review" with decent confidence
            if top_label == "review" and top_score >= 0.7:
                final_reviews.append(chunk)

        return final_reviews


if __name__ == "__main__":
    # 1. Create scraper
    scraper = GeneralizedScraper(
        shopping_website="https://www.ebay.com",
        home_page="https://www.ebay.com"
    )

    # 2. Pipeline to open homepage -> open product URL -> scrape all comments
    home_url = "https://www.ebay.com"
    product_url = "https://www.ebay.com/itm/387423894005?_trkparms=amclksrc%3DITM%26aid%3D1110013%26algo%3DHOMESPLICE.SIMRXI%26ao%3D1%26asc%3D20230918095141%26meid%3Da1a8c4dc4fda48ffb8f1a3dfc529fb65%26pid%3D101843%26rk%3D2%26rkt%3D23%26itm%3D387423894005%26pmt%3D1%26noa%3D0%26pg%3D4375194%26algv%3DSimRXIV2BaseWithHPPrerankerOptimizedFilteringRVICIIEmbeddingRecall%26brand%3DUnbranded&_trksid=p4375194.c101843.m3021&itmprp=cksum%3A387423894005a1a8c4dc4fda48ffb8f1a3dfc529fb65%7Cenc%3AAQAJAAABMPIUntTq2Gv6ns2UEoKw%252B6dEe2ar%252F1a0hFj0eXUL%252FQmvyFLcIe7Isl%252BBv6BPSbBg8bufZGKmIQY7seLe03p9IC4wJJRkmxMJ695EaIrGN%252FtVWXWnkurL0JSc41%252Br4oqA0%252FOaFA1yc8hdOUbZ6Bt4T04%252BjBVySvxf8jbLaU%252BQuTHgtJZQI7S4QwvHptZ5Z6EXxttWppFvCETEstY9736BRCOgfEgFVEucrZWMCiUCSt7PI7ms8iVp7mGsU4Dwlr4rxZxhFGnn5GRveqc8aDIjPtCwoxTnYoBtPnbpL%252F%252Bic70COgPHdqVNsc0phwRdngdmE79JyG5Tm3qgRiUexp1gsUloCa2yrBItKgIOFYVOC9cQri4M3Ei%252BLzB%252FWX8NzK18Eetv2pkvBbd%252BDstRayVPaRg%253D%7Campid%3APL_CLK%7Cclp%3A4375194&itmmeta=01JGKG8TQ1992WA3K6XRRD61P4&_trkparms=parentrq%3A2704695c1940a626cd9fe5d3ffffd74a%7Cpageci%3A2fe2e456-c906-11ef-9a78-2e2a4490a4fb%7Ciid%3A1%7Cvlpname%3Avlp_homepage"  # example product

    scraper.scrape_comments_for_product(home_url, product_url)

    # 3. Close driver
    scraper.close_driver()

    # 1. Create scraper
    scraper = GeneralizedScraper(
        shopping_website="https://www.amazon.com",
        home_page="https://www.amazon.com"
    )

    # 2. Pipeline to open homepage -> open product URL -> scrape all comments
    home_url = "https://www.amazon.com"
    product_url = "https://www.amazon.com/AmazonBasics-Extra-Thick-Exercise-Carrying/dp/B01LP0U5X0/?_encoding=UTF8&pd_rd_w=kEPhA&content-id=amzn1.sym.9929d3ab-edb7-4ef5-a232-26d90f828fa5&pf_rd_p=9929d3ab-edb7-4ef5-a232-26d90f828fa5&pf_rd_r=B4BFFWFE0Z18GNTAJB5G&pd_rd_wg=UPiln&pd_rd_r=e771d60f-1763-4ae6-adea-227cce6d5f98&ref_=pd_hp_d_btf_crs_zg_bs_3375251&th=1"

    scraper.scrape_comments_for_product(home_url, product_url)

    # 3. Close driver
    scraper.close_driver()