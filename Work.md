[START OF AI INSTRUCTION BLOCK]
TASK: Implement Image Pasting, Resizing, and Smart Preview for Notes Feature
FILE: app/image_routes.py
CONTEXT: Create a backend endpoint to handle image uploads from the notes paste action.
This endpoint must resize the image to a thumbnail (max 500x500) for inline display,
save the original, and return a unique ID to the frontend.
import os
import uuid
import json
import io
from PIL import Image, ImageDraw, ImageFont
from flask import Blueprint, render_template, request, jsonify, send_file

... (Keep existing imports like os, json, datetime, cv2, np, etc.)
IMAGE_UPLOAD_DIR = os.path.join('data', 'notes_images') # Add this global constant

Create the upload directory if it doesn't exist (CRITICAL)
os.makedirs(IMAGE_UPLOAD_DIR, exist_ok=True)

Add the new API route for image upload and resizing
@image_bp.route('/api/notes_image_upload', methods=['POST'])
def notes_image_upload():
"""
Handles image uploads from the notes editor paste action.
Saves original and thumbnail (max 500x500), and returns the ID.
"""
try:
if 'image' not in request.files:
return jsonify({'success': False, 'error': 'No image file'}), 400

    file = request.files['image']
    
    # Generate unique ID for this image pair
    image_id = str(uuid.uuid4())
    original_path = os.path.join(IMAGE_UPLOAD_DIR, f'{image_id}_original.webp')
    thumbnail_path = os.path.join(IMAGE_UPLOAD_DIR, f'{image_id}_thumb.webp')
    
    # Load image using PIL
    img = Image.open(file.stream).convert("RGB")
    
    # 1. Save Original (as WebP for better compression/quality trade-off)
    img.save(original_path, 'WEBP', quality=90)

    # 2. Create Thumbnail (max 500x500)
    thumb = img.copy()
    thumb.thumbnail((500, 500))
    
    # Save Thumbnail (as WebP)
    thumb.save(thumbnail_path, 'WEBP', quality=85)
    
    return jsonify({
        'success': True,
        'id': image_id,
        'url_thumb': f'/image/notes_images/{image_id}/thumb',
        'url_original': f'/image/notes_images/{image_id}/original'
    })
    
except Exception as e:
    print(f"[ERROR] Notes image upload failed: {str(e)}")
    return jsonify({'success': False, 'error': str(e)}), 500
Add the route to serve the stored images
@image_bp.route('/notes_images/<image_id>/<size>', methods=['GET'])
def serve_notes_image(image_id, size):
"""Serve the original or thumbnail notes image by ID."""
try:
if size == 'original':
filename = f'{image_id}_original.webp'
elif size == 'thumb':
filename = f'{image_id}_thumb.webp'
else:
return jsonify({'error': 'Invalid size parameter'}), 400

    filepath = os.path.join(IMAGE_UPLOAD_DIR, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'Image not found'}), 404
        
    return send_file(filepath, mimetype='image/webp')
    
except Exception as e:
    return jsonify({'error': str(e)}), 500
FILE: app/static/css/style.css
/* CONTEXT: Add CSS for embedded notes image, the image row, and the Smart Preview /
/ Image Embedded Styles */
.notes-image-embed {
display: block;
max-width: 100%;
height: auto;
border-radius: 4px;
margin: 5px 0;
cursor: pointer;
transition: all 0.2s;
box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.notes-image-embed:hover {
box-shadow: 0 4px 8px rgba(0, 224, 255, 0.5);
filter: brightness(1.1);
}

/* Image Row for multiple inline images /
.notes-image-row {
display: flex;
gap: 8px; / Khoảng cách giữa các ảnh */
margin: 8px 0;
align-items: center;
justify-content: flex-start;
flex-wrap: wrap;
}

.notes-image-row .notes-image-embed {
flex-shrink: 0;
max-width: 150px; /* Max width for compact display in a row */
height: auto;
}

/* Image Preview Tooltip Styles (Smart Preview) /
#notes-image-preview-tooltip {
position: fixed;
top: 0;
left: 0;
z-index: 10000;
background: #1a1d21;
border: 2px solid #00e0ff;
border-radius: 8px;
padding: 5px;
box-shadow: 0 8px 32px rgba(0, 224, 255, 0.3), 0 0 10px rgba(0, 224, 255, 0.2);
display: none;
pointer-events: none;
max-width: 400px; / Max preview size */
max-height: 400px;
overflow: hidden;
}

#notes-image-preview-tooltip img {
display: block;
max-width: 100%;
max-height: 100%;
height: auto;
border-radius: 4px;
}
/* Ensure the preview tooltip is added to the HTML/Body so it can float over everything */

#notes-lightbox-modal .modal-content {
background: rgba(0, 0, 0, 0.8);
border: none;
}

#notes-lightbox-modal .modal-body {
display: flex;
justify-content: center;
align-items: center;
max-height: 90vh;
padding: 0;
}

#notes-lightbox-modal img {
max-width: 100%;
max-height: 100%;
object-fit: contain;
display: block;
}

