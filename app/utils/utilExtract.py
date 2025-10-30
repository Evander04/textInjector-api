import base64
import re
ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def pdf_to_data_url(pdf_bytes: bytes) -> str:
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    return f"data:application/pdf;base64,{b64}"

# Optional post-fixes (defensive formatting in case the model misses a rule)
_phone_digits = re.compile(r"\D")
def fix_phone(val: str) -> str:
    if not val: return ""
    digits = _phone_digits.sub("", val)
    return f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}" if len(digits) == 10 else val

def fix_id(val: str) -> str:
    if not val: return ""
    # Keep leading letters (e.g., D193681930), then group digits by 3
    m = re.match(r"^([A-Za-z]*)([\d]+)$", val.replace(" ", ""))
    if not m: return val
    prefix, digits = m.groups()
    chunks = [digits[i:i+3] for i in range(0, len(digits), 3)]
    return (prefix + " " if prefix else "") + " ".join(chunks)

def normalize_address(val: str) -> str:
    if not val: return ""
    # collapse spaces, ensure comma+space formatting
    s = re.sub(r"\s*,\s*", ", ", val)
    s = re.sub(r"\s{2,}", " ", s).strip()
    s = s.replace(" ,", ",")
    return s

def postprocess_payload(payload: dict) -> dict:
    # Ensure all keys exist
    keys = ["firstName","middleName","lastName","dob","phone","address",
            "ssn","id","email","units","modules","receiptDates","graduatedDate",
            "certificateNumber","registryNumber"]
    for k in keys:
        payload.setdefault(k, [] if k in {"units","modules","receiptDates"} else "")

    payload["phone"] = fix_phone(payload.get("phone",""))
    payload["id"] = fix_id(payload.get("id",""))
    payload["address"] = normalize_address(payload.get("address",""))

    # Arrays must be lists
    for ak in ("units","modules","receiptDates"):
        v = payload.get(ak)
        if not isinstance(v, list): payload[ak] = [] if not v else [v]
    return payload