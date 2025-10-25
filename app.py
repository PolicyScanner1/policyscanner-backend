import os
import json
import pdfplumber
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def home():
    return "✅ PolicyScanner backend is running."

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']

        # Extract text from PDF using pdfplumber
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        if not text.strip():
            return jsonify({"error": "No readable text found in PDF"}), 400

        # 🔍 Define your full extraction prompt
        prompt = """
You are an expert insurance document parser.
The user will provide the text of a home insurance renewal schedule or policy document (after OCR).

Your task is to extract ALL relevant details, including core policy fields and full risk/quote fields.

Return the data as structured JSON in the following schema:

{
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
    {
      "date": "",
      "type": "",
      "amount": ""
    }
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
    {
      "item": "",
      "value": ""
    }
  ],
  "endorsements": [],
  "exclusions": []
}

Rules:
- If the document does not contain a field, return null for that field.
- Extract numerical values as numbers where possible (e.g., 250000 not "£250,000").
- Dates should be returned in ISO format (YYYY-MM-DD).
- For Yes/No fields, return exactly "Yes" or "No".
- Only output valid JSON, nothing else.
        """

        # 🔥 Send to OpenAI
        response = client.responses.create(
            model="gpt-4o-mini",
            input=f"{prompt}\n\nDocument text:\n{text}",
            temperature=0
        )

        raw_output = response.output[0].content[0].text.strip()
        print("🧾 GPT raw output:", raw_output)

        # Try to clean and parse JSON safely
        try:
            cleaned_output = raw_output.strip("`").replace("json\n", "").replace("```", "").strip()
            parsed = json.loads(cleaned_output)
        except Exception as e:
            print("⚠️ JSON parsing failed:", e)
            return jsonify({"error": "Invalid JSON returned from model", "raw_output": raw_output}), 500

        return jsonify(parsed)

    except Exception as e:
        import traceback
        print("❌ Error during processing:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
