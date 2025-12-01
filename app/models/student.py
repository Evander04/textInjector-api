from app.extensions import db
from sqlalchemy.dialects.postgresql import ARRAY

class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(100), nullable=False)
    middleName = db.Column(db.String(100), nullable=False)
    lastName = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    ssn = db.Column(db.String(20), nullable=False)
    studentId = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    payload = db.Column(db.String, nullable=False)
    filename = db.Column(db.String, unique=True, nullable=False)
    units = db.Column(ARRAY(db.String),default=[])
    modules = db.Column(ARRAY(db.String),default=[])
    receiptDates = db.Column(ARRAY(db.String),default=[])
    classId = db.Column(db.Integer,nullable=False,default=0)
    graduationDate = db.Column(db.String(20))
    certiDate = db.Column(db.String(20))
    workStatus = db.Column(db.String(20), nullable=True, default="Not Employed")
    agency = db.Column(db.String(100), nullable=True, default="")
    interested = db.Column(db.String(10), nullable=True, default="")
    lot= db.Column(db.Integer, nullable=True, default=0)
    campaign= db.Column(db.Integer, nullable=True, default=0)

    

    def __repr__(self):
        return f"<Student {self.firstName} {self.lastName}>"
    

    def to_dict(self):
        return {
            "id": self.id,
            "firstName": self.firstName,
            "middleName": self.middleName,
            "lastName": self.lastName,
            "address": self.address,
            "phone": self.phone,
            "dob": self.dob,
            "ssn": self.ssn,
            "studentId": self.studentId,
            "email": self.email,            
            "filename": self.filename,
            "units": self.units or [],
            "modules": self.modules or [],
            "receiptDates": self.receiptDates or [],
            "classId": self.classId,
            "graduationDate": self.graduationDate,
            "certiDate": self.certiDate,
            "workStatus": self.workStatus,
            "agency": self.agency,
            "interested": self.interested,
        }