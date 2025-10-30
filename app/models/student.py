from app.extensions import db
from sqlalchemy.dialects.postgresql import ARRAY

class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(100), nullable=False)
    middleName = db.Column(db.String(100), nullable=False)
    lastName = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    dob = db.Column(db.String(20), nullable=False)
    ssn = db.Column(db.String(20), nullable=False)
    studentId = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    payload = db.Column(db.String, nullable=False)
    filename = db.Column(db.String, unique=True, nullable=False)
    units = db.Column(ARRAY(db.String),default=[])
    modules = db.Column(ARRAY(db.String),default=[])
    receiptDates = db.Column(ARRAY(db.String),default=[])
    def __repr__(self):
        return f"<Student {self.firstName} {self.lastName}>"