from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from functools import wraps


def detect_captcha_detector(func):
    """
    A decorator to detect CAPTCHA challenges on a webpage and prompt the user to manually solve it.

    This decorator checks the current URL or the presence of CAPTCHA elements on the page after the wrapped function
    executes. If CAPTCHA is detected, the user is prompted to solve it manually and press Enter to continue.

    Args:
        func (function): The function to be wrapped, typically a method interacting with a web page.

    Returns:
        function: Wrapped function with added CAPTCHA detection.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs) -> any:  # 'any' return type since it wraps arbitrary functions
        # Execute the original function
        result = func(self, *args, **kwargs)

        # Check if CAPTCHA is present either by URL or elements on the page
        if "validateCaptcha" in self.driver.current_url or self.is_captcha_present():
            print("CAPTCHA detected. Please solve the CAPTCHA manually.")
            input("Once solved, press Enter to proceed: ")

        return result

    return wrapper


def normalize_price(price_str: str) -> str:
    """
    Normalize a price string by removing thousands separators and ensuring a period is used as the decimal separator.

    This function handles different formats of price strings which may contain both commas and periods in different
    countries' conventions. It ensures the string is properly formatted for further numerical processing.

    Args:
        price_str (str): The price string to be normalized.

    Returns:
        str: A normalized price string with the appropriate decimal separator.
    """
    # Remove spaces and strip any leading/trailing whitespace
    price_str = price_str.strip()

    # Both comma and period are present in the string
    if ',' in price_str and '.' in price_str:
        last_comma = price_str.rfind(',')
        last_period = price_str.rfind('.')

        # If the last comma appears after the last period, it's likely the decimal separator
        if last_comma > last_period:
            # Remove period (thousands separator) and replace comma with period (decimal separator)
            price_str = price_str.replace('.', '')
            price_str = price_str.replace(',', '.')
        else:
            # Remove comma (thousands separator)
            price_str = price_str.replace(',', '')

    # If only comma is present, assume it's the decimal separator
    elif ',' in price_str:
        price_str = price_str.replace('.', '')  # Remove any stray periods
        price_str = price_str.replace(',', '.')

    # If only period is present, assume it's already the decimal separator
    elif '.' in price_str:
        price_str = price_str.replace(',', '')  # Remove any stray commas

    # Return the cleaned price string
    return price_str


def normalize_url(base_url: str, product_url: str) -> str:
    """
    Normalize and resolve relative URLs by adding protocols if missing and cleaning up the query parameters.

    This function ensures that relative URLs are properly converted to absolute URLs based on a base URL. It also
    removes unnecessary tracking parameters from the URL query string to produce a clean, normalized URL.

    Args:
        base_url (str): The base URL to use for resolving relative URLs.
        product_url (str): The product URL, which can be absolute or relative.

    Returns:
        str: The normalized URL, or None if the input URL is invalid.
    """
    # Return None if the product_url is None or an empty string
    if not product_url:
        return None

    # If the URL doesn't start with a protocol, resolve it using the base URL
    if not product_url.startswith(('http://', 'https://')):
        product_url = urljoin(base_url, product_url)

    # Parse the URL to handle its components (path, query, etc.)
    parsed_url = urlparse(product_url)

    # Normalize the path (e.g., resolve ".." or multiple slashes)
    normalized_path = parsed_url.path

    # If the URL lacks a scheme (e.g., 'http' or 'https'), default to the base URL's scheme
    if not parsed_url.scheme:
        product_url = urljoin(base_url, product_url)

    # Parse and clean query parameters, removing tracking parameters (e.g., UTM tags)
    query_params = parse_qs(parsed_url.query)

    # Remove tracking-related parameters from the query string
    tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'gclid', 'fbclid']
    query_params = {k: v for k, v in query_params.items() if k not in tracking_params}

    # Rebuild the normalized URL with cleaned query parameters
    normalized_query = urlencode(query_params, doseq=True)
    normalized_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        normalized_path,
        parsed_url.params,
        normalized_query,
        parsed_url.fragment
    ))

    return normalized_url

