import json
import csv
import time
from contextlib import closing

import requests
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def fetch_all_page_urls(base_url, max_pages=1):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }
    if 'page=' not in base_url:
        base_url += '&page=1'
    page_urls = [base_url]
    current_url = base_url
    pages_fetched = 0  # Initialize pages_fetched to 0
    
    print("Fetching URLs from base URL...")
    while True:
        response = requests.get(current_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        current_page_number = int(current_url.split('page=')[-1]) if 'page=' in current_url else 1
        page_links = soup.find_all('a', {'data-testid': 'paginator-page-button'})
        page_numbers = [int(link.get_text()) for link in page_links if link.get_text().isdigit()]
        
        if pages_fetched < max_pages:
            pages_fetched += 1
            print(f"Fetched page {pages_fetched} URL.")
            
            # Look for the next page only if under the max_pages limit
            if pages_fetched < max_pages:
                next_page_candidates = [link['href'] for link in page_links if int(link.get_text()) == current_page_number + 1]
                if next_page_candidates:
                    next_url = 'https://www.domain.com.au' + next_page_candidates[0]
                    if next_url not in page_urls:
                        page_urls.append(next_url)
                        current_url = next_url
                else:
                    break
        else:
            print(f"Reached the maximum of {max_pages} pages.")
            break

    return page_urls

def fetch_listings(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    listings = []
    divs_type1 = soup.find_all('div', {'data-testid': 'listing-card-child-listing'}, class_="css-hlnxku")
    divs_type2 = soup.find_all('div', attrs={"data-testid": "listing-card-wrapper-premiumplus"})
    for div in divs_type1 + divs_type2:
        listings.append(process_listing_card(div))
    return listings


def process_listing_card(div):
    listing_info = {
        'url': div.find('a', href=True)['href'] if div.find('a', href=True) else "URL not found",
        'price': div.find('p', {'data-testid': 'listing-card-price'}).text.strip() if div.find('p', {'data-testid': 'listing-card-price'}) else "Price not listed",
        'features': {}
    }

    # Attempt to find property type from the usual 'div'
    property_type_tag = div.find('div', {'data-testid': 'listing-card-property-type'})
    if property_type_tag:
        listing_info['property_type'] = property_type_tag.text.strip()
    else:
        # Fallback to alternative 'span' within a 'div' as seen in the screenshot
        property_type_tag = div.find('span', {'class': 'css-693528'})  # Update this class based on actual observation or a more stable identifier
        listing_info['property_type'] = property_type_tag.text.strip() if property_type_tag else "Type not listed"

    # Extract features
    features_wrapper = div.find('div', {'data-testid': 'property-features-wrapper'})
    if features_wrapper:
        for feature_span in features_wrapper.find_all('span', {'data-testid': 'property-features-feature'}):
            feature_type_tag = feature_span.find('span', {'data-testid': 'property-features-text'})
            feature_container = feature_span.find('span', {'data-testid': 'property-features-text-container'})

            if feature_container and feature_type_tag:
                feature_number = feature_container.text.split()[0]
                feature_type = feature_type_tag.text.strip()
                listing_info['features'][feature_type] = feature_number
            elif feature_container:  # Assuming this is for land size or similar feature without explicit type
                feature_text = feature_container.text.strip()
                if feature_text.endswith("m²"):
                    listing_info['features']['Land size'] = feature_text
                else:
                    print("Unrecognized feature format:", feature_text)

    return listing_info


def extract_additional_details(url):
    soup = load_page_and_expand_content(url)
    title = extract_title(soup)
    features = extract_features(soup)
    description_details = extract_headline_and_multiple_paragraphs(soup)
    return {
        "title": title,
        "features_list": features,
        "headline": description_details["headline"],
        "paragraphs": description_details["paragraphs"]
    }
def extract_title(soup):
    """
    Extracts the title from a BeautifulSoup object based on a specified class name.

    Parameters:
    soup (BeautifulSoup): The BeautifulSoup object from which to extract the title.

    Returns:
    str: The extracted title or an empty string if not found.
    """
    # Attempt to find the first h1 element with the specified class
    title_element = soup.find("h1", class_="css-164r41r")
    
    # Check if the title element is found and return its text; otherwise, return an empty string
    if title_element:
        return title_element.text.strip()
    else:
        return ""
def extract_features(soup):
    """
    Extracts additional features listed under li elements from a BeautifulSoup object.

    Parameters:
    soup (BeautifulSoup): The BeautifulSoup object from which to extract the features.

    Returns:
    list: A list containing the texts of each feature found.
    """
    # Combine lists of elements with different data-testid values
    feature_elements_suggested = soup.find_all('li', {'data-testid': 'listing-details__additional-features-suggested'})
    feature_elements_listing = soup.find_all('li', {'data-testid': 'listing-details__additional-features-listing'})
    
    
    # Combine both lists
    feature_elements = feature_elements_suggested+feature_elements_listing 

    # Extract the text from each feature element
    features = [feature.text.strip() for feature in feature_elements]

    return features


def extract_headline_and_multiple_paragraphs(soup):
    """
    Extracts a headline and texts from all paragraphs within a specific div 
    in a BeautifulSoup object, based on `data-testid` and class attributes.

    Parameters:
    soup (BeautifulSoup): The BeautifulSoup object from which to extract the headline and paragraphs.

    Returns:
    dict: A dictionary containing the headline and a list of all paragraph texts found within the specified div.
    """
    # Find the specific div by `data-testid` and class
    description_div = soup.find('div', {'data-testid': 'listing-details__description', 'class': 'css-bq4jj8'})

    # If the specific div is not found, return a message indicating missing data
    if not description_div:
        return {
            "headline": "Description div not found",
            "paragraphs": []
        }

    # Extract the headline from the div
    headline = description_div.find('h3', {'data-testid': 'listing-details__description-headline'})
    headline_text = headline.text.strip() if headline else "Headline not found"

    # Extract all paragraph texts from the div
    paragraphs = [p.text.strip() for p in description_div.find_all('p')]

    return {
        "headline": headline_text,
        "paragraphs": paragraphs
    }
    

def load_page_and_expand_content(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    try:
        wait = WebDriverWait(driver, 20)  # Increased timeout
        try:
            # Attempt to click the "Read More" button if it exists
            read_more_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="listing-details__description-button"]')))
            read_more_button.click()
            time.sleep(1)  # Wait for content to load after click
        except (TimeoutException, NoSuchElementException):
            # If button is not present, handle gracefully
            print("Read more button not found or page took too long to respond, proceeding with available content.")
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    finally:
        driver.quit()

    return soup

def main():
    print("Welcome to the Listing Scraper!")
    base_url = input("Please enter the base URL for the listings: ")
    max_pages = int(input("Please enter the maximum number of pages to fetch: "))

    all_page_urls = fetch_all_page_urls(base_url, max_pages=max_pages)
    
    print(f"Total pages to fetch: {len(all_page_urls)}")  # Print the total number of pages
    
    fieldnames = ['url', 'price', 'property_type', 'features', 'title', 'features_list', 'headline', 'paragraphs']

    output_file_name = 'listings_detailed.csv'
    with open(output_file_name, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        total_listings_count = 0  # Initialize total listings count

        for page_index, page_url in enumerate(all_page_urls, start=1):
            listings = fetch_listings(page_url)
            print(f"Fetching page {page_index}/{len(all_page_urls)} with {len(listings)} listings.")
            for listing_index, listing in enumerate(listings, start=1):
                total_listings_count += 1  # Increment total count for each listing
                print(f"Processing listing {total_listings_count} from {listing['url']}")
                try:
                    additional_details = extract_additional_details(listing['url'])
                    listing.update(additional_details)
                    writer.writerow(listing)
                    print(f"Saved details for listing {total_listings_count}.")
                except Exception as e:
                    print(f"Failed to fetch details for listing {total_listings_count} ({listing['url']}): {e}")
                    listing.update({'title': '', 'features_list': '', 'headline': '', 'paragraphs': []})
                    writer.writerow(listing)

        print(f'All data has been saved to {output_file_name}. Total listings processed: {total_listings_count}.')

if __name__ == "__main__":
    main()

