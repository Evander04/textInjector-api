from app.extensions import db
from sqlalchemy.dialects.postgresql import ARRAY


class Caregiver(db.Model):
    __tablename__ = "caregivers"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(300), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    registry_number = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(150), nullable=True)
    agency = db.Column(db.String(200), nullable=True)
    license = db.Column(db.String(100), nullable=True)
    agencies = db.Column(ARRAY(db.String), nullable=True)
    workStatus = db.Column(db.String(50), nullable=True)
    queryStatus = db.Column(db.String(50), nullable=True, default="pending")
    workStartDate = db.Column(db.DateTime, nullable=True)
    benefitStatus = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "phone": self.phone,
            "registry_number": self.registry_number,
            "city": self.city,
            "agency": self.agency,
            "license": self.license,
            "agencies": self.agencies,
            "workStatus": self.workStatus,
            "queryStatus": self.queryStatus,
            "workStartDate": self.workStartDate.isoformat() if self.workStartDate else None,
            "benefitStatus": self.benefitStatus,
        }
