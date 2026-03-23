from app.extensions import db
from sqlalchemy.dialects.postgresql import ARRAY

class Scrap(db.Model):
    __tablename__ = "scrap"

    id = db.Column(db.Integer, primary_key=True)
    fullName = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.String(100), nullable=False)
    startDate = db.Column(db.String(100), nullable=False)
    certifiedDate = db.Column(db.String(100), nullable=False,default="")
    certifiedDate2 = db.Column(db.String(100), nullable=True, default="")   
    registryNumber = db.Column(db.String(100), nullable=True)
    methodology = db.Column(db.String(200), nullable=True)
    methodology2 = db.Column(db.String(200), nullable=True, default="")
    filename = db.Column(db.String(200), nullable=False)
    agencies = db.Column(ARRAY(db.String), nullable=True)
    workStatus = db.Column(db.String(50), nullable=True)
    queryStatus = db.Column(db.String(50), nullable=True, default="pending") # e.g., "completed", "failed"," pending"
    workStartDate = db.Column(db.DateTime, nullable=True)
    benefitStatus = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<Scrap {self.fullName}>"
    

    def to_dict(self):
        return {
            "id": self.id,
            "fullName": self.fullName,
            "dob": self.dob,
            "startDate": self.startDate,
            "certifiedDate": self.certifiedDate,
            "certifiedDate2": self.certifiedDate2,
            "registryNumber": self.registryNumber,
            "methodology": self.methodology,
            "methodology2": self.methodology2,
            "filename": self.filename,
            "agencies": self.agencies,
            "workStatus": self.workStatus,
            "queryStatus": self.queryStatus,
            "workStartDate": self.workStartDate.isoformat() if self.workStartDate else None,
            "benefitStatus": self.benefitStatus
        }