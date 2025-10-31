from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.student import Student

student_bp = Blueprint("students", __name__)

@student_bp.route("/", methods=["GET"])
def list_student():
    list = Student.query.all()
    return jsonify([c.to_dict() for c in list])

@student_bp.route("/getByClass/<int:id>", methods=["GET"])
def getStudentsByClass(id):
    list = Student.query.filter_by(classId=int(id))
    return jsonify([c.to_dict() for c in list])