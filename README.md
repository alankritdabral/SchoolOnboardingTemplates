# School Onboarding & Data Population Assignment

## 📂 Folder Structure

```
├── create_tables.sql              # SQL script to create database schema
├── data_loader.py                 # Python ETL script to load Excel → MySQL
├── SchoolOnboardingTemplates.xlsx # Input Excel with sample data
├── student_attendance_prediction.ipynb # ML notebook for attendance-based risk prediction
├── SQL-ML-Assignment.pdf          # Assignment problem statement
└── README.md                      # Documentation
```

---

## 🚀 How to Run

### 1. Setup Database

```bash
mysql -u root -p < create_tables.sql
```

This creates the `schooldb` schema with all required tables (17 total, including salary & payslip tables).

### 2. Install Dependencies

```bash
pip install pandas sqlalchemy pymysql openpyxl jupyter scikit-learn matplotlib
```

### 3. Load Data from Excel

```bash
python data_loader.py \
  --mysql "mysql+pymysql://root:password@localhost:3306/schooldb" \
  --excel SchoolOnboardingTemplates.xlsx
```

If successful, you’ll see:

```
Load complete.
```

### 4. Run ML Notebook

Launch Jupyter and open the notebook:

```bash
jupyter notebook student_attendance_prediction.ipynb
```

The notebook demonstrates attendance-based student risk prediction.

---

## 📝 Features Implemented

### ✅ Part A: Database ETL Automation

* Reads **all sheets** from `SchoolOnboardingTemplates.xlsx`:

  * `schools`, `grades`, `sections`, `subjects`, `teachers`, `students`
  * `teacher_subjects`, `teacher_grade_section`, `timeslots`, `timetable`
  * `attendance`, `homework`, `class_diary`, `fees_summary`, `installments`
  * `salary_structure`, `salary_payslips`
* Inserts into **all 17 tables** (`ss_t_schools`, `ss_t_grades`, …, `ss_t_teacher_salary_payslip`).
* Maintains **referential integrity** by inserting in the correct order.
* Uses **upsert logic** (avoids duplicates, updates existing records).
* Auto-handles missing fields with `None`.

### ✅ Part B: ML Insight Generation

* Implemented a **Student Performance Risk Classifier**:

  * Features: Attendance %, Homework completion ratio.
  * Output: Risk Level → High, Medium, Low.
  * Extensible: can incorporate diary remarks or fee payment delays.
* Delivered via Jupyter notebook: `student_attendance_prediction.ipynb`.

---

## 📊 Assignment Criteria Coverage

1. **School Setup** → 1 school, 3 grades, 2 sections each.
2. **Students** → 60 students inserted, attendance ≥ 80%.
3. **Teachers** → 8 teachers, each mapped to ≥2 sections, subjects, homework (3 per teacher), class diary (2 per teacher).
4. **Timetable** → Weekly structure with free/lunch/leave periods.
5. **Fees** → Each student has installments, at least one paid → reflected in income.
6. **Salary** → Salary structure + payslips for June & July.
7. **ML** → Attendance-driven student risk classifier included.

---

## ⚙️ Notes & Changes Made

* Used **SQLAlchemy + Pandas** for robust ETL.
* Added **upsert logic** to allow repeated runs.
* `ensure_keys()` utility fills missing Excel fields with `None`.
* Extra columns (`*_id_hint`) help map Excel rows to DB IDs.
* Added **Jupyter notebook** for ML experimentation.

---

## ✅ Verification Reports

Run SQL queries to validate requirements:

* **Attendance >80%**

```sql
SELECT student_id,
       SUM(status='Present') / COUNT(*) * 100 AS attendance_pct
FROM ss_t_attendance
GROUP BY student_id;
```

* **Homework per teacher = 3 (Pending, Submitted, Completed)**

```sql
SELECT teacher_id, status, COUNT(*)
FROM ss_t_homework_details
GROUP BY teacher_id, status;
```

* **Class diary = 2 entries per teacher**

```sql
SELECT teacher_id, COUNT(*)
FROM ss_t_class_diary
GROUP BY teacher_id;
```

* **At least 1 fee installment paid**

```sql
SELECT student_id, COUNT(*)
FROM ss_t_installments
WHERE paid_status='Paid'
GROUP BY student_id;
```

* **Salary slips for June & July**

```sql
SELECT teacher_id, year, month
FROM ss_t_teacher_salary_payslip;
```

---

## 📌 Conclusion

* Database setup & ETL fully automated.
* Assignment requirements (Part A + Part B ML task) satisfied.
* Added ML notebook for predictive insights.
* Code modular, clean, and extensible.
