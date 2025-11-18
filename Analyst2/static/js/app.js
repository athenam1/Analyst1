// Get DOM elements
const urlInput = document.getElementById('urlInput');
const gatherBtn = document.getElementById('gatherBtn');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const errorMessage = document.getElementById('errorMessage');
const resultSection = document.getElementById('resultSection');
const resultUrl = document.getElementById('resultUrl');
const resultTitleText = document.getElementById('resultTitleText');
const resultContent = document.getElementById('resultContent');
const copyContentBtn = document.getElementById('copyContentBtn');
const clearBtn = document.getElementById('clearBtn');
const linksCard = document.getElementById('linksCard');
const linksList = document.getElementById('linksList');
const linksCount = document.getElementById('linksCount');
const imagesCard = document.getElementById('imagesCard');
const imagesList = document.getElementById('imagesList');
const imagesCount = document.getElementById('imagesCount');

// Handle Enter key press
urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        gatherInfo();
    }
});

// Handle gather button click
gatherBtn.addEventListener('click', gatherInfo);

// Gather information from URL
async function gatherInfo() {
    const url = urlInput.value.trim();
    
    if (!url) {
        showError('Please enter a URL');
        return;
    }
    
    // Hide previous results and errors
    hideError();
    resultSection.style.display = 'none';
    
    // Show loading
    loading.style.display = 'block';
    gatherBtn.disabled = true;
    
    try {
        const response = await fetch('/gather-info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        const data = await response.json();
        
        // Hide loading
        loading.style.display = 'none';
        gatherBtn.disabled = false;
        
        if (data.success) {
            // Display results
            displayResults(data);
        } else {
            showError(data.error || 'Failed to gather information');
        }
    } catch (err) {
        loading.style.display = 'none';
        gatherBtn.disabled = false;
        showError('Error: ' + err.message);
    }
}

// Display gathered information
function displayResults(data) {
    // Set URL
    resultUrl.textContent = data.url;
    
    // Set title
    resultTitleText.textContent = data.title || 'No title found';
    
    // Set content
    resultContent.value = data.content || 'No content found';
    
    // Display links
    if (data.links && data.links.length > 0) {
        linksCount.textContent = data.links.length;
        linksList.innerHTML = '';
        data.links.forEach(link => {
            const linkItem = document.createElement('div');
            linkItem.className = 'link-item';
            linkItem.innerHTML = `
                <a href="${link.url}" target="_blank" rel="noopener noreferrer">${link.url}</a>
                ${link.text ? `<div class="link-text">${escapeHtml(link.text)}</div>` : ''}
            `;
            linksList.appendChild(linkItem);
        });
        linksCard.style.display = 'block';
    } else {
        linksCard.style.display = 'none';
    }
    
    // Display images
    if (data.images && data.images.length > 0) {
        imagesCount.textContent = data.images.length;
        imagesList.innerHTML = '';
        data.images.forEach(image => {
            const imageItem = document.createElement('div');
            imageItem.className = 'image-item';
            imageItem.innerHTML = `
                <img src="${image.url}" alt="${escapeHtml(image.alt)}" onerror="this.style.display='none'">
                <div class="image-info">
                    <div class="image-alt">${escapeHtml(image.alt)}</div>
                    <div class="image-url">${image.url}</div>
                </div>
            `;
            imagesList.appendChild(imageItem);
        });
        imagesCard.style.display = 'block';
    } else {
        imagesCard.style.display = 'none';
    }
    
    // Show result section
    resultSection.style.display = 'block';
    
    // Scroll to results
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Copy content to clipboard
copyContentBtn.addEventListener('click', async () => {
    try {
        await navigator.clipboard.writeText(resultContent.value);
        copyContentBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyContentBtn.textContent = 'Copy Content';
        }, 2000);
    } catch (err) {
        // Fallback for older browsers
        resultContent.select();
        document.execCommand('copy');
        copyContentBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyContentBtn.textContent = 'Copy Content';
        }, 2000);
    }
});

// Clear and reset
clearBtn.addEventListener('click', () => {
    urlInput.value = '';
    resultSection.style.display = 'none';
    hideError();
    urlInput.focus();
});

// Show error
function showError(message) {
    errorMessage.textContent = message;
    error.style.display = 'block';
    error.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Hide error
function hideError() {
    error.style.display = 'none';
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

