from flask import Flask, request, send_file, jsonify
import subprocess
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_epub():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are supported"}), 400

    unique_id = str(uuid.uuid4())
    input_pdf_path = os.path.join(UPLOAD_FOLDER, unique_id + ".pdf")
    output_epub_path = os.path.join(CONVERTED_FOLDER, unique_id + ".epub")
    
    file.save(input_pdf_path)

    try:
        subprocess.run(
            ['ebook-convert', input_pdf_path, output_epub_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Conversion failed", "details": e.stderr.decode()}), 500
    
    return send_file(
        output_epub_path,
        as_attachment=True,
        download_name=file.filename.rsplit('.', 1)[0] + '.epub'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)