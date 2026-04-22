from flask import Blueprint, request, jsonify
from sqlalchemy import or_, func
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models.referral import Referral
from datetime import datetime


referral_bp = Blueprint("referrals", __name__)

UPDATABLE_REFERRAL_FIELDS = {
    "agency",
    "decision_status",
}


def _parse_filter_date(value):
    if not value:
        return None

    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
        try:
            return datetime.strptime(value.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


@referral_bp.route("/", methods=["GET"])
def list_referrals():
    query = Referral.query

    name = (request.args.get("name") or "").strip()
    city = (request.args.get("city") or "").strip()
    graduation_date = (request.args.get("graduationDate") or "").strip()
    graduation_date_from = _parse_filter_date(request.args.get("graduationDateFrom") or "")
    graduation_date_to = _parse_filter_date(request.args.get("graduationDateTo") or "")
    methodology_order = (request.args.get("methodologyOrder") or "asc").lower()
    page = max(int(request.args.get("page", 1)), 1)
    per_page = max(min(int(request.args.get("perPage", 20)), 100), 1)
    graduation_date1_expr = func.to_date(Referral.graduationDate1, 'MM/DD/YYYY')
    graduation_date2_expr = func.to_date(Referral.graduationDate2, 'MM/DD/YYYY')

    if name:
        pattern = f"%{name}%"
        query = query.filter(
            or_(
                Referral.fullName.ilike(pattern),
                Referral.student_full_name.ilike(pattern),
                Referral.scrap_full_name.ilike(pattern),
            )
        )

    if city:
        query = query.filter(Referral.city.ilike(f"%{city}%"))

    if graduation_date:
        query = query.filter(
            or_(
                Referral.graduationDate1 == graduation_date,
                Referral.graduationDate2 == graduation_date,
            )
        )

    if graduation_date_from:
        query = query.filter(
            or_(
                graduation_date1_expr >= graduation_date_from,
                graduation_date2_expr >= graduation_date_from,
            )
        )

    if graduation_date_to:
        query = query.filter(
            or_(
                graduation_date1_expr <= graduation_date_to,
                graduation_date2_expr <= graduation_date_to,
            )
        )

    methodology_sort = func.coalesce(Referral.methodology1, Referral.methodology2, "")
    if methodology_order == "desc":
        query = query.order_by(methodology_sort.desc(), Referral.created_at.desc(), Referral.id.desc())
    else:
        query = query.order_by(methodology_sort.asc(), Referral.created_at.desc(), Referral.id.desc())

    try:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({
            "items": [referral.to_dict() for referral in pagination.items],
            "page": pagination.page,
            "perPage": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "hasNext": pagination.has_next,
            "hasPrev": pagination.has_prev,
        })
    except SQLAlchemyError as exc:
        db.session.rollback()
        return jsonify({
            "error": "Unable to read referral records. Check database permissions for table 'referral'.",
            "details": str(exc.__cause__ or exc),
        }), 500


@referral_bp.route("/<int:id>", methods=["PUT", "PATCH"])
def update_referral(id):
    data = request.get_json() or {}
    referral = Referral.query.get(id)

    if not referral:
        return jsonify({"error": "Referral not found"}), 404

    if not data:
        return jsonify({"error": "No data provided"}), 400

    invalid_fields = [key for key in data.keys() if key not in UPDATABLE_REFERRAL_FIELDS]
    if invalid_fields:
        return jsonify({
            "error": "Invalid fields in request",
            "fields": invalid_fields
        }), 400

    previous_agency = (referral.agency or "").strip()

    for field, value in data.items():
        setattr(referral, field, value)

    new_agency = (referral.agency or "").strip()
    if "agency" in data:
        if new_agency and new_agency != previous_agency:
            referral.assigned_date = datetime.utcnow()
        elif not new_agency:
            referral.assigned_date = None

    try:
        db.session.commit()
        return jsonify({
            "message": "Referral updated successfully",
            "body": referral.to_dict()
        }), 200
    except SQLAlchemyError as exc:
        db.session.rollback()
        return jsonify({
            "error": "Unable to update referral",
            "details": str(exc.__cause__ or exc),
        }), 500
