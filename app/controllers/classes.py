from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.classes import Classes

classes_bp = Blueprint("classes",__name__)

@classes_bp.route("/", methods=["GET"])
def list_classes():
    classList = Classes.query.all()
    return jsonify([c.to_dict() for c in classList])


@classes_bp.route("/<int:id>", methods=["GET"])
def getById(id):
    c = Classes.query.get(id)
    return jsonify(c.to_dict())


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
        classType = data.get("classType")
    )
    db.session.add(classObj)
    db.session.commit()
    return jsonify({"message": "Class created", "code": 200,"body":classObj.to_dict()}), 201