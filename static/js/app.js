
let currentPage = 1;

function getApiKey() {
    return document.getElementById('api-key').value;
}

function showAlert(message) {
    const alertContainer = document.getElementById('alert-container');
    const alert = document.createElement('p');
    alert.textContent = message;
    alert.style.color = 'green';
    alertContainer.appendChild(alert);
    
    setTimeout(() => alert.remove(), 5000);
}

function showError(message) {
    const alertContainer = document.getElementById('alert-container');
    const alert = document.createElement('p');
    alert.textContent = message;
    alert.style.color = 'red';
    alertContainer.appendChild(alert);
    
    setTimeout(() => alert.remove(), 5000);
}

// Upload file
document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const apiKey = getApiKey();
    const file = document.getElementById('file-input').files[0];
    if (!file) {
        showError('Please select a file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const uploadBtn = document.getElementById('upload-btn');
    const spinner = document.getElementById('upload-spinner');
    
    uploadBtn.disabled = true;
    spinner.style.display = 'inline';
    
    try {
        const response = await fetch(`/api/upload`, {
            method: 'POST',
            headers: {
                'X-API-KEY': apiKey
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert(`File "${data.Message}" uploaded successfully!`);
            document.getElementById('file-input').value = '';
            loadFiles();
        } else {
            showError(data.error || 'Upload failed');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        uploadBtn.disabled = false;
        spinner.style.display = 'none';
    }
});

// Load files list
async function loadFiles(page = 1) {
    const apiKey = getApiKey();
    if (!apiKey) {
        document.getElementById('files-container').innerHTML = 
            '<p>Please enter your API key above to view files</p>';
        return;
    }
    
    const perPage = document.getElementById('items-per-page').value;
    currentPage = page;
    
    document.getElementById('files-container').innerHTML = '<p>Loading files...</p>';
    
    try {
        const response = await fetch(`/api/list?page=${page}&per_page=${perPage}`, {
            headers: {
                'X-API-KEY': apiKey
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayFiles(data.files);
            displayPagination(data.pagination);
        } else {
            document.getElementById('files-container').innerHTML = 
                `<p style="color:red;">${data.error || 'Failed to load files'}</p>`;
        }
    } catch (error) {
        document.getElementById('files-container').innerHTML = 
            `<p style="color:red;">Network error: ${error.message}</p>`;
    }
}

// Display files
function displayFiles(files) {
    const container = document.getElementById('files-container');
    
    if (files.length === 0) {
        container.innerHTML = '<p>No files uploaded yet</p>';
        return;
    }
    
    let html = '<table border="1" cellpadding="10" cellspacing="0">';
    html += '<tr><th>Id</th><th>File Name</th><th>Status</th><th>Upload Date</th><th>Actions</th></tr>';
    
    files.forEach(file => {

        const toggle_button = file.status === 'DELETED' 
        ? ""
        : 
        `<button onclick="downloadFile(${file.id})">Download</button>
        <button onclick="deleteFile(${file.id})">Delete</button>`
        html += `
            <tr>
                <td>${file.id}</td>
                <td>${file.filename}</td>
                <td>${file.status}</td>
                <td>${file.date_created}</td>
                <td>${toggle_button}</td>
            </tr>
        `;
    });
    
    html += '</table>';
    container.innerHTML = html;
}

// Display pagination
function displayPagination(pagination) {
    const paginationEl = document.getElementById('pagination');
    
    if (pagination.pages <= 1) {
        paginationEl.innerHTML = '';
    }
    
    let html = '<p>';
    
    if (pagination.has_prev) {
        html += `<button onclick="loadFiles(${pagination.page - 1})">Previous</button> `;
    }
    
    html += `Page ${pagination.page} of ${pagination.pages} `;
    
    if (pagination.has_next) {
        html += `<button onclick="loadFiles(${pagination.page + 1})">Next</button>`;
    }
    
    html += '</p>';
    paginationEl.innerHTML = html;
}

// Download file
async function downloadFile(fileId) {
    const apiKey = getApiKey();
    
    try {
        const response = await fetch(`/api/download/${fileId}`, {
            headers: {
                'X-API-KEY': apiKey
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            navigator.clipboard.writeText(data.URL);
            showAlert('Download URL copied to clipboard')
        } else {
            showError(data.error || 'Failed to generate download link');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

// Delete file
async function deleteFile(fileId) {
    if (!confirm('Are you sure you want to delete this file?')) {
        return;
    }
    
    const apiKey = getApiKey();
    
    try {
        const response = await fetch(`/api/delete/${fileId}`, {
            method: 'DELETE',
            headers: {
                'X-API-KEY': apiKey
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showAlert('File deleted successfully');
            loadFiles(currentPage);
        } else {
            showError(data.error || 'Failed to delete file');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

