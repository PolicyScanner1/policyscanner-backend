from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import io
import os
from openai import OpenAI
import json

app = Flask(__name__)
CORS(app)

# Load OpenAI key from Render environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/upload", methods=["POST"])
def upload():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if not file.filename.lower().endswith(".pdf"):
            return jsonify({"error": "Only PDF files are supported"}), 400

        # Extract text from PDF
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"

        # === GPT parsing prompt ===
        prompt = f"""
You are an expert insurance document parser. 
The user will provide the text of a home insurance renewal schedule or policy document (after OCR).

Your task is to extract ALL relevant details, including core policy fields and full risk/quote fields.

Return the data as structured JSON in the following schema:

{{
  "policyholder_name": "",
  "insurer_name": "",
  "policy_number": "",
  "start_date": "",
  "end_date": "",
  "renewal_premium": "",
  "address": "",
  "postcode": "",
  "property_type": "",
  "bedrooms": "",
  "bathrooms": "",
  "year_built": "",
  "construction_type": "",
  "roof_type": "",
  "flat_roof_percentage": "",
  "listed_status": "",
  "occupancy_type": "",
  "security_features": [],
  "date_of_birth": "",
  "occupation": "",
  "marital_status": "",
  "no_claims_discount_years": "",
  "previous_claims": [
    {{
      "date": "",
      "type": "",
      "amount": ""
    }}
  ],
  "buildings_sum_insured": "",
  "contents_sum_insured": "",
  "accidental_damage_cover": "",
  "legal_expenses_cover": "",
  "personal_possessions_cover": "",
  "home_emergency_cover": "",
  "excess_standard": "",
  "excess_voluntary": "",
  "specified_items": [
    {{
      "item": "",
      "value": ""
    }}
  ],
  "endorsements": [],
  "exclusions": []
}}

Rules:
- If the document does not contain a field, return null for that field.
- Extract numerical values as numbers where possible (e.g., 250000 not "£250,000").
- Dates should be returned in ISO format (YYYY-MM-DD).
- For Yes/No fields, return exactly "Yes" or "No".
- Only output valid JSON, nothing else.

Document text:
{text}
"""

        completion = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
            temperature=0.1,
        )

        result_text = completion.output[0].content[0].text.strip()

        # Clean markdown fences if present
        if result_text.startswith("```"):
            result_text = result_text.split("```json")[-1].split("```")[-1].strip()

        try:
            data = json.loads(result_text)
        except:
            data = {"raw_response": result_text}

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return "PolicyScanner Backend is running with GPT extraction!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

