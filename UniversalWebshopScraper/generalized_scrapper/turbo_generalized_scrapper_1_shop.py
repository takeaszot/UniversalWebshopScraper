import os
import tempfile
import pandas as pd
from multiprocessing import Process, Manager, set_start_method
from UniversalWebshopScraper.generalized_scrapper.generalized_scrapper import GeneralizedScraper
import time

def run_scraper(site_info, categories_amazon_products, detected_image_urls, user_data_dir, shared_stored_products, worker_id, n_workers):
    # Initialize the scraper once per worker
    scraper = GeneralizedScraper(shopping_website=site_info["home_url"], user_data_dir=user_data_dir)
    scraper.detected_image_urls = detected_image_urls  # Use shared list

    if not scraper.open_home_page(site_info["home_url"]):
        print(f"[ERROR] Worker {worker_id}: Failed to open home page for {site_info['name']}")
        return

    print(f"***** Worker {worker_id} started for {site_info['name']} *****")

    for category, products in categories_amazon_products.items():
        print(f"Worker {worker_id} starting category: {category}")

        # Split the product list across all workers using worker_id and n_workers
        product_chunk = products[worker_id::n_workers]

        for product in product_chunk:
            print(f"Worker {worker_id} searching for product: {product}")
            search_url = site_info["search_url_template"].format(
                base_url=site_info["home_url"], query=product.replace(" ", "+"), page_number="{page_number}"
            )

            scraper.open_search_url(search_url.format(page_number=1))
            scraper.scrape_all_products(scroll_based=False, url_template=search_url, page_number_supported=True)

        # Append the results of this worker to the shared list
        shared_stored_products.extend(scraper.stored_products)
        scraper.stored_products = []  # Clear stored products for the next category

        print(f"***** Worker {worker_id} finished category {category} for {site_info['name']} *****")

    print(f"Worker {worker_id}: Closing Chrome driver...")
    scraper.close_driver()  # Close the driver after all categories are done

def main_scraper(site_info, categories_amazon_products, n_workers=2):
    manager = Manager()
    detected_image_urls = manager.list()  # Shared list across processes
    shared_stored_products = manager.list()  # Shared list to gather products across workers

    processes = []
    for i in range(n_workers):
        # Create a unique temporary directory for each Chrome instance
        temp_dir = tempfile.mkdtemp()
        print(f"[INFO] Created temporary directory for Chrome instance: {temp_dir}")

        process = Process(
            target=run_scraper,
            args=(site_info, categories_amazon_products, detected_image_urls, temp_dir, shared_stored_products, i, n_workers)
        )
        processes.append(process)
        process.start()

        time.sleep(2)

    # Wait for all worker processes to complete
    for process in processes:
        process.join()

    # After all workers complete, save the collected results for each category
    site_save_path = os.path.join('./scraped_data', site_info["name"].lower())
    os.makedirs(site_save_path, exist_ok=True)

    for category in categories_amazon_products.keys():
        # Filter out only the products for this category
        category_products = [product for product in shared_stored_products if product.get("Category") == category]

        if category_products:
            category_save_path = os.path.join(site_save_path, f"{category.replace(' ', '_')}.csv")
            df = pd.DataFrame(category_products)
            df.to_csv(category_save_path, index=False)
            print(f"Saved {len(category_products)} products for category {category} to {category_save_path}")

