# Analyst1 - Screenshot to Text Converter

A local web application that converts screenshots and images into copy-pasteable text using OCR (Optical Character Recognition).

## Features

- **Paste Screenshots**: Simply paste screenshots directly using Ctrl+V (Cmd+V on Mac)
- **Upload Images**: Click to upload or drag and drop image files
- **OCR Processing**: Extracts text from images using Tesseract OCR
- **Copy to Clipboard**: One-click copy of extracted text
- **Modern UI**: Clean, responsive interface

## Prerequisites

1. **Python 3.7+** installed on your system
2. **Tesseract OCR** installed:
   - **macOS**: `brew install tesseract`
   - **Linux (Ubuntu/Debian)**: `sudo apt-get install tesseract-ocr`
   - **Windows**: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki) and install

## Installation

1. Navigate to the project directory:
   ```bash
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

## Running the Application

1. Make sure your virtual environment is activated (if using one)

2. Run the Flask application:
   ```bash
   python app.py
   ```

3. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

## Usage

1. **Paste a screenshot**: Take a screenshot and press Ctrl+V (Cmd+V on Mac) while the page is focused
2. **Upload an image**: Click the upload area or drag and drop an image file
3. **View extracted text**: The text will appear in the text area below
4. **Copy text**: Click the "Copy to Clipboard" button to copy the extracted text

## Troubleshooting

### Tesseract not found

If you get an error about Tesseract not being found, you may need to configure the path in `app.py`. Uncomment and adjust the line:

```python
pytesseract.pytesseract.tesseract_cmd = '/path/to/tesseract'
```

Common paths:
- macOS (Homebrew): `/opt/homebrew/bin/tesseract` or `/usr/local/bin/tesseract`
- Linux: Usually `/usr/bin/tesseract`
- Windows: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### Port already in use

If port 5000 is already in use, you can change it in `app.py`:

```python
app.run(debug=True, host='127.0.0.1', port=5001)  # Change 5001 to any available port
```

## License

This project is open source and available for personal use.

