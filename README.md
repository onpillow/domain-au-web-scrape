# Domain.com.au Property Listing Scraper

## Overview
This sub-project aims to provide a robust listing source from Domain.com.au, specifically for the Melbourne area, to support my side project (for learning purposes). The data fields included in the tool are:

- Price
- Property Type: House, Townhouse, Apartment / Unit / Flat, House & Land
- Features: Number of Bedrooms, Bathrooms, Parking spaces, and Land size (in m²)
- Additional Feature List: e.g., Air conditioning, Ensuite, Built-in wardrobes, Secure Parking, Rainwater storage tank
- Property Description

The scraper's base URL is based on filtering the features mentioned (excluding land type) and targets properties in the Melbourne area. You can check out areas of interest by modifying the base URL at the start of the program.

## How to Use
This application uses `selenium` to interact with "Read More" buttons to collect data. Ensure all necessary packages are installed from `requirements.txt` and that [`ChromeDriver`](https://developer.chrome.com/docs/chromedriver/get-started) is correctly set up.

### Execution

1. **Start the Program**
    ```bash
    python3 domainauScraper.py
    ```

2. **Interactive Command Line Interface**
    - Enter your base URL based on your search preferences.
    - Specify the maximum number of pages to scrape (default is one page, maximum 50 on the Domain website).

    Example:
    ```
    Welcome to the Listing Scraper!
    Please enter the base URL for the listings:
    https://www.domain.com.au/sale/melbourne-region-vic/?ptype=apartment-unit-flat,block-of-units,duplex,free-standing,new-apartments,new-home-designs,new-house-land,pent-house,semi-detached,studio,terrace,town-house,villa&excludeunderoffer=1&page=20

    Please enter the maximum number of pages to fetch: 1
    ```

3. **Sample Output**
    ```
    Fetching URLs from base URL...
    Fetched page 1 URL.
    Reached the maximum of 1 pages.
    Total pages to fetch: 1
    Fetching page 1/1 with 20 listings.
    Processing listing 1 from https://www.domain.com.au/10-law-street-south-melbourne-vic-3205-2019451811
    Saved details for listing 1.
    ...
    ```

    Check out the sample data in the Repo for more details on the output.

## Note
This tool is intended solely for learning and educational purposes. All data gathered using this tool is for educational use only. Any commercial use, misuse, or exaggeration of this tool may violate the terms and conditions of Domain.com.au.