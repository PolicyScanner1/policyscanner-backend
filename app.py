from flask import Flask, request, jsonify
from flask_cors import CORS
from PyPDF2 import PdfReader
import tempfile, os
from openai import OpenAI

app = Flask(__name__)
CORS(app, origins=["https://policyscanner.co.uk"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/", methods=["GET"])
def home():
    return "PolicyScanner backend running 🚀"

@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files["file"]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            file.save(tmp.name)
            reader = PdfReader(tmp.name)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""

        prompt = (
            "Extract all home insurance policy details as structured JSON.\n\n"
            f"{text}"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return jsonify(response.choices[0].message.content)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

