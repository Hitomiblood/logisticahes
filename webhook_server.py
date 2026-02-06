#!/usr/bin/env python3
"""
Servidor Webhook para recibir archivos Excel desde Power Automate
"""
import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# Configuración
UPLOAD_FOLDER = '/app/data'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'hesego_logistica_2024')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB máximo

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de salud"""
    return jsonify({
        'status': 'healthy',
        'service': 'webhook-server',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint para recibir archivos desde Power Automate
    Espera:
    - Header: X-Webhook-Secret para autenticación
    - Form data: file (archivo Excel)
    - Form data: category (ALMACENES, COMPRAS, TRANSPORTE)
    """
    # Verificar secreto
    secret = request.headers.get('X-Webhook-Secret')
    if secret != WEBHOOK_SECRET:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Verificar que hay archivo
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only Excel files allowed'}), 400
    
    # Obtener categoría
    category = request.form.get('category', 'ALMACENES')
    if category not in ['ALMACENES', 'COMPRAS', 'TRANSPORTE']:
        return jsonify({'error': 'Invalid category'}), 400
    
    # Crear directorio de categoría si no existe
    category_folder = os.path.join(app.config['UPLOAD_FOLDER'], category)
    os.makedirs(category_folder, exist_ok=True)
    
    # Guardar archivo con nombre seguro
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    final_filename = f"{timestamp}_{filename}"
    filepath = os.path.join(category_folder, final_filename)
    
    try:
        file.save(filepath)
        return jsonify({
            'success': True,
            'filename': final_filename,
            'category': category,
            'path': filepath,
            'timestamp': timestamp
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to save file: {str(e)}'}), 500

if __name__ == '__main__':
    # Crear directorio de datos si no existe
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=5000, debug=False)