#notes-image-preview-tooltip {
position: fixed;
top: 0; left: 0;
z-index: 10000;
background: #1a1d21;
border: 2px solid #00e0ff;
border-radius: 8px;
padding: 5px;
box-shadow: 0 8px 32px rgba(0, 224, 255, 0.3), 0 0 10px rgba(0, 224, 255, 0.2);
display: none;
pointer-events: none;
max-width: 400px;
max-height: 400px;
overflow: hidden;
}

#notes-image-preview-tooltip img {
display: block;
max-width: 100%;
max-height: 100%;
height: auto;
border-radius: 4px;
}

#notes-image-preview-tooltip {
position: fixed;
top: 0; left: 0;
z-index: 10000;
background: #1a1d21;
border: 2px solid #00e0ff;
border-radius: 8px;
padding: 5px;
box-shadow: 0 8px 32px rgba(0, 224, 255, 0.3), 0 0 10px rgba(0, 224, 255, 0.2);
display: none;
pointer-events: none;
max-width: 400px;
max-height: 400px;
overflow: hidden;
}

#notes-image-preview-tooltip img {
display: block;
max-width: 100%;
max-height: 100%;
height: auto;
border-radius: 4px;
}

#notes-image-preview-tooltip {
position: fixed;
top: 0; left: 0;
z-index: 10000;
background: #1a1d21;
border: 2px solid #00e0ff;
border-radius: 8px;
padding: 5px;
box-shadow: 0 8px 32px rgba(0, 224, 255, 0.3), 0 0 10px rgba(0, 224, 255, 0.2);
display: none;
pointer-events: none;
max-width: 400px;
max-height: 400px;
overflow: hidden;
}

#notes-image-preview-tooltip img {
display: block;
max-width: 100%;
max-height: 100%;
height: auto;
border-radius: 4px;
}

#notes-image-preview-tooltip {
position: fixed;
top: 0; left: 0;
z-index: 10000;
background: #1a1d21;
border: 2px solid #00e0ff;
border-radius: 8px;
padding: 5px;
box-shadow: 0 8px 32px rgba(0, 224, 255, 0.3), 0 0 10px rgba(0, 224, 255, 0.2);
display: none;
pointer-events: none;
max-width: 400px;
max-height: 400px;
overflow: hidden;
}

#notes-image-preview-tooltip img {
display: block;
max-width: 100%;
max-height: 100%;
height: auto;
border-radius: 4px;
}

#notes-image-preview-tooltip {
position: fixed;
top: 0; left: 0;
z-index: 10000;
background: #1a1d21;
border: 2px solid #00e0ff;
border-radius: 8px;
padding: 5px;
box-shadow: 0 8px 32px rgba(0, 224, 255, 0.3), 0 0 10px rgba(0, 224, 255, 0.2);
display: none;
pointer-events: none;
max-width: 400px;
max-height: 400px;
overflow: hidden;
}

#notes-image-preview-tooltip img {
display: block;
max-width: 100%;
max-height: 100%;
height: auto;
border-radius: 4px;
}

#notes-image-preview-tooltip {
position: fixed;
top: 0; left: 0;
z-index: 10000;
background: #1a1d21;
border: 2px solid #00e0ff;
border-radius: 8px;
padding: 5px;
box-shadow: 0 8px 32px rgba(0, 224, 255, 0.3), 0 0 10px rgba(0, 224, 255, 0.2);
display: none;
pointer-events: none;
max-width: 400px;
max-height: 400px;
overflow: hidden;
}

#notes-image-preview-tooltip img {
display: block;
max-width: 100%;
max-height: 100%;
height: auto;
border-radius: 4px;
}

/* FILE: app/templates/notes.html */

CONTEXT:
1. Add Image Lightbox Modal.
2. Add an invisible element for image preview tooltip outside the main structure (will be fixed position).
3. Add image paste and smart preview/lightbox logic to JS.
4. Modify 'Gán Link' save logic.
INSERT AFTER: <div class="modal fade" id="notes-confirmDeleteModal" tabindex="-1">...</div>
END OF FILE
<div class="modal fade" id="notes-lightbox-modal" tabindex="-1">
<div class="modal-dialog modal-xl modal-dialog-centered">
<div class="modal-content">
<div class="modal-header">
<h5 class="modal-title text-muted" id="notes-lightbox-title"></h5>
<button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
</div>
<div class="modal-body">
<img id="notes-lightbox-image" src="" alt="Image Preview">
</div>
</div>
</div>
</div>

INSERT BEFORE </body> END TAG IN app/templates/layouts/base.html
CONTEXT: This element needs to live outside the main flow to use position: fixed effectively.
<div id="notes-image-preview-tooltip" style="display: none;">
<img id="notes-preview-img" src="" alt="Image Preview">
</div>

