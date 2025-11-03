from app.extensions import db
from sqlalchemy.dialects.postgresql import ARRAY

class Classes(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)
    program = db.Column(db.String,nullable=False)       
    course = db.Column(db.String,nullable=False)       
    startDate = db.Column(db.String,nullable=False)       
    endDate = db.Column(db.String,nullable=False)  
    graduationDate = db.Column(db.String,nullable=False)    
    certiDate = db.Column(db.String,nullable=False)    
    teacher = db.Column(db.String,nullable=False)    
    hours = db.Column(db.String,nullable=False)    
    days = db.Column(db.String)
    sessionType = db.Column(db.String)
    total = db.Column(db.String,nullable=False)    
    registration = db.Column(db.String,nullable=False)    
    tuition = db.Column(db.String,nullable=False)    
    dateUnits = db.Column(ARRAY(db.String),default=[])
    dateModules = db.Column(ARRAY(db.String),default=[])
    classType = db.Column(db.Integer,nullable=False) #1:PCA, 2: Upgrade, 3:HHA
    
    def __repr__(self):
        return f"<Class {self.firstName} {self.program}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "program": self.program,
            "course": self.course,
            "startDate": self.startDate,
            "endDate": self.endDate,
            "graduationDate": self.graduationDate,
            "certiDate": self.certiDate,
            "teacher": self.teacher,
            "hours": self.hours,
            "days": self.days,
            "sessionType": self.sessionType,
            "total": self.total,
            "registration": self.registration,
            "tuition": self.tuition,
            "dateUnits": self.dateUnits or [],
            "dateModules": self.dateModules or [],
            "classType": self.classType,
        }