if __name__ == "__main__":
    set_start_method("spawn", force=True)

    shopping_sites = [
        {"name": "ebay", "home_url": "https://www.ebay.com", "search_url_template": "{base_url}/sch/i.html?_nkw={query}&_pgn={{page_number}}"}
    ]

    categories_products = {
    "Electronics": [
        "Wireless Bluetooth Earbuds", "4K UHD Smart TV", "Noise-Cancelling Headphones",
        "Portable Power Bank", "Smartphone with Triple Camera", "Smartwatch with Fitness Tracker",
        "Laptop with Intel i7", "Wireless Charging Pad", "Bluetooth Speaker", "Digital Camera",
        "Home Security Camera", "VR Headset", "External Hard Drive", "Gaming Mouse",
        "Mechanical Gaming Keyboard", "Wi-Fi 6 Router", "4K Action Camera", "USB-C Hub",
        "Portable SSD", "Gaming Headset", "Tablet with Stylus", "Streaming Stick",
        "Smart Light Bulbs", "Drone with 4K Camera", "Smart Doorbell", "Fitness Tracker",
        "Wireless HDMI Adapter", "Bluetooth Car Adapter", "Smart Thermostat",
        "Electric Scooter", "Video Doorbell", "USB-C Fast Charger", "Phone Gimbal",
        "Digital Photo Frame", "Smart Display", "Smart Speaker", "Waterproof Bluetooth Speaker",
        "Gaming Console", "Graphics Card", "1080p Webcam", "Portable Projector",
        "E-Reader", "Smart Glasses", "Smart Plug", "Electric Skateboard",
        "Robotic Vacuum Cleaner", "Dash Cam", "Bluetooth Transmitter", "Fitness Smart Scale",
        "Mini Drone", "Wireless Earphones", "Solar Charger", "Monitor Stand", "Wireless Mouse",
        "Smartphone Gimbal Stabilizer", "Laptop Cooling Pad", "Smart Body Weight Scale",
        "Digital Alarm Clock", "USB Flash Drive", "Car Phone Mount", "Portable DVD Player",
        "Video Game Controller", "HDMI Splitter", "Car Backup Camera", "Bluetooth Headset",
        "Electric Toothbrush", "Laser Printer", "Portable Fan", "Bluetooth Keyboard",
        "Gaming Monitor", "Smart Key Finder", "Smartwatch Bands", "Gaming Chair",
        "Portable Hard Drive", "Phone Charging Stand", "Tripod for Smartphones",
        "Smart Lock", "3D Printer", "Portable Charger", "Camera Lens Kit",
        "Bluetooth Audio Receiver", "Wi-Fi Range Extender", "Smart LED Strip Lights",
        "Smart Garage Door Opener", "Car Dash Mount", "Home Theater System",
        "Laptop Backpack", "Wireless Presenter", "Fitness Smartwatch",
        "Digital Piano", "Electric Bike", "Smart Bulb Socket", "Virtual Assistant Speaker",
        "Security Camera System", "Memory Card", "Noise Cancelling Earbuds",
        "Home Automation Hub", "Cordless Phone", "Action Camera Accessories",
        "Wi-Fi Extender", "Power Bank with Solar Charger"
    ],

    "Home & Kitchen": [
        "Memory Foam Mattress", "Air Fryer", "Electric Pressure Cooker",
        "Stand Mixer", "Robot Vacuum", "Non-Stick Cookware Set", "Cast Iron Skillet",
        "Electric Kettle", "Coffee Maker", "Water Filter Pitcher", "Blender",
        "Refrigerator Organizer Bins", "Silicone Baking Mats", "Food Processor",
        "Cordless Stick Vacuum", "Weighted Blanket", "Essential Oil Diffuser",
        "Portable Air Conditioner", "Espresso Machine", "Microwave Oven", "Waterproof Mattress Protector",
        "Ceramic Bakeware Set", "Cotton Bed Sheets", "Stainless Steel Knife Set",
        "Smart Thermostat", "Touchless Soap Dispenser", "French Press Coffee Maker",
        "Indoor Herb Garden Kit", "Bamboo Cutting Board", "Reusable Silicone Food Bags",
        "Cast Iron Dutch Oven", "Double Walled Insulated Mug", "Electric Griddle",
        "Wall-Mounted Pot Rack", "Automatic Pet Feeder", "Salt Lamp", "Food Storage Container Set",
        "Silicone Cooking Utensils", "Ceiling Fan with Remote", "Glass Water Bottle",
        "Laundry Hamper with Lid", "Electric Wine Opener", "Stainless Steel Mixing Bowls",
        "Digital Meat Thermometer", "Smart WiFi Air Purifier", "Reusable Beeswax Food Wraps",
        "Adjustable Standing Desk", "Rolling Kitchen Island", "Bathroom Organizer Tray",
        "Cold Brew Coffee Maker", "Handheld Steamer", "Smart LED Ceiling Light",
        "Wireless Vacuum Cleaner", "Ceramic Mug Warmer", "Bamboo Bathtub Tray",
        "Stainless Steel Water Pitcher", "Portable Ice Maker", "Electric Milk Frother",
        "Insulated Lunch Bag", "Adjustable Bed Frame", "Collapsible Laundry Basket",
        "Wine Rack", "Portable Heater", "Cordless Stick Blender", "Bamboo Drawer Organizer",
        "Microwaveable Food Containers", "Electric Salt and Pepper Grinder",
        "Wool Dryer Balls", "Stainless Steel Trash Can", "Silicone Oven Mitts",
        "Indoor Plant Watering Can", "Electric Can Opener", "Smart Light Switch",
        "Weighted Eye Mask", "Non-Slip Kitchen Rug", "Stainless Steel Straws",
        "Electric Blanket", "Under-Sink Water Filter", "Silicone Baking Cups",
        "Dish Drying Rack", "Automatic Hand Soap Dispenser", "Toaster Oven",
        "Floor Lamp with Shelves", "Thermal Blackout Curtains", "Reversible Duvet Cover",
        "Stainless Steel Bread Box", "Insulated Water Bottle", "Wall Mounted Spice Rack",
        "Automatic Coffee Grinder", "Electric Hand Mixer", "Bamboo Shower Mat",
        "Smart Light Dimmer", "Portable Washing Machine", "Stainless Steel Whisk",
        "Tabletop Fire Pit", "Bamboo Charcoal Air Purifying Bags", "Wine Aerator",
        "Electric Crepe Maker", "Double Waffle Maker", "Smart WiFi Humidifier",
        "Digital Kitchen Scale", "Adjustable Table Lamp"
    ],

    "Sports & Outdoors": [
        "Yoga Mat", "Dumbbell Set", "Camping Tent", "Hiking Backpack", "Mountain Bike",
        "Resistance Bands", "Foam Roller", "Portable Hammock", "Fitness Tracker Watch",
        "Waterproof Hiking Boots", "Cycling Helmet", "Portable Grill", "Sleeping Bag",
        "Kayak", "Camping Stove", "Treadmill", "Hiking Poles", "Bicycle Pump",
        "Fitness Jump Rope", "Running Shoes", "Inflatable Paddle Board",
        "Outdoor Smart Watch", "Hydration Pack", "Bicycle Phone Mount", "Ski Goggles",
        "Swimming Fins", "Adjustable Weight Bench", "Electric Scooter", "Tennis Racket",
        "Punching Bag", "Elliptical Machine", "Golf Club Set", "Outdoor Table Tennis Set",
        "Surfboard", "Weightlifting Gloves", "Soccer Ball", "Outdoor Sleeping Pad",
        "Bow and Arrow Set", "Volleyball Net", "Climbing Rope", "Ski Jacket",
        "Tennis Ball Machine", "Portable Basketball Hoop", "Electric Skateboard",
        "Mountain Bike Helmet", "Outdoor Fitness Tracker", "Camping Cooler",
        "Thermal Water Bottle", "Adjustable Dumbbell", "Portable Solar Charger",
        "Sleeping Bag Liner", "Smart Bike Lock", "Waterproof Bluetooth Speaker",
        "Fitness Tracker Band", "Camping Lantern", "Hiking Socks", "Outdoor Canopy Tent",
        "Tactical Flashlight", "Waterproof Jacket", "Electric Bike", "Fishing Rod",
        "Electric Air Pump", "Golf Bag", "Running Hydration Belt", "Foldable Kayak",
        "Portable Fire Pit", "Hiking GPS Device", "Adjustable Weight Vest",
        "Snorkel Set", "Camping Air Mattress", "Rock Climbing Shoes",
        "Foam Pool Float", "Tennis Ball Hopper", "Electric Skateboard Remote",
        "Bike Repair Kit", "Swim Cap", "Portable Sun Shelter", "Camping Chair",
        "Bowling Ball", "Electric Scooter Helmet", "Outdoor Sleeping Cot",
        "Archery Set", "Waterproof Phone Pouch", "Surfboard Leash",
        "Adjustable Ski Poles", "Smart Bike Helmet", "Kayak Paddle",
        "Inflatable Sofa", "Outdoor Basketball", "Tennis Ball Launcher",
        "Portable Oxygen Monitor", "Cycling Water Bottle", "Rock Climbing Harness",
        "Outdoor Fitness Tracker", "Camping Cookware Set", "Portable Fire Starter",
        "Rugged GPS Watch", "Climbing Carabiners", "Running GPS Watch", "Inflatable Snow Tube"
    ],
    "Toys & Games": [
        "Building Block Set", "Remote Control Car", "Puzzle Board Game",
        "Plush Stuffed Animal", "Action Figure Set", "LEGO Building Kit",
        "Interactive Robot Toy", "Board Game for Kids", "Dollhouse with Furniture",
        "Toy Train Set", "Electric Ride-On Car", "Kite with String",
        "Foam Dart Blaster", "Musical Instrument Toy", "Play-Doh Modeling Compound",
        "Educational Flash Cards", "Toy Kitchen Set", "Magic Tricks Set",
        "Remote Control Drone", "Bubble Blower Machine", "Magnetic Building Blocks",
        "Waterproof Art Easel", "Outdoor Playhouse", "Kids Bowling Set",
        "Walkie Talkies for Kids", "Toy Doctor Kit", "Glow in the Dark Stars",
        "Toy Car Garage", "Stuffed Animal Storage Bean Bag", "RC Helicopter",
        "Toy Construction Vehicles", "Wooden Train Set", "Action Hero Playset",
        "Play Tent with Tunnel", "Dinosaur Action Figures", "Finger Painting Set",
        "Interactive Talking Book", "Ball Pit with Balls", "Inflatable Pool Toy",
        "Mini Golf Set for Kids", "Pretend Play Tool Set", "Kids' Science Experiment Kit",
        "Toy Basketball Hoop", "Toy Cash Register", "Electric Toy Guitar",
        "Toy Race Car Track", "Wooden Puzzle Blocks", "Toy Story Action Figures",
        "Kid's Microscope Set", "Aquatic Animal Bath Toys", "Play Kitchen Food Set",
        "Kids Learning Tablet", "Magic Wand with Lights", "Educational Globe",
        "Toy Pirate Ship", "Junior Archery Set", "Toy Airplane Kit",
        "Marble Run Set", "Interactive Pet Robot", "Toy Boat for Bath",
        "Balance Bike for Kids", "Kids Trampoline", "Toy Popcorn Machine",
        "Toy Drum Set", "STEM Building Kit", "Finger Puppets Set",
        "Toy Construction Tools", "Tic Tac Toe Game", "Slime Making Kit",
        "Toy Cement Mixer", "Toy Boat with Remote Control", "Toy Cash Register with Scanner",
        "Wooden Dollhouse Furniture", "Interactive Baby Doll", "Pretend Grocery Store",
        "Bouncy Castle with Blower", "Kids Walkie Talkie Set", "Toy Ice Cream Truck",
        "Toy Train Table", "Toy Pirate Playset", "RC Monster Truck",
        "Kids' Playhouse Tent", "Toy Ambulance Set", "Toy Castle Building Blocks",
        "Toy Firefighter Gear", "Kids' Karaoke Microphone", "Toy Police Car with Lights",
        "Plastic Dinosaur Figures", "Playdough Set with Molds", "Rock Painting Kit",
        "Toy Helicopter with Remote", "Water Balloon Launcher", "Card Game for Kids",
        "Toy Soldier Set", "Toy Construction Crane", "Toy Robot Dog",
        "Superhero Cape and Mask Set", "Toy Garbage Truck", "Pretend Doctor's Bag",
        "Toy Airplane with Lights", "Alphabet Learning Blocks", "Toy Garage Playset",
        "Electric Toy Train", "Toy Pirate Treasure Chest"
    ],

    "Health & Personal Care": [
        "Electric Toothbrush", "Massage Gun", "Water Flosser",
        "Digital Blood Pressure Monitor", "Infrared Thermometer", "Essential Oil Diffuser",
        "Organic Vitamin C Serum", "Reusable Face Mask", "Sleep Sound Machine",
        "Electric Foot Massager", "Fitness Tracker", "Portable Massage Chair",
        "Electric Hair Clipper", "Orthopedic Memory Foam Pillow", "Teeth Whitening Kit",
        "Reusable Heat Therapy Pads", "Hair Growth Serum", "Electric Scalp Massager",
        "Weighted Blanket", "Body Fat Scale", "Electric Shaver", "Aromatherapy Diffuser",
        "Eyebrow Trimmer", "Anti-Aging Face Cream", "Heating Pad for Back Pain",
        "Blood Glucose Monitor", "Silicone Face Scrubber", "Rejuvenating Face Mask",
        "Handheld Electric Massager", "Hydrating Face Mist", "Compression Socks",
        "Orthotic Insoles", "Natural Deodorant", "Pain Relief Gel", "Sleep Mask with Earplugs",
        "Organic Shampoo and Conditioner", "Wireless Hair Trimmer", "Moisturizing Hand Cream",
        "Personal Humidifier", "Reusable Makeup Remover Pads", "Electric Hair Brush",
        "Organic Sunscreen Lotion", "Acupressure Mat", "Adjustable Posture Corrector",
        "LED Light Therapy Mask", "Electric Tooth Polisher", "Anti-Snoring Device",
        "Wireless Ear Thermometer", "Smart Scale with App", "Hair Straightening Brush",
        "Portable Oxygen Concentrator", "UV Light Sanitizer Wand", "All-Natural Sleep Aid",
        "Deep Tissue Massage Gun", "Collagen Peptide Powder", "Organic Face Toner",
        "Cordless Water Flosser", "Adjustable Neck Brace", "Organic Body Scrub",
        "Smartphone UV Sanitizer", "Magnesium Supplement", "Foot Callus Remover",
        "Wireless Neck Massager", "Reusable Ice Pack", "Adjustable Knee Brace",
        "Portable Air Purifier", "Silk Sleep Mask", "Electric Head Massager",
        "Memory Foam Bath Pillow", "Nasal Irrigation System", "All-Natural Hand Sanitizer",
        "Cordless Handheld Massager", "Vitamin D3 Supplement", "Magnetic Posture Brace",
        "Detox Foot Pads", "Organic Essential Oils Set", "TENS Unit Muscle Stimulator",
        "Foam Roller for Muscle Recovery", "Caffeine Eye Cream", "Memory Foam Travel Pillow",
        "Cordless Hair Dryer", "Portable Hair Curler", "Organic Beard Oil",
        "Foot Spa with Heat", "Reusable Silicone Earplugs", "Organic Lip Balm Set",
        "Posture Support Cushion", "Organic Coconut Oil", "Smart Sleep Tracker",
        "Electric Body Brush", "Reusable Face Shields", "Digital Pregnancy Test",
        "Electric Callus Remover", "Anti-Wrinkle Serum", "Copper Infused Compression Gloves",
        "Painless Hair Removal Cream", "Waterproof Cast Cover", "Vitamin B12 Supplement",
        "Electric Nose Hair Trimmer", "Electric Back Scratcher", "Portable Steam Inhaler",
        "Massage Pillow", "Acne Treatment Light Therapy"
    ],

    "Automotive": [
        "Dash Cam", "Car Vacuum Cleaner", "Portable Jump Starter",
        "Bluetooth FM Transmitter", "Car Phone Mount", "Tire Pressure Gauge",
        "Seat Cushion for Car", "Car Wash Kit", "Digital Tire Inflator",
        "Wireless Backup Camera", "Car Floor Mats", "Leather Car Seat Covers",
        "Windshield Sun Shade", "Portable Air Compressor", "Car Emergency Kit",
        "Car Battery Charger", "Trunk Organizer", "Car Cover", "Car Cleaning Gel",
        "OBD2 Scanner", "LED Headlight Bulbs", "Car Trash Can", "Windshield Repair Kit",
        "Portable Car Fridge", "Smart Key Finder", "Car Dash Mount Holder",
        "Steering Wheel Cover", "Sun Visor Organizer", "Car Seat Gap Filler",
        "Car Seatbelt Adjuster", "Hydraulic Jack", "Portable Tire Inflator",
        "Car Window Breaker Tool", "Car Bluetooth Adapter", "Magnetic Car Phone Holder",
        "Car Polishing Kit", "Car Battery Jump Starter", "Smart Car Charger",
        "Portable Tire Inflator with Gauge", "Car Diagnostic Tool", "Car Seat Massager",
        "Car Air Purifier", "Car Cigarette Lighter Splitter", "Car Trunk Storage Box",
        "Car Dent Repair Kit", "LED Car Interior Lights", "Car Detailing Kit",
        "Universal Car Seat Cushion", "Car Windshield Cleaner", "Car Roof Cargo Box",
        "Car Power Inverter", "Auto Glass Cleaner", "Car Scratch Remover",
        "Leather Cleaner for Car Seats", "GPS Navigation System", "Car Mirror Dash Cam",
        "Car Window Sunshade", "Car Vacuum with LED Light", "Car Windshield Snow Cover",
        "Car Seat Protector Mat", "Digital Air Pressure Gauge", "Car Tablet Mount",
        "Rearview Mirror Camera", "Car Bluetooth Speaker", "Car Seat Back Organizer",
        "Tire Inflator with LED Light", "Car Battery Tester", "Keyless Car Remote",
        "USB Car Charger", "Smart Keyless Entry System", "Car Windshield Defroster",
        "Car Tire Pump", "Car Paint Protection Film", "Car Radar Detector",
        "Car Headlight Restoration Kit", "Portable Car Battery Jump Starter",
        "Car Seat Back Hook", "Car Diagnostic Scanner", "Car Smartphone Holder",
        "Car Seat Gap Organizer", "Portable Car Vacuum Cleaner", "Wireless Car Charger",
        "Car GPS Tracker", "Car Phone Charger", "Car Sun Visor Extender",
        "Car Cup Holder Expander", "Tire Pressure Monitoring System",
        "Magnetic Phone Mount", "Car Window Tint Kit", "Car Organizer Tray"
    ],

    "Beauty": [
    "Face Cream", "Lip Balm", "Body Lotion", "Hair Serum", "Face Mask", "Eyeliner Pen",
    "Nail Polish", "Makeup Remover", "Hair Mousse", "Blush Powder", "Eyeshadow Palette",
    "Makeup Brush Set", "Face Scrub", "Hand Cream", "Foundation Liquid", "Lipstick",
    "Lip Gloss", "Makeup Primer", "Highlighter Stick", "Concealer", "Facial Toner",
    "Brow Pencil", "Shampoo", "Conditioner", "Hair Oil", "Body Wash", "Fragrance Mist",
    "Perfume", "Sunblock Lotion", "Tinted Moisturizer", "Facial Cleanser", "Hair Straightener",
    "Hair Dryer", "Curling Iron", "Face Serum", "Eye Cream", "Makeup Sponge",
    "Exfoliating Pads", "Face Mist", "Deodorant", "Cuticle Oil", "Hair Spray",
    "Eyebrow Gel", "Lip Scrub", "Facial Oil", "Sheet Mask", "Facial Roller",
    "Clay Mask", "Shaving Cream", "Razors", "Beard Oil", "Pore Strips",
    "Body Scrub", "Hair Mask", "BB Cream", "CC Cream", "Detangling Spray",
    "Dry Shampoo", "Scalp Scrub", "Hair Clips", "Hairbrush", "Nail File",
    "Cuticle Trimmer", "False Eyelashes", "Eyelash Curler", "Eyebrow Stencil",
    "Face Sponge", "Tweezers", "Foot Cream", "Body Butter", "Hair Tie",
    "Lip Liner", "Face Peeling Gel", "Body Exfoliator", "Hot Rollers",
    "Hair Extensions", "Leave-in Conditioner", "Heat Protectant Spray", "Nail Buffer",
    "Lip Plumper", "Body Powder", "Hydrating Mist", "Facial Peel",
    "Nail Strengthener", "Hair Removal Wax", "Self-Tanner", "Bronzer",
    "Body Oil", "Antibacterial Soap", "Facial Steamer", "Hair Growth Serum",
    "Stretch Mark Cream", "Tattoo Balm", "Face Wipes", "Aftershave",
    "Whitening Strips", "Nail Clippers", "Hair Perfume", "Body Mist",
    "Makeup Setting Spray", "Makeup Organizer", "Hair Detangler", "Nail Art Kit"
    ],

    "Garden & Outdoors": [
        "Garden Hose", "Lawn Mower", "Plant Pots", "Outdoor String Lights", "Fertilizer",
        "Garden Trowel", "Pruning Shears", "Watering Can", "Patio Umbrella", "Outdoor Grill",
        "Garden Gloves", "Lawn Chair", "BBQ Tools", "Solar Garden Lights", "Plant Soil",
        "Flower Seeds", "Weed Killer", "Wheelbarrow", "Outdoor Fire Pit", "Bird Feeder",
        "Garden Kneeler", "Garden Rake", "Hedge Trimmer", "Lawn Edger", "Garden Sprinkler",
        "Leaf Blower", "Outdoor Storage Box", "Patio Heater", "Mosquito Repellent",
        "Garden Netting", "Seed Starter Kit", "Compost Bin", "Plant Stand", "Outdoor Fountain",
        "Hammock", "Garden Stakes", "Garden Fence", "Planter Box", "Outdoor Sofa",
        "Rain Barrel", "Garden Scissors", "Potting Bench", "Garden Trellis", "Patio Set",
        "Outdoor Rug", "Garden Statue", "Bird Bath", "Watering Wand", "Outdoor Lanterns",
        "Garden Shovel", "Raised Garden Bed", "Outdoor Fan", "Leaf Rake", "Patio Table",
        "Outdoor Cushions", "Garden Arch", "Lawn Fertilizer", "Tree Pruner", "Garden Thermometer",
        "Outdoor Bench", "Pest Control Spray", "Garden Hoe", "Greenhouse Kit", "Garden Cart",
        "Garden Shed", "Outdoor Timer", "Patio Awning", "Garden Spade", "Fountain Pump",
        "Landscape Fabric", "Outdoor Daybed", "Garden Fork", "Patio Gazebo", "Planter Hooks",
        "Orchid Potting Mix", "Hose Nozzle", "Bird House", "Outdoor Swing", "Patio Gazebo",
        "Wind Chimes", "Outdoor Wall Art", "Rain Gauge", "Garden Lights", "Firewood Rack",
        "Lawn Sweeper", "Garden Markers", "Garden Irrigation System", "Hose Reel", "Garden Bench",
        "Plant Labels", "Outdoor Playset", "Garden Border", "Outdoor Cooler", "Sun Shade Sail",
        "Grass Seed", "Garden Tiller", "Patio Curtains", "Patio Storage Chest", "Terrarium Kit"
    ],

    "Tools & Home Improvement": [
        "Cordless Drill", "Screwdriver Set", "Hammer", "Tape Measure", "Stud Finder",
        "Power Saw", "Socket Wrench Set", "Level Tool", "Safety Glasses", "Ladder",
        "Toolbox", "Flashlight", "Allen Wrench Set", "Drill Bits", "Work Gloves",
        "Pliers Set", "Adjustable Wrench", "Electric Sander", "Circular Saw", "Multimeter",
        "Pipe Wrench", "Voltage Tester", "Staple Gun", "Crowbar", "Nail Gun",
        "Utility Knife", "Tile Cutter", "Angle Grinder", "Air Compressor", "Measuring Tape",
        "Wire Stripper", "Chisel Set", "Claw Hammer", "Heat Gun", "Power Screwdriver",
        "Caulking Gun", "Handsaw", "Wood Glue", "Metal Detector", "Work Apron",
        "Paint Roller", "Extension Cord", "Sledgehammer", "Cordless Impact Driver", "Nail Set",
        "Putty Knife", "Shop Vacuum", "Tool Belt", "Laser Level", "Dremel Tool",
        "Sandpaper Set", "Bolt Cutter", "Paint Sprayer", "Work Light", "Socket Set",
        "Paint Tray", "Measuring Wheel", "Pipe Cutter", "Drywall Saw", "Angle Clamp",
        "Wire Brush", "Hex Key Set", "Drill Press", "Electric Screwdriver", "Reciprocating Saw",
        "Adjustable Pliers", "Welding Helmet", "Jigsaw", "Torque Wrench", "Workbench",
        "Plumb Bob", "Cordless Grinder", "Chalk Line", "Extension Ladder", "Wood Chisel",
        "Ratchet Set", "Welding Gloves", "Heat Shrink Tubing", "Tool Cabinet",
        "Air Hose", "Circular Saw Blade", "Hacksaw", "Paint Scraper", "Cordless Nail Gun",
        "Pipe Bender", "Stud Punch", "Wire Cutter", "Grinder Wheel", "Pressure Washer",
        "Masonry Drill Bits", "Torque Driver", "Tool Organizer", "Magnetic Tray",
        "Paint Mixer", "Power Inverter", "Voltage Meter", "Hex Driver", "Carpenter's Square"
    ],

    "Baby Products": [
        "Baby Crib", "Stroller", "Diapers", "Baby Wipes", "Baby Monitor",
        "Pacifiers", "Baby Bottle", "Baby Bibs", "Changing Pad", "Baby Clothes",
        "Baby Blanket", "High Chair", "Diaper Bag", "Baby Carrier", "Teething Toys",
        "Nursing Pillow", "Baby Bathtub", "Baby Shampoo", "Baby Lotion", "Baby Thermometer",
        "Baby Swing", "Playpen", "Baby Rattle", "Sippy Cup", "Baby Walker",
        "Breast Pump", "Crib Sheets", "Baby Socks", "Car Seat", "Baby Gates",
        "Baby Formula", "Baby Shoes", "Baby Food", "Baby Humidifier", "Baby Toothbrush",
        "Diaper Pail", "Burp Cloths", "Baby Hair Brush", "Baby Pacifier Clips", "Baby Sleep Sack",
        "Baby Sunscreen", "Baby Detergent", "Baby Bottle Warmer", "Nasal Aspirator", "Baby Toys",
        "Baby Knee Pads", "Baby Nail Clipper", "Baby Food Maker", "Baby Washcloths", "Baby Soap",
        "Baby Towels", "Baby Head Shaping Pillow", "Baby Play Mat", "Baby Night Light", "Baby Wipes Warmer",
        "Baby Book", "Baby Tooth Gel", "Baby Food Storage", "Diaper Cream", "Baby Changing Station",
        "Baby Knee Pads", "Teething Mittens", "Baby Thermometer", "Baby Sound Machine", "Baby Safety Locks",
        "Baby Cradle", "Infant Car Seat Cover", "Portable Changing Mat", "Baby Feeding Chair", "Baby Bassinet",
        "Swaddle Blanket", "Baby Toothbrush", "Baby Foam Playmat", "Diaper Caddy", "Bottle Sterilizer",
        "Baby Mobile", "Baby Feeding Set", "Infant Mittens", "Baby Safety Helmet", "Baby Food Freezer Tray",
        "Reusable Swim Diapers", "Breastfeeding Cover", "Baby Stroller Organizer", "Baby Travel Bed",
        "Car Seat Protector", "Babyproofing Corner Guards", "Baby Bath Toys", "Baby Socks Gripper", "Baby Snack Container",
        "Baby Hair Clippers", "Baby Rocker", "Baby Towel Warmer", "Baby Monitor Wall Mount", "Baby Bottle Drying Rack"
    ],

    "Pet Supplies": [
        "Dog Food", "Cat Food", "Dog Leash", "Cat Litter", "Pet Bed", "Dog Crate",
        "Cat Carrier", "Pet Water Fountain", "Pet Food Bowl", "Dog Collar", "Cat Scratching Post",
        "Dog Toy Ball", "Cat Toy Mouse", "Dog Chew Toy", "Pet Grooming Brush", "Cat Litter Box",
        "Pet Shampoo", "Dog Treats", "Cat Treats", "Flea Collar", "Pet Nail Clippers",
        "Dog Waste Bags", "Pet Stain Remover", "Pet Odor Spray", "Pet Hair Roller",
        "Pet Training Pads", "Dog Muzzle", "Cat Tunnel", "Dog Harness", "Pet Gate",
        "Pet Stroller", "Pet Travel Bag", "Dog Life Jacket", "Cat Water Fountain",
        "Bird Cage", "Bird Seed", "Hamster Cage", "Hamster Food", "Pet Carrier Backpack",
        "Reptile Heat Lamp", "Aquarium", "Fish Food", "Pet Feeder", "Pet Cooling Mat",
        "Dog Sweater", "Cat Bed", "Pet First Aid Kit", "Dog Water Bottle", "Pet Hair Vacuum",
        "Pet Dental Chews", "Dog Raincoat", "Pet Thermometer", "Dog Ear Cleaner", "Dog Car Seat",
        "Pet Playpen", "Pet Camera", "Pet Calming Spray", "Dog Booties", "Cat Brush",
        "Pet Food Mat", "Pet Nail Grinder", "Catnip Toys", "Pet Flea Spray", "Bird Perch",
        "Dog Bandana", "Aquarium Filter", "Fish Tank Cleaner", "Pet Paw Balm", "Pet Cage Liners",
        "Cat Litter Scoop", "Dog Tug Toy", "Reptile Hideout", "Hamster Wheel", "Dog House",
        "Bird Feeder", "Pet Fountain Filters", "Dog Bone Chew", "Pet Blanket", "Cat Tree",
        "Dog Bed Cover", "Aquarium Gravel", "Pet Collar Light", "Pet Deodorizing Wipes", "Cat Grass",
        "Dog Brush", "Pet Feeding Station", "Pet Waste Station", "Pet Leash Hook", "Cat Nail Caps",
        "Bird Swing", "Pet Cooling Bandana", "Dog Training Whistle", "Pet Flea Comb", "Pet Hammock"
    ],

    "Jewelry": [
        "Gold Necklace", "Silver Earrings", "Diamond Ring", "Pearl Bracelet", "Choker Necklace",
        "Cufflinks", "Brooch Pin", "Pendant Necklace", "Stud Earrings", "Hoop Earrings",
        "Anklet", "Engagement Ring", "Wedding Band", "Charm Bracelet", "Beaded Necklace",
        "Friendship Bracelet", "Birthstone Ring", "Tennis Bracelet", "Gold Bracelet",
        "Silver Chain", "Rose Gold Ring", "Gold Earrings", "Drop Earrings", "Toe Ring",
        "Infinity Bracelet", "Heart Locket", "Cuban Link Chain", "Bangle Bracelet",
        "Layered Necklace", "Gold Watch", "Sterling Silver Ring", "Opal Earrings", "Gemstone Ring",
        "Turquoise Necklace", "Crystal Pendant", "Moonstone Ring", "Cross Necklace",
        "Initial Necklace", "Diamond Studs", "Stackable Rings", "Bar Necklace", "Leather Bracelet",
        "Magnetic Bracelet", "Cubic Zirconia Ring", "Sapphire Necklace", "Ruby Earrings",
        "Emerald Ring", "Amethyst Pendant", "Gold Cuff Bracelet", "Silver Anklet",
        "Beaded Anklet", "Rose Quartz Pendant", "Shell Necklace", "Pearl Studs", "Charm Anklet",
        "Lapis Lazuli Ring", "Aquamarine Necklace", "Garnet Earrings", "Onyx Ring",
        "Gold Nose Ring", "Cartilage Earrings", "Diamond Bracelet", "Rhinestone Necklace",
        "Tassel Earrings", "Rose Gold Earrings", "Huggie Earrings", "Personalized Necklace",
        "Zodiac Necklace", "Charm Necklace", "Infinity Necklace", "Rope Chain", "Tennis Chain",
        "Snake Chain", "Locket Bracelet", "Leather Necklace", "Coin Necklace", "Mala Beads",
        "Turquoise Ring", "Druzy Earrings", "Adjustable Bracelet", "Dainty Necklace", "Vintage Brooch",
        "Cameo Pendant", "Gold Brooch", "Silver Locket", "Butterfly Necklace", "Flower Earrings",
        "Leaf Pendant", "Feather Earrings", "Tree of Life Necklace", "Lotus Pendant",
        "Citrine Ring", "Tiger's Eye Necklace", "Dreamcatcher Earrings", "Celtic Knot Ring",
        "Mandala Necklace", "Arrow Necklace", "Sun Necklace", "Moon Earrings", "Rainbow Bracelet"
    ],

    "Appliances": [
        "Refrigerator", "Dishwasher", "Washing Machine", "Dryer", "Microwave",
        "Toaster", "Blender", "Coffee Maker", "Slow Cooker", "Electric Kettle",
        "Air Fryer", "Rice Cooker", "Juicer", "Food Processor", "Stand Mixer",
        "Espresso Machine", "Electric Grill", "Vacuum Cleaner", "Steam Mop",
        "Clothes Steamer", "Ice Maker", "Dehumidifier", "Humidifier", "Air Purifier",
        "Space Heater", "Fan", "Ceiling Fan", "Water Cooler", "Electric Skillet",
        "Pressure Cooker", "Induction Cooktop", "Electric Oven", "Deep Fryer",
        "Popcorn Maker", "Soda Maker", "Portable Dishwasher", "Robot Vacuum",
        "Handheld Vacuum", "Garment Steamer", "Hair Dryer", "Bread Maker",
        "Ice Cream Maker", "Waffle Maker", "Electric Griddle", "Food Dehydrator",
        "Electric Can Opener", "Toaster Oven", "Hot Water Dispenser", "Wine Cooler",
        "Electric Pressure Washer", "Sous Vide Cooker", "Electric Knife",
        "Electric Meat Grinder", "Electric Yogurt Maker", "Pasta Maker",
        "Countertop Oven", "Electric Citrus Juicer", "Pizza Oven", "Mini Fridge",
        "Portable Air Conditioner", "Electric Fireplaces", "Portable Fan",
        "Garbage Disposal", "Portable Heater", "Water Filter", "Electric Stove",
        "Electric Toothbrush", "Hair Straightener", "Curling Iron", "Foot Massager",
        "Neck Massager", "Oil Diffuser", "Electric Blanket", "Heated Mattress Pad",
        "Portable Blender", "Cordless Vacuum", "Stick Vacuum", "Floor Steamer",
        "Dish Drying Rack", "Electric Tea Kettle", "Slow Cooker Insert", "Electric Rice Steamer",
        "Portable Washing Machine", "Window Air Conditioner", "Tower Fan",
        "Countertop Ice Maker", "Electric Knife Sharpener", "Smart Thermostat",
        "Garbage Compactor", "Carpet Cleaner", "Steam Iron", "Hand Mixer",
        "Electric Carving Knife", "Compact Dishwasher", "Ice Crusher", "Vacuum Sealer"
    ],

    "Furniture": [
        "Sofa", "Coffee Table", "Dining Table", "Dining Chairs", "Bed Frame",
        "Nightstand", "Bookshelf", "Dresser", "Wardrobe", "TV Stand", "Recliner",
        "Office Desk", "Office Chair", "End Table", "Patio Set", "Outdoor Bench",
        "Outdoor Table", "Lounge Chair", "Bar Stool", "Sectional Sofa",
        "Storage Ottoman", "Futon", "Console Table", "Accent Chair", "Loveseat",
        "Rocking Chair", "Chaise Lounge", "Hammock", "Bunk Bed", "Shoe Rack",
        "Vanity Table", "Bedside Lamp Table", "Couch", "Dining Bench", "Room Divider",
        "Chest of Drawers", "Side Table", "Armchair", "Folding Table", "Folding Chair",
        "Kitchen Island", "Entryway Bench", "TV Console", "Standing Desk", "Bookcase",
        "Buffet Table", "Pantry Cabinet", "Sideboard", "Storage Cabinet", "Display Cabinet",
        "Coat Rack", "Hall Tree", "Gaming Chair", "Sleeper Sofa", "Corner Shelf",
        "Bar Cabinet", "Breakfast Bar", "Wine Rack", "Lift-Top Coffee Table",
        "Entryway Table", "Murphy Bed", "Massage Chair", "Bean Bag Chair", "Hanging Chair",
        "Convertible Sofa", "Daybed", "Kids Table", "Kids Chairs", "Foldable Desk",
        "Adjustable Desk", "Console Desk", "Bar Cart", "Kitchen Cart", "Reclining Sofa",
        "TV Bench", "Accent Stool", "Nesting Tables", "Media Console", "Ladder Shelf",
        "Entry Bench", "Patio Lounger", "Garden Swing", "Outdoor Dining Table",
        "Outdoor Dining Chairs", "Patio Umbrella", "Chaise Chair", "Wall Shelf",
        "Rolling Cart", "Wardrobe Closet", "Storage Bench", "Filing Cabinet",
        "Curio Cabinet", "Display Shelf", "Bathroom Vanity", "Towel Rack", "Shoe Cabinet"
    ],

    "Musical Instruments": [
        "Acoustic Guitar", "Electric Guitar", "Bass Guitar", "Drum Set", "Keyboard",
        "Piano", "Violin", "Trumpet", "Saxophone", "Flute", "Clarinet", "Trombone",
        "Ukulele", "Mandolin", "Banjo", "Harmonica", "Accordion", "Xylophone",
        "Bongo Drums", "Conga Drums", "Tambourine", "Maracas", "Snare Drum",
        "Cymbals", "Tuba", "Oboe", "Bassoon", "Bagpipes", "Didgeridoo", "Synthesizer",
        "Electric Violin", "Electric Drum Kit", "Steel Drums", "Ocarina", "Cello",
        "Double Bass", "French Horn", "Piccolo", "Pan Flute", "Recorder", "Lute",
        "Glockenspiel", "Djembe Drum", "Chimes", "Cajón", "Concertina", "Baglama",
        "Bouzouki", "Tabla", "Sitar", "Dulcimer", "Viola", "Baritone Horn",
        "Tenor Saxophone", "Soprano Saxophone", "Flugelhorn", "Melodica", "Finger Cymbals",
        "Triangle", "Bass Drum", "Marching Snare", "Cowbell", "Shaker", "Kazoo",
        "Bodhrán Drum", "Timpani", "Talking Drum", "Hang Drum", "Irish Whistle",
        "Native American Flute", "Jew's Harp", "Bass Clarinet", "Contrabassoon", "Sousaphone",
        "Zither", "Guitar Effects Pedal", "Drumsticks", "Guitar Strings", "Violin Bow",
        "Trumpet Mouthpiece", "Guitar Amp", "Drum Machine", "Audio Interface",
        "Recording Microphone", "Stage Piano", "Electronic Drum Pads", "Loop Pedal",
        "Electric Bass Amp", "MIDI Controller", "Practice Pad", "Drum Throne", "Clarinet Reeds",
        "Trumpet Case", "Guitar Strap", "Sheet Music Stand", "Conductor's Baton"
    ],

    "Polish Random Products": [
            "Zestaw do pielęgnacji brody",
            "Podgrzewacz do wosku",
            "Śmietnik automatyczny",
            "Elektryczny młynek do kawy",
            "Wieszak na ścianę",
            "Poduszka ortopedyczna",
            "Organizer na biurko",
            "Lampka do czytania na biurko",
            "Zegarek na rękę",
            "Kubek termiczny",
            "Torba sportowa",
            "Zestaw sztućców",
            "Składana parasolka",
            "Zamek szyfrowy",
            "Ręcznik szybkoschnący",
            "Termometr bezdotykowy",
            "Lodówka turystyczna",
            "Koc elektryczny",
            "Pojemnik na lunch",
            "Podkładka pod mysz z żelem",
            "Plecak turystyczny",
            "Kamera samochodowa",
            "Elektryczny grill",
            "Masażer do stóp",
            "Zestaw wierteł",
            "Świeca zapachowa",
            "Sokowirówka",
            "Waga kuchenna",
            "Torba na laptopa",
            "Suszarka do ubrań",
            "Mata do jogi",
            "Lusterko kosmetyczne z oświetleniem",
            "Kubek z zaparzaczem",
            "Składany stolik na laptopa",
            "Mop parowy",
            "Miska dla psa",
            "Zestaw kieliszków do wina",
            "Kompresy żelowe na oczy",
            "Kask rowerowy",
            "Termos na jedzenie"
        ]

    }


    n_workers = 10  # Define the number of workers

    for site_info in shopping_sites:
        main_scraper(site_info, categories_products, n_workers=n_workers)

    print("***** All searches completed *****")
