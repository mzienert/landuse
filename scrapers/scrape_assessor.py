from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
import os

# Setup Selenium function
def create_driver():
    service = Service(executable_path="./chromedriver")
    options = Options()
    # Remove headless mode to see what's happening for initial testing
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--max_old_space_size=4096")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    return webdriver.Chrome(service=service, options=options)

def main():
    # Initialize driver
    driver = create_driver()
    wait = WebDriverWait(driver, 15)
    
    try:
        print("Loading assessor login page...")
        driver.get("https://eagleweb.lpcgov.org/assessor/web/login.jsp")
        
        # Wait for page to load
        time.sleep(3)
        
        print("Page loaded. Looking for 'Enter EagleWeb' form...")
        
        # Find the form with the submit button
        submit_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Enter EagleWeb']"))
        )
        
        print("Found 'Enter EagleWeb' button. Clicking...")
        submit_button.click()
        
        # Wait for the new page to load
        time.sleep(5)
        
        print(f"New page loaded. Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Get page source to see what we have
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Print some basic info about the page
        print("\n=== PAGE CONTENT PREVIEW ===")
        print(f"Page length: {len(page_source)} characters")
        
        # Look for forms, links, or other interactive elements
        forms = soup.find_all('form')
        print(f"Found {len(forms)} forms on the page")
        
        links = soup.find_all('a')
        print(f"Found {len(links)} links on the page")
        
        # Print first few forms and links for analysis
        if forms:
            print("\nFirst few forms:")
            for i, form in enumerate(forms[:3]):
                print(f"Form {i+1}: {form.get('action', 'No action')} - {form.get('method', 'No method')}")
                inputs = form.find_all('input')
                for inp in inputs[:3]:  # First 3 inputs per form
                    print(f"  Input: type={inp.get('type', 'unknown')}, name={inp.get('name', 'unnamed')}, value={inp.get('value', 'no value')}")
        
        if links:
            print("\nFirst few links:")
            for i, link in enumerate(links[:5]):
                href = link.get('href', 'No href')
                text = link.get_text(strip=True)[:50]  # First 50 chars
                print(f"Link {i+1}: {href} - '{text}'")
        
        # Save full page source for analysis
        os.makedirs("assessor_data", exist_ok=True)
        with open("assessor_data/login_result_page.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        
        print("\nFull page source saved to 'assessor_data/login_result_page.html'")
        
        # Now look for the Parcel Classification section
        print("\n=== LOOKING FOR PARCEL CLASSIFICATION ===")
        
        # Find the table header with "Parcel Classification"
        parcel_class_header = soup.find('th', string=lambda text: text and 'Parcel Classification' in text)
        if parcel_class_header:
            print("Found 'Parcel Classification' header!")
            
            # First, find and check the "Search over all account types" checkbox
            all_types_checkbox = soup.find('input', {'id': 'allTypesCB', 'type': 'checkbox'})
            if all_types_checkbox:
                print("Found 'Search over all account types' checkbox!")
                
                # Check if it's already checked
                is_checked = all_types_checkbox.get('checked') is not None
                print(f"Checkbox is {'already checked' if is_checked else 'not checked'}")
                
                # Use Selenium to check the checkbox if not already checked
                try:
                    checkbox_element = driver.find_element(By.ID, "allTypesCB")
                    if not is_checked:
                        print("Checking 'Search over all account types' checkbox...")
                        checkbox_element.click()
                        time.sleep(1)  # Wait for any dynamic updates
                    else:
                        print("Checkbox already checked, proceeding...")
                        
                except Exception as checkbox_error:
                    print(f"Error with checkbox: {checkbox_error}")
                    # Continue anyway, might still work
            else:
                print("Could not find 'Search over all account types' checkbox")
            
            # Look for the multi-select dropdown with accountTypeID
            target_select = soup.find('select', {'id': 'accountTypeID', 'name': 'accountTypeID'})
            
            if target_select and target_select.get('multiple') is not None:
                print("Found multi-select dropdown with id 'accountTypeID'!")
                
                # Get all available options for logging
                options = target_select.find_all('option')
                print(f"Found {len(options)} total options in the dropdown")
                
                # Use Selenium to select ALL options (except the empty one)
                try:
                    dropdown = driver.find_element(By.ID, "accountTypeID")
                    
                    from selenium.webdriver.support.ui import Select
                    select_obj = Select(dropdown)
                    
                    # Get all option values except the empty one
                    all_options = select_obj.options
                    selected_count = 0
                    
                    for option in all_options:
                        option_value = option.get_attribute('value')
                        option_text = option.text.strip()
                        
                        # Skip empty option
                        if option_value and option_value.strip():
                            select_obj.select_by_value(option_value)
                            print(f"Selected: {option_value} - {option_text}")
                            selected_count += 1
                    
                    print(f"Successfully selected {selected_count} property classification options!")
                    
                    time.sleep(2)  # Wait for any dynamic updates
                    
                    # Now find and click the Search button
                    search_button = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Search']")
                    print("Found Search button. Clicking...")
                    search_button.click()
                    
                    # Wait for search results to load
                    time.sleep(5)
                    
                    print(f"Search completed! New URL: {driver.current_url}")
                    print(f"New page title: {driver.title}")
                    
                    # Initialize data storage
                    all_properties = {}
                    page_num = 1
                    
                    # Create directory for assessor data
                    os.makedirs("assessor_data", exist_ok=True)
                    
                    # Load existing data if resuming
                    properties_file = "assessor_data/full_properties.json"
                    if os.path.exists(properties_file):
                        with open(properties_file, "r", encoding="utf-8") as f:
                            all_properties = json.load(f)
                        print(f"Loaded {len(all_properties)} existing properties. Resuming...")
                    
                    while True:
                        print(f"\n=== PROCESSING PAGE {page_num} ===")
                        
                        # Get current page source
                        page_source = driver.page_source
                        soup = BeautifulSoup(page_source, 'html.parser')
                        
                        # Find the results table
                        results_table = soup.find('table', {'id': 'searchResultsTable'})
                        if not results_table:
                            print("No searchResultsTable found on this page")
                            break
                        
                        # Find all property rows (skip header row)
                        property_rows = results_table.find_all('tr')[1:]  # Skip header
                        print(f"Found {len(property_rows)} property records on page {page_num}")
                        
                        page_properties = 0
                        for row in property_rows:
                            try:
                                # Extract account number from first column
                                account_cell = row.find('td')
                                if not account_cell:
                                    continue
                                    
                                account_link = account_cell.find('a')
                                if not account_link:
                                    continue
                                
                                account_num = account_link.get_text(strip=True)
                                
                                # Skip if already processed
                                if account_num in all_properties:
                                    print(f"Skipping already processed account: {account_num}")
                                    continue
                                
                                # Extract summary data from second column
                                summary_cell = row.find_all('td')[1] if len(row.find_all('td')) > 1 else None
                                if not summary_cell:
                                    continue
                                
                                # Parse the nested table in summary
                                summary_table = summary_cell.find('table')
                                if summary_table:
                                    summary_row = summary_table.find('tr')
                                    if summary_row:
                                        cells = summary_row.find_all('td')
                                        
                                        # Extract key data points
                                        parcel_id = ""
                                        tax_area = ""
                                        owner_name = ""
                                        description = ""
                                        
                                        if len(cells) >= 1:
                                            # First cell: Parcel ID and Tax Area
                                            cell1_text = cells[0].get_text(strip=True)
                                            lines = cell1_text.split('\n')
                                            for line in lines:
                                                if '-' in line and len(line) > 5:  # Likely parcel ID
                                                    parcel_id = line.strip()
                                                elif 'TAX AREA' in line:
                                                    tax_area = line.strip()
                                        
                                        if len(cells) >= 2:
                                            # Second cell: Owner name
                                            owner_name = cells[1].get_text(strip=True).split('\n')[0]
                                        
                                        if len(cells) >= 4:
                                            # Fourth cell: Property description
                                            description = cells[3].get_text(strip=True)
                                
                                # Store property data
                                property_data = {
                                    'account_number': account_num,
                                    'parcel_id': parcel_id,
                                    'tax_area': tax_area,
                                    'owner_name': owner_name,
                                    'description': description,
                                    'page_found': page_num
                                }
                                
                                all_properties[account_num] = property_data
                                page_properties += 1
                                print(f"  Extracted: {account_num} - {owner_name[:30]}...")
                                
                            except Exception as e:
                                print(f"Error processing row: {e}")
                                continue
                        
                        print(f"Extracted {page_properties} new properties from page {page_num}")
                        
                        # Save checkpoint every page
                        with open(properties_file, "w", encoding="utf-8") as f:
                            json.dump(all_properties, f, indent=4)
                        print(f"Checkpoint saved: {len(all_properties)} total properties")
                        
                        # Look for next page link
                        next_page_link = None
                        pagination_links = soup.find_all('a', href=lambda x: x and 'results.jsp?start=' in x)
                        
                        if pagination_links:
                            # Find the next sequential page number
                            next_page_num = page_num + 1
                            for link in pagination_links:
                                link_text = link.get_text(strip=True)
                                if link_text == str(next_page_num):
                                    next_page_link = link
                                    break
                        
                        if next_page_link:
                            print(f"Found next page link for page {next_page_num}. Clicking...")
                            try:
                                # Click the next page link
                                href = next_page_link.get('href')
                                if href.startswith('../'):
                                    # Handle relative URL
                                    base_url = driver.current_url.rsplit('/', 1)[0]
                                    next_url = base_url + '/' + href[3:]  # Remove '../'
                                else:
                                    next_url = href
                                
                                driver.get(next_url)
                                time.sleep(3)  # Wait for page load
                                page_num += 1
                                
                            except Exception as e:
                                print(f"Error navigating to next page: {e}")
                                break
                        else:
                            print("No more pages found. Scraping complete!")
                            break
                    
                    # Final save
                    with open(properties_file, "w", encoding="utf-8") as f:
                        json.dump(all_properties, f, indent=4)
                    
                    print(f"\n=== SCRAPING COMPLETE ===")
                    print(f"Total properties extracted: {len(all_properties)}")
                    print(f"Data saved to: {properties_file}")
                    print("Ready for next steps!")
                    
                except Exception as select_error:
                    print(f"Error selecting option or clicking search: {select_error}")
            else:
                print("Could not find select dropdown with '01 - VACANT LAND' option")
        else:
            print("Could not find 'Parcel Classification' header")
        
        print("Ready for next steps!")
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Current URL: {driver.current_url}")
        
        # Save error page source
        try:
            os.makedirs("assessor_data", exist_ok=True)
            with open("assessor_data/error_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Error page source saved to 'assessor_data/error_page.html'")
        except:
            print("Could not save error page source")
    
    finally:
        # Keep browser open for inspection in non-headless mode
        input("Press Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    main()