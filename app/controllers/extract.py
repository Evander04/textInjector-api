from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.student import Student
from werkzeug.utils import secure_filename
from openai import OpenAI
import os
import json 
from app.utils.utilExtract import postprocess_payload, pdf_to_data_url,allowed_file
from app.utils.ocrPdf import pdf_to_page_images

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
- Examine the entire image (or all pages).
- Do NOT infer values. Only extract what is explicitly visible on the provided images.
- 'Units' → look for section headers like “UNIDAD A”, “UNIDAD B”, … or “UNIT A”, “UNIT B”, … up to H.
- For each, read the numeric score (e.g., 100%, 90%, etc.) near that section and map:
  100→A+, 90→A, 80→B, 70→C.
- 'Modules' → same for “MÓDULO 1...12” or “MODULE 1...12”.
- If only units appear, return them; if only modules appear, return them; if both appear, include both arrays.
- Return all grades in the correct order (A...H or 1...12); use "" if a slot is missing.
- "receiptDates" → all dates found in RECEIPT sections; format as mm/dd/yyyy.
- "graduatedDate" → date after phrases like "as of" / "graduated on"; format mm/dd/yyyy.
- "certificateNumber" → numeric after "CERTIFICATE NUMBER".
- "registryNumber" → numeric after "HOME CARE REGISTRY NUMBER".
- Format:
  - phone → (###) ###-####
  - id → group every 3 digits with spaces (keep leading letters if present, e.g., D193 681 930)
  - address → "street, city, state, zip" (comma separated)
- If a field is missing, return an empty string ("") or [] for arrays.
- Do not add explanations; output pure JSON only.
"""

@extract_bp.route("/extractData", methods=["GET"])
def extract():
        
    return jsonify({"response":"debbuginf"})


@extract_bp.route("/pdf", methods=["POST","OPTIONS"])
def extract_pdf():
    
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    f = request.files["file"]
    classId = request.form["classId"]

    if f.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not allowed_file(f.filename):
        return jsonify({"error": "Only PDF is allowed"}), 400

    fileName = secure_filename(f.filename)
    student = Student.query.filter_by(filename=fileName).first()
    
    # validate file already scanned
    if student:
        return jsonify({"message": "Already scanned"}), 200
    
    # READ FILE
    pdf_bytes = f.read()
    if not pdf_bytes:
        return jsonify({"error": "Empty file"}), 400

    try:
        # API CALL

        #Convert to images
        data_url = pdf_to_page_images(pdf_bytes,dpi=300,max_pages=20)
        content_parts = [{"type": "text", "text": SCHEMA_HINT}]
        content_parts += [{"type": "image_url", "image_url": {"url": u}} for u in data_url]
        resp = client.chat.completions.create(
            model="gpt-5-mini",
            temperature=1,
            messages=[
                {"role": "system", "content": "You extract structured data from documents and output strict JSON."},
                {"role": "user", "content": content_parts}
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
        student = Student(
            firstName=payload["firstName"],
            middleName=payload["middleName"],
            lastName=payload["lastName"],
            phone=payload["phone"],
            dob=payload["dob"],
            ssn=payload["ssn"],
            studentId=payload["id"],
            email=payload["email"],
            payload=str(content_parts),
            filename=fileName,
            units=payload["units"],
            modules=payload["modules"],
            receiptDates=payload["receiptDates"],
            classId = int(classId)
        )
        db.session.add(student)
        db.session.commit()
        return jsonify(payload), 200    

    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500