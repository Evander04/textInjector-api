from flask import Blueprint, request, jsonify, send_file
from sqlalchemy.orm import defer
from app.extensions import db
from app.models.student import Student
from app.models.classes import Classes
from app.utils.injectData import injectTemplate, injectCnaTemplate, getFinalGrade, getGPA, parseFinalGrade, getFinalGradeSAP, getCnaFinalGrade, getCnaFinalGradeSAP, insertLedgerValues, insertCnaLedgerValues

student_bp = Blueprint("students", __name__)

UPDATABLE_STUDENT_FIELDS = {
    "firstName",
    "middleName",
    "lastName",
    "address",
    "phone",
    "dob",
    "ssn",
    "studentId",
    "email",
    "filename",
    "units",
    "modules",
    "receiptDates",
    "receiptNumbers",
    "receiptAmounts",
    "classId",
    "graduationDate",
    "certiDate",
    "workStatus",
    "agency",
    "interested",
}

@student_bp.route("/", methods=["GET"])
def list_student():
    list = Student.query.all()
    return jsonify([c.to_dict() for c in list])

@student_bp.route("/getByClass/<int:id>", methods=["GET"])
def getStudentsByClass(id):
    list = Student.query.options(defer(Student.payload)).filter_by(classId=int(id)).order_by(Student.id.asc()).all()
    return jsonify([c.to_dict() for c in list])


@student_bp.route("/<int:id>", methods=["PUT", "PATCH"])
def update_student(id):
    data = request.get_json() or {}
    student = Student.query.get(id)

    if not student:
        return jsonify({"error": "Student not found"}), 404

    if not data:
        return jsonify({"error": "No data provided"}), 400

    invalid_fields = [key for key in data.keys() if key not in UPDATABLE_STUDENT_FIELDS]
    if invalid_fields:
        return jsonify({
            "error": "Invalid fields in request",
            "fields": invalid_fields
        }), 400

    if "classId" in data:
        class_obj = Classes.query.get(int(data["classId"]))
        if not class_obj:
            return jsonify({"error": "Class not found"}), 404

    for field, value in data.items():
        setattr(student, field, value)

    db.session.commit()
    return jsonify({
        "message": "Student updated successfully",
        "body": student.to_dict()
    }), 200

@student_bp.route("/updateStudentWorkStatus", methods=["POST"])
def updateStudentWorkStatus():
    data = request.get_json() or {}
    studentId = data.get("studentId")
    workStatus = data.get("workStatus")
    agency = data.get("agency")
    interested = data.get("interested")

    studentObj = Student.query.get(int(studentId))
    if studentObj:
        studentObj.workStatus = workStatus
        studentObj.agency = agency
        studentObj.interested = interested
        db.session.commit()
        return jsonify({"message": "Student work status updated successfully"}), 200
    else:
        return jsonify({"error": "Student not found"}), 404    

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
        "@expectedGraduationDate": classObj.graduationDate,
        "@teacher": classObj.teacher,
        "@total": f"{classObj.total}",
        "@registration": f"{classObj.registration}",
        "@tuition": f"{classObj.tuition}",
        "@hours": classObj.hours,
        "@finalSsn":student.get("ssn")[-4:] if ssn !="" else "0000",
        "@finalHours":classObj.hours[:2],
        "@certiDate":student.get("certiDate"),
        "@email":student.get("email") if "lincoln" not in student.get("email") else "",
        "@days":classObj.days,
        "@sessionType":classObj.sessionType,          
        "@midpoint":classObj.midpoint  
    }   


    # HANDLE MODULES
    moduleGrades = [""]*12
    moduleDates = [""]*12
    fscore = ""    
    unig = ""
    if len(student.get("modules")) > 1:
        moduleGrades = student.get("modules")
        fscore = moduleGrades[11]    

    if len(classObj.dateModules) > 1:
        moduleDates = classObj.dateModules
        unig = moduleDates[11]
    
    for i,grade in enumerate(moduleGrades):
        key = ("@mg" if i<9 else "@mge") +str(i+1)
        replacements[key]=grade

    for i,date in enumerate(moduleDates):
        key = ("@md" if i<9 else "@mde")  +str(i+1)
        replacements[key]=date      

    # HANDLE UNITS
    unitGrades = [""]*8
    unitDates = [""]*8
    
    if len(student.get("units")) > 1:
        unitGrades = student.get("units")
        fscore = unitGrades[7]

    if len(classObj.dateUnits) > 1:
        unitDates = classObj.dateUnits
        unig = unitDates[1]
    
    for i,grade in enumerate(unitGrades):
        key = "@ug"+str(i+1)
        replacements[key]=grade

    for i,date in enumerate(unitDates):
        key = "@ud"+str(i+1)
        replacements[key]=date       
    
    finalGrade = getFinalGrade(moduleGrades,unitGrades,classObj.classType)
    finalGradeSAP = getFinalGradeSAP(moduleGrades,unitGrades,classObj.classType)
    replacements["@unig"] = unig
    replacements["@fscore"] = fscore
    replacements["@fgrade"] = parseFinalGrade(finalGrade)
    replacements["@gpa"] = str(getGPA(finalGrade))
    replacements["@sapGpa"] =str(getGPA(finalGradeSAP))
    insertLedgerValues(replacements,student,classObj)
    
    file = injectTemplate(replacements,type)    
    return send_file(
        file,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=student.get("firstName")+student.get("lastName")
    )


@student_bp.route("/generateCnaFiles/<int:type>", methods=["POST"])
def generateCnaFiles(type):
    student = request.get_json() or {}
    address = (student.get("address") or ",,,").split(",")
    ssn = student.get("ssn") or ""
    classObj = Classes.query.get(student.get("classId"))

    if not classObj:
        return jsonify({"error": "Class not found"}), 404

    while len(address) < 4:
        address.append("")

    replacements = {
        "@firstName": student.get("firstName", ""),
        "@middleName": student.get("middleName", ""),
        "@lastName": student.get("lastName", ""),
        "@dob": student.get("dob", ""),
        "@phone": student.get("phone", ""),
        "@address": student.get("address", ""),
        "@shortAd": address[0].strip(),
        "@city": address[1].strip(),
        "@state": address[2].strip(),
        "@zip": address[3].strip(),
        "@ssn": ssn,
        "@id": student.get("studentId", ""),
        "@program": classObj.program,
        "@course": classObj.course,
        "@startDate": classObj.startDate,
        "@endDate": classObj.endDate,
        "@graduationDate": student.get("graduationDate", ""),
        "@expectedGraduationDate": classObj.graduationDate,
        "@teacher": classObj.teacher,
        "@total": f"{classObj.total}",
        "@registration": f"{classObj.registration}",
        "@tuition": f"{classObj.tuition}",
        "@hours": classObj.hours,
        "@finalSsn": ssn[-4:] if ssn else "0000",
        "@finalHours": classObj.hours,
        "@certiDate": student.get("certiDate", ""),
        "@email": student.get("email", "") if "lincoln" not in student.get("email", "") else "",
        "@days": classObj.days,
        "@sessionType": classObj.sessionType,
        "@midpoint": classObj.midpoint,
    }

    moduleGrades = [""] * 11
    moduleDates = [""] * 11
    fscore = ""
    unig = ""

    if len(student.get("modules", [])) > 1:
        moduleGrades = student.get("modules")[:11]
        fscore = moduleGrades[-1]

    if len(classObj.dateModules) > 1:
        moduleDates = classObj.dateModules[:11]
        unig = moduleDates[-1]

    for i, grade in enumerate(moduleGrades):
        key = ("@mg" if i < 9 else "@mge") + str(i + 1)
        replacements[key] = grade

    for i, date in enumerate(moduleDates):
        key = ("@md" if i < 9 else "@mde") + str(i + 1)
        replacements[key] = date

    finalGrade = getCnaFinalGrade(moduleGrades)
    finalGradeSAP = getCnaFinalGradeSAP(moduleGrades, moduleDates, classObj.midpoint)
    replacements["@unig"] = unig
    replacements["@fscore"] = fscore
    replacements["@fgrade"] = parseFinalGrade(finalGrade)
    replacements["@gpa"] = str(getGPA(finalGrade))
    replacements["@sapGpa"] = str(getGPA(finalGradeSAP))
    insertCnaLedgerValues(replacements, student, classObj)

    file = injectCnaTemplate(replacements, type)
    return send_file(
        file,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=student.get("firstName", "") + student.get("lastName", "")
    )
