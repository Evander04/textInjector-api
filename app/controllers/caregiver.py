from flask import Blueprint, request, jsonify
from sqlalchemy import or_, func
from app.extensions import db
from app.models.caregiver import Caregiver
from app.utils.scrapper import lookup_current_employment
from datetime import datetime


caregiver_bp = Blueprint("caregivers", __name__)

UPDATABLE_CAREGIVER_FIELDS = {
    "full_name",
    "phone",
    "registry_number",
    "city",
    "agency",
    "license",
    "agencies",
    "workStatus",
    "queryStatus",
    "workStartDate",
    "benefitStatus",
}


def _normalize_registry_number(value):
    if value is None:
        return ""
    return str(value).strip()


def _build_agencies(job_info):
    agencies = []
    for job in job_info:
        agency = (job or {}).get("agency", "").strip()
        if agency and agency not in agencies:
            agencies.append(agency)
    return agencies


def _parse_work_start_date(job_info):
    if not job_info:
        return None

    for job in job_info:
        start_date = (job or {}).get("startDate", "").strip()
        if not start_date:
            continue
        for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(start_date, fmt)
            except ValueError:
                continue

    return None


def _parse_datetime_value(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    text = str(value).strip()
    if not text:
        return None

    for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


@caregiver_bp.route("/", methods=["GET"])
def list_caregivers():
    name = (request.args.get("name") or "").strip()
    query = Caregiver.query

    if name:
        query = query.filter(Caregiver.full_name.ilike(f"%{name}%"))

    caregivers = query.order_by(Caregiver.id.asc()).all()
    return jsonify([caregiver.to_dict() for caregiver in caregivers])


@caregiver_bp.route("/pending", methods=["GET"])
def list_pending_caregivers():
    caregivers = (
        Caregiver.query
        .filter(Caregiver.registry_number.isnot(None))
        .filter(func.trim(Caregiver.registry_number) != "")
        .filter(
            or_(
                Caregiver.queryStatus.is_(None),
                func.trim(Caregiver.queryStatus) == "",
                Caregiver.queryStatus == "pending"
            )
        )
        .order_by(Caregiver.id.asc())
        .all()
    )

    return jsonify([caregiver.to_dict() for caregiver in caregivers])


@caregiver_bp.route("/sync-hcr/<registry_number>", methods=["POST"])
def sync_caregiver_hcr(registry_number):
    normalized_registry_number = _normalize_registry_number(registry_number)

    if not normalized_registry_number:
        return jsonify({"error": "Registry number is required"}), 400

    caregivers = Caregiver.query.filter_by(registry_number=normalized_registry_number).order_by(Caregiver.id.asc()).all()
    if not caregivers:
        return jsonify({"error": "Caregiver not found for registry number"}), 404

    try:
        job_info = lookup_current_employment(normalized_registry_number, headless=True)
    except Exception as exc:
        for caregiver in caregivers:
            caregiver.queryStatus = "failed"
        db.session.commit()
        return jsonify({
            "error": "HCR lookup failed",
            "details": str(exc),
            "registry_number": normalized_registry_number,
        }), 502

    agencies = _build_agencies(job_info)
    work_start_date = _parse_work_start_date(job_info)

    for caregiver in caregivers:
        caregiver.agencies = agencies
        caregiver.workStatus = "employed" if job_info else "unemployed"
        caregiver.queryStatus = "completed"
        caregiver.workStartDate = work_start_date

    db.session.commit()

    return jsonify({
        "message": "Caregiver HCR sync completed",
        "registry_number": normalized_registry_number,
        "work_status": "employed" if job_info else "unemployed",
        "employment_records": job_info,
        "updated": [caregiver.to_dict() for caregiver in caregivers],
    }), 200


@caregiver_bp.route("/<int:id>", methods=["GET"])
def get_caregiver(id):
    caregiver = Caregiver.query.get(id)
    if not caregiver:
        return jsonify({"error": "Caregiver not found"}), 404
    return jsonify(caregiver.to_dict())


@caregiver_bp.route("/", methods=["POST"])
def create_caregiver():
    data = request.get_json() or {}

    caregiver = Caregiver(
        full_name=data.get("full_name", ""),
        phone=data.get("phone"),
        registry_number=data.get("registry_number"),
        city=data.get("city"),
        agency=data.get("agency"),
        license=data.get("license"),
        agencies=data.get("agencies"),
        workStatus=data.get("workStatus"),
        queryStatus=data.get("queryStatus", "pending"),
        workStartDate=_parse_datetime_value(data.get("workStartDate")),
        benefitStatus=data.get("benefitStatus"),
    )
    db.session.add(caregiver)
    db.session.commit()
    return jsonify({"message": "Caregiver created", "body": caregiver.to_dict()}), 201


@caregiver_bp.route("/<int:id>", methods=["PUT", "PATCH"])
def update_caregiver(id):
    data = request.get_json() or {}
    caregiver = Caregiver.query.get(id)

    if not caregiver:
        return jsonify({"error": "Caregiver not found"}), 404

    if not data:
        return jsonify({"error": "No data provided"}), 400

    invalid_fields = [key for key in data.keys() if key not in UPDATABLE_CAREGIVER_FIELDS]
    if invalid_fields:
        return jsonify({"error": "Invalid fields in request", "fields": invalid_fields}), 400

    if "workStartDate" in data:
        data["workStartDate"] = _parse_datetime_value(data.get("workStartDate"))

    if "registry_number" in data and data.get("registry_number") != caregiver.registry_number:
        data.setdefault("queryStatus", "pending")
        data.setdefault("workStatus", None)
        data.setdefault("workStartDate", None)
        data.setdefault("agencies", None)

    for field, value in data.items():
        setattr(caregiver, field, value)

    db.session.commit()
    return jsonify({"message": "Caregiver updated successfully", "body": caregiver.to_dict()}), 200


@caregiver_bp.route("/<int:id>", methods=["DELETE"])
def delete_caregiver(id):
    caregiver = Caregiver.query.get(id)
    if not caregiver:
        return jsonify({"error": "Caregiver not found"}), 404

    db.session.delete(caregiver)
    db.session.commit()
    return jsonify({"message": "Caregiver deleted successfully"}), 200