FILE: app/templates/notes.html (JavaScript Section)
CONTEXT: Implement all core logic for paste, preview, and new link functionality.
Find the following block near the end of the script:
// --- Event Listeners ---
document.addEventListener('click', hideAllContextMenus);
notesPane.addEventListener('contextmenu', handleTabContextMenu);
REPLACE ENTIRE JAVASCRIPT SECTION (starting from 'document.addEventListener('DOMContentLoaded', function () {') with the updated logic:
document.addEventListener('DOMContentLoaded', function () {
const notesPane = document.getElementById('notes-tool-pane');
if (!notesPane) return;

// --- DOM Elements ---
const container = document.getElementById('notes-container');
const searchInput = document.getElementById('notes-search-input');
const listWrapper = document.getElementById('notes-list-wrapper');
const detailWrapper = document.getElementById('notes-detail-wrapper');

// Modal Elements
const modalEl = document.getElementById('notes-addEditModal');
const notesModal = new bootstrap.Modal(modalEl);
const form = document.getElementById('notes-addEditForm');
const modalTitle = document.getElementById('notes-modalTitle');
const editIdInput = document.getElementById('notes-editId');
const titleInput = document.getElementById('notes-title-input');
const contentEditor = document.getElementById('notes-content-editor');

// Context Menu Elements
const noteCardMenu = document.getElementById('note-card-context-menu');
const editorContextMenu = document.getElementById('notes-context-menu');
const notesTabMenu = document.getElementById('notes-tab-context-menu');
const addLinkModal = new bootstrap.Modal(document.getElementById('notes-addLinkModal'));
const linkUrlInput = document.getElementById('notes-link-url');
const saveLinkBtn = document.getElementById('notes-save-link-btn');

// Lightbox Elements
const lightboxModalEl = document.getElementById('notes-lightbox-modal');
const lightboxModal = new bootstrap.Modal(lightboxModalEl);
const lightboxImage = document.getElementById('notes-lightbox-image');
const lightboxTitle = document.getElementById('notes-lightbox-title');

// Image Preview Elements
const previewTooltip = document.getElementById('notes-image-preview-tooltip');
const previewImage = document.getElementById('notes-preview-img');

// --- State Variables ---
let activeNoteId = null;
let autoSaveTimer = null;
let savedSelection = null;
let blockNextBlurSave = false;
window.notesData = [];
window.filteredNotes = [];

// --- Core Functions ---
function formatTimeAgo(isoString) {
    if (!isoString) return '';
    const seconds = Math.round((new Date() - new Date(isoString)) / 1000);
    if (seconds < 60) return "vài giây trước";
    const intervals = { 'năm': 31536000, 'tháng': 2592000, 'ngày': 86400, 'giờ': 3600, 'phút': 60 };
    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
        const value = Math.floor(seconds / secondsInUnit);
        if (value >= 1) return `${value} ${unit} trước`;
    }
    return "vài giây trước";
}

async function fetchAndRenderNotes(searchTerm = '') {
    try {
        const response = await fetch("{{ url_for('notes_feature.api_get_notes') }}");
        if (!response.ok) throw new Error(`Lỗi Server: ${response.status}`);
        
        const notes = await response.json();
        window.notesData = notes.sort((a, b) => new Date(b.modified_at) - new Date(a.modified_at));
        
        window.filteredNotes = searchTerm
            ? window.notesData.filter(note => 
                ((note.title_html || '').toLowerCase().includes(searchTerm) || 
                 (note.content_html || '').toLowerCase().includes(searchTerm)))
            : [...window.notesData];

        renderNotes(window.filteredNotes);

    } catch (error) {
        showToast(`Tải ghi chú thất bại: ${error.message}`, 'error');
    }
}

function renderNotes(notesToRender) {
    container.innerHTML = '';
    
    let displayList = [...notesToRender];
    if (activeNoteId) {
        const activeNoteIndex = displayList.findIndex(n => n.id === activeNoteId);
        if (activeNoteIndex > -1) {
            const [activeNote] = displayList.splice(activeNoteIndex, 1);
            displayList.unshift(activeNote);
        }
    }

    if (displayList.length === 0) {
        const emptyMessage = searchInput.value 
            ? `<div class="col-12 text-center text-muted p-5"><h6>Không tìm thấy ghi chú nào.</h6></div>`
            : `<div class="col-12 text-center text-muted p-5"><h6>Không có ghi chú nào.</h6><button class="btn btn-primary mt-3" onclick="window.prepareAddNoteModal()"><i class="bi bi-plus-lg"></i> Tạo ghi chú đầu tiên</button></div>`;
        container.innerHTML = emptyMessage;
        return;
    }
    
    displayList.forEach(note => container.appendChild(createNoteCard(note)));
    
    // Re-apply active class after rendering
    if (activeNoteId) {
        const activeCard = document.querySelector(`.card[data-note-id="${activeNoteId}"]`);
        if (activeCard) activeCard.classList.add('note-card-active');
    }
}

function createNoteCard(note) {
    const col = document.createElement('div');
    col.className = 'note-card-wrapper';
    
    const markedIconHTML = note.is_marked ? `<i class="bi bi-star-fill text-warning me-2" title="Đã đánh dấu"></i>` : '';
    const title = note.title_html || 'Ghi chú không tiêu đề';
    const content = note.content_html || '...';

    col.innerHTML = `
        <div class="card h-100" data-note-id="${note.id}">
            <div class="card-body d-flex flex-column">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h5 class="card-title mb-0 text-truncate">${title}</h5>
                    <div class="d-flex align-items-center flex-shrink-0 ms-2">
                        ${markedIconHTML}
                        <small class="text-muted" title="${new Date(note.modified_at).toLocaleString('vi-VN')}">${formatTimeAgo(note.modified_at)}</small>
                    </div>
                </div>
                <div class="card-text card-note-body flex-grow-1">${content}</div>
            </div>
        </div>`;

    const cardElement = col.querySelector('.card');
    cardElement.addEventListener('click', (e) => {
        if (e.target.closest('button')) return;
        showNoteDetail(note);
    });

    cardElement.addEventListener('contextmenu', (e) => handleNoteCardContextMenu(e, note));
    return col;
}

function openDetailPanel() {
    listWrapper.classList.add('shrunk');
    detailWrapper.classList.add('visible');
    container.classList.remove('notes-grid-view');
    container.classList.add('notes-list-view');
}

window.closeDetailPanel = () => {
    listWrapper.classList.remove('shrunk');
    detailWrapper.classList.remove('visible');
    container.classList.remove('notes-list-view');
    container.classList.add('notes-grid-view');
    document.querySelectorAll('#notes-container .card').forEach(card => card.classList.remove('note-card-active'));
    activeNoteId = null;
    
    // Reset detail panel
    const detailHeader = detailWrapper.querySelector('.card-header');
    const detailContent = detailWrapper.querySelector('#notes-detail-content');
    const detailPlaceholder = detailWrapper.querySelector('#notes-detail-placeholder');
    detailHeader.innerHTML = '';
    detailContent.classList.add('d-none');
    detailPlaceholder.classList.remove('d-none');
    
    // Stop image preview if active
    hideImagePreview();
};

function showNoteDetail(note) {
    activeNoteId = note.id;

    document.querySelectorAll('#notes-container .card').forEach(card => card.classList.remove('note-card-active'));
    const clickedCard = document.querySelector(`.card[data-note-id="${note.id}"]`);
    if (clickedCard) clickedCard.classList.add('note-card-active');
    
    openDetailPanel();

    const detailHeader = detailWrapper.querySelector('.card-header');
    const detailContent = detailWrapper.querySelector('#notes-detail-content');
    const detailPlaceholder = detailWrapper.querySelector('#notes-detail-placeholder');
    
    detailHeader.innerHTML = `
        <div class="d-flex justify-content-between align-items-center w-100">
            <small class="text-muted" title="${new Date(note.modified_at).toLocaleString('vi-VN')}">
                <i class="bi bi-clock-history"></i> ${formatTimeAgo(note.modified_at)}
            </small>
            <div>
                <button class="btn btn-sm btn-primary" onclick="window.prepareAddNoteModal()" title="Thêm ghi chú mới"><i class="bi bi-plus-lg"></i></button>
                <button class="btn btn-sm btn-outline-info" onclick="window.setAlarmForNote('${note.id}')" title="Đặt báo thức"><i class="bi bi-alarm"></i></button>
                <button class="btn btn-sm btn-outline-danger" onclick="window.deleteNoteWrapper('${note.id}', event)" title="Xóa ghi chú"><i class="bi bi-trash-fill"></i></button>
                <button class="btn-close btn-close-white" onclick="window.closeDetailPanel()" title="Đóng chi tiết" style="font-size: 0.8rem;"></button>
            </div>
        </div>`;

    detailContent.innerHTML = `<div id="detail-editable-full" contenteditable="true" spellcheck="false" data-placeholder="Dòng đầu là tiêu đề...">${note.title_html || ''}<br>${note.content_html || ''}</div>`;
    const editorEl = document.getElementById('detail-editable-full');
    
    // Set initial content for comparison
    editorEl.setAttribute('data-initial-content', editorEl.innerHTML);
    
    // Focus handler - update initial content
    editorEl.addEventListener('focus', () => {
        editorEl.setAttribute('data-initial-content', editorEl.innerHTML);
    });
    
    // Blur handler - save immediately if content changed
    editorEl.addEventListener('blur', () => {
        if (blockNextBlurSave) {
            blockNextBlurSave = false;
            return;
        }
        saveNoteChanges(note.id);
    });
    
    // --- NEW IMAGE LOGIC BINDINGS ---
    editorEl.addEventListener('paste', handleContentPaste);
    editorEl.addEventListener('mouseover', handleImageHover);
    editorEl.addEventListener('mouseout', handleImageOut);
    editorEl.addEventListener('click', handleImageClick);
    editorEl.addEventListener('contextmenu', handleEditorContextMenu);
    
    detailPlaceholder.classList.add('d-none');
    detailContent.classList.remove('d-none');
}

// --- NEW: Image and Paste Handlers ---

function isImageFile(file) {
    return file && file.type.startsWith('image/');
}

async function handleContentPaste(e) {
    // Find if any files/images are in clipboard
    const clipboardItems = e.clipboardData.items;
    const imageFiles = [];
    for (let i = 0; i < clipboardItems.length; i++) {
        const item = clipboardItems[i];
        if (item.kind === 'file' && isImageFile(item.type)) {
            imageFiles.push(item.getAsFile());
        }
    }

    if (imageFiles.length > 0) {
        e.preventDefault(); // Stop default paste behavior
        await processPastedImages(imageFiles);
    }
    
    // Auto-save after paste (even if not an image, content might have changed)
    setTimeout(() => {
        if (activeNoteId) {
            saveNoteChanges(activeNoteId, true);
        }
    }, 100);
}

async function processPastedImages(files) {
    const editorEl = document.getElementById('detail-editable-full');
    if (!editorEl || !activeNoteId) return;

    showToast(`Đang tải lên ${files.length} ảnh...`, 'info');
    
    // Placeholder container for multiple images
    const rowDiv = document.createElement('div');
    rowDiv.className = 'notes-image-row';
    
    for (const file of files) {
        const formData = new FormData();
        formData.append('image', file, 'pasted_image.png');
        
        try {
            const response = await fetch('/image/api/notes_image_upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) throw new Error('Upload failed');
            
            const data = await response.json();
            
            const img = document.createElement('img');
            img.src = data.url_thumb;
            img.alt = 'Ghi chú ảnh';
            img.className = 'notes-image-embed';
            img.dataset.originalSrc = data.url_original;
            img.dataset.imageId = data.id;
            
            rowDiv.appendChild(img);
            
            showToast(`✅ Upload ảnh ${files.indexOf(file) + 1}/${files.length} thành công.`, 'success');
            
        } catch (error) {
            console.error('Image upload error:', error);
            showToast(`❌ Upload ảnh ${files.indexOf(file) + 1}/${files.length} thất bại.`, 'error');
        }
    }
    
    // Insert the row (even if only one image) into the content
    // Need to ensure the cursor position is preserved/used
    editorEl.focus();
    const selection = window.getSelection();
    if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0);
        range.deleteContents();
        range.insertNode(rowDiv);
        
        // Move cursor after the inserted row for continued typing
        range.setStartAfter(rowDiv);
        range.setEndAfter(rowDiv);
        selection.removeAllRanges();
        selection.addRange(range);
    } else {
        editorEl.appendChild(rowDiv);
    }
    
    // Force save immediately after insertion
    saveNoteChanges(activeNoteId, true);
}

