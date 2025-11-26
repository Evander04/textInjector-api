#!/usr/bin/env python3
"""
Migrate data for `classes` and `students` tables
from one PostgreSQL server to another over local network.

Assumptions:
- Both DBs are PostgreSQL.
- Both have the same schema for `classes` and `students`.
- You want to FULLY REPLACE data in target for these tables.
"""

import os
from sqlalchemy import text
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    delete,
    func,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import SQLAlchemyError

# -----------------------------
# CONFIG – change these!
# -----------------------------
SOURCE_DB_URL = os.getenv(
    "SOURCE_DB_URL",
    "postgresql+psycopg2://devuser:developer123@localhost:5432/paperwork_dev",
)

TARGET_DB_URL = os.getenv(
    "TARGET_DB_URL",
    "postgresql+psycopg2://devuser:developer123@192.168.0.130:5432/paperwork_dev",
)

Base = declarative_base()

# -----------------------------
# MODELS (same as your Flask ones)
# -----------------------------


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
# HELPER FUNCTIONS
# -----------------------------


def make_session(db_url: str):
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return engine, Session()


def row_to_dict(obj, model_cls):
    """Extract plain dict of column_name -> value from ORM instance."""
    return {
        col.name: getattr(obj, col.name)
        for col in model_cls.__table__.columns
    }

def migrate_classes_with_new_ids(src_session, dst_session):
    """
    Insert Classes rows from source into target,
    letting target generate NEW IDs.

    Returns dict: {old_id: new_id}
    """
    print("\n=== Migrating `classes` with new IDs ===")
    class_id_map = {}

    try:
        src_rows = src_session.query(Classes).all()
        print(f" - Found {len(src_rows)} classes in source")

        for src_obj in src_rows:
            data = row_to_dict(src_obj, Classes)
            old_id = data.pop("id", None)  # remove PK so target autoincrements

            # Create new instance WITHOUT id
            new_obj = Classes(**data)
            dst_session.add(new_obj)
            dst_session.flush()  # get new_obj.id assigned by DB

            if old_id is not None:
                class_id_map[old_id] = new_obj.id

        dst_session.commit()
        print(f" ✅ Inserted {len(src_rows)} classes into target")
        return class_id_map

    except SQLAlchemyError as e:
        dst_session.rollback()
        print(f" ❌ Error migrating classes: {e}")
        return {}


def migrate_students_with_new_ids(src_session, dst_session, class_id_map):
    """
    Insert Student rows from source into target,
    letting target generate NEW IDs and remapping classId using class_id_map.
    """
    print("\n=== Migrating `students` with new IDs ===")
    inserted = 0
    skipped_conflicts = 0

    try:
        src_rows = src_session.query(Student).all()
        print(f" - Found {len(src_rows)} students in source")

        for src_obj in src_rows:
            data = row_to_dict(src_obj, Student)

            # Remove primary key so a new one is generated
            data.pop("id", None)

            # Remap classId if we created a new one for that class
            old_class_id = data.get("classId")
            if old_class_id in class_id_map:
                data["classId"] = class_id_map[old_class_id]
            # else: keep the existing classId as-is (maybe that class already existed in target)

            # Optional: skip if filename already exists in target to avoid unique constraint error
            # existing = dst_session.query(Student).filter_by(filename=data["filename"]).first()
            # if existing:
            #     skipped_conflicts += 1
            #     continue

            new_student = Student(**data)
            dst_session.add(new_student)
            inserted += 1
            dst_session.flush()
            
                

        dst_session.commit()
        print(f" ✅ Inserted {inserted} students into target")
        if skipped_conflicts:
            print(f" ⚠️ Skipped {skipped_conflicts} students due to conflicts (e.g. filename unique)")

    except SQLAlchemyError as e:
        dst_session.rollback()
        print(f" ❌ Error migrating students: {e}")


def main():
    print(f"Connecting to SOURCE: {SOURCE_DB_URL}")
    print(f"Connecting to TARGET: {TARGET_DB_URL}")

    # Create engines and sessions
    src_engine, src_session = make_session(SOURCE_DB_URL)
    dst_engine, dst_session = make_session(TARGET_DB_URL)

    # Simple connection test
    try:
        with src_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        with dst_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Both DB connections OK")
    except SQLAlchemyError as e:
        print(f"❌ Error connecting to databases: {e}")
        return

    # Ensure tables exist on target (no schema changes on source)
    print("\nEnsuring tables exist on target DB ...")
    Base.metadata.create_all(bind=dst_engine)

    # 1) Insert classes with new IDs and build map
    class_id_map = migrate_classes_with_new_ids(src_session, dst_session)

    # 2) Insert students with new IDs and remapped classId
    migrate_students_with_new_ids(src_session, dst_session, class_id_map)

    src_session.close()
    dst_session.close()
    print("\nAll done ✅")


if __name__ == "__main__":
    main()