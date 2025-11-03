from flask import Blueprint, request, jsonify, send_file
from app.extensions import db
from app.models.student import Student
from app.models.classes import Classes
from app.utils.injectData import injectTemplate

student_bp = Blueprint("students", __name__)

@student_bp.route("/", methods=["GET"])
def list_student():
    list = Student.query.all()
    return jsonify([c.to_dict() for c in list])

@student_bp.route("/getByClass/<int:id>", methods=["GET"])
def getStudentsByClass(id):
    list = Student.query.filter_by(classId=int(id)).order_by(Student.id.asc()).all()
    return jsonify([c.to_dict() for c in list])


@student_bp.route("/generateFiles/<int:type>", methods=["POST"])
def generateFiles(type):
    student = request.get_json() or {}          
    address = student.get("address").split(",")
    ssn = student.get("ssn")
    classObj = Classes.query.get(student.get("classId"))    
    replacements = {
        "@firstName": student.get("firstName"),
        "@middleName": student.get("middleName"),
        "@lastName": student.get("lastName"),
        "@dob": student.get("dob"),
        "@phone": student.get("phone"),
        "@address": student.get("address"),
        "@shortAd": address[0],
        "@city": address[1],
        "@state": address[2],
        "@zip": address[3],
        "@ssn": student.get("ssn"),
        "@id": student.get("studentId"),
        "@program": classObj.program,
        "@course": classObj.course,
        "@startDate": classObj.startDate,
        "@endDate": classObj.endDate,
        "@graduationDate": student.get("graduationDate"),
        "@teacher": classObj.teacher,
        "@total": classObj.total,
        "@registration": classObj.registration,
        "@tuition": classObj.tuition,
        "@hours": classObj.hours,
        "@finalSsn":student.get("ssn")[-4:] if ssn !="" else "0000",
        "@finalHours":classObj.hours[:2],
        "@certiDate":classObj.certiDate,
        "@email":student.get("email") if "lincoln" not in student.get("email") else "",        
    }      

    file = injectTemplate(replacements,type)    
    return send_file(
        file,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name="Ledger"+student.get("firstName")+student.get("lastName")
    )