// --- NEW: Image Preview (Hover) ---
function showImagePreview(imgElement, originalSrc) {
    if (!previewTooltip || !previewImage) return;

    // Load original image into preview tooltip
    previewImage.src = originalSrc;
    
    // Calculate smart position
    const rect = imgElement.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    const margin = 10;
    
    // Set tooltip max size for measurement
    previewTooltip.style.maxWidth = '400px';
    previewTooltip.style.maxHeight = '400px';
    previewTooltip.style.display = 'block';
    
    // Temporarily move to measure size
    previewTooltip.style.left = '0px';
    previewTooltip.style.top = '0px';
    const tooltipRect = previewTooltip.getBoundingClientRect();
    
    let newX, newY;
    
    // 1. Horizontal positioning (Default: right of the cursor)
    if (rect.right + tooltipRect.width + margin < viewportWidth) {
        // Fits on the right
        newX = rect.right + margin;
    } else if (rect.left - tooltipRect.width - margin > 0) {
        // Fits on the left
        newX = rect.left - tooltipRect.width - margin;
    } else {
        // Doesn't fit well, try centered horizontally
        newX = Math.max(margin, (viewportWidth - tooltipRect.width) / 2);
    }
    
    // 2. Vertical positioning (Default: center to the element)
    newY = rect.top + (rect.height / 2) - (tooltipRect.height / 2);
    
    // Clamp top/bottom
    newY = Math.max(margin, newY);
    newY = Math.min(viewportHeight - tooltipRect.height - margin, newY);
    
    previewTooltip.style.left = `${newX}px`;
    previewTooltip.style.top = `${newY}px`;
    previewTooltip.style.display = 'block';
}

