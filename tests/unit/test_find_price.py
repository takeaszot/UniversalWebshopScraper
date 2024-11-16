import pytest
from bs4 import BeautifulSoup
from UniversalWebshopScraper.generalized_scrapper.core.generalized_scrapper import GeneralizedScraper


@pytest.fixture
def scraper():
    """
    Create an instance of the GeneralizedScraper class in offline mode for testing.
    """
    return GeneralizedScraper(offline_mode=True)


@pytest.mark.parametrize(
    "html_input, expected_price",
    [
        # Test case 1: Single block with a price
        (
            """<div><span>100</span><span>.99</span><span>$</span></div>""",
            "100.99$"
        ),
        # Test case 2: Noise text with price
        (
            """<div><span>Inteligentne zegarki Fitness Tracker IP 68,</span><span>100</span><span>$</span></div>""",
            "100$"
        ),
        # Test case 3: Complex price format
        (
            """<div><span>Special offer: </span><span>1,000</span><span>.50</span><span>USD</span></div>""",
            "1,000.50USD"
        ),
        # Test case 4: No price present
        (
            """<div><span>No price available</span></div>""",
            None
        ),
        # Test case 5: real-world example with price
        (
            """<div class="msa3_z4 m3h2_8"><span aria-label="437,70&nbsp;zł aktualna cena" tabindex="0"><span class="mli8_k4 msa3_z4 mqu1_1 mp0t_ji m9qz_yo mgmw_qw mgn2_27 mgn2_30_s">437,<span class="mgn2_19 mgn2_21_s m9qz_yq">70</span>&nbsp;<span class="mgn2_19 mgn2_21_s m9qz_yq">zł</span></span></span></div>""",
            "437,70zł"
        ),
    ],
)

def test_find_price(scraper, html_input, expected_price):
    """
    Test the find_price function from GeneralizedScraper.
    """
    soup = BeautifulSoup(html_input, "html.parser")
    block = soup.div  # Assume we're testing the <div> block

    # Call the find_price function
    detected_price = scraper.find_price(block)

    # Assert the output matches the expected price
    assert detected_price == expected_price
