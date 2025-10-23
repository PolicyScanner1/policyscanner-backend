from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from pdf2image import convert_from_path
import tempfile, os
from openai import OpenAI

app = Flask(__name__)

# ✅ Allow your website to access this backend
CORS(app, origins=["https://policyscanner.co.uk"])

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET"])
def home():
    return "PolicyScanner backend running 🚀"

@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files["file"]
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            file.save(tmp.name)
            images = convert_from_path(tmp.name)
            text = ""
            for img in images:
                text += pytesseract.image_to_string(img)

        prompt = (
            "Extract all home insurance policy details as structured JSON.\n\n"
            f"{text}"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        # Return the JSON parsed by GPT
        return jsonify(response.choices[0].message.content)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