function hideImagePreview() {
    if (previewTooltip) {
        previewTooltip.style.display = 'none';
    }
}

function handleImageHover(e) {
    const imgElement = e.target.closest('.notes-image-embed');
    if (imgElement) {
        const originalSrc = imgElement.dataset.originalSrc;
        if (originalSrc) {
            showImagePreview(imgElement, originalSrc);
        }
    }
}

function handleImageOut(e) {
    const imgElement = e.target.closest('.notes-image-embed');
    if (imgElement) {
        hideImagePreview();
    }
}

// --- NEW: Image Click (Lightbox) ---
function handleImageClick(e) {
    const imgElement = e.target.closest('.notes-image-embed');
    if (imgElement) {
        e.preventDefault();
        e.stopPropagation();
        hideImagePreview();
        
        const originalSrc = imgElement.dataset.originalSrc;
        const title = `Ảnh Gốc (ID: ${imgElement.dataset.imageId}) - Click ngoài để đóng`;
        
        lightboxImage.src = originalSrc;
        lightboxTitle.textContent = title;
        lightboxModal.show();
    }
}

// --- Update Link Logic ---

saveLinkBtn.addEventListener('click', () => {
    const url = linkUrlInput.value.trim();
    if (!url) {
        showToast('Vui lòng nhập URL!', 'error');
        return;
    }
    
    // 1. Auto-Link Detection: Check if only a single URL was entered
    let actualUrl = url;
    const urlRegex = /^(https?:\/\/[^\s$.?#].[^\s]*)$/i;
    
    if (urlRegex.test(url)) {
        // Only a URL, use it directly
        actualUrl = url;
    } else if (url.startsWith('www.')) {
        // Missing protocol, assume https
        actualUrl = 'https://' + url;
    }
    
    if (actualUrl) {
        restoreSelection(); // Restore selection before creating link
        document.execCommand('createLink', false, actualUrl);
        addLinkModal.hide();
        savedSelection = null; // Clear saved selection
        setTimeout(() => saveNoteChanges(activeNoteId), 100);
    } else {
        showToast('Link không hợp lệ!', 'error');
    }
});

async function saveNoteChanges(noteId, forceSave = false) {
    if (!noteId) return;
    
    const editorEl = document.getElementById('detail-editable-full');
    if (!editorEl) return;
    
    const initialContent = editorEl.getAttribute('data-initial-content');
    const currentContent = editorEl.innerHTML;
    
    // Skip save if content unchanged and not forced
    if (!forceSave && currentContent === initialContent) {
        return;
    }
    
    // Wrap images in a temporary row if they aren't already (e.g. from copy/paste issues)
    const tempContainer = document.createElement('div');
    tempContainer.innerHTML = currentContent;
    const orphanImages = tempContainer.querySelectorAll('.notes-image-embed:not(.notes-image-row .notes-image-embed)');
    if (orphanImages.length > 0) {
        orphanImages.forEach(img => {
            const row = document.createElement('div');
            row.className = 'notes-image-row';
            img.parentNode.insertBefore(row, img);
            row.appendChild(img);
        });
    }
    const finalizedContent = tempContainer.innerHTML;
    
    const fullContent = finalizedContent;
    const parts = fullContent.split('<br>');
    const payload = { 
        title_html: parts.shift() || '', 
        content_html: parts.join('<br>') 
    };
    
    try {
        showToast('Đang lưu...', 'info');
        
        const response = await fetch(`{{ url_for('notes_feature.api_update_note', note_id='') }}${noteId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) throw new Error('Lỗi khi lưu trên server');
        
        const updatedNote = await response.json();
        
        // Update local data immediately
        const index = window.notesData.findIndex(n => n.id === noteId);
        if (index !== -1) {
            window.notesData[index] = updatedNote;
        }
        
        // Update initial content to new saved state
        editorEl.setAttribute('data-initial-content', currentContent);
        
        showToast('Đã lưu thay đổi!', 'success');
        
        // Update only the specific card without full re-render (Simplified)
        fetchAndRenderNotes(searchInput.value.toLowerCase().trim());
        
    } catch (error) {
        showToast('Lỗi khi tự động lưu!', 'error');
    }
}

// --- Context Menu Logic (Keep unchanged, except for adding hideImagePreview) ---
// ... (All other context menu logic remains the same, just ensure they call hideImagePreview) ...
function hideAllContextMenus() {
    console.log('hideAllContextMenus called');
    document.querySelectorAll('.custom-context-menu').forEach(menu => menu.style.display = 'none');
    hideImagePreview(); // Ensure image preview is hidden when any menu is clicked
}

// ... (Keep the rest of the existing JS logic, including initialization) ...
Ensure all other functions (e.g., prepareAddNoteModal, deleteNoteWrapper, etc.) from the original notes.html are preserved here.
... (Insert remaining unchanged JS code here) ...
Event delegation for the new image preview element (this is placed globally but hidden inside base.html for scope)
document.addEventListener('mouseover', handleImageHover);
document.addEventListener('mouseout', handleImageOut);
document.addEventListener('click', hideImagePreview); // Hide preview if clicking anywhere else

// --- Initial Setup ---
async function initializeNotesView() {
applySavedCardSize(); // Apply saved card size preference
await fetchAndRenderNotes();
if (window.notesData.length > 0) {
showNoteDetail(window.notesData[0]);
}
}

// --- Card Size Modifier (Chế độ xem) ---
function applySavedCardSize() {
const savedModifier = localStorage.getItem('notesCardSizeModifier') || 'default';
container.classList.remove('h-minus-2', 'h-minus-4');
if (savedModifier !== 'default') {
container.classList.add(savedModifier);
}

// Update checkmarks in menu
const tabMenu = document.getElementById('notes-tab-context-menu');
if (tabMenu) {
    const allChecks = tabMenu.querySelectorAll('.submenu .bi-check-circle-fill');
    allChecks.forEach(check => check.classList.add('d-none'));
    
    const activeCheck = tabMenu.querySelector(`.submenu [data-size-modifier="${savedModifier}"] i`);
    if (activeCheck) {
        activeCheck.classList.remove('d-none');
    }
}
}

// Event listener for size modifier menu
const sizeModifierMenu = document.getElementById('notes-tab-context-menu');
if (sizeModifierMenu) {
sizeModifierMenu.addEventListener('click', (e) => {
const sizeItem = e.target.closest('.submenu .menu-item[data-size-modifier]');
if (sizeItem) {
const modifier = sizeItem.dataset.sizeModifier;
localStorage.setItem('notesCardSizeModifier', modifier);
applySavedCardSize();
hideAllContextMenus();
}
});
}

document.addEventListener('click', hideAllContextMenus);
notesPane.addEventListener('contextmenu', handleTabContextMenu);

// --- Context Menu Logic (Keep unchanged) ---
function restoreSelection() {
if (savedSelection) {
const selection = window.getSelection();
selection.removeAllRanges();
selection.addRange(savedSelection);
}
}

function handleNoteCardContextMenu(e, note) {
    console.log('handleNoteCardContextMenu triggered for note:', note.id);
    e.preventDefault();
    e.stopPropagation();
    hideAllContextMenus();
    
    const markBtn = noteCardMenu.querySelector('#context-mark-note');
    markBtn.innerHTML = note.is_marked ? '<i class="bi bi-star me-2"></i> Bỏ Đánh Dấu' : '<i class="bi bi-star-fill me-2"></i> Đánh Dấu';
    
    noteCardMenu.dataset.noteId = note.id;
    showMenu(noteCardMenu, e.clientX, e.clientY);
}

function handleEditorContextMenu(e) {
    console.log('handleEditorContextMenu triggered');
    e.preventDefault();
    e.stopPropagation();
    hideAllContextMenus();

    const selection = window.getSelection();
    if (selection.toString().length > 0) {
        savedSelection = selection.getRangeAt(0).cloneRange();
        showMenu(editorContextMenu, e.clientX, e.clientY);
    }
}

function handleTabContextMenu(e) {
    console.log('handleTabContextMenu triggered at:', e.clientX, e.clientY);
    
    // Only check if NOT clicking on a note card
    const noteCard = e.target.closest('.card[data-note-id]');
    
    if (!noteCard) {
        console.log('Condition met: showing notesTabMenu');
        e.preventDefault();
        e.stopPropagation();
        hideAllContextMenus();
        showMenu(notesTabMenu, e.clientX, e.clientY);
    } else {
        console.log('Condition not met: click was on a note card');
    }
}

function showMenu(menu, x, y) {
    console.log('showMenu called for menu:', menu.id, 'at', x, y);
    menu.style.left = `${x}px`;
    menu.style.top = `${y}px`;
    menu.style.display = 'block';
}


// Main form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = editIdInput.value;
    const url = id
        ? `{{ url_for('notes_feature.api_update_note', note_id='') }}${id}`
        : "{{ url_for('notes_feature.api_add_note') }}";

    const payload = {
        title_html: titleInput.innerHTML,
        content_html: contentEditor.innerHTML,
    };

    if (!payload.title_html && !payload.content_html) {
        alert('Ghi chú không được để trống.');
        return;
    }

    try {
        const response = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        if (!response.ok) throw new Error('Lỗi khi lưu trên server');
        const savedNote = await response.json();
        notesModal.hide();
        await fetchAndRenderNotes(searchInput.value.toLowerCase().trim());
        showToast(id ? 'Đã cập nhật ghi chú!' : 'Đã tạo ghi chú mới!', 'success');
        showNoteDetail(savedNote); // Show the newly created/updated note
    } catch (error) {
        showToast('Lỗi: Không thể lưu ghi chú.', 'error');
    }
});

// Search input
searchInput.addEventListener('input', () => {
    fetchAndRenderNotes(searchInput.value.toLowerCase().trim());
});

// Context menu actions for note card
noteCardMenu.addEventListener('click', async (e) => {
    const markItem = e.target.closest('#context-mark-note');
    const deleteItem = e.target.closest('#context-delete-note');
    
    e.stopPropagation();
    const noteId = noteCardMenu.dataset.noteId;
    if (!noteId) return;
    
    if (markItem) {
        // Handle mark/unmark
        try {
            const response = await fetch(`{{ url_for('notes_feature.api_toggle_mark', note_id='') }}${noteId}`, { method: 'POST' });
            if (!response.ok) throw new Error('Server error');
            await fetchAndRenderNotes(searchInput.value.toLowerCase().trim());
            showToast('Đã cập nhật đánh dấu!', 'success');
        } catch (error) {
            showToast('Lỗi khi đánh dấu.', 'error');
        } finally {
            hideAllContextMenus();
        }
    } else if (deleteItem) {
        // Handle delete
        hideAllContextMenus();
        pendingDeleteNoteId = noteId;
        confirmDeleteModal.show();
    }
});

document.querySelector('#context-copy').addEventListener('click', () => {
    restoreSelection();
    document.execCommand('copy');
    hideAllContextMenus();
});
document.querySelector('#context-bold').addEventListener('click', () => {
    restoreSelection();
    document.execCommand('bold');
    hideAllContextMenus();
    setTimeout(() => saveNoteChanges(activeNoteId), 100);
});

document.querySelector('#context-color .color-palette').addEventListener('click', (e) => {
    if (e.target.matches('span[data-color]')) {
        restoreSelection();
        const color = e.target.dataset.color;
        document.execCommand('foreColor', false, color);
        hideAllContextMenus();
        setTimeout(() => saveNoteChanges(activeNoteId), 100);
    }
});

document.querySelector('#context-link').addEventListener('click', () => {
    // The selection is already saved, just show the modal
    linkUrlInput.value = 'https://';
    addLinkModal.show();
});

// Profile Modal Elements
const profileModal = new bootstrap.Modal(document.getElementById('notes-addProfileModal'));
const profileIdInput = document.getElementById('notes-profile-id');
const profilePasswordInput = document.getElementById('notes-profile-password');
const profileContentInput = document.getElementById('notes-profile-content');
const saveProfileBtn = document.getElementById('notes-save-profile-btn');
const deleteProfileBtn = document.getElementById('notes-delete-profile-btn');
const copyProfileIdBtn = document.getElementById('notes-copy-profile-id-btn');
const copyProfilePasswordBtn = document.getElementById('notes-copy-profile-password-btn');
const profileSpanMenu = document.getElementById('profile-span-context-menu');
let currentProfileSpan = null;

// Profile: Click "Gán Profile" in context menu
document.querySelector('#context-profile').addEventListener('click', () => {
    const selection = window.getSelection();
    if (selection.toString().length === 0) {
        alert('Vui lòng bôi đen đoạn chữ cần gán Profile.');
        return;
    }
    
    savedSelection = selection.getRangeAt(0).cloneRange();
    profileIdInput.value = '';
    profilePasswordInput.value = '';
    profileContentInput.value = '';
    deleteProfileBtn.style.display = 'none';
    blockNextBlurSave = true;
    hideAllContextMenus();
    profileModal.show();
});

// Profile: Save button
saveProfileBtn.addEventListener('click', () => {
    const profileId = profileIdInput.value.trim();
    const profilePassword = profilePasswordInput.value.trim();
    const profileContent = profileContentInput.value.trim();
    
    if (!profileId) {
        alert('Vui lòng nhập ID.');
        return;
    }
    
    if (currentProfileSpan) {
        // Editing existing profile
        currentProfileSpan.dataset.profileId = profileId;
        currentProfileSpan.dataset.profilePassword = profilePassword;
        currentProfileSpan.dataset.profileContent = profileContent;
        currentProfileSpan.textContent = profileId;
    } else if (savedSelection) {
        // Creating new profile
        restoreSelection();
        const span = document.createElement('span');
        span.className = 'has-profile';
        span.dataset.profileId = profileId;
        span.dataset.profilePassword = profilePassword;
        span.dataset.profileContent = profileContent;
        span.textContent = profileId;
        span.style.color = '#00e0ff';
        
        savedSelection.deleteContents();
        savedSelection.insertNode(span);
    }
    
    profileModal.hide();
    savedSelection = null;
    currentProfileSpan = null;
    saveNoteChanges(activeNoteId, true);
});

// Profile: Delete button
deleteProfileBtn.addEventListener('click', () => {
    if (currentProfileSpan && confirm('Xóa profile này?')) {
        const text = currentProfileSpan.textContent;
        currentProfileSpan.replaceWith(document.createTextNode(text));
        profileModal.hide();
        currentProfileSpan = null;
        saveNoteChanges(activeNoteId, true);
    }
});

// Profile: Copy buttons
copyProfileIdBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(profileIdInput.value);
    showToast('Đã copy ID!', 'success');
});

copyProfilePasswordBtn.addEventListener('click', () => {
    navigator.clipboard.writeText(profilePasswordInput.value);
    showToast('Đã copy Password!', 'success');
});

// Profile Span Context Menu
document.addEventListener('contextmenu', (e) => {
    const profileSpan = e.target.closest('.has-profile');
    if (profileSpan) {
        e.preventDefault();
        e.stopPropagation();
        hideAllContextMenus();
        currentProfileSpan = profileSpan;
        showMenu(profileSpanMenu, e.clientX, e.clientY);
    }
});

// Profile Span: Click to edit
document.addEventListener('click', (e) => {
    const profileSpan = e.target.closest('.has-profile');
    if (profileSpan && e.target.classList.contains('has-profile')) {
        e.preventDefault();
        e.stopPropagation();
        currentProfileSpan = profileSpan;
        profileIdInput.value = profileSpan.dataset.profileId || '';
        profilePasswordInput.value = profileSpan.dataset.profilePassword || '';
        profileContentInput.value = profileSpan.dataset.profileContent || '';
        deleteProfileBtn.style.display = 'block';
        blockNextBlurSave = true;
        profileModal.show();
    }
});

// Profile Span: Change color
profileSpanMenu.addEventListener('click', (e) => {
    const colorOption = e.target.closest('.color-option');
    if (colorOption && currentProfileSpan) {
        const newColor = colorOption.dataset.color;
        currentProfileSpan.style.color = newColor;
        hideAllContextMenus();
        saveNoteChanges(activeNoteId, true);
    }
});

// Profile Span: Delete
document.querySelector('#context-delete-profile').addEventListener('click', () => {
    if (currentProfileSpan && confirm('Xóa profile này?')) {
        const text = currentProfileSpan.textContent;
        currentProfileSpan.replaceWith(document.createTextNode(text));
        hideAllContextMenus();
        currentProfileSpan = null;
        saveNoteChanges(activeNoteId, true);
    }
});

// Profile Span: Click to edit
document.addEventListener('click', (e) => {
    const profileSpan = e.target.closest('.has-profile');
    if (profileSpan) {
        e.preventDefault();
        e.stopPropagation();
        currentProfileSpan = profileSpan;
        profileIdInput.value = profileSpan.dataset.profileId || '';
        profilePasswordInput.value = profileSpan.dataset.profilePassword || '';
        profileContentInput.value = profileSpan.dataset.profileContent || '';
        deleteProfileBtn.style.display = 'block';
        profileModal.show();
    }
});
initializeNotesView();
});
[END OF AI INSTRUCTION BLOCK]