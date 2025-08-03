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

# Base URL
base_url = "https://online.encodeplus.com/regs/la-plata-co/doc-viewer.aspx"

# Setup Selenium function (to recreate driver)
def create_driver():
    service = Service(executable_path="./chromedriver")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")  # Helps with stability
    options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    options.add_argument("--disable-web-security")  # May help with some timeout issues
    options.add_argument("--disable-features=VizDisplayCompositor")  # Stability improvement
    options.add_argument("--max_old_space_size=4096")  # Increase memory limit
    options.add_argument("--disable-background-timer-throttling")  # Prevent background throttling
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    return webdriver.Chrome(service=service, options=options)

# Function to initialize driver and expand TOC
def initialize_driver_and_toc(expanded_params):
    """Initialize driver, load page, and re-expand TOC to previous state"""
    driver = create_driver()
    wait = WebDriverWait(driver, 15)  # Reduced timeout to fail faster
    
    # Load the initial page
    driver.get(base_url)
    
    # Wait for TOC to load
    try:
        toc_element = wait.until(EC.presence_of_element_located((By.ID, "toc-list")))
        print("TOC loaded successfully after restart.")
    except:
        print("TOC not found after restart.")
        driver.quit()
        return None, None
    
    # Re-expand previously expanded parameters with better error handling
    if expanded_params:
        print(f"Re-expanding {len(expanded_params)} previously expanded parameters...")
        time.sleep(5)  # Longer initial wait for page to fully load
        
        successful_expansions = 0
        for param in expanded_params:
            try:
                # Use the same logic as the original expansion - look for collapsed expanders
                collapsed_check = driver.find_elements(By.XPATH, f'//a[contains(@onclick, "Expand(\'{param}\')")]//img[@class="expander" and contains(@src, "plus_sign.gif")]')
                if collapsed_check:  # Only expand if still collapsed
                    if DEBUG_MODE:
                        print(f"DEBUG: Re-expanding param '{param}'")
                    driver.execute_script(f"ZP.TOCView.Expand('{param}');")
                    time.sleep(3)  # Wait for expansion to complete
                    successful_expansions += 1
                elif DEBUG_MODE:
                    print(f"DEBUG: Param '{param}' already expanded or not found")
                    
                # Every 10 expansions, wait longer to let the DOM stabilize
                if successful_expansions % 10 == 0 and successful_expansions > 0:
                    time.sleep(8)
                    
            except Exception as e:
                if DEBUG_MODE:
                    print(f"DEBUG: Failed to re-expand param '{param}': {str(e)}")
                continue
        
        print(f"TOC re-expansion complete. Successfully expanded {successful_expansions}/{len(expanded_params)} parameters.")
        time.sleep(8)  # Final wait for DOM to stabilize
    
    return driver, wait

driver, wait = initialize_driver_and_toc([])
if driver is None:
    print("Failed to initialize driver. Exiting.")
    exit()

# Iterative expansion for nesting
print("Starting iterative expansion of nested TOC...")
expanded_params = set()
max_iterations = 20
iteration = 0

# Memory management: Set garbage collection
import gc

while iteration < max_iterations:
    iteration += 1
    # Find current collapsed expanders
    collapsed_as = driver.find_elements(By.XPATH, '//img[@class="expander" and contains(@src, "plus_sign.gif")]/..')
    if not collapsed_as:
        print("No more collapsed folders. Expansion complete.")
        break
    
    current_params = set()
    for a in collapsed_as:
        onclick = a.get_attribute("onclick")
        if onclick and "Expand" in onclick:
            param_start = onclick.find("Expand('") + 8
            param_end = onclick.find("');", param_start)
            if param_start != -1 and param_end != -1:
                param = onclick[param_start:param_end]
                if param not in expanded_params:
                    current_params.add(param)
    
    if not current_params:
        print("No new params to expand in this batch.")
        break
    
    print(f"Iteration {iteration}: Expanding {len(current_params)} new params: {current_params}")
    
    for param in list(current_params):
        print(f"Expanding param: '{param}'")
        driver.execute_script(f"ZP.TOCView.Expand('{param}');")
        expanded_params.add(param)
        time.sleep(5)  # Wait for DOM to stabilize after each expand

if iteration >= max_iterations:
    print("Reached max iterations. Proceeding with partial expansion.")

# Get full TOC HTML after expansion
time.sleep(5)  # Final wait
toc_html = driver.page_source
soup = BeautifulSoup(toc_html, 'html.parser')

# Find all links with ?secid= in href
toc_links = soup.find_all('a', href=lambda href: href and '?secid=' in href)

secids = []
for link in toc_links:
    href = link['href']
    secid = href.split('?secid=')[-1].split('&')[0]
    if secid not in secids and secid != '-1':
        secids.append(secid)
        print(f"Found secid: {secid}")

print(f"Total unique sections found: {len(secids)}")

# Directory to save
os.makedirs("la_plata_code", exist_ok=True)

# Load existing extracted_data if exists for resume
extracted_data_file = "la_plata_code/full_code.json"
extracted_data = {}
if os.path.exists(extracted_data_file):
    with open(extracted_data_file, "r", encoding="utf-8") as json_file:
        extracted_data = json.load(json_file)
    print(f"Loaded {len(extracted_data)} existing sections. Resuming...")

# Fetch each section with error handling and checkpointing
checkpoint_interval = 10  # Save JSON every 10 sections
max_retries = 3  # Maximum retries per section
driver_restart_interval = 20  # Restart driver every 20 sections to prevent memory buildup (reduced after discovering crashes are context-dependent)

# Debug mode for investigating problematic sections
DEBUG_MODE = False  # Set to True to enable detailed logging and single section testing
TEST_SECTION = '312'  # Section to test when DEBUG_MODE is True

print(f"\nStarting extraction of {len(secids)} total sections...")
print(f"Already extracted: {len(extracted_data)} sections")
print(f"Remaining to extract: {len(secids) - len(extracted_data)} sections")

# Debug mode override
if DEBUG_MODE:
    if TEST_SECTION in secids:
        print(f"DEBUG MODE: Testing problematic section {TEST_SECTION}")
        secids = [TEST_SECTION]
    else:
        print(f"DEBUG MODE: Section {TEST_SECTION} not found in secids. Testing first section instead.")
        secids = [secids[0]]
    extracted_data = {}  # Clear existing data for clean test
    print(f"DEBUG MODE: Will test section(s): {secids}")

for i, secid in enumerate(secids):
    progress = f"[{i+1}/{len(secids)}]"
    
    if secid in extracted_data:
        print(f"{progress} Skipping already extracted secid {secid}.")
        continue
    
    print(f"{progress} Processing secid {secid}...")
    
    if DEBUG_MODE:
        print(f"DEBUG: Testing section {secid} with detailed logging...")
    
    # Retry loop for each section
    retry_count = 0
    section_extracted = False
    
    while retry_count <= max_retries and not section_extracted:
        section_url = f"{base_url}?secid={secid}"
        try:
            if DEBUG_MODE:
                print(f"DEBUG: Loading URL: {section_url}")
            
            driver.get(section_url)
            time.sleep(7)  # Longer delay for dynamic load
            
            if DEBUG_MODE:
                print(f"DEBUG: Page loaded, waiting for content elements...")
                print(f"DEBUG: Current URL: {driver.current_url}")
                print(f"DEBUG: Page title: {driver.title}")
            
            # Try multiple selectors for content - be more flexible
            content_element = None
            content_selectors = [
                (By.CLASS_NAME, "secLvl2"),
                (By.ID, "thePage"), 
                (By.CLASS_NAME, "document-content"),
                (By.XPATH, "//div[contains(@class, 'sec')]")
            ]
            
            for selector_type, selector_value in content_selectors:
                try:
                    content_element = wait.until(EC.presence_of_element_located((selector_type, selector_value)))
                    if DEBUG_MODE:
                        print(f"DEBUG: Found content using selector: {selector_type}='{selector_value}'")
                    break
                except:
                    if DEBUG_MODE:
                        print(f"DEBUG: Selector {selector_type}='{selector_value}' not found")
                    continue
            
            if not content_element:
                if DEBUG_MODE:
                    print("DEBUG: No content element found with any selector. Page source preview:")
                    page_source = driver.page_source
                    print(page_source[:1000] + "..." if len(page_source) > 1000 else page_source)
                raise Exception("No content element found with any selector")
            
            # Parse content
            content_html = driver.page_source
            content_soup = BeautifulSoup(content_html, 'html.parser')
            content_div = content_soup.find('div', id="thePage")
            
            if not content_div:
                # Try alternative content containers
                content_div = content_soup.find('div', class_="secLvl2") or content_soup.find('div', class_="document-content")
                
            if content_div:
                text = content_div.get_text(strip=True, separator="\n")
                if DEBUG_MODE:
                    print(f"DEBUG: Extracted {len(text)} characters of text")
                    print(f"DEBUG: Text preview: {text[:200]}...")
                    
                extracted_data[secid] = text
                with open(f"la_plata_code/section_{secid}.txt", "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"{progress} ✓ Extracted section {secid}")
                section_extracted = True
                
                # Checkpoint save
                if (i + 1) % checkpoint_interval == 0:
                    with open(extracted_data_file, "w", encoding="utf-8") as json_file:
                        json.dump(extracted_data, json_file, indent=4)
                    print(f"Checkpoint saved at section {i + 1}.")
                
                # Periodic driver restart to prevent memory buildup
                if (i + 1) % driver_restart_interval == 0:
                    print(f"Performing periodic driver restart after {i + 1} sections...")
                    try:
                        driver.quit()
                    except:
                        pass
                    
                    # Force garbage collection
                    gc.collect()
                    
                    driver, wait = initialize_driver_and_toc(expanded_params)
                    if driver is None:
                        print("Failed to restart driver during periodic restart. Aborting.")
                        break
                    print("Periodic driver restart complete.")
            else:
                print(f"No content div found for secid {secid}.")
                section_extracted = True  # Don't retry if content structure is wrong
                
        except Exception as e:
            retry_count += 1
            error_str = str(e)
            print(f"Error on secid {secid} (attempt {retry_count}/{max_retries + 1}): {error_str}")
            
            if DEBUG_MODE:
                print(f"DEBUG: Full error details for secid {secid}:")
                print(f"DEBUG: Error type: {type(e).__name__}")
                print(f"DEBUG: Error message: {error_str}")
                import traceback
                print(f"DEBUG: Traceback: {traceback.format_exc()}")
            
            # Check if this is a driver crash that suggests the section should be skipped permanently
            is_driver_crash = ("Stacktrace:" in error_str or 
                             "chromedriver" in error_str or 
                             "Connection refused" in error_str or
                             "InvalidSessionIdException" in error_str)
            
            is_timeout = "TimeoutException" in error_str
            
            if retry_count <= max_retries:
                if is_driver_crash:
                    print("Detected driver crash. Restarting driver and retrying...")
                elif is_timeout:
                    print("Detected timeout. Restarting driver and retrying...")
                else:
                    print("Retrying after error...")
                    
                try:
                    driver.quit()
                except:
                    pass
                
                # Force garbage collection before restart
                gc.collect()
                
                # Restart driver and re-expand TOC
                print(f"Restarting driver for secid {secid}...")
                driver, wait = initialize_driver_and_toc(expanded_params)
                if driver is None:
                    print("Failed to restart driver. Aborting.")
                    break
                
                print(f"Driver restarted successfully. Retrying secid {secid}...")
                time.sleep(3)  # Wait before retry
            else:
                print(f"Max retries exceeded for secid {secid}. Recording failure and continuing.")
                
                # Mark as failed but don't crash the whole process
                extracted_data[secid] = f"[FAILED AFTER {max_retries} RETRIES: {error_str[:100]}...]"
                
                if DEBUG_MODE:
                    print(f"DEBUG: Marked secid {secid} as failed and continuing")
    
    if section_extracted:
        time.sleep(3)  # Polite delay between successful extractions
        
        # Additional memory management every 10 sections
        if (i + 1) % 10 == 0:
            gc.collect()  # Force garbage collection
            print(f"Memory cleanup performed after {i + 1} sections")

# Final save
with open(extracted_data_file, "w", encoding="utf-8") as json_file:
    json.dump(extracted_data, json_file, indent=4)

driver.quit()
print("Scraping complete. Check 'la_plata_code' folder.")
