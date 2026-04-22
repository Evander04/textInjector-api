from app.extensions import db


class Referral(db.Model):
    __tablename__ = "referral"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=True)
    scrap_id = db.Column(db.Integer, nullable=True)
    student_full_name = db.Column(db.String(300), nullable=True)
    scrap_full_name = db.Column(db.String(300), nullable=True)
    fullName = db.Column("fullName", db.String(300), nullable=False)
    dob = db.Column(db.String(100), nullable=True)
    street = db.Column(db.String(300), nullable=True)
    city = db.Column(db.String(150), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    graduationDate1 = db.Column("graduationDate1", db.String(100), nullable=True)
    methodology1 = db.Column(db.String(200), nullable=True)
    graduationDate2 = db.Column("graduationDate2", db.String(100), nullable=True)
    methodology2 = db.Column(db.String(200), nullable=True)
    registryNumber = db.Column("registryNumber", db.String(100), nullable=True)
    match_confidence = db.Column(db.Numeric(6, 5), nullable=True)
    match_type = db.Column(db.String(30), nullable=False)
    decision_status = db.Column(db.String(30), nullable=True, default="PENDING")
    agency = db.Column(db.String(200), nullable=True)
    assigned_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "scrap_id": self.scrap_id,
            "student_full_name": self.student_full_name,
            "scrap_full_name": self.scrap_full_name,
            "fullName": self.fullName,
            "dob": self.dob,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "phone": self.phone,
            "email": self.email,
            "graduationDate1": self.graduationDate1,
            "methodology1": self.methodology1,
            "graduationDate2": self.graduationDate2,
            "methodology2": self.methodology2,
            "registryNumber": self.registryNumber,
            "match_confidence": float(self.match_confidence) if self.match_confidence is not None else None,
            "match_type": self.match_type,
            "decision_status": self.decision_status,
            "agency": self.agency,
            "assigned_date": self.assigned_date.isoformat() if self.assigned_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
