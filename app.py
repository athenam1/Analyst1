from flask import Flask, render_template, request, jsonify
import pytesseract
from PIL import Image
import io
import base64
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time
import threading
import logging
import random
from datetime import datetime

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG to see extraction details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analyst1.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
# Reduce noise from other loggers
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('selenium').setLevel(logging.WARNING)

# Configure Tesseract path (only if not in Docker/standard location)
# In Docker, Tesseract is in the standard PATH, so we only set this if needed
if os.path.exists('/opt/homebrew/bin/tesseract'):
    pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
# Docker/standard Linux installation will use the default PATH


# ============================================================================
# Portal Landing Page
# ============================================================================

@app.route('/')
def portal():
    try:
        return render_template('portal.html')
    except Exception as e:
        return f"Error loading template: {str(e)}", 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200

# ============================================================================
# Analyst1 - OCR Text Extraction
# ============================================================================

@app.route('/analyst1')
def analyst1_index():
    return render_template('analyst1/index.html')

@app.route('/analyst1/extract-text', methods=['POST'])
def extract_text():
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Extract base64 image data
        image_data = data['image']
        
        # Remove data URL prefix if present (e.g., "data:image/png;base64,")
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Perform OCR
        extracted_text = pytesseract.image_to_string(image)
        
        return jsonify({
            'success': True,
            'text': extracted_text
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# Analyst2 - LinkedIn Employee Count Scraper
# ============================================================================

# Global driver instance (thread-safe)
driver_lock = threading.Lock()
driver_instance = None

def is_driver_session_valid(driver):
    """Check if the driver session is still valid"""
    if driver is None:
        return False
    try:
        # Try to get the current URL - this will fail if session is invalid
        _ = driver.current_url
        # Also check if we can get window handles (more reliable check)
        _ = driver.window_handles
        return True
    except (InvalidSessionIdException, WebDriverException, AttributeError):
        return False
    except Exception:
        # For any other exception, assume session might be invalid
        return False

def random_delay(min_seconds=0.5, max_seconds=2.0):
    """Generate a random delay between min and max seconds"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay

def human_like_delay():
    """Human-like delay (reduced: 0.5-1.5 seconds)"""
    return random_delay(0.5, 1.5)

def short_delay():
    """Short delay between actions (0.3-0.8 seconds)"""
    return random_delay(0.3, 0.8)

def move_mouse_randomly(driver):
    """Simulate random mouse movements"""
    try:
        actions = ActionChains(driver)
        # Perform 1-3 small random mouse movements
        num_movements = random.randint(1, 3)
        for _ in range(num_movements):
            # Small random offsets (50-200 pixels in any direction)
            offset_x = random.randint(-200, 200)
            offset_y = random.randint(-200, 200)
            actions.move_by_offset(offset_x, offset_y)
            actions.pause(random.uniform(0.1, 0.3))
        
        actions.perform()
        logger.debug("Performed random mouse movements")
    except Exception as e:
        logger.debug(f"Mouse movement failed: {e}")

def scroll_page_human_like(driver):
    """Scroll the page in a human-like manner (reduced for efficiency)"""
    try:
        # Get viewport height
        viewport_height = driver.execute_script("return window.innerHeight")
        
        # Reduced scrolling: 1-2 steps instead of 3-6
        scroll_steps = random.randint(1, 2)
        for i in range(scroll_steps):
            # Random scroll amount (30-50% of viewport)
            scroll_amount = random.randint(int(viewport_height * 0.3), int(viewport_height * 0.5))
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            random_delay(0.2, 0.4)  # Reduced pause between scrolls (0.2-0.4s instead of 0.3-0.8s)
        
        logger.debug("Performed human-like scrolling")
    except Exception as e:
        logger.debug(f"Scrolling failed: {e}")

def create_driver():
    """Create a new Chrome driver instance (non-headless for better anti-detection)"""
    start_time = time.time()
    logger.info("Starting Chrome driver creation...")
    chrome_options = Options()
    
    # REMOVED headless mode - browser will be visible (better anti-detection)
    # chrome_options.add_argument('--headless=new')  # REMOVED
    
    # Keep essential options
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    # Remove headless-specific options (not needed for visible browser)
    # chrome_options.add_argument('--disable-gpu')  # REMOVED
    # chrome_options.add_argument('--disable-software-rasterizer')  # REMOVED
    chrome_options.add_argument('--disable-extensions')  # Keep this to avoid extension conflicts
    
    # Anti-detection: Use a realistic user agent (Chrome on macOS - common and realistic)
    # This is a real user agent string from Chrome 131 on macOS
    realistic_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'--user-agent={realistic_user_agent}')
    logger.info(f"Using realistic user agent: {realistic_user_agent[:50]}...")
    
    # Anti-detection: Disable automation flags that websites can detect
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Additional anti-detection: Disable features that can identify automation
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Find Chrome
    chrome_paths = [
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
    ]
    
    chrome_found = False
    for chrome_path in chrome_paths:
        if os.path.exists(chrome_path):
            chrome_options.binary_location = chrome_path
            logger.info(f"Using Chrome at: {chrome_path}")
            chrome_found = True
            break
    
    if not chrome_found:
        logger.warning("Chrome binary not found in standard locations, using system default")
    
    try:
        # Find chromedriver
        exact_path = os.path.expanduser('~/.wdm/drivers/chromedriver/mac64/142.0.7444.175/chromedriver-mac-arm64/chromedriver')
        if os.path.exists(exact_path):
            logger.info(f"Using chromedriver at: {exact_path}")
            os.chmod(exact_path, 0o755)
            driver = webdriver.Chrome(
                service=Service(exact_path),
                options=chrome_options
            )
        else:
            logger.info("ChromeDriver not found at exact path, installing via ChromeDriverManager...")
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
        # Set timeouts to prevent hanging
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        # Anti-detection: Remove webdriver property from navigator object
        # This is a common way websites detect Selenium
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        logger.debug("Removed webdriver property from navigator object")
        
        elapsed = time.time() - start_time
        logger.info(f"Chrome driver created successfully in {elapsed:.2f} seconds")
        return driver
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Failed to create Chrome driver after {elapsed:.2f} seconds: {str(e)}")
        raise Exception(f"Failed to start Chrome: {str(e)}")

def get_driver():
    """Get or create a Chrome driver instance, recreating if session is invalid"""
    global driver_instance
    with driver_lock:
        if driver_instance is None:
            logger.info("Creating new Chrome driver instance")
            driver_instance = create_driver()
        elif not is_driver_session_valid(driver_instance):
            logger.warning("Driver session invalid, recreating driver")
            # Close old driver if it exists but is invalid
            if driver_instance is not None:
                try:
                    driver_instance.quit()
                    logger.info("Closed invalid driver instance")
                except Exception as e:
                    logger.warning(f"Error closing invalid driver: {e}")
            driver_instance = create_driver()
            logger.info("New driver instance created")
        else:
            logger.debug("Reusing existing valid driver instance")
        return driver_instance

def reset_driver():
    """Reset the global driver instance (close and recreate)"""
    global driver_instance, linkedin_logged_in
    logger.warning("Resetting driver instance (closing and clearing)")
    with driver_lock:
        if driver_instance is not None:
            try:
                driver_instance.quit()
                logger.info("Driver instance closed successfully")
            except Exception as e:
                logger.warning(f"Error closing driver during reset: {e}")
        driver_instance = None
        linkedin_logged_in = False  # Reset login status when driver is reset
        logger.info("Driver instance reset complete, login status cleared")

def login_to_linkedin(driver, wait):
    """Automatically log in to LinkedIn using environment variables with human-like behavior"""
    linkedin_email = os.environ.get('LINKEDIN_EMAIL')
    linkedin_password = os.environ.get('LINKEDIN_PASSWORD')
    
    if not linkedin_email or not linkedin_password:
        return False  # No credentials provided
    
    try:
        # Check if driver session is valid before attempting login
        if not is_driver_session_valid(driver):
            return False
        
        # Go to LinkedIn login page
        logger.info("Navigating to LinkedIn login page...")
        driver.get('https://www.linkedin.com/login')
        human_like_delay()  # Random 1-3 second delay
        
        # Move mouse randomly
        move_mouse_randomly(driver)
        short_delay()
        
        # Find and fill email field with human-like typing
        logger.info("Filling email field...")
        email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        email_field.click()
        short_delay()
        email_field.clear()
        
        # Type email with human-like delays between characters
        for char in linkedin_email:
            email_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))  # Random delay between keystrokes
        
        human_like_delay()  # Pause before password field
        
        # Find and fill password field with human-like typing
        logger.info("Filling password field...")
        password_field = driver.find_element(By.ID, "password")
        password_field.click()
        short_delay()
        password_field.clear()
        
        # Type password with human-like delays
        for char in linkedin_password:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        
        human_like_delay()  # Pause before clicking login
        
        # Move mouse to login button and click
        logger.info("Clicking login button...")
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        # Move mouse to button first (more human-like)
        actions = ActionChains(driver)
        actions.move_to_element(login_button)
        actions.pause(random.uniform(0.2, 0.5))
        actions.click()
        actions.perform()
        
        # Wait for login to complete with random delay
        human_like_delay()
        
        # Check if we're logged in (not on login page anymore)
        current_url = driver.current_url
        if 'login' not in current_url.lower():
            logger.info("Login successful")
            return True  # Successfully logged in
        
        # Check if LinkedIn is asking for verification code
        logger.info("Checking if verification code is required...")
        try:
            # Look for common verification/challenge indicators
            page_text = driver.page_source.lower()
            verification_indicators = [
                'verification code',
                'security challenge',
                'enter the code',
                'verify your identity',
                'challenge',
                'two-step verification'
            ]
            
            needs_verification = any(indicator in page_text for indicator in verification_indicators)
            
            if needs_verification:
                logger.warning("=" * 80)
                logger.warning("VERIFICATION CODE REQUIRED!")
                logger.warning("LinkedIn is asking for a verification code.")
                logger.warning("Please enter the code in the browser window.")
                logger.warning("The scraper will wait up to 5 minutes for you to complete verification...")
                logger.warning("=" * 80)
                
                # Wait for user to enter verification code (check every 2 seconds, up to 5 minutes)
                max_wait_time = 300  # 5 minutes
                check_interval = 2  # Check every 2 seconds
                elapsed_time = 0
                
                while elapsed_time < max_wait_time:
                    time.sleep(check_interval)
                    elapsed_time += check_interval
                    
                    # Check current URL
                    current_url = driver.current_url
                    if 'login' not in current_url.lower():
                        logger.info(f"✓ Verification completed! Logged in after {elapsed_time} seconds")
                        return True
                    
                    # Check if still on verification page
                    page_text = driver.page_source.lower()
                    still_verifying = any(indicator in page_text for indicator in verification_indicators)
                    
                    if not still_verifying and 'login' not in current_url.lower():
                        logger.info(f"✓ Verification completed! Logged in after {elapsed_time} seconds")
                        return True
                
                logger.warning(f"✗ Verification timeout after {max_wait_time} seconds (5 minutes)")
                return False
            else:
                logger.warning("Still on login page after login attempt (no verification detected)")
                return False
                
        except Exception as e:
            logger.warning(f"Error checking for verification: {e}")
            logger.warning("Still on login page after login attempt")
            return False
    except InvalidSessionIdException:
        # Reset driver if session is invalid
        reset_driver()
        return False
    except Exception as e:
        # If we get an invalid session error, return False so driver can be recreated
        error_msg = str(e).lower()
        if 'invalid session id' in error_msg or 'session' in error_msg:
            reset_driver()
        return False

def extract_employee_count(driver):
    """
    Extract employee count from LinkedIn /people/ page.
    Searches for "associated members" text using Ctrl+F approach (page source search).
    Also tries the specific element class: artdeco-carousel__heading
    Returns None if not found.
    """
    extract_start = time.time()
    logger.info("Starting employee count extraction (looking for 'associated members')...")
    
    try:
        # Wait for page to fully load with minimal delay
        logger.info("Waiting for page content to load...")
        short_delay()  # Reduced: just a short delay (0.3-0.8s) instead of 1-3s
        
        # Minimal human-like interaction (scrolling already done before extraction)
        logger.debug("Performing minimal human-like interactions...")
        move_mouse_randomly(driver)
        # Note: Scrolling is done in scrape_linkedin_company before calling this function, so we skip it here
        
        # PRIMARY METHOD: Element lookup (faster and more precise)
        logger.info("Primary method: Searching for element with class 'artdeco-carousel__heading'...")
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, ".artdeco-carousel__heading")
            logger.info(f"Found {len(elements)} elements with class 'artdeco-carousel__heading'")
            
            for el in elements:
                try:
                    txt = el.text.strip()
                    if txt:
                        logger.info(f"Found text in carousel heading: {txt[:200]}")
                        if 'associated members' in txt.lower():
                            m = re.search(r"([\d,]+)\s+associated\s+members", txt, re.IGNORECASE)
                            if m:
                                num_str = m.group(1).replace(",", "")
                                count = int(num_str)
                                logger.info(f"✓ [ELEMENT METHOD] Found employee count in carousel heading: {count}")
                                return count
                except Exception as e:
                    logger.debug(f"Error processing carousel element: {e}")
                    continue
        except Exception as e:
            logger.debug(f"Element search failed: {e}")
        
        # FALLBACK METHOD: Page source search (slower but more resilient to structure changes)
        logger.info("Fallback method: Searching page source for 'associated members'...")
        page_source_start = time.time()
        try:
            # Get page source (like Ctrl+F would search)
            page_source = driver.page_source
            page_source_elapsed = time.time() - page_source_start
            logger.info(f"Page source retrieved in {page_source_elapsed:.2f}s, length: {len(page_source)} characters")
            
            # Search for "associated members" in page source (case insensitive)
            if 'associated members' in page_source.lower():
                logger.info("Found 'associated members' text in page source")
                
                # Extract the number before "associated members"
                # Pattern: any number (with or without commas) followed by "associated members"
                pattern = r"([\d,]+)\s+associated\s+members"
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                
                if matches:
                    logger.info(f"Found {len(matches)} matches: {matches[:5]}")
                    # Use the first match
                    try:
                        num_str = str(matches[0]).replace(",", "")
                        count = int(num_str)
                        logger.info(f"✓ [HTML METHOD] Found employee count via page source search (fallback): {count}")
                        return count
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Could not convert '{matches[0]}' to int: {e}")
                else:
                    # Try to find context around "associated members" for debugging
                    idx = page_source.lower().find('associated members')
                    if idx > 0:
                        context = page_source[max(0, idx-100):idx+200]
                        logger.info(f"Found 'associated members' but no number pattern. Context: {context}")
            else:
                logger.warning("'associated members' text not found in page source")
                
        except Exception as e:
            page_source_elapsed = time.time() - page_source_start
            logger.warning(f"Page source search failed after {page_source_elapsed:.2f}s: {e}")
        
        total_elapsed = time.time() - extract_start
        logger.warning(f"Employee count extraction completed in {total_elapsed:.2f}s but 'associated members' not found")
        return None
    except Exception as e:
        total_elapsed = time.time() - extract_start
        logger.error(f"Exception in extract_employee_count after {total_elapsed:.2f}s: {e}")
        return None

# Track if we've logged in this session
linkedin_logged_in = False

def scrape_linkedin_company(url, driver, wait):
    """Scrape employee count from a LinkedIn company page - Direct /people/ navigation"""
    global linkedin_logged_in
    url_start_time = time.time()
    logger.info(f"Starting scrape for URL: {url}")
    
    try:
        # Log in to LinkedIn if we haven't already (and credentials are provided)
        if not linkedin_logged_in:
            login_start = time.time()
            logger.info("Attempting LinkedIn login...")
            if login_to_linkedin(driver, wait):
                linkedin_logged_in = True
                login_elapsed = time.time() - login_start
                logger.info(f"LinkedIn login successful in {login_elapsed:.2f} seconds")
            else:
                login_elapsed = time.time() - login_start
                logger.warning(f"LinkedIn login failed or skipped in {login_elapsed:.2f} seconds")
            # Continue anyway - maybe user is already logged in or will handle manually
        
        # Convert company URL to /people/ URL directly
        if '/people/' not in url:
            # Remove trailing slash and add /people/
            people_url = url.rstrip('/') + '/people/'
        else:
            people_url = url
        
        logger.info(f"Navigating to: {people_url}")
        # Set page load timeout
        driver.set_page_load_timeout(15)
        page_load_start = time.time()
        driver.get(people_url)
        page_load_elapsed = time.time() - page_load_start
        logger.info(f"Page loaded in {page_load_elapsed:.2f} seconds")
        
        # Wait for page to load - use WebDriverWait for efficiency
        wait_start = time.time()
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            wait_elapsed = time.time() - wait_start
            logger.debug(f"Body element found in {wait_elapsed:.2f} seconds")
        except Exception as e:
            wait_elapsed = time.time() - wait_start
            logger.warning(f"Body element wait timed out after {wait_elapsed:.2f} seconds: {e}")
        
        # Human-like behavior: random delay, mouse movement, scrolling (reduced)
        logger.debug("Simulating human-like behavior...")
        short_delay()  # Reduced: just a short delay (0.3-0.8s)
        move_mouse_randomly(driver)
        scroll_page_human_like(driver)  # Reduced scrolling (1-2 steps instead of 3-6)
        
        # Extract employee count
        extract_start = time.time()
        logger.debug("Extracting employee count...")
        count = extract_employee_count(driver)
        extract_elapsed = time.time() - extract_start
        logger.info(f"Employee count extraction took {extract_elapsed:.2f} seconds, result: {count}")
        
        total_elapsed = time.time() - url_start_time
        if count is not None:
            logger.info(f"Successfully scraped {url} in {total_elapsed:.2f} seconds, count: {count}")
            return {
                'url': url,
                'employee_count': str(count),
                'error': None
            }
        else:
            logger.warning(f"Could not extract employee count from {url} after {total_elapsed:.2f} seconds")
            return {
                'url': url,
                'employee_count': 'NA',
                'error': 'Could not parse employee count. LinkedIn may require authentication or the page structure changed.'
            }
    
    except InvalidSessionIdException as e:
        total_elapsed = time.time() - url_start_time
        logger.error(f"InvalidSessionIdException for {url} after {total_elapsed:.2f} seconds: {e}")
        # Reset driver for next attempt
        reset_driver()
        return {
            'url': url,
            'employee_count': 'NA',
            'error': 'Browser session expired. Please try again - the driver will be recreated automatically.'
        }
    except Exception as e:
        total_elapsed = time.time() - url_start_time
        error_msg = str(e)
        logger.error(f"Exception for {url} after {total_elapsed:.2f} seconds: {error_msg}")
        # Check for other session-related errors
        if 'invalid session id' in error_msg.lower() or 'session' in error_msg.lower():
            # Reset driver for next attempt
            reset_driver()
            error_msg = 'Browser session expired. Please try again - the driver will be recreated automatically.'
        elif 'timeout' in error_msg.lower():
            logger.error(f"Timeout error for {url}: {error_msg}")
            error_msg = 'Request timed out. LinkedIn may be blocking automated access or the page is slow to load.'
        return {
            'url': url,
            'employee_count': 'NA',
            'error': error_msg
        }

@app.route('/analyst2')
def analyst2_index():
    return render_template('analyst2/index.html')

@app.route('/analyst2/scrape-linkedin', methods=['POST'])
def scrape_linkedin():
    request_start_time = time.time()
    logger.info("=" * 80)
    logger.info(f"New scrape request received at {datetime.now().isoformat()}")
    
    try:
        data = request.get_json()
        
        if not data or 'urls' not in data:
            logger.error("No URLs provided in request")
            return jsonify({'success': False, 'error': 'No URLs provided'}), 400
        
        urls = data['urls']
        logger.info(f"Received {len(urls)} URLs to process")
        
        if not isinstance(urls, list):
            logger.error(f"URLs is not a list: {type(urls)}")
            return jsonify({'success': False, 'error': 'URLs must be a list'}), 400
        
        if not urls:
            logger.error("URL list is empty")
            return jsonify({'success': False, 'error': 'URL list cannot be empty'}), 400
        
        # Clean and validate URLs
        cleaned_urls = []
        for url in urls:
            url = url.strip()
            if url:
                # Ensure it's a LinkedIn company URL
                if 'linkedin.com/company/' not in url:
                    logger.warning(f"Skipping invalid URL (not a LinkedIn company URL): {url}")
                    continue
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                cleaned_urls.append(url)
        
        logger.info(f"After validation: {len(cleaned_urls)} valid URLs to process")
        if not cleaned_urls:
            logger.error("No valid LinkedIn company URLs after validation")
            return jsonify({'success': False, 'error': 'No valid LinkedIn company URLs provided'}), 400
        
        # Get driver
        driver_init_start = time.time()
        try:
            logger.info("Initializing Chrome driver...")
            driver = get_driver()
            wait = WebDriverWait(driver, 20)
            driver_init_elapsed = time.time() - driver_init_start
            logger.info(f"Driver initialized in {driver_init_elapsed:.2f} seconds")
        except Exception as e:
            driver_init_elapsed = time.time() - driver_init_start
            error_msg = str(e)
            logger.error(f"Driver initialization failed after {driver_init_elapsed:.2f} seconds: {error_msg}")
            if 'ChromeDriverManager' in error_msg or 'timeout' in error_msg.lower():
                error_msg = 'Chrome driver initialization is taking too long. This may happen on first run when downloading ChromeDriver. Please wait and try again, or ensure you have a stable internet connection.'
            return jsonify({
                'success': False,
                'error': f'Failed to initialize browser: {error_msg}. Make sure Chrome is installed.'
            }), 500
        
        # Scrape each URL with timeout protection
        results = []
        scraping_start_time = time.time()
        logger.info(f"Starting to scrape {len(cleaned_urls)} URLs...")
        try:
            for i, url in enumerate(cleaned_urls):
                url_num = i + 1
                logger.info(f"[{url_num}/{len(cleaned_urls)}] Processing URL {url_num}: {url}")
                url_iteration_start = time.time()
                try:
                    # Get fresh driver (will recreate if session is invalid)
                    driver = get_driver()
                    wait = WebDriverWait(driver, 20)
                    
                    result = scrape_linkedin_company(url, driver, wait)
                    results.append(result)
                    url_iteration_elapsed = time.time() - url_iteration_start
                    logger.info(f"[{url_num}/{len(cleaned_urls)}] Completed in {url_iteration_elapsed:.2f} seconds")
                    
                    # Random delay between URLs (reduced: 1-3 seconds) to avoid rate limiting
                    if i < len(cleaned_urls) - 1:  # Don't sleep after last URL
                        delay = random_delay(1.0, 3.0)  # Reduced from 2-5s to 1-3s
                        logger.debug(f"Waiting {delay:.2f} seconds before next URL...")
                        # Optional: move mouse during wait to simulate activity
                        move_mouse_randomly(driver)
                except InvalidSessionIdException as e:
                    url_iteration_elapsed = time.time() - url_iteration_start
                    logger.error(f"[{url_num}/{len(cleaned_urls)}] InvalidSessionIdException after {url_iteration_elapsed:.2f} seconds: {e}")
                    # Reset driver and retry once
                    logger.info(f"[{url_num}/{len(cleaned_urls)}] Resetting driver and retrying...")
                    reset_driver()
                    retry_start = time.time()
                    try:
                        driver = get_driver()
                        wait = WebDriverWait(driver, 20)
                        result = scrape_linkedin_company(url, driver, wait)
                        results.append(result)
                        retry_elapsed = time.time() - retry_start
                        logger.info(f"[{url_num}/{len(cleaned_urls)}] Retry successful in {retry_elapsed:.2f} seconds")
                    except Exception as retry_e:
                        retry_elapsed = time.time() - retry_start
                        logger.error(f"[{url_num}/{len(cleaned_urls)}] Retry failed after {retry_elapsed:.2f} seconds: {retry_e}")
                        results.append({
                            'url': url,
                            'employee_count': 'NA',
                            'error': f'Browser session expired and retry failed: {str(retry_e)}'
                        })
                except Exception as e:
                    url_iteration_elapsed = time.time() - url_iteration_start
                    error_msg = str(e)
                    logger.error(f"[{url_num}/{len(cleaned_urls)}] Exception after {url_iteration_elapsed:.2f} seconds: {error_msg}")
                    # Check for other session-related errors
                    if 'invalid session id' in error_msg.lower() or 'session' in error_msg.lower():
                        # Reset driver and retry once
                        logger.info(f"[{url_num}/{len(cleaned_urls)}] Session error detected, resetting driver and retrying...")
                        reset_driver()
                        retry_start = time.time()
                        try:
                            driver = get_driver()
                            wait = WebDriverWait(driver, 20)
                            result = scrape_linkedin_company(url, driver, wait)
                            results.append(result)
                            retry_elapsed = time.time() - retry_start
                            logger.info(f"[{url_num}/{len(cleaned_urls)}] Retry successful in {retry_elapsed:.2f} seconds")
                        except Exception as retry_e:
                            retry_elapsed = time.time() - retry_start
                            logger.error(f"[{url_num}/{len(cleaned_urls)}] Retry failed after {retry_elapsed:.2f} seconds: {retry_e}")
                            results.append({
                                'url': url,
                                'employee_count': 'NA',
                                'error': f'Browser session expired and retry failed: {str(retry_e)}'
                            })
                    else:
                        # If one URL fails, continue with others
                        results.append({
                            'url': url,
                            'employee_count': 'NA',
                            'error': f'Error processing URL: {error_msg}'
                        })
        finally:
            # Clean up driver if needed (but keep it for reuse)
            scraping_elapsed = time.time() - scraping_start_time
            logger.info(f"Completed scraping all URLs in {scraping_elapsed:.2f} seconds")
        
        total_request_time = time.time() - request_start_time
        successful = sum(1 for r in results if r.get('error') is None)
        failed = len(results) - successful
        logger.info(f"Request completed in {total_request_time:.2f} seconds: {successful} successful, {failed} failed")
        logger.info("=" * 80)
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        total_request_time = time.time() - request_start_time
        logger.error(f"Fatal error in scrape_linkedin after {total_request_time:.2f} seconds: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # Changed to 5001 to avoid macOS AirPlay conflict
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV') != 'production'
    # Increase timeout for long-running requests (30 minutes)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    logger.info(f"Starting Flask app on {host}:{port}")
    app.run(debug=debug, host=host, port=port, threaded=True)
