#!/usr/bin/env python3
"""
python data_loader.py   --mysql 
"mysql+pymysql://user:pass@localhost:3306/schooldb"   --excel SchoolOnboardingTemplates.xlsx

Extended data_loader.py for additional tables:
- Handles students, teacher_subjects, teacher_grade_section, timeslots, timetable, attendance,
  homework_details, class_diary, fees_summary, installments, teacher_salary_structure, teacher_salary_payslip
- Uses ensure_keys() to auto-fill missing Excel columns with None
- Inserts or upserts data, preserving referential integrity
"""

import argparse
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from typing import Dict
import math

def ensure_keys(row_dict, required_keys):
    """Ensure all required keys exist, fill with None if missing or NaN."""
    d = dict(row_dict)
    for k in required_keys:
        val = d.get(k, None)
        if pd.isna(val) or (isinstance(val, float) and math.isnan(val)):
            d[k] = None
        else:
            d.setdefault(k, val)
    return d

def upsert_school(engine: Engine, df: pd.DataFrame) -> Dict[str, int]:
    m = {}
    with engine.begin() as conn:
        for _, r in df.iterrows():
            d = ensure_keys(r, [
                "school_name", "profile_pic_location", "address",
                "primary_phone_number", "secondary_phone_number", "email",
                "established_year", "medium_of_instruction", "principal_head_name",
                "administrative_contact", "number_of_staff", "is_active"
            ])
            conn.execute(text("""
                INSERT INTO ss_t_schools
                (school_name, profile_pic_location, address, primary_phone_number, secondary_phone_number, email,
                 established_year, medium_of_instruction, principal_head_name, administrative_contact, number_of_staff, is_active)
                VALUES (:school_name, :profile_pic_location, :address, :primary_phone_number, :secondary_phone_number, :email,
                        :established_year, :medium_of_instruction, :principal_head_name, :administrative_contact, :number_of_staff, :is_active)
                ON DUPLICATE KEY UPDATE
                  school_name = VALUES(school_name)
            """), d)
        q = conn.execute(text("SELECT school_id, school_name FROM ss_t_schools"))
        for row in q.fetchall():
            m[row.school_name] = row.school_id
    return m

def insert_grades(engine: Engine, df: pd.DataFrame, school_id: int) -> Dict[str, int]:
    mapping = {}
    with engine.begin() as conn:
        for _, r in df.iterrows():
            d = ensure_keys(r, [
                "grade_name", "description", "tuition_fee", "admission_fee", "development_fee",
                "activity_fee", "lab_fee", "transportation_fee", "late_fee_penalty",
                "annual_event_fee", "examination_fee", "other_fee", "payment_methods_accepted"
            ])
            d["school_id"] = school_id
            conn.execute(text("""
                INSERT INTO ss_t_grades (school_id, grade_name, description, tuition_fee, admission_fee, development_fee,
                    activity_fee, lab_fee, transportation_fee, late_fee_penalty, annual_event_fee, examination_fee, other_fee, payment_methods_accepted)
                VALUES (:school_id, :grade_name, :description, :tuition_fee, :admission_fee, :development_fee,
                        :activity_fee, :lab_fee, :transportation_fee, :late_fee_penalty, :annual_event_fee, :examination_fee, :other_fee, :payment_methods_accepted)
                ON DUPLICATE KEY UPDATE description=VALUES(description)
            """), d)
        q = conn.execute(text("SELECT grade_id, grade_name FROM ss_t_grades WHERE school_id=:sid"), {"sid": school_id})
        mapping = {row.grade_name: row.grade_id for row in q.fetchall()}
    return mapping

def insert_sections(engine: Engine, df: pd.DataFrame, grade_map: Dict[str, int]) -> Dict[str, Dict[str, int]]:
    out = {g: {} for g in grade_map.keys()}
    with engine.begin() as conn:
        for _, r in df.iterrows():
            if pd.isna(r["grade_name"]) or pd.isna(r["section_name"]):
                continue
            if r["grade_name"] not in grade_map:
                continue
            d = ensure_keys(r, ["grade_name", "section_name", "capacity"])
            d["grade_id"] = int(grade_map[r["grade_name"]])
            conn.execute(text("""
                INSERT INTO ss_t_sections (grade_id, section_name, capacity)
                VALUES (:grade_id, :section_name, :capacity)
                ON DUPLICATE KEY UPDATE capacity=VALUES(capacity)
            """), d)
        for grade_name, gid in grade_map.items():
            q = conn.execute(text("SELECT section_id, section_name FROM ss_t_sections WHERE grade_id=:gid"), {"gid": gid})
            out[grade_name] = {row.section_name: row.section_id for row in q.fetchall()}
    return out

