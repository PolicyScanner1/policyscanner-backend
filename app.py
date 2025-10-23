from flask import Flask, request, jsonify
import pytesseract
from pdf2image import convert_from_path
import tempfile, os
from openai import OpenAI

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        file.save(tmp.name)
        images = convert_from_path(tmp.name)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img)

    prompt = f"Extract all home insurance policy details as structured JSON.\n\n{text}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return jsonify(response.choices[0].message.content)

@app.route("/", methods=["GET"])
def home():
    return "PolicyScanner backend running 🚀"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
