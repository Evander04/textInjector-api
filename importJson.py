#!/usr/bin/env python3
"""
Read multiple JSON files from a folder and insert data into PostgreSQL:

- Each JSON file contains an array of students with fields:
    {
        "firstName": "...",
        "middleName": "",
        "lastName": "...",
        "dob": "06/25/1982",
        "phone": "(929) 385-4674",
        "address": "1258 Metcalf Ave, Bronx, NY, 10472",
        "ssn": "677-62-1105",
        "id": "398 457 040",
        "email": "N/A"
    }

- Each file represents ONE class.
- We create (or reuse) a `Classes` row based on the file name.
- Then create `Student` rows linked to that class.

Usage:
    export DB_URL="postgresql+psycopg2://user:pass@host:5432/dbname"
    python import_json_students.py /path/to/json_folder
"""

import os
import sys
import json
from pathlib import Path

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import SQLAlchemyError

# -----------------------------
# CONFIG
# -----------------------------
DB_URL = os.getenv(
    "DB_URL",
    "postgresql+psycopg2://devuser:developer123@localhost:5432/paperwork_dev",
)

Base = declarative_base()


class Classes(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True)
    program = Column(String, nullable=False)
    course = Column(String, nullable=False)
    startDate = Column(String, nullable=False)
    endDate = Column(String, nullable=False)
    graduationDate = Column(String, nullable=False)
    certiDate = Column(String, nullable=False)
    teacher = Column(String, nullable=False)
    hours = Column(String, nullable=False)
    days = Column(String)
    sessionType = Column(String)
    total = Column(String, nullable=False)
    registration = Column(String, nullable=False)
    tuition = Column(String, nullable=False)
    dateUnits = Column(ARRAY(String), default=[])
    dateModules = Column(ARRAY(String), default=[])
    classType = Column(Integer, nullable=False)  # 1:PCA, 2:Upgrade, 3:HHA
    midpoint = Column(String)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    firstName = Column(String(100), nullable=False)
    middleName = Column(String(100), nullable=False)
    lastName = Column(String(100), nullable=False)
    address = Column(String(500), nullable=False)
    phone = Column(String(20), nullable=False)
    dob = Column(String(20), nullable=False)
    ssn = Column(String(20), nullable=False)
    studentId = Column(String(20), nullable=False)
    email = Column(String(120), nullable=False)
    payload = Column(String, nullable=False)
    filename = Column(String, nullable=False, unique=True)
    units = Column(ARRAY(String), default=[])
    modules = Column(ARRAY(String), default=[])
    receiptDates = Column(ARRAY(String), default=[])
    classId = Column(Integer, nullable=False, default=0)
    graduationDate = Column(String(20))
    certiDate = Column(String(20))


# -----------------------------
# DB helpers
# -----------------------------

def get_session():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    return Session()


# -----------------------------
# Class name parsing helpers
# -----------------------------

def infer_class_type_from_name(course_name: str) -> int:    
    if not course_name:
        return 0
        
    if "UPGRADE" in course_name.upper():
        return 2
    if "HHA" in course_name.upper():
        return 3
    return 1


def build_class_from_filename(session, filename_stem: str) -> Classes:
    course_name = filename_stem.strip()    


    # Defaults / placeholders – adjust as needed
    registration = "0"
    tuition = "0"
    total = "0"

    new_class = Classes(
        program=course_name,
        course=course_name,
        startDate="00/00/0000",
        endDate="00/00/0000",
        graduationDate="00/00/0000",
        certiDate="00/00/0000",
        teacher="N/A",
        hours="N/A",
        days=None,
        sessionType=None,
        total=total,
        registration=registration,
        tuition=tuition,
        dateUnits=[],
        dateModules=[],
        classType=infer_class_type_from_name(course_name),
        midpoint=None,
    )
    session.add(new_class)
    session.flush()  # to get new_class.id
    return new_class


# -----------------------------
# Main import logic
# -----------------------------

def import_json_file(session, json_path: Path):
    """
    Read one JSON file and insert its students + class.
    """
    print(f"\nProcessing file: {json_path.name}")

    filename_stem = json_path.stem  # e.g. "HHA Spanish AM 3-1"
    # 1) Get or create class
    class_obj = build_class_from_filename(session, filename_stem)
    class_id = class_obj.id
    print(f" - Using class id={class_id}, course='{class_obj.course}'")

    # 2) Read JSON array
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f" ❌ Invalid JSON in {json_path.name}: {e}")
        return

    if not isinstance(data, list):
        print(f" ❌ Expected an array in {json_path.name}, got {type(data)}")
        return

    inserted = 0
    for item in data:
        if not isinstance(item, dict):
            continue

        # Extract fields with fallbacks
        first_name = item.get("firstName", "").strip()
        middle_name = item.get("middleName", "").strip()
        last_name = item.get("lastName", "").strip()
        dob = item.get("dob", "00/00/0000").strip()
        phone = item.get("phone", "").strip()
        address = item.get("address", "").strip()
        ssn = item.get("ssn", "").strip()
        student_id = item.get("id", "").strip()
        email = item.get("email", "N/A").strip() or "N/A"

        # Create a unique filename based on JSON file + student id
        # e.g. "HHA Spanish AM 3-1_398 457 040"
        student_filename = f"{filename_stem}_{student_id or inserted}"

        
        # Skip if essential fields are missing (adjust as you like)
        if not first_name or not last_name:
            print(f"   - Skipping entry without name: {item}")
            continue

        # Check if this filename already exists (avoid unique constraint crash)
        existing_student = session.query(Student).filter_by(studentId=student_id).first()
        if existing_student:
            print(f"   - Student with studentId '{student_id}' already exists, skipping")
            continue

        student = Student(
            firstName=first_name,
            middleName=middle_name,
            lastName=last_name,
            address=address,
            phone=phone,
            dob=dob,
            ssn=ssn,
            studentId=student_id,
            email=email,
            payload="",
            filename=student_filename,
            units=[],
            modules=[],
            receiptDates=[],
            classId=class_id,
            graduationDate=None,
            certiDate=None,
        )
        session.add(student)
        inserted += 1

    session.commit()
    print(f" ✅ Inserted {inserted} students from {json_path.name}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_json_students.py /path/to/json_folder")
        sys.exit(1)

    folder = Path(sys.argv[1])
    if not folder.is_dir():
        print(f"❌ Not a directory: {folder}")
        sys.exit(1)

    session = get_session()

    # Process all *.json files in the folder
    json_files = sorted(folder.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {folder}")
        return

    try:
        for json_path in json_files:
            import_json_file(session, json_path)
    except SQLAlchemyError as e:
        session.rollback()
        print(f" ❌ DB error: {e}")
    finally:
        session.close()

    print("\nAll done ✅")


if __name__ == "__main__":
    main()