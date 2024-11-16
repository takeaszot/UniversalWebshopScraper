import pytest
from UniversalWebshopScraper.generalized_scrapper.core.generalized_scrapper import GeneralizedScraper
from UniversalWebshopScraper.generalized_scrapper.core.functions import normalize_price, normalize_url

# Test cases for normalize_price
@pytest.mark.parametrize("input_price, expected_output", [
    ("1,999.00", "1999.00"),  # US format
    ("1.999,25", "1999.25"),  # European format
    ("2,499.00", "2499.00"),  # US format
    ("2.499,00", "2499.00"),  # European format
    ("2499,00", "2499.00"),
    ("2499.00", "2499.00"),
    ("1,234.56", "1234.56"),  # US format
    ("9,25", "9.25"),         # Small value with comma as decimal separator
    ("9.25", "9.25"),         # Small value with period as decimal separator
])
def test_normalize_price(input_price, expected_output):
    assert normalize_price(input_price) == expected_output

# Test cases for normalize_url
@pytest.mark.parametrize("base_url, product_url, expected_output", [
    ("https://example.com", "/product/123", "https://example.com/product/123"),
    ("https://example.com", "https://other.com/product/123", "https://other.com/product/123"),
    ("https://example.com", "product/123", "https://example.com/product/123"),
    ("https://example.com", "", None),
    ("https://example.com", None, None),
])

def test_normalize_url(base_url, product_url, expected_output):
    assert normalize_url(base_url, product_url) == expected_output
