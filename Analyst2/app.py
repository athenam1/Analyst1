from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
import re

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# User agent to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def is_valid_url(url):
    """Check if the URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def clean_text(text):
    """Clean and format extracted text"""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def extract_content(url):
    """Extract content from a URL"""
    try:
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Validate URL
        if not is_valid_url(url):
            return {
                'success': False,
                'error': 'Invalid URL format'
            }
        
        # Fetch the page
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "meta", "link"]):
            script.decompose()
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text() if title else "No title found"
        
        # Extract main content - try different strategies
        content = None
        
        # Try to find main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|post|article', re.I))
        
        if main_content:
            content = main_content.get_text(separator='\n', strip=True)
        else:
            # Fallback to body
            body = soup.find('body')
            if body:
                content = body.get_text(separator='\n', strip=True)
        
        # Clean the content
        content = clean_text(content) if content else "No content found"
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True)
            if href and text:
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, href)
                links.append({
                    'text': text[:100],  # Limit text length
                    'url': absolute_url
                })
        
        # Extract images
        images = []
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            alt = img.get('alt', 'No alt text')
            if src:
                absolute_url = urljoin(url, src)
                images.append({
                    'alt': alt[:100],
                    'url': absolute_url
                })
        
        return {
            'success': True,
            'url': url,
            'title': clean_text(title_text),
            'content': content,
            'links': links[:50],  # Limit to 50 links
            'images': images[:20],  # Limit to 20 images
            'status_code': response.status_code
        }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timed out. The website may be slow or unreachable.'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Connection error. Please check the URL and your internet connection.'
        }
    except requests.exceptions.HTTPError as e:
        return {
            'success': False,
            'error': f'HTTP error: {e.response.status_code} - {e.response.reason}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error fetching content: {str(e)}'
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gather-info', methods=['POST'])
def gather_info():
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': 'No URL provided'}), 400
        
        url = data['url'].strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL cannot be empty'}), 400
        
        # Extract content from URL
        result = extract_content(url)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host=host, port=port)

