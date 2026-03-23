from flask import Blueprint, request, jsonify
from app.extensions import db
from werkzeug.utils import secure_filename
from openai import OpenAI
from app.utils.ocrPdf import pdf_to_page_images
import os
import json
from app.utils.utilExtract import postprocess_payload, pdf_to_data_url,allowed_file
from app.models.scrap import Scrap
from app.utils.scrapper import lookup_current_employment

hcr_bp = Blueprint("hcr",__name__)
# ----- Config -----
OPENAI_API_KEY = os.getenv("OPEN_AI_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

SCHEMA_HINT = """
You are a data extraction engine.

Extract the following fields from the provided document:
- full_name
- date of birth 
- start_date
- certified_date
- registry_number
- methodology

Rules:
- Extract only data explicitly present in the document.
- Do NOT infer, guess, normalize, or fix values.
- If a field is missing or not clearly stated, use null.
- Preserve dates exactly as written in the document.
- Return ONLY valid JSON.
- Return ONLY an array of objects.
- Do NOT include explanations, comments, or additional text.
- Do NOT wrap the array inside another object.
- Each person in the document must be a separate object.

Required output format:
[
  {
    "full_name": string | null,
    "start_date": string | null,
    "date_of_birth": string | null,
    "certified_date": string | null,
    "registry_number": string | null,
    "methodology": string | null
  }
]
"""


@hcr_bp.route("/", methods=["GET"])
def processHCR():    
    print("Starting HCR endpoint processing")
    scraps = Scrap.query.filter_by(queryStatus="pending").all()
    print(f"Found {len(scraps)} pending scraps to process.")

    for scrap in scraps:
        if not scrap.registryNumber:
            print(f"Skipping scrap ID {scrap.id} due to missing registry number.")
            scrap.queryStatus = "failed"
            db.session.commit()
            continue
        jobInfo = lookup_current_employment(scrap.registryNumber, headless=True)
        print(f"Registry Number: {scrap.registryNumber} scanned, found {len(jobInfo)} employment records.")
        scrap.queryStatus = "completed"
        scrap.agencies = [job["agency"] for job in jobInfo]
        scrap.workStatus = "employed" if jobInfo else "unemployed"
        db.session.commit()

    return jsonify({"response":"HCR endpoint working","code":200}), 200


@hcr_bp.route("/extractRN", methods=["POST","OPTIONS"])
def extractRN():
    
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    f = request.files["file"]    

    if f.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not allowed_file(f.filename):
        return jsonify({"error": "Only PDF is allowed"}), 400

    fileName = secure_filename(f.filename)
    
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
                {"role": "system", "content": "Extract the requested fields from this document."},
                {"role": "user", "content": content_parts}
            ],
        )        
        raw = resp.choices[0].message.content.strip()
        # Extract the JSON block safely
        start = raw.find("[")
        end = raw.rfind("]")
        if start == -1 or end == -1:
            return jsonify({"error": "Extractor did not return JSON Array", "raw": raw}), 502
            
        payload = json.loads(raw[start:end+1])
        result = []
        for entry in payload:
            validate = Scrap.query.filter_by(registryNumber=entry.get("registry_number")).first()
            if validate:
                if validate.methodology != entry.get("methodology"):
                    validate.methodology2 = entry.get("methodology")
                    validate.certifiedDate2 = entry.get("certified_date")
                    db.session.commit()
                result.append(validate.to_dict())
                continue  # skip duplicates
            scrap = Scrap(
                fullName=entry.get("full_name"),
                dob=entry.get("date_of_birth"),
                startDate=entry.get("start_date"),
                certifiedDate=entry.get("certified_date"),
                registryNumber=entry.get("registry_number"),
                methodology=entry.get("methodology"),
                filename=fileName
            )
            db.session.add(scrap)
            db.session.commit()
            result.append(scrap.to_dict())

        return jsonify(result), 200    

    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500
    
@hcr_bp.route("/<int:id>", methods=["GET"])
def getByRegistry(id):
    s = Scrap.query.filter_by(registryNumber=str(id)).first()
    
    return jsonify(s.to_dict())


@hcr_bp.route("/updateWonderlic/<int:id>", methods=["GET"])
def updateWonderlic(id):
    s = Scrap.query.filter_by(registryNumber=str(id)).first()
    if not s:
        return jsonify({"error": "Scrap not found"}), 404
    s.benefitStatus = "Wonderlic"
    db.session.commit()
    return jsonify(s.to_dict())  