from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.classes import Classes

classes_bp = Blueprint("classes",__name__)

UPDATABLE_CLASS_FIELDS = {
    "program",
    "course",
    "startDate",
    "endDate",
    "graduationDate",
    "certiDate",
    "teacher",
    "hours",
    "days",
    "sessionType",
    "total",
    "registration",
    "tuition",
    "dateUnits",
    "dateModules",
    "classType",
    "midpoint",
}

@classes_bp.route("/", methods=["GET"])
def list_classes():
    classList = Classes.query.order_by(Classes.id.asc()).all()
    return jsonify([c.to_dict() for c in classList])


@classes_bp.route("/<int:id>", methods=["GET"])
def getById(id):
    c = Classes.query.get(id)
    return jsonify(c.to_dict())


@classes_bp.route("/<int:id>", methods=["PUT", "PATCH"])
def update_class(id):
    data = request.get_json() or {}
    class_obj = Classes.query.get(id)

    if not class_obj:
        return jsonify({"error": "Class not found"}), 404

    if not data:
        return jsonify({"error": "No data provided"}), 400

    invalid_fields = [key for key in data.keys() if key not in UPDATABLE_CLASS_FIELDS]
    if invalid_fields:
        return jsonify({
            "error": "Invalid fields in request",
            "fields": invalid_fields
        }), 400

    for field, value in data.items():
        setattr(class_obj, field, value)

    db.session.commit()
    return jsonify({
        "message": "Class updated successfully",
        "body": class_obj.to_dict()
    }), 200


@classes_bp.route("/save", methods=["POST"])
def create_user():
    data = request.get_json() or {}

    classObj = Classes(
        program = data.get("program"),
        course = data.get("course"),
        startDate = data.get("startDate"),
        endDate = data.get("endDate"),
        graduationDate = data.get("graduationDate"),
        certiDate = data.get("certiDate"),
        teacher = data.get("teacher"),
        hours = data.get("hours"),
        days = data.get("days"),
        sessionType = data.get("sessionType"),
        total = data.get("total"),
        registration = data.get("registration"),
        tuition = data.get("tuition"),
        dateUnits = data.get("dateUnits"),
        dateModules = data.get("dateModules"),
        classType = data.get("classType"),
        midpoint = data.get("midpoint"),
    )
    db.session.add(classObj)
    db.session.commit()
    return jsonify({"message": "Class created", "code": 200,"body":classObj.to_dict()}), 201
