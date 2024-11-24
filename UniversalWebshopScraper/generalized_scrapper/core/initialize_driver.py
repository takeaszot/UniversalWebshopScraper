import undetected_chromedriver as uc
import tempfile

def initialize_driver_single(self):
    """
    Initialize the Chrome driver with necessary options for avoiding CAPTCHA detection.
    Returns:
        driver: The initialized Chrome driver with customized options.
    """
    options = uc.ChromeOptions()
    user_data_dir = r"---"
    profile = "Profile 2"
    options.add_argument(f"user-data-dir={user_data_dir}")
    options.add_argument(f"profile-directory={profile}")
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = uc.Chrome(options=options)
    return driver

def initialize_driver_base(self):
    """
    Sets up a Selenium WebDriver instance using undetected-chromedriver, configured
    to avoid detection on sites with anti-bot measures and simulate foreground behavior.

    This method configures Chrome options for stealth browsing, disables throttling,
    and enforces dynamic content rendering even in the background.

    Returns:
        WebDriver: A configured instance of undetected-chromedriver's Chrome WebDriver.
    """
    import undetected_chromedriver as uc

    # Set up Chrome options to avoid detection
    options = uc.ChromeOptions()

    # User data directory for separate profiles
    options.add_argument(f"user-data-dir={self.user_data_dir}")
    options.add_argument("--no-first-run")
    options.add_argument("--new-window")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")

    # Prevent throttling and simulate foreground activity
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--force-device-scale-factor=1")

    # Optional: Enable debugging to analyze behavior
    # options.add_argument("--remote-debugging-port=9222")

    # Optional: Set a user-agent string to simulate a real browser
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.178 Safari/537.36"
    )

    # Create a unique temporary directory for undetected_chromedriver data_path
    temp_data_path = tempfile.mkdtemp()

    # Initialize Chrome driver with the specified options and unique data_path
    driver = uc.Chrome(options=options, user_data_dir=temp_data_path)

    # Move browser window to the foreground by simulating activity
    try:
        driver.set_window_position(0, 0)  # Move to top-left corner of the screen
        driver.set_window_size(1920, 1080)  # Set window size to ensure visibility
    except Exception as e:
        print(f"Failed to move browser to the foreground: {e}")

    return driver
