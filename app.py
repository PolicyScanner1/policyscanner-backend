from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import json
import io

app = Flask(__name__)
CORS(app)

@app.route("/upload", methods=["POST"])
def upload():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported"}), 400

        # Read PDF text
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

        # --- Here’s your simple mock structured output ---
        # (In production, you’ll parse the extracted text or use GPT to do it.)
        mock_data = {
            "homeInsurancePolicy": {
                "policyholder": {
                    "name": "Mr. John Example",
                    "date_of_birth": "14 March 1983",
                    "occupation": "IT Consultant",
                    "marital_status": "Married"
                },
                "insurer": {
                    "name": "Hastings Insurance Services Ltd",
                    "policy_number": "HST-000123456"
                },
                "policy_period": {
                    "start_date": "01 October 2025",
                    "end_date": "30 September 2026"
                },
                "annual_renewal_premium": "£245.67",
                "property_details": {
                    "address": "12 Cherry Lane, Leicester",
                    "postcode": "LE1 2AB",
                    "type": "Detached House",
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "year_built": 1987,
                    "construction_type": "Brick Walls",
                    "roof_type": "Tiled",
                    "flat_roof_percentage": "0%",
                    "listed_status": "Not Listed",
                    "occupancy_type": "Owner Occupied",
                    "security_features": ["Approved locks on doors/windows"]
                }
            }
        }

        # Return valid JSON
        return jsonify(mock_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return "PolicyScanner Backend is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
