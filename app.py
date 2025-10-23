from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import io
import pdfplumber
import json
import os

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Extract text using pdfplumber (better for insurance PDFs)
    text = ""
    with pdfplumber.open(io.BytesIO(file.read())) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    print("=== Extracted PDF text preview ===")
    print(text[:1000])  # show first 1000 chars in logs

    # Full prompt with every schema field
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
    - If a field isn’t in the document, return null.
    - Dates in YYYY-MM-DD format.
    - For Yes/No fields, return exactly "Yes" or "No".
    - Only output valid JSON, nothing else.
    """

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=f"{prompt}\n\nDocument text:\n{text}",
            temperature=0
        )

        result_text = response.output[0].content[0].text.strip()

        print("=== GPT raw response ===")
        print(result_text)

        # Try to parse JSON cleanly
        try:
            data = json.loads(result_text)
        except json.JSONDecodeError:
            # Attempt to fix minor JSON issues
            fixed = result_text.strip("```json").strip("```").strip()
            try:
                data = json.loads(fixed)
            except Exception:
                data = {"error": "Invalid JSON from GPT", "raw": result_text}

        return jsonify(data)

    except Exception as e:
        print("Error during processing:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return "PolicyScanner backend running successfully."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
