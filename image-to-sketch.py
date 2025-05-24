from flask import Flask, request, render_template_string, jsonify, Response
import cv2
import base64
import numpy as np

app = Flask(__name__)


def image_to_sketch(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    inverted_image = cv2.bitwise_not(gray_image)
    blurred = cv2.GaussianBlur(inverted_image, (5, 5), sigmaX=0, sigmaY=0)
    inverted_blurred = cv2.bitwise_not(blurred)
    blurred_gray_image = cv2.GaussianBlur(inverted_blurred, (5, 5), sigmaX=0, sigmaY=0)
    edges = cv2.Canny(blurred_gray_image, 30, 70)
    inverted_edges = cv2.bitwise_not(edges)
    sketch = cv2.divide(gray_image, inverted_edges, scale=256.0)
    return sketch


current_frame = None
sketch_encoded = None


def generate_frames():
    global current_frame, sketch_encoded
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            current_frame = frame.copy()
            sketch_frame = image_to_sketch(frame)
            ret, buffer = cv2.imencode('.jpg', sketch_frame)
            sketch_encoded = base64.b64encode(buffer).decode('utf-8')
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')


HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image to Sketch Converter</title>
    <style>
        body {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    margin: 20;
    background: linear-gradient(#e66465, #9198e5);
    font-family: 'Arial', sans-serif;
}

.container {
    text-align: center;
    background: #ffffff;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
    max-width: 80%;
    margin: 20px;
    transition: all 0.3s ease;
}

h1 {
    margin-bottom: 20px;
    color: #333;
}

img {
    width: 100%;
    max-width: 600px;
    border-radius: 10px;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
    transition: transform 0.3s ease;
}

img:hover {
    transform: scale(1.05);
}

.buttons {
    margin-top: 20px;
}

button, input[type="file"], .reset-button, .snap-button {
    margin: 5px;
    padding: 10px 20px;
    font-size: 16px;
    cursor: pointer;
    border: none;
    border-radius: 5px;
    background-color: #e66465;
    color: white;
    transition: background-color 0.3s ease, transform 0.3s ease;
}

button:hover, input[type="file"]:hover, .reset-button:hover, .snap-button:hover {
    background-color: #9198e5;
    transform: scale(1.05);
}


@media (max-width: 768px) {
    .container {
        padding: 15px;
    }

    button, input[type="file"], .reset-button, .snap-button {
        padding: 8px 16px;
        font-size: 14px;
    }
}

@media (max-width: 480px) {
    button, input[type="file"], .reset-button, .snap-button {
        padding: 6px 12px;
        font-size: 12px;
    }
}
    </style>
</head>
<body>
    <div class="container">
        <h1>Image to Sketch Converter</h1>
        <div id="video-container" style="display:none;">
            <img id="video" src="/video_feed" alt="Live Stream">
        </div>
        <div class="buttons">
            <button id="snapBtn" onclick="toggleVideo()">Snap Image</button>
            <button id="captureBtn" style="display:none" onclick="captureImage()">Capture Image</button>
            <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data" style="display:inline;">
                <input type="file" name="file" id="fileInput" onchange="this.form.submit()">
            </form>
             <button class="reset-button" onclick="resetApp()" style="display:none;">Reset</button>
             <button class="save-button" style="display:none;" onclick="saveImage()">Save Image</button>
        </div>
        {% if sketch_image %}
            <h2>Sketch Image</h2>
            <img id="sketchImage" src="data:image/jpeg;base64,{{ sketch_image }}" alt="Sketch Image">
        {% endif %}
        

    </div>
    <script>
        function toggleVideo() {
            var videoContainer = document.getElementById('video-container');
            var snapBtn = document.getElementById('snapBtn');
            var captureBtn = document.getElementById('captureBtn');
            var uploadForm = document.getElementById('uploadForm');
            var resetBtn = document.querySelector('.reset-button');
            if (videoContainer.style.display === 'none') {
                videoContainer.style.display = 'block';
                snapBtn.style.display = 'none';
                captureBtn.style.display = 'inline-block';
                uploadForm.style.display = 'none';
                resetBtn.style.display = 'inline-block';
                document.getElementById('video').src = '/video_feed';
            } else {
                videoContainer.style.display = 'none';
                snapBtn.style.display = 'inline-block'
                captureBtn.style.display = 'none';
                uploadForm.style.display = 'inline';
                resetBtn.style.display = 'none';
                document.getElementById('video').src = '/capture';
            }
        }
        function captureImage() {
            fetch('/capture').then(response => response.json()).then(data => {
                if (data.sketch_image) {
                    document.getElementById('video').src = 'data:image/jpeg;base64,' + data.sketch_image;
                    document.getElementById('captureBtn').style.display = 'none';
                    document.getElementById('uploadForm').style.display = 'none';
                    document.querySelector('.reset-button').style.display = 'inline-block';
                    document.querySelector('.save-button').style.display = 'inline-block';
                }
            });
        }

        function saveImage() {
            var img = document.getElementById('video').src;
            var link = document.createElement('a');
            link.href = img;
            link.download = 'sketch_image.jpg';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        function resetApp() {
            var videoContainer = document.getElementById('video-container');
            var uploadForm = document.getElementById('uploadForm');
            var resetBtn = document.querySelector('.reset-button');
            var saveBtn = document.querySelector('.save-button');
            videoContainer.style.display = 'none';
            snapBtn.style.display = 'inline-block';
            uploadForm.style.display = 'inline-block';
            resetBtn.style.display = 'none';
            saveBtn.style.display = 'none';
            document.getElementById('video').src = '';
        }
    </script>
</body>
</html>
'''


@app.route('/')
def sketch_app():
    return render_template_string(HTML_TEMPLATE)


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/capture')
def capture():
    global current_frame, sketch_encoded
    if current_frame is not None:
        sketch = image_to_sketch(current_frame)
        ret, buffer = cv2.imencode('.jpg', sketch)
        sketch_encoded = base64.b64encode(buffer).decode('utf-8')
        return jsonify({'sketch_image': sketch_encoded})
    return jsonify({'error': "Nothing captured"})


@app.route('/upload', methods=['POST'])
def upload_file():
    global sketch_encoded
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    image_stream = file.read()
    np_arr = np.frombuffer(image_stream, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    sketch = image_to_sketch(image)
    ret, buffer = cv2.imencode('.jpg', sketch)
    sketch_encoded = base64.b64encode(buffer).decode('utf-8')
    return render_template_string(HTML_TEMPLATE, sketch_image=sketch_encoded)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)