def insert_subjects(engine: Engine, df: pd.DataFrame, school_id: int) -> Dict[str, int]:
    with engine.begin() as conn:
        for _, r in df.iterrows():
            d = ensure_keys(r, ["subject_name"])
            d["school_id"] = school_id
            conn.execute(text("""
                INSERT INTO ss_t_subjects (school_id, subject_name)
                VALUES (:school_id, :subject_name)
                ON DUPLICATE KEY UPDATE subject_name=VALUES(subject_name)
            """), d)
        q = conn.execute(text("SELECT subject_id, subject_name FROM ss_t_subjects WHERE school_id=:sid"), {"sid": school_id})
        return {row.subject_name: row.subject_id for row in q.fetchall()}

def insert_teachers(engine: Engine, df: pd.DataFrame, school_id: int) -> Dict[str, int]:
    with engine.begin() as conn:
        for _, r in df.iterrows():
            d = ensure_keys(r, [
                "first_name", "middle_name", "last_name", "profile_pic_location", "gender", "date_of_birth",
                "mobile_number", "email", "communication_address", "languages_known"
            ])
            d["school_id"] = school_id
            conn.execute(text("""
                INSERT INTO ss_t_teachers
                (school_id, first_name, middle_name, last_name, profile_pic_location, gender, date_of_birth, mobile_number,
                 email, communication_address, languages_known, is_active)
                VALUES (:school_id, :first_name, :middle_name, :last_name, :profile_pic_location, :gender, :date_of_birth, :mobile_number,
                        :email, :communication_address, :languages_known, 1)
                ON DUPLICATE KEY UPDATE first_name=VALUES(first_name), last_name=VALUES(last_name), is_active=1
            """), d)
        q = conn.execute(text("SELECT teacher_id, email FROM ss_t_teachers WHERE school_id=:sid"), {"sid": school_id})
        return {row.email: row.teacher_id for row in q.fetchall()}

def insert_students(engine: Engine, df: pd.DataFrame, grade_map: Dict[str, int], section_map: Dict[str, Dict[str, int]]) -> Dict[int, int]:
    student_hint_map = {}
    with engine.begin() as conn:
        for _, r in df.iterrows():
            if pd.isna(r.get("grade_name")) or pd.isna(r.get("section_name")):
                continue
            if r["grade_name"] not in grade_map or r["section_name"] not in section_map.get(r["grade_name"], {}):
                continue
            d = ensure_keys(r, [
                "school_id", "first_name", "middle_name", "last_name", "profile_pic_location", "gender", "date_of_birth",
                "mobile_number", "email", "communication_address", "languages_known", "guardian_name", "guardian_mobile"
            ])
            d["school_id"] = r.get("school_id")
            d["grade_id"] = int(grade_map[r["grade_name"]])
            d["section_id"] = int(section_map[r["grade_name"]][r["section_name"]])
            conn.execute(text("""
                INSERT INTO ss_t_students
                (school_id, grade_id, section_id, first_name, middle_name, last_name, profile_pic_location,
                 gender, date_of_birth, mobile_number, email, communication_address, languages_known, guardian_name, guardian_mobile)
                VALUES (:school_id, :grade_id, :section_id, :first_name, :middle_name, :last_name, :profile_pic_location,
                        :gender, :date_of_birth, :mobile_number, :email, :communication_address, :languages_known, :guardian_name, :guardian_mobile)
                ON DUPLICATE KEY UPDATE first_name=VALUES(first_name), last_name=VALUES(last_name),
                  guardian_name=VALUES(guardian_name), guardian_mobile=VALUES(guardian_mobile)
            """), d)
        # Build mapping of student_id_hint -> student_id via email
        q = conn.execute(text("SELECT student_id, email FROM ss_t_students"))
        email_to_id = {row.email: row.student_id for row in q.fetchall() if row.email is not None}
        for _, r in df.iterrows():
            hint = r.get("student_id_hint")
            email = r.get("email")
            if not pd.isna(hint) and not pd.isna(email):
                sid = email_to_id.get(email)
                if sid:
                    student_hint_map[int(hint)] = sid
    return student_hint_map

def insert_teacher_subjects(engine: Engine, df: pd.DataFrame, teacher_hint_map: Dict[int,int], subject_hint_map: Dict[int,int]):
    with engine.begin() as conn:
        for _, r in df.iterrows():
            if pd.isna(r.get("teacher_id_hint")) or pd.isna(r.get("subject_id_hint")):
                continue
            teacher_id = teacher_hint_map.get(int(r["teacher_id_hint"]))
            subject_id = subject_hint_map.get(int(r["subject_id_hint"]))
            if not teacher_id or not subject_id:
                continue
            conn.execute(text("""
                INSERT INTO ss_t_teacher_subject (teacher_id, subject_id)
                VALUES (:teacher_id, :subject_id)
                ON DUPLICATE KEY UPDATE teacher_id=VALUES(teacher_id)
            """), {"teacher_id": teacher_id, "subject_id": subject_id})

def insert_teacher_grade_section(engine: Engine, df: pd.DataFrame, teacher_hint_map: Dict[int,int], grade_map: Dict[str,int], section_map: Dict[str, Dict[str,int]]):
    with engine.begin() as conn:
        for _, r in df.iterrows():
            if pd.isna(r.get("teacher_id_hint")) or pd.isna(r.get("grade_name")) or pd.isna(r.get("section_name")):
                continue
            if r["grade_name"] not in grade_map or r["section_name"] not in section_map.get(r["grade_name"], {}):
                continue
            teacher_id = teacher_hint_map.get(int(r["teacher_id_hint"]))
            grade_id = int(grade_map[r["grade_name"]])
            section_id = int(section_map[r["grade_name"]][r["section_name"]])
            if not teacher_id:
                continue
            conn.execute(text("""
                INSERT INTO ss_t_teacher_grade_section (teacher_id, grade_id, section_id)
                VALUES (:teacher_id, :grade_id, :section_id)
                ON DUPLICATE KEY UPDATE teacher_id=VALUES(teacher_id)
            """), {"teacher_id": teacher_id, "grade_id": grade_id, "section_id": section_id})

def insert_timeslots(engine: Engine, df: pd.DataFrame):
    with engine.begin() as conn:
        for _, r in df.iterrows():
            if pd.isna(r.get("day_of_week")) or pd.isna(r.get("period_number")):
                continue
            d = ensure_keys(r, ["day_of_week", "period_number", "start_time", "end_time"])
            conn.execute(text("""
                INSERT INTO ss_t_timeslots (day_of_week, period_number, start_time, end_time)
                VALUES (:day_of_week, :period_number, :start_time, :end_time)
                ON DUPLICATE KEY UPDATE start_time=VALUES(start_time), end_time=VALUES(end_time)
            """), d)

def insert_timetable(engine: Engine, df: pd.DataFrame, grade_map: Dict[str,int], section_map: Dict[str, Dict[str,int]], subject_map: Dict[str,int], teacher_map: Dict[str,int]):
    with engine.begin() as conn:
        for _, r in df.iterrows():
            if pd.isna(r.get("grade_name")) or pd.isna(r.get("section_name")) or pd.isna(r.get("day_of_week")) or pd.isna(r.get("period_number")):
                continue
            if r["grade_name"] not in grade_map or r["section_name"] not in section_map.get(r["grade_name"], {}):
                continue
            d = ensure_keys(r, ["grade_name", "section_name", "day_of_week", "period_number", "subject_name", "teacher_email", "room_number"])
            grade_id = int(grade_map[r["grade_name"]])
            section_id = int(section_map[r["grade_name"]][r["section_name"]])
            # find timeslot_id via day and period
            ts_q = conn.execute(text("SELECT timeslot_id FROM ss_t_timeslots WHERE day_of_week=:dow AND period_number=:pn"), 
                                {"dow": r["day_of_week"], "pn": int(r["period_number"])})
            ts_row = ts_q.fetchone()
            if not ts_row:
                continue
            timeslot_id = ts_row.timeslot_id
            teacher_id = teacher_map.get(r["teacher_email"])
            subject_id = subject_map.get(r["subject_name"])
            if not teacher_id or not subject_id:
                continue
            conn.execute(text("""
                INSERT INTO ss_t_timetable (grade_id, section_id, timeslot_id, subject_id, teacher_id, room_number, is_active)
                VALUES (:grade_id, :section_id, :timeslot_id, :subject_id, :teacher_id, :room_number, 1)
                ON DUPLICATE KEY UPDATE subject_id=VALUES(subject_id), teacher_id=VALUES(teacher_id), room_number=VALUES(room_number)
            """), {"grade_id": grade_id, "section_id": section_id, "timeslot_id": timeslot_id, 
                  "subject_id": subject_id, "teacher_id": teacher_id, "room_number": r.get("room_number")})

def insert_attendance(engine: Engine, df: pd.DataFrame, student_hint_map: Dict[int,int]):
    with engine.begin() as conn:
        for _, r in df.iterrows():
            if pd.isna(r.get("student_id_hint")) or pd.isna(r.get("date")) or pd.isna(r.get("status")):
                continue
            student_id = student_hint_map.get(int(r["student_id_hint"]))
            if not student_id:
                continue
            conn.execute(text("""
                INSERT INTO ss_t_attendance (student_id, attendance_date, status)
                VALUES (:student_id, :attendance_date, :status)
                ON DUPLICATE KEY UPDATE status=VALUES(status)
            """), {"student_id": student_id, "attendance_date": r["date"], "status": r["status"]})

def insert_homework_details(engine: Engine, df: pd.DataFrame, grade_map: Dict[str,int], section_map: Dict[str, Dict[str,int]], subject_map: Dict[str,int], teacher_map: Dict[str,int]):
    with engine.begin() as conn:
        for _, r in df.iterrows():
            if pd.isna(r.get("teacher_email")) or pd.isna(r.get("grade_name")) or pd.isna(r.get("section_name")) or pd.isna(r.get("subject_name")) or pd.isna(r.get("title")) or pd.isna(r.get("assigned_date")):
                continue
            if r["grade_name"] not in grade_map or r["section_name"] not in section_map.get(r["grade_name"], {}):
                continue
            teacher_id = teacher_map.get(r["teacher_email"])
            grade_id = int(grade_map[r["grade_name"]])
            section_id = int(section_map[r["grade_name"]][r["section_name"]])
            subject_id = subject_map.get(r["subject_name"])
            if not teacher_id or not subject_id:
                continue
            conn.execute(text("""
                INSERT INTO ss_t_homework_details
                (teacher_id, grade_id, section_id, subject_id, title, more_details, assigned_date, due_date, status)
                VALUES (:teacher_id, :grade_id, :section_id, :subject_id, :title, :more_details, :assigned_date, :due_date, :status)
            """), {"teacher_id": teacher_id, "grade_id": grade_id, "section_id": section_id, 
                   "subject_id": subject_id, "title": r.get("title"), "more_details": r.get("more_details"),
                   "assigned_date": r.get("assigned_date"), "due_date": r.get("due_date"), "status": r.get("status")})

def insert_class_diary(engine: Engine, df: pd.DataFrame, grade_map: Dict[str,int], section_map: Dict[str, Dict[str,int]], subject_map: Dict[str,int], teacher_map: Dict[str,int]):
    with engine.begin() as conn:
        for _, r in df.iterrows():
            if pd.isna(r.get("teacher_email")) or pd.isna(r.get("grade_name")) or pd.isna(r.get("section_name")) or pd.isna(r.get("subject_name")) or pd.isna(r.get("date")) or pd.isna(r.get("title")):
                continue
            if r["grade_name"] not in grade_map or r["section_name"] not in section_map.get(r["grade_name"], {}):
                continue
            teacher_id = teacher_map.get(r["teacher_email"])
            grade_id = int(grade_map[r["grade_name"]])
            section_id = int(section_map[r["grade_name"]][r["section_name"]])
            subject_id = subject_map.get(r["subject_name"])
            if not teacher_id or not subject_id:
                continue
            conn.execute(text("""
                INSERT INTO ss_t_class_diary
                (teacher_id, grade_id, section_id, subject_id, entry_date, title, description)
                VALUES (:teacher_id, :grade_id, :section_id, :subject_id, :entry_date, :title, :description)
            """), {"teacher_id": teacher_id, "grade_id": grade_id, "section_id": section_id,
                   "subject_id": subject_id, "entry_date": r.get("date"), "title": r.get("title"),
                   "description": r.get("description")})

def insert_fees_summary(engine: Engine, df: pd.DataFrame, student_hint_map: Dict[int,int]) -> Dict[int,int]:
    fee_map = {}
    with engine.begin() as conn:
        for _, r in df.iterrows():
            if pd.isna(r.get("student_id_hint")):
                continue
            student_id = student_hint_map.get(int(r["student_id_hint"]))
            if not student_id:
                continue
            d = ensure_keys(r, ["total_fee", "concession", "net_payable", "amount_paid"])
            conn.execute(text("""
                INSERT INTO ss_t_fees_summary (student_id, total_fee, concession, net_payable, amount_paid)
                VALUES (:student_id, :total_fee, :concession, :net_payable, :amount_paid)
                ON DUPLICATE KEY UPDATE total_fee=VALUES(total_fee), concession=VALUES(concession), net_payable=VALUES(net_payable), amount_paid=VALUES(amount_paid)
            """), {"student_id": student_id, "total_fee": d.get("total_fee"), "concession": d.get("concession"),
                   "net_payable": d.get("net_payable"), "amount_paid": d.get("amount_paid")})
        q = conn.execute(text("SELECT fee_id, student_id FROM ss_t_fees_summary"))
        fee_map = {row.student_id: row.fee_id for row in q.fetchall()}
    return fee_map

def insert_installments(engine: Engine, df: pd.DataFrame, student_hint_map: Dict[int,int], fee_map: Dict[int,int]):
    with engine.begin() as conn:
        for _, r in df.iterrows():
            if pd.isna(r.get("student_id_hint")) or pd.isna(r.get("installment_no")):
                continue
            student_id = student_hint_map.get(int(r["student_id_hint"]))
            if not student_id:
                continue
            fee_id = fee_map.get(student_id)
            if not fee_id:
                continue
            d = ensure_keys(r, ["installment_no", "amount", "due_date", "paid_date", "paid_status"])
            conn.execute(text("""
                INSERT INTO ss_t_installments (fee_id, installment_no, amount, due_date, paid_date, paid_status)
                VALUES (:fee_id, :installment_no, :amount, :due_date, :paid_date, :paid_status)
                ON DUPLICATE KEY UPDATE amount=VALUES(amount), due_date=VALUES(due_date), paid_date=VALUES(paid_date), paid_status=VALUES(paid_status)
            """), {"fee_id": fee_id, "installment_no": d.get("installment_no"), "amount": d.get("amount"),
                   "due_date": d.get("due_date"), "paid_date": d.get("paid_date"), "paid_status": d.get("paid_status")})

def insert_teacher_salary_structure(engine: Engine, df: pd.DataFrame, teacher_map: Dict[str,int]):
    with engine.begin() as conn:
        for _, r in df.iterrows():
            if pd.isna(r.get("teacher_email")):
                continue
            teacher_id = teacher_map.get(r["teacher_email"])
            if not teacher_id:
                continue
            d = ensure_keys(r, ["basic_pay", "allowances", "deductions"])
            conn.execute(text("""
                INSERT INTO ss_t_teacher_salary_structure (teacher_id, basic_pay, allowances, deductions)
                VALUES (:teacher_id, :basic_pay, :allowances, :deductions)
                ON DUPLICATE KEY UPDATE basic_pay=VALUES(basic_pay), allowances=VALUES(allowances), deductions=VALUES(deductions)
            """), {"teacher_id": teacher_id, "basic_pay": d.get("basic_pay"), "allowances": d.get("allowances"), "deductions": d.get("deductions")})

def insert_teacher_salary_payslip(engine: Engine, df: pd.DataFrame, teacher_map: Dict[str,int]):
    with engine.begin() as conn:
        for _, r in df.iterrows():
            if pd.isna(r.get("teacher_email")) or pd.isna(r.get("year")) or pd.isna(r.get("month")):
                continue
            teacher_id = teacher_map.get(r["teacher_email"])
            if not teacher_id:
                continue
            d = ensure_keys(r, ["year", "month", "basic_pay", "allowances", "deductions", "net_pay"])
            conn.execute(text("""
                INSERT INTO ss_t_teacher_salary_payslip (teacher_id, year, month, basic_pay, allowances, deductions, net_pay)
                VALUES (:teacher_id, :year, :month, :basic_pay, :allowances, :deductions, :net_pay)
                ON DUPLICATE KEY UPDATE basic_pay=VALUES(basic_pay), allowances=VALUES(allowances), deductions=VALUES(deductions), net_pay=VALUES(net_pay)
            """), {"teacher_id": teacher_id, "year": int(d.get("year")), "month": int(d.get("month")),
                   "basic_pay": d.get("basic_pay"), "allowances": d.get("allowances"),
                   "deductions": d.get("deductions"), "net_pay": d.get("net_pay")})

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mysql", required=True, help="SQLAlchemy MySQL URL")
    ap.add_argument("--excel", required=True, help="Path to SchoolOnboardingTemplates.xlsx")
    args = ap.parse_args()

    engine = create_engine(args.mysql, future=True)
    xls = pd.ExcelFile(args.excel)

    # Read sheets
    df_schools = pd.read_excel(xls, "schools")
    df_grades = pd.read_excel(xls, "grades")
    df_sections = pd.read_excel(xls, "sections")
    df_subjects = pd.read_excel(xls, "subjects")
    df_teachers = pd.read_excel(xls, "teachers")
    df_students = pd.read_excel(xls, "students")
    df_teacher_subjects = pd.read_excel(xls, "teacher_subjects")
    df_teacher_grade_section = pd.read_excel(xls, "teacher_grade_section")
    df_timeslots = pd.read_excel(xls, "timeslots")
    df_timetable = pd.read_excel(xls, "timetable")
    df_attendance = pd.read_excel(xls, "attendance")
    df_homework = pd.read_excel(xls, "homework")
    df_class_diary = pd.read_excel(xls, "class_diary")
    df_fees_summary = pd.read_excel(xls, "fees_summary")
    df_installments = pd.read_excel(xls, "installments")
    df_salary_structure = pd.read_excel(xls, "salary_structure")
    df_salary_payslips = pd.read_excel(xls, "salary_payslips")

    # Insert data in order respecting foreign keys
    school_map = upsert_school(engine, df_schools)
    school_name = df_schools.iloc[0]["school_name"]
    school_id = school_map.get(school_name)

    grade_map = insert_grades(engine, df_grades, school_id)
    section_map = insert_sections(engine, df_sections, grade_map)
    subject_map = insert_subjects(engine, df_subjects, school_id)
    teacher_map = insert_teachers(engine, df_teachers, school_id)

    # Build teacher_hint_map and subject_hint_map for cross references
    teacher_hint_map = {}
    if 'teacher_id_hint' in df_teachers.columns:
        for _, r in df_teachers.iterrows():
            if not pd.isna(r.get("teacher_id_hint")):
                email = r.get("email")
                if email in teacher_map:
                    teacher_hint_map[int(r["teacher_id_hint"])] = teacher_map[email]
    subject_hint_map = {}
    if 'subject_id_hint' in df_subjects.columns:
        for _, r in df_subjects.iterrows():
            if not pd.isna(r.get("subject_id_hint")):
                subj_name = r.get("subject_name")
                if subj_name in subject_map:
                    subject_hint_map[int(r["subject_id_hint"])] = subject_map[subj_name]

    student_hint_map = insert_students(engine, df_students, grade_map, section_map)

    insert_teacher_subjects(engine, df_teacher_subjects, teacher_hint_map, subject_hint_map)
    insert_teacher_grade_section(engine, df_teacher_grade_section, teacher_hint_map, grade_map, section_map)

    insert_timeslots(engine, df_timeslots)
    insert_timetable(engine, df_timetable, grade_map, section_map, subject_map, teacher_map)

    insert_attendance(engine, df_attendance, student_hint_map)

    insert_homework_details(engine, df_homework, grade_map, section_map, subject_map, teacher_map)
    insert_class_diary(engine, df_class_diary, grade_map, section_map, subject_map, teacher_map)

    fee_map = insert_fees_summary(engine, df_fees_summary, student_hint_map)
    insert_installments(engine, df_installments, student_hint_map, fee_map)

    insert_teacher_salary_structure(engine, df_salary_structure, teacher_map)
    insert_teacher_salary_payslip(engine, df_salary_payslips, teacher_map)

    print("Load complete.")

if __name__ == "__main__":
    sys.exit(main())
