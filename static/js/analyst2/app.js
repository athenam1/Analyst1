// Get DOM elements
const urlsInput = document.getElementById('urlsInput');
const scrapeBtn = document.getElementById('scrapeBtn');
const clearBtn = document.getElementById('clearBtn');
const loading = document.getElementById('loading');
const loadingText = document.getElementById('loadingText');
const progressInfo = document.getElementById('progressInfo');
const error = document.getElementById('error');
const errorMessage = document.getElementById('errorMessage');
const resultSection = document.getElementById('resultSection');
const resultsTableBody = document.getElementById('resultsTableBody');
const exportCsvBtn = document.getElementById('exportCsvBtn');
const copyTableBtn = document.getElementById('copyTableBtn');

let resultsData = [];

// Handle scrape button click
scrapeBtn.addEventListener('click', scrapeLinkedIn);

// Handle clear button click
clearBtn.addEventListener('click', () => {
    urlsInput.value = '';
    resultSection.style.display = 'none';
    clearBtn.style.display = 'none';
    hideError();
    resultsData = [];
});

// Scrape LinkedIn URLs
async function scrapeLinkedIn() {
    const urlsText = urlsInput.value.trim();
    
    if (!urlsText) {
        showError('Please enter at least one LinkedIn company URL');
        return;
    }
    
    // Parse URLs from textarea (one per line)
    const urls = urlsText.split('\n')
        .map(url => url.trim())
        .filter(url => url.length > 0);
    
    if (urls.length === 0) {
        showError('Please enter at least one valid LinkedIn company URL');
        return;
    }
    
    // Hide previous results and errors
    hideError();
    resultSection.style.display = 'none';
    
    // Show loading
    loading.style.display = 'block';
    scrapeBtn.disabled = true;
    loadingText.textContent = `Processing ${urls.length} LinkedIn URLs...`;
    progressInfo.textContent = '';
    
    try {
        // Add timeout to fetch request (5 minutes for multiple URLs)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minutes
        
        const response = await fetch('/analyst2/scrape-linkedin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ urls: urls }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Server error (${response.status}): ${errorText}`);
        }
        
        const data = await response.json();
        
        // Hide loading
        loading.style.display = 'none';
        scrapeBtn.disabled = false;
        
        if (data.success) {
            // Display results
            resultsData = data.results;
            displayResults(data.results);
        } else {
            showError(data.error || 'Failed to scrape LinkedIn URLs');
        }
    } catch (err) {
        loading.style.display = 'none';
        scrapeBtn.disabled = false;
        
        let errorMessage = 'Error: ';
        if (err.name === 'AbortError') {
            errorMessage = 'Request timed out. This may take a while for multiple URLs. Please try with fewer URLs or check if the server is still running.';
        } else if (err.message) {
            errorMessage += err.message;
        } else {
            errorMessage += 'Failed to connect to server. Make sure the Flask app is running.';
        }
        
        showError(errorMessage);
        console.error('Fetch error:', err);
    }
}

// Display results in table
function displayResults(results) {
    resultsTableBody.innerHTML = '';
    
    results.forEach(result => {
        const row = document.createElement('tr');
        
        const urlCell = document.createElement('td');
        const urlLink = document.createElement('a');
        urlLink.href = result.url;
        urlLink.target = '_blank';
        urlLink.rel = 'noopener noreferrer';
        urlLink.textContent = result.url;
        urlLink.style.color = '#f5576c';
        urlLink.style.textDecoration = 'none';
        urlLink.style.wordBreak = 'break-all';
        urlLink.addEventListener('mouseenter', () => {
            urlLink.style.textDecoration = 'underline';
        });
        urlLink.addEventListener('mouseleave', () => {
            urlLink.style.textDecoration = 'none';
        });
        urlCell.appendChild(urlLink);
        
        const countCell = document.createElement('td');
        countCell.textContent = result.employee_count;
        countCell.className = result.employee_count === 'NA' ? 'status-na' : 'status-success';
        
        const statusCell = document.createElement('td');
        if (result.error) {
            statusCell.textContent = result.error;
            statusCell.className = 'status-error';
        } else {
            statusCell.textContent = 'Success';
            statusCell.className = 'status-success';
        }
        
        row.appendChild(urlCell);
        row.appendChild(countCell);
        row.appendChild(statusCell);
        resultsTableBody.appendChild(row);
    });
    
    // Show result section and clear button
    resultSection.style.display = 'block';
    clearBtn.style.display = 'inline-block';
    
    // Scroll to results
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Export to CSV
exportCsvBtn.addEventListener('click', () => {
    if (resultsData.length === 0) {
        showError('No results to export');
        return;
    }
    
    // Create CSV content
    let csv = 'LinkedIn URL,Employee Count,Status\n';
    resultsData.forEach(result => {
        const url = result.url;
        const count = result.employee_count;
        const status = result.error || 'Success';
        csv += `"${url}","${count}","${status}"\n`;
    });
    
    // Create download link
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `linkedin_employee_counts_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
});

// Copy table to clipboard
copyTableBtn.addEventListener('click', async () => {
    if (resultsData.length === 0) {
        showError('No results to copy');
        return;
    }
    
    // Create tab-separated text
    let text = 'LinkedIn URL\tEmployee Count\tStatus\n';
    resultsData.forEach(result => {
        const url = result.url;
        const count = result.employee_count;
        const status = result.error || 'Success';
        text += `${url}\t${count}\t${status}\n`;
    });
    
    try {
        await navigator.clipboard.writeText(text);
        copyTableBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyTableBtn.textContent = 'Copy Table';
        }, 2000);
    } catch (err) {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        copyTableBtn.textContent = 'Copied!';
        setTimeout(() => {
            copyTableBtn.textContent = 'Copy Table';
        }, 2000);
    }
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
