from flask import Blueprint, render_template, request, jsonify
import os

image_bp = Blueprint('image', __name__, url_prefix='/image')

@image_bp.route('/')
def index():
    """Main Image page with tabs"""
    return render_template('image.html')

@image_bp.route('/edit')
def edit_image():
    """Edit Image tab"""
    return render_template('image.html', active_tab='edit')

@image_bp.route('/collage')
def photo_collage():
    """Photo Collage tab"""
    return render_template('image.html', active_tab='collage')

# API endpoints for image editing
@image_bp.route('/api/upload', methods=['POST'])
def upload_image():
    """Upload image for editing"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected file'}), 400
        
        # Save to image_editor_files folder
        upload_folder = os.path.join('data', 'image_editor_files')
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, file.filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'path': filepath
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@image_bp.route('/api/collage/create', methods=['POST'])
def create_collage():
    """Create photo collage"""
    try:
        data = request.json
        images = data.get('images', [])
        layout = data.get('layout', '1:1')
        
        # TODO: Implement collage creation logic
        
        return jsonify({
            'success': True,
            'message': 'Collage created successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
