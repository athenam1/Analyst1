// Get DOM elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewSection = document.getElementById('previewSection');
const previewImage = document.getElementById('previewImage');
const resultSection = document.getElementById('resultSection');
const extractedText = document.getElementById('extractedText');
const copyBtn = document.getElementById('copyBtn');
const clearBtn = document.getElementById('clearBtn');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const errorMessage = document.getElementById('errorMessage');

// Handle paste event
document.addEventListener('paste', async (e) => {
    const items = e.clipboardData.items;
    
    for (let item of items) {
        if (item.type.indexOf('image') !== -1) {
            e.preventDefault();
            const blob = item.getAsFile();
            await processImage(blob);
            break;
        }
    }
});

// Handle file input
fileInput.addEventListener('change', async (e) => {
    if (e.target.files.length > 0) {
        await processImage(e.target.files[0]);
    }
});

// Handle click on upload area
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// Handle drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', async (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    if (e.dataTransfer.files.length > 0) {
        await processImage(e.dataTransfer.files[0]);
    }
});

// Process image and extract text
async function processImage(file) {
    // Hide error
    hideError();
    
    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        previewSection.style.display = 'block';
        uploadArea.style.display = 'none';
    };
    reader.readAsDataURL(file);
    
    // Convert file to base64
    const base64 = await fileToBase64(file);
    
    // Show loading
    loading.style.display = 'block';
    resultSection.style.display = 'none';
    
    try {
        // Send to server
        const response = await fetch('/extract-text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: base64 })
        });
        
        const data = await response.json();
        
        // Hide loading
        loading.style.display = 'none';
        
        if (data.success) {
            // Show result
            extractedText.value = data.text;
            resultSection.style.display = 'block';
        } else {
            showError(data.error || 'Failed to extract text from image');
        }
    } catch (err) {
        loading.style.display = 'none';
        showError('Error: ' + err.message);
    }
}

// Convert file to base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
    });
}

// Copy text to clipboard
copyBtn.addEventListener('click', async () => {
    try {
        await navigator.clipboard.writeText(extractedText.value);
        copyBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyBtn.textContent = 'Copy to Clipboard';
        }, 2000);
    } catch (err) {
        // Fallback for older browsers
        extractedText.select();
        document.execCommand('copy');
        copyBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyBtn.textContent = 'Copy to Clipboard';
        }, 2000);
    }
});

// Clear and reset
clearBtn.addEventListener('click', () => {
    previewSection.style.display = 'none';
    resultSection.style.display = 'none';
    uploadArea.style.display = 'block';
    fileInput.value = '';
    hideError();
});

// Show error
function showError(message) {
    errorMessage.textContent = message;
    error.style.display = 'block';
}

// Hide error
function hideError() {
    error.style.display = 'none';
}

