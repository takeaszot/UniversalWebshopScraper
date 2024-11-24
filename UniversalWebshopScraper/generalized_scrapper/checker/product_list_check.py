import os
from UniversalWebshopScraper.generalized_scrapper.core.product_categories import categories_products


def check_missing_products(shop_name, scraped_data_path, categories_products):
    """
    Checks for missing products in the scraped data for a specific shop.

    This function compares the list of expected products for each category in a shop
    against the CSV files available in the respective category folders. It identifies
    categories and products that are either missing or incomplete.

    Parameters:
    - shop_name (str): The name of the shop (e.g., 'aliexpress').
    - scraped_data_path (str): The base path where the scraped data is stored.
    - categories_products (dict): A dictionary where keys are category names (str)
      and values are lists of expected product names (list of str).

    Returns:
    - missing_products (dict): A dictionary of missing products organized by category.
      Each key is a category name, and the value is a list of missing product names.
    """
    missing_products = {}

    # Iterate through each category and its associated products
    for category, products in categories_products.items():
        # Construct the full path to the category folder
        category_path = os.path.join(scraped_data_path, shop_name, category)

        # Debugging: Print the path being checked for clarity
        print(f"Checking path: {category_path}")

        # Check if the category folder exists
        if not os.path.exists(category_path):
            print(f"Category folder '{category}' not found in shop '{shop_name}'.")
            # If the folder doesn't exist, consider all products in the category as missing
            missing_products[category] = products
            continue

        # Get a list of available files (without extensions) in the category folder
        scraped_files = [os.path.splitext(file)[0] for file in os.listdir(category_path) if file.endswith(".csv")]

        # Identify products in the category that are not found in the scraped files
        missing_in_category = [product for product in products if product not in scraped_files]

        # If any products are missing, add them to the missing_products dictionary
        if missing_in_category:
            missing_products[category] = missing_in_category

    return missing_products

def generate_missing_products_file(shop_name, scraped_data_path, categories_products, output_file):
    """
    Generates a Python dictionary of missing products for each category.

    Parameters:
    - shop_name (str): The name of the shop (e.g., 'aliexpress').
    - scraped_data_path (str): The base path where the scraped data is stored.
    - categories_products (dict): A dictionary where keys are category names (str)
      and values are lists of expected product names (list of str).
    - output_file (str): The path to the file where the missing products dictionary should be saved.

    Returns:
    None
    """
    missing_products = {}

    # Iterate through each category and its associated products
    for category, products in categories_products.items():
        # Construct the full path to the category folder
        category_path = os.path.join(scraped_data_path, shop_name, category)

        # Check if the category folder exists
        if not os.path.exists(category_path):
            # If the folder doesn't exist, consider all products in the category as missing
            missing_products[category] = products
            continue

        # Get a list of available files (without extensions) in the category folder
        scraped_files = [os.path.splitext(file)[0] for file in os.listdir(category_path) if file.endswith(".csv")]

        # Identify products in the category that are not found in the scraped files
        missing_in_category = [product for product in products if product not in scraped_files]

        # If any products are missing, add them to the missing_products dictionary
        if missing_in_category:
            missing_products[category] = missing_in_category

    # Save the missing products dictionary to the specified output file
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("# Missing Products\n")
        file.write("categories_products = " + str(missing_products))

if __name__ == "__main__":
    # Identify the current working directory of the script
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the base path for the scraped data folder relative to the current directory
    scraped_data_path = os.path.join(current_dir, "../../../../Data/scrapped_data")

    # Specify the shop name to check (e.g., 'aliexpress')
    shop_name = "aliexpress"

    # Output file to save the missing products dictionary
    output_file = os.path.join(current_dir, "missing_products.py")

    # Perform the check for missing products and generate the file
    generate_missing_products_file(shop_name, scraped_data_path, categories_products, output_file)

    print(f"Missing products file generated: {output_file}")

