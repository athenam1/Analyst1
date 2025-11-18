# Analyst Portal

A unified web portal hosting two powerful analysis tools: **Analyst1** for OCR text extraction and **Analyst2** for web information gathering. Both tools are containerized and can be run together in a single Docker container.

## Tools

### Analyst1 - Screenshot to Text Converter
Extract text from images and screenshots using OCR technology.

**Features:**
- Paste screenshots directly using Ctrl+V (Cmd+V on Mac)
- Upload images via click or drag and drop
- OCR processing using Tesseract
- One-click copy to clipboard
- Modern, responsive UI

### Analyst2 - Web Information Gatherer
Extract content, links, and images from any website.

**Features:**
- Extract text content from web pages
- Gather all links found on a page
- Extract images with metadata
- Clean, formatted output
- Copy content to clipboard

## Quick Start with Docker

The easiest way to run the portal is using Docker Compose:

```bash
# Build and start the portal
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the portal
docker-compose down
```

The portal will be available at: `http://localhost:5000`

## Manual Installation

### Prerequisites

1. **Python 3.11+** installed on your system
2. **Tesseract OCR** installed (for Analyst1):
   - **macOS**: `brew install tesseract`
   - **Linux (Ubuntu/Debian)**: `sudo apt-get install tesseract-ocr`
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/athenam1/Analyst1.git
   cd Analyst1
   ```

2. Create a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the Flask application:
   ```bash
   python app.py
   ```

5. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## Usage

### Portal Landing Page
When you first visit the portal, you'll see a landing page with two tool cards. Click on either **Analyst1** or **Analyst2** to use that tool.

### Using Analyst1 (OCR)
1. Navigate to `/analyst1` or click the Analyst1 card
2. Paste a screenshot (Ctrl+V / Cmd+V) or upload an image
3. View the extracted text
4. Click "Copy to Clipboard" to copy the text

### Using Analyst2 (Web Scraping)
1. Navigate to `/analyst2` or click the Analyst2 card
2. Enter a URL in the input field
3. Click "Gather Info" to extract information
4. View the extracted content, links, and images
5. Copy content using the "Copy Content" button

## Docker Configuration

The application is fully containerized. The `Dockerfile` includes:
- Python 3.11 base image
- Tesseract OCR for Analyst1
- All required system and Python dependencies
- Health checks for monitoring

The `docker-compose.yml` file configures:
- Port mapping (5000:5000)
- Environment variables
- Automatic restart policy
- Health checks

## Project Structure

```
Analyst1/
├── app.py                 # Unified Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image configuration
├── docker-compose.yml    # Docker Compose configuration
├── templates/
│   ├── portal.html       # Landing page
│   ├── analyst1/
│   │   └── index.html    # Analyst1 interface
│   └── analyst2/
│       └── index.html    # Analyst2 interface
└── static/
    ├── css/
    │   ├── portal.css     # Portal styles
    │   ├── analyst1/
    │   │   └── style.css  # Analyst1 styles
    │   └── analyst2/
    │       └── style.css  # Analyst2 styles
    └── js/
        ├── analyst1/
        │   └── app.js     # Analyst1 JavaScript
        └── analyst2/
            └── app.js     # Analyst2 JavaScript
```

## API Endpoints

### Analyst1
- `GET /analyst1` - Analyst1 interface
- `POST /analyst1/extract-text` - Extract text from image

### Analyst2
- `GET /analyst2` - Analyst2 interface
- `POST /analyst2/gather-info` - Gather information from URL

### Portal
- `GET /` - Portal landing page

## Troubleshooting

### Tesseract not found (Analyst1)
If running locally (not in Docker), you may need to configure the Tesseract path in `app.py`. The Docker container has Tesseract pre-installed.

### Port already in use
Change the port in `docker-compose.yml` or set the `PORT` environment variable.

### Web scraping errors (Analyst2)
Some websites may block automated requests. The tool uses a standard user agent, but some sites may still restrict access.

## Technology Stack

- **Backend**: Flask (Python)
- **OCR Engine**: Tesseract OCR (Analyst1)
- **Web Scraping**: BeautifulSoup4, Requests (Analyst2)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Containerization**: Docker, Docker Compose

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
