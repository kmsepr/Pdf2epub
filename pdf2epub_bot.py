from flask import Flask, request, send_file, jsonify
import subprocess
import os
import uuid

app = Flask(__name__)

# Folders for storing uploaded PDFs and generated EPUBs
UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_epub():
    # Check if file part is present in request
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']

    # Check if a file is selected
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Accept only PDF files
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are supported"}), 400

    # Generate a unique filename to avoid conflicts
    unique_id = str(uuid.uuid4())
    input_pdf_path = os.path.join(UPLOAD_FOLDER, unique_id + ".pdf")
    output_epub_path = os.path.join(CONVERTED_FOLDER, unique_id + ".epub")

    # Save uploaded PDF
    file.save(input_pdf_path)

    # Convert PDF to EPUB using Calibre's ebook-convert CLI
    try:
        subprocess.run(
            ['ebook-convert', input_pdf_path, output_epub_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else "Unknown error"
        return jsonify({"error": "Conversion failed", "details": error_msg}), 500

    # Return the converted EPUB as a file download
    return send_file(
        output_epub_path,
        as_attachment=True,
        download_name=file.filename.rsplit('.', 1)[0] + '.epub'
    )


if __name__ == '__main__':
    # Run the Flask server on all interfaces, port 5000
    app.run(host='0.0.0.0', port=5000)