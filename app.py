from flask import Flask, render_template, request, jsonify
import pytesseract
from PIL import Image
import io
import base64
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import threading

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure Tesseract path (only if not in Docker/standard location)
# In Docker, Tesseract is in the standard PATH, so we only set this if needed
if os.path.exists('/opt/homebrew/bin/tesseract'):
    pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
# Docker/standard Linux installation will use the default PATH

# User agent for web scraping
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

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

def get_driver():
    """Get or create a Chrome driver instance"""
    global driver_instance
    with driver_lock:
        if driver_instance is None:
            chrome_options = Options()
            
            # Use headless mode for simplicity
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Find Chrome
            chrome_paths = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '/Applications/Chromium.app/Contents/MacOS/Chromium',
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    chrome_options.binary_location = chrome_path
                    break
            
            try:
                # Find chromedriver
                exact_path = os.path.expanduser('~/.wdm/drivers/chromedriver/mac64/142.0.7444.175/chromedriver-mac-arm64/chromedriver')
                if os.path.exists(exact_path):
                    os.chmod(exact_path, 0o755)
                    driver_instance = webdriver.Chrome(
                        service=Service(exact_path),
                        options=chrome_options
                    )
                else:
                    driver_instance = webdriver.Chrome(
                        service=Service(ChromeDriverManager().install()),
                        options=chrome_options
                    )
            except Exception as e:
                raise Exception(f"Failed to start Chrome: {str(e)}")
        return driver_instance

def login_to_linkedin(driver, wait):
    """Automatically log in to LinkedIn using environment variables"""
    linkedin_email = os.environ.get('LINKEDIN_EMAIL')
    linkedin_password = os.environ.get('LINKEDIN_PASSWORD')
    
    if not linkedin_email or not linkedin_password:
        return False  # No credentials provided
    
    try:
        # Go to LinkedIn login page
        driver.get('https://www.linkedin.com/login')
        time.sleep(2)
        
        # Find and fill email field
        email_field = wait.until(EC.presence_of_element_located((By.ID, "username")))
        email_field.clear()
        email_field.send_keys(linkedin_email)
        
        # Find and fill password field
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(linkedin_password)
        
        # Click login button
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        # Wait for login to complete (check for home page or any redirect)
        time.sleep(3)
        
        # Check if we're logged in (not on login page anymore)
        current_url = driver.current_url
        if 'login' not in current_url.lower():
            return True  # Successfully logged in
        
        return False
    except Exception as e:
        return False

def extract_employee_count(driver):
    """
    Extract employee count from LinkedIn /people/ page.
    Searches for "associated members" and extracts the number in front of it.
    Returns None if not found.
    """
    try:
        # Search for elements containing "associated members"
        # Try different selectors to find the text
        selectors = [
            "//*[contains(text(), 'associated members')]",
            "//span[contains(text(), 'associated members')]",
            "//div[contains(text(), 'associated members')]",
            "//a[contains(text(), 'associated members')]",
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for el in elements:
                    txt = el.text.strip()
                    if 'associated members' in txt.lower():
                        # Extract number before "associated members"
                        # Pattern: "1,234 associated members" or "1234 associated members"
                        m = re.search(r"([\d,]+)\s+associated\s+members", txt, re.IGNORECASE)
                        if m:
                            try:
                                num_str = m.group(1).replace(",", "")
                                return int(num_str)
                            except (ValueError, TypeError):
                                continue
            except Exception:
                continue
        
        # Fallback: Check page source
        try:
            page_source = driver.page_source
            m = re.search(r"([\d,]+)\s+associated\s+members", page_source, re.IGNORECASE)
            if m:
                try:
                    num_str = m.group(1).replace(",", "")
                    return int(num_str)
                except (ValueError, TypeError):
                    pass
        except Exception:
            pass
        
        return None
    except Exception:
        return None

# Track if we've logged in this session
linkedin_logged_in = False

def scrape_linkedin_company(url, driver, wait):
    """Scrape employee count from a LinkedIn company page - Direct /people/ navigation"""
    global linkedin_logged_in
    
    try:
        # Log in to LinkedIn if we haven't already (and credentials are provided)
        if not linkedin_logged_in:
            if login_to_linkedin(driver, wait):
                linkedin_logged_in = True
            # Continue anyway - maybe user is already logged in or will handle manually
        
        # Convert company URL to /people/ URL directly
        if '/people/' not in url:
            # Remove trailing slash and add /people/
            people_url = url.rstrip('/') + '/people/'
        else:
            people_url = url
        
        # Set page load timeout
        driver.set_page_load_timeout(15)
        driver.get(people_url)
        
        # Wait for page to load - use WebDriverWait for efficiency
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except:
            pass  # Continue even if wait times out
        
        # Give minimal time for dynamic content to load
        time.sleep(1.5)
        
        # Extract employee count
        count = extract_employee_count(driver)
        
        if count is not None:
            return {
                'url': url,
                'employee_count': str(count),
                'error': None
            }
        else:
            return {
                'url': url,
                'employee_count': 'NA',
                'error': 'Could not parse employee count. LinkedIn may require authentication or the page structure changed.'
            }
    
    except Exception as e:
        error_msg = str(e)
        if 'timeout' in error_msg.lower():
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
    try:
        data = request.get_json()
        
        if not data or 'urls' not in data:
            return jsonify({'success': False, 'error': 'No URLs provided'}), 400
        
        urls = data['urls']
        
        if not isinstance(urls, list):
            return jsonify({'success': False, 'error': 'URLs must be a list'}), 400
        
        if not urls:
            return jsonify({'success': False, 'error': 'URL list cannot be empty'}), 400
        
        # Clean and validate URLs
        cleaned_urls = []
        for url in urls:
            url = url.strip()
            if url:
                # Ensure it's a LinkedIn company URL
                if 'linkedin.com/company/' not in url:
                    continue
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                cleaned_urls.append(url)
        
        if not cleaned_urls:
            return jsonify({'success': False, 'error': 'No valid LinkedIn company URLs provided'}), 400
        
        # Get driver
        try:
            driver = get_driver()
            wait = WebDriverWait(driver, 20)
        except Exception as e:
            error_msg = str(e)
            if 'ChromeDriverManager' in error_msg or 'timeout' in error_msg.lower():
                error_msg = 'Chrome driver initialization is taking too long. This may happen on first run when downloading ChromeDriver. Please wait and try again, or ensure you have a stable internet connection.'
            return jsonify({
                'success': False,
                'error': f'Failed to initialize browser: {error_msg}. Make sure Chrome is installed.'
            }), 500
        
        # Scrape each URL with timeout protection
        results = []
        try:
            for i, url in enumerate(cleaned_urls):
                try:
                    result = scrape_linkedin_company(url, driver, wait)
                    results.append(result)
                    # OPTIMIZATION: Reduced delay between requests (was 2s, now 0.5s)
                    # LinkedIn may still rate limit, but this is faster for testing
                    if i < len(cleaned_urls) - 1:  # Don't sleep after last URL
                        time.sleep(0.5)
                except Exception as e:
                    # If one URL fails, continue with others
                    results.append({
                        'url': url,
                        'employee_count': 'NA',
                        'error': f'Error processing URL: {str(e)}'
                    })
        finally:
            # Clean up driver if needed (but keep it for reuse)
            pass
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # Changed to 5001 to avoid macOS AirPlay conflict
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host=host, port=port)
