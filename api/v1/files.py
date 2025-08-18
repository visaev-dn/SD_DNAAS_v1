#!/usr/bin/env python3
"""
Files Routes
Handles listing, downloading, reading, deleting, and saving configuration files
"""

from flask import request, jsonify, send_file
from datetime import datetime
from pathlib import Path
import logging

from api.v1 import api_v1

logger = logging.getLogger(__name__)


@api_v1.route('/files/list', methods=['GET'])
def list_files():
    """List files in the project directory"""
    try:
        path = request.args.get('path', '.')
        base_path = Path(path)
        
        if not base_path.exists():
            return jsonify({"error": "Path not found"}), 404
        
        files = []
        for item in base_path.iterdir():
            if item.name.startswith('.'):
                continue  # Skip hidden files
            
            file_info = {
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0,
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            }
            files.append(file_info)
        
        # Sort: directories first, then files
        files.sort(key=lambda x: (x['type'] == 'file', x['name'].lower()))
        
        return jsonify({
            "path": str(base_path),
            "files": files
        })
        
    except Exception as e:
        logger.error(f"List files error: {e}")
        return jsonify({"error": "Failed to list files"}), 500


@api_v1.route('/files/download/<path:filepath>', methods=['GET'])
def download_file(filepath):
    """Download a file"""
    try:
        file_path = Path(filepath)
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"Download file error: {e}")
        return jsonify({"error": "Failed to download file"}), 500


@api_v1.route('/files/content/<path:filepath>', methods=['GET'])
def get_file_content(filepath):
    """Get file content as text"""
    try:
        file_path = Path(filepath)
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        if not file_path.is_file():
            return jsonify({"error": "Not a file"}), 400
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            "content": content,
            "filename": file_path.name,
            "size": file_path.stat().st_size,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Get file content error: {e}")
        return jsonify({"error": "Failed to read file content"}), 500


@api_v1.route('/files/delete/<path:filepath>', methods=['DELETE'])
def delete_file(filepath):
    """Delete a file"""
    try:
        file_path = Path(filepath)
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        
        # Only allow deletion of files in configs directories for safety
        if not (str(file_path).startswith('configs/') or str(file_path).startswith('./configs/')):
            return jsonify({"error": "Can only delete files in configs directory"}), 403
        
        file_path.unlink()
        
        return jsonify({
            "success": True,
            "message": f"File {file_path.name} deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        return jsonify({"error": "Failed to delete file"}), 500


@api_v1.route('/files/save-config', methods=['POST'])
def save_file_configuration():
    """Save generated configuration to pending directory"""
    try:
        data = request.get_json()
        config_content = data.get('content')
        filename = data.get('filename')
        
        if not config_content:
            return jsonify({"error": "Configuration content is required"}), 400
        
        if not filename:
            return jsonify({"error": "Filename is required"}), 400
        
        # Ensure configs/pending directory exists
        pending_dir = Path("configs/pending")
        pending_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the configuration
        config_path = pending_dir / filename
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        return jsonify({
            "success": True,
            "message": f"Configuration saved as {filename}",
            "path": str(config_path)
        })
        
    except Exception as e:
        logger.error(f"Save configuration error: {e}")
        return jsonify({"error": "Failed to save configuration"}), 500
