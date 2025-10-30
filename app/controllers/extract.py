from flask import Blueprint, request, jsonify
from app.extensions import db
from werkzeug.utils import secure_filename
from openai import OpenAI
import os
import json 
from app.utils.utilExtract import postprocess_payload, pdf_to_data_url,allowed_file

extract_bp = Blueprint("extract", __name__)

# ----- Config -----
OPENAI_API_KEY = os.getenv("OPEN_AI_KEY")


client = OpenAI(api_key=OPENAI_API_KEY)

SCHEMA_HINT = """
You are a document data extractor.
Return ONLY valid JSON, nothing else.

Expected JSON schema:
{
  "firstName": "",
  "middleName": "",
  "lastName": "",
  "dob": "",
  "phone": "",
  "address": "",
  "ssn": "",
  "id": "",
  "email": "",
  "units": ["A+", "A", "B", "C"],
  "modules": ["A+", "A", "B", "C"],
  "receiptDates": ["mm/dd/yyyy"],
  "graduatedDate": "mm/dd/yyyy",
  "certificateNumber": "",
  "registryNumber": ""
}

Rules and conversions:
- Input is a scanned PDF (may be images only) of school enrollment/receipts/evaluations/certificates.
- Extract values exactly as printed; English or Spanish.
- "units" → list of grades for UNIT A..H (map numeric scores to letters: 100=A+, 90=A, 80=B, 70=C).
- "modules" → list of grades for MODULE 1..12 (same mapping).
- "receiptDates" → all dates found in RECEIPT sections; format as mm/dd/yyyy.
- "graduatedDate" → date after phrases like "as of" / "graduated on"; format mm/dd/yyyy.
- "certificateNumber" → numeric after "CERTIFICATE NUMBER".
- "registryNumber" → numeric after "HOME CARE REGISTRY NUMBER".
- Format:
  - phone → (###) ###-####
  - id → group every 3 digits with spaces (keep leading letters if present, e.g., D193 681 930)
  - address → "street, city, state, zip" (comma separated)
- If a field is missing, return an empty string ("") or [] for arrays.
- No explanations or extra text—JSON only.
"""

@extract_bp.route("/extractData", methods=["GET"])
def extract():
        
    return jsonify({"response":"debbuginf"})


@extract_bp.route("/pdf", methods=["POST","OPTIONS"])
def extract_pdf():
    """
    Accepts multipart/form-data:
      - file: PDF file
    Returns:
      - JSON object with extracted fields (schema above)
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not allowed_file(f.filename):
        return jsonify({"error": "Only PDF is allowed"}), 400

    filename = secure_filename(f.filename)
    pdf_bytes = f.read()
    if not pdf_bytes:
        return jsonify({"error": "Empty file"}), 400

    try:
        data_url = pdf_to_data_url(pdf_bytes)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",   # vision-capable + cost-effective
            temperature=0,
            messages=[
                {"role": "system", "content": "You extract structured data from documents and output strict JSON."},
                {"role": "user", "content": [
                    {"type": "text", "text": SCHEMA_HINT},
                    {"type": "image_url", "image_url": data_url}
                ]}
            ],
        )
        raw = resp.choices[0].message.content.strip()

        # Extract the JSON block safely
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1:
            return jsonify({"error": "Extractor did not return JSON", "raw": raw}), 502

        payload = json.loads(raw[start:end+1])
        payload = postprocess_payload(payload)
        return jsonify(payload), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500