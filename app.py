from flask import Flask, request, jsonify, send_file, send_from_directory
import yt_dlp
import os
import uuid

app = Flask(__name__)

# Create a downloads folder if it doesn't exist
DOWNLOADS = "downloads"
os.makedirs(DOWNLOADS, exist_ok=True)

@app.route('/')
def home():
    # Serve the HTML page
    return send_from_directory('.', 'index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    url = data.get('url')
    format = data.get('format')  # 'mp3' or 'mp4'

    if not url or not format:
        return jsonify({'error': 'Invalid input'}), 400

    # Unique filename to prevent clashes
    unique_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOADS, f'{unique_id}.%(ext)s')

    # Download options
    options = {
        'format': 'bestaudio/best' if format == 'mp3' else 'bestvideo+bestaudio/best',
        'outtmpl': output_template,
        'noplaylist': True,
        'quiet': True
    }

    if format == 'mp3':
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        # Find the file just downloaded
        for file in os.listdir(DOWNLOADS):
            if unique_id in file:
                return jsonify({ 'download_url': f'/file/{file}' })

        return jsonify({'error': 'File not found'}), 404

    except Exception as e:
        print("Download failed:", e)
        return jsonify({'error': 'Download failed'}), 500

@app.route('/file/<filename>')
def serve_file(filename):
    file_path = os.path.join(DOWNLOADS, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'File does not exist'}), 404

if __name__ == '__main__':
    app.run(debug=True)
