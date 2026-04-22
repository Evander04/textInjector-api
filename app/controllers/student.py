from flask import Blueprint, request, jsonify, send_file
from sqlalchemy import or_
from sqlalchemy.orm import defer
from app.extensions import db
from app.models.student import Student
from app.models.classes import Classes
from werkzeug.utils import secure_filename
from datetime import datetime
from app.utils.injectData import injectTemplate, injectCnaTemplate, injectUploadedTemplate, injectLocalTemplate, getFinalGrade, getGPA, parseFinalGrade, getFinalGradeSAP, getCnaFinalGrade, getCnaFinalGradeSAP, insertLedgerValues, insertCnaLedgerValues

student_bp = Blueprint("students", __name__)

TYPE_CLASS_PRICING = {
    "HHA": {"total": "700", "registration": "50", "tuition": "600", "book": "30", "uniform": "20"},
    "PCA": {"total": "380", "registration": "30", "tuition": "300", "book": "30", "uniform": "20"},
    "PCA Upgrade": {"total": "330", "registration": "30", "tuition": "300", "book": "0", "uniform": "0"},
}


def _format_receipt_date(value):
    if not value:
        return ""

    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).strftime("%m/%d/%Y")
        except ValueError:
            continue

    return value


def _build_receipt_replacements(form):
    first_name = form.get("firstName", "")
    middle_name = form.get("middleName", "")
    last_name = form.get("lastName", "")
    short_address = form.get("shortAd", form.get("stAdress", ""))
    city = form.get("city", "")
    state = form.get("state", "")
    zip_code = form.get("zip", form.get("zipcode", ""))
    phone = form.get("phone", form.get("phoneNumber", ""))
    receipt_date = _format_receipt_date(form.get("receiptDate", ""))
    type_class = form.get("typeClass", "")
    pricing = TYPE_CLASS_PRICING.get(type_class, {"total": "", "registration": "", "tuition": "", "book": "", "uniform": ""})

    return {
        "@firstName": first_name,
        "@middleName": middle_name,
        "@lastName": last_name,
        "@shortAd": short_address,
        "@stAdress": short_address,
        "@city": city,
        "@state": state,
        "@zip": zip_code,
        "@zipcode": zip_code,
        "@phone": phone,
        "@phoneNumber": phone,
        "@receiptDate": receipt_date,
        "@ledate1": receipt_date,
        "@typeClass": type_class,
        "@program": type_class,
        "@total": pricing["total"],
        "@registration": pricing["registration"],
        "@tuition": pricing["tuition"],
        "@book": pricing["book"],
        "@uniform": pricing["uniform"],
    }

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


@student_bp.route("/search", methods=["GET"])
def search_students_by_name():
    name = (request.args.get("name") or "").strip()
    query = Student.query.options(defer(Student.payload))

    if name:
        pattern = f"%{name}%"
        query = query.filter(
            or_(
                Student.firstName.ilike(pattern),
                Student.middleName.ilike(pattern),
                Student.lastName.ilike(pattern),
            )
        )

    students = query.order_by(Student.id.asc()).all()
    return jsonify([student.to_dict() for student in students])

@student_bp.route("/getByClass/<int:id>", methods=["GET"])
def getStudentsByClass(id):
    list = Student.query.options(defer(Student.payload)).filter_by(classId=int(id)).order_by(Student.id.asc()).all()
    return jsonify([c.to_dict() for c in list])


@student_bp.route("/injectWordDocument", methods=["POST"])
def inject_word_document():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".docx"):
        return jsonify({"error": "Only .docx Word documents are allowed"}), 400

    replacements = _build_receipt_replacements(request.form)

    injected_file = injectUploadedTemplate(replacements, file.stream)
    return send_file(
        injected_file,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename
    )


@student_bp.route("/receipt", methods=["POST"])
def generate_receipt():
    replacements = _build_receipt_replacements(request.form)
    receipt_file = injectLocalTemplate(replacements, "Template Receipt.docx")

    download_name = (
        f"{request.form.get('firstName', '')}{request.form.get('lastName', '')}Receipt.docx"
    )

    return send_file(
        receipt_file,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=download_name
    )


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
        "@finalHours":classObj.hours,
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
    student_modules = student.get("modules") or []
    student_units = student.get("units") or []
    class_module_dates = classObj.dateModules or []
    class_unit_dates = classObj.dateUnits or []

    if len(student_modules) > 1:
        moduleGrades = student_modules[:12]
        fscore = moduleGrades[-1]

    if len(class_module_dates) > 1:
        moduleDates = class_module_dates[:12]
        unig = moduleDates[-1]
    
    for i,grade in enumerate(moduleGrades):
        key = ("@mg" if i<9 else "@mge") +str(i+1)
        replacements[key]=grade

    for i,date in enumerate(moduleDates):
        key = ("@md" if i<9 else "@mde")  +str(i+1)
        replacements[key]=date      

    # HANDLE UNITS
    unitGrades = [""]*8
    unitDates = [""]*8
    
    if len(student_units) > 1:
        unitGrades = student_units[:8]

    if len(class_unit_dates) > 1:
        unitDates = class_unit_dates[:8]
    
    for i,grade in enumerate(unitGrades):
        key = "@ug"+str(i+1)
        replacements[key]=grade

    for i,date in enumerate(unitDates):
        key = "@ud"+str(i+1)
        replacements[key]=date

    if classObj.classType == 2 and len(unitGrades) > 0:
        fscore = unitGrades[-1]
        if len(unitDates) > 0:
            unig = unitDates[-1]
    elif classObj.classType == 3 and len(unitGrades) > 0:
        fscore = unitGrades[-1]
        if len(unitDates) > 0:
            unig = unitDates[-1]
    
    finalGrade = getFinalGrade(moduleGrades,unitGrades,classObj.classType)
    finalGradeSAP = getFinalGradeSAP(
        moduleGrades,
        unitGrades,
        classObj.classType,
        moduleDates=moduleDates,
        unitDates=unitDates,
        midpoint=classObj.midpoint,
    )
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
