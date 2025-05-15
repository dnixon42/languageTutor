from flask import Flask, render_template, request, jsonify, send_file
from gtts import gTTS
import os
import requests
import json
import uuid
import re

app = Flask(__name__)

AIServerURL = "http://127.0.0.1"
AIServerPort = "1234"
modelsURI = "/v1/models"
completionsURI = "/v1/chat/completions"
headers = {"Content-Type": "application/json"}
roleSystem = "You are a peppy and perky assistant named Zhu Li who knows Chinese and you are helping someone in learning chinese. You understand and respond in Chinese to the students English or Chinese conversations. Reply in Chinese characters and not the pinyin."

def getModels():
    getURL = AIServerURL + ":" + AIServerPort + modelsURI
    try:
        response = requests.get(getURL)
        response.raise_for_status()
        return response.json()['data'][0]['id']
    except Exception as e:
        print(f"Error fetching models: {e}")
        return None

def send_chat_prompt(prompt: str) -> str:
    uri = AIServerURL + ":" + AIServerPort + completionsURI
    payload = {
        "model": getModels(),
        "messages": [
            {"role": "system", "content": roleSystem},
            {"role": "user", "content": prompt}
        ],
    }
    try:
        response = requests.post(uri, data=json.dumps(payload), headers=headers, timeout=120)
        response.raise_for_status()
        out = response.json()
        content = out['choices'][0]['message']['content']
        # Remove content inside <think> tags
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        return content
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return f"Error: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    if not user_message.strip():
        return jsonify({"error": "Message cannot be empty"}), 400

    bot_response = send_chat_prompt(user_message)
    return jsonify({"response": bot_response})

@app.route('/tts', methods=['POST'])
def tts():
    text = request.json.get('text', '')
    if not text.strip():
        return jsonify({"error": "Text cannot be empty"}), 400

    try:
        # Generate a unique filename for the audio file
        filename = f"tts_{uuid.uuid4().hex}.aiff"  # macOS generates AIFF files
        print(f"Generating TTS for text: {text}")

        # Use macOS `say` command to generate the audio file
        os.system(f'say -o {filename} "[[rate 100]] {text}"')

        # Convert AIFF to MP3 for browser compatibility
        mp3_filename = filename.replace('.aiff', '.mp3')
        os.system(f"ffmpeg -i {filename} {mp3_filename}")

        # Stream the MP3 file to the client
        return send_file(mp3_filename, mimetype='audio/mpeg', as_attachment=False)

    except Exception as e:
        print(f"Error generating TTS: {e}")
        return jsonify({"error": "Failed to generate speech"}), 500
    finally:
        # Clean up the audio files after sending them
        if os.path.exists(filename):
            os.remove(filename)
        if os.path.exists(mp3_filename):
            os.remove(mp3_filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
