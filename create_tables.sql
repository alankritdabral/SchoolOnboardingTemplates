-- School Management Schema (MySQL)
-- Engine & charset defaults

DROP DATABASE IF EXISTS schooldb;
CREATE DATABASE schooldb CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

USE schooldb;
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS=0;

DROP TABLE IF EXISTS ss_t_teacher_salary_payslip;
DROP TABLE IF EXISTS ss_t_teacher_salary_structure;
DROP TABLE IF EXISTS ss_t_installments;
DROP TABLE IF EXISTS ss_t_fees_summary;
DROP TABLE IF EXISTS ss_t_class_diary;
DROP TABLE IF EXISTS ss_t_homework_details;
DROP TABLE IF EXISTS ss_t_attendance;
DROP TABLE IF EXISTS ss_t_timetable;
DROP TABLE IF EXISTS ss_t_timeslots;
DROP TABLE IF EXISTS ss_t_teacher_grade_section;
DROP TABLE IF EXISTS ss_t_teacher_subject;
DROP TABLE IF EXISTS ss_t_students;
DROP TABLE IF EXISTS ss_t_teachers;
DROP TABLE IF EXISTS ss_t_subjects;
DROP TABLE IF EXISTS ss_t_sections;
DROP TABLE IF EXISTS ss_t_grades;
DROP TABLE IF EXISTS ss_t_schools;

CREATE TABLE ss_t_schools (
  school_id INT AUTO_INCREMENT PRIMARY KEY,
  school_name VARCHAR(100) NOT NULL,
  profile_pic_location VARCHAR(255),
  address VARCHAR(255),
  primary_phone_number VARCHAR(30),
  secondary_phone_number VARCHAR(30),
  email VARCHAR(100),
  established_year INT,
  medium_of_instruction VARCHAR(50),
  principal_head_name VARCHAR(100),
  administrative_contact VARCHAR(100),
  number_of_staff INT,
  is_active TINYINT(1) DEFAULT 1,
  rec_created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  rec_updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_grades (
  grade_id INT AUTO_INCREMENT PRIMARY KEY,
  school_id INT NOT NULL,
  grade_name VARCHAR(50) NOT NULL,
  description VARCHAR(255),
  tuition_fee DECIMAL(10,2) DEFAULT 0,
  admission_fee DECIMAL(10,2) DEFAULT 0,
  development_fee DECIMAL(10,2) DEFAULT 0,
  activity_fee DECIMAL(10,2) DEFAULT 0,
  lab_fee DECIMAL(10,2) DEFAULT 0,
  transportation_fee DECIMAL(10,2) DEFAULT 0,
  late_fee_penalty DECIMAL(10,2) DEFAULT 0,
  annual_event_fee DECIMAL(10,2) DEFAULT 0,
  examination_fee DECIMAL(10,2) DEFAULT 0,
  other_fee DECIMAL(10,2) DEFAULT 0,
  payment_methods_accepted VARCHAR(100) DEFAULT 'Cash,UPI,Card',
  UNIQUE KEY uq_grade (school_id, grade_name),
  KEY idx_grade_school (school_id),
  CONSTRAINT fk_grade_school FOREIGN KEY (school_id) REFERENCES ss_t_schools(school_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_sections (
  section_id INT AUTO_INCREMENT PRIMARY KEY,
  grade_id INT NOT NULL,
  section_name VARCHAR(10) NOT NULL,
  capacity INT DEFAULT 40,
  UNIQUE KEY uq_section (grade_id, section_name),
  KEY idx_section_grade (grade_id),
  CONSTRAINT fk_section_grade FOREIGN KEY (grade_id) REFERENCES ss_t_grades(grade_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_subjects (
  subject_id INT AUTO_INCREMENT PRIMARY KEY,
  school_id INT NOT NULL,
  subject_name VARCHAR(80) NOT NULL,
  UNIQUE KEY uq_subject_school (school_id, subject_name),
  KEY idx_subject_school (school_id),
  CONSTRAINT fk_subject_school FOREIGN KEY (school_id) REFERENCES ss_t_schools(school_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_teachers (
  teacher_id INT AUTO_INCREMENT PRIMARY KEY,
  school_id INT NOT NULL,
  first_name VARCHAR(50) NOT NULL,
  middle_name VARCHAR(50),
  last_name VARCHAR(50),
  profile_pic_location VARCHAR(255),
  gender VARCHAR(10),
  date_of_birth DATE,
  mobile_number VARCHAR(20),
  email VARCHAR(100),
  communication_address VARCHAR(255),
  languages_known VARCHAR(100),
  is_active TINYINT(1) DEFAULT 1,
  UNIQUE KEY uq_teacher_email (email),
  KEY idx_teacher_school (school_id),
  CONSTRAINT fk_teacher_school FOREIGN KEY (school_id) REFERENCES ss_t_schools(school_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_students (
  student_id INT AUTO_INCREMENT PRIMARY KEY,
  school_id INT NOT NULL,
  grade_id INT NOT NULL,
  section_id INT NOT NULL,
  first_name VARCHAR(50) NOT NULL,
  middle_name VARCHAR(50),
  last_name VARCHAR(50),
  profile_pic_location VARCHAR(255),
  gender VARCHAR(10),
  date_of_birth DATE,
  mobile_number VARCHAR(20),
  email VARCHAR(100),
  communication_address VARCHAR(255),
  languages_known VARCHAR(100),
  guardian_name VARCHAR(100),
  guardian_mobile VARCHAR(20),
  UNIQUE KEY uq_student_email (email),
  KEY idx_student_grade_section (grade_id, section_id),
  CONSTRAINT fk_student_school FOREIGN KEY (school_id) REFERENCES ss_t_schools(school_id),
  CONSTRAINT fk_student_grade FOREIGN KEY (grade_id) REFERENCES ss_t_grades(grade_id),
  CONSTRAINT fk_student_section FOREIGN KEY (section_id) REFERENCES ss_t_sections(section_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_teacher_subject (
  teacher_subject_id INT AUTO_INCREMENT PRIMARY KEY,
  teacher_id INT NOT NULL,
  subject_id INT NOT NULL,
  UNIQUE KEY uq_teacher_subject (teacher_id, subject_id),
  KEY idx_ts_teacher (teacher_id),
  KEY idx_ts_subject (subject_id),
  CONSTRAINT fk_ts_teacher FOREIGN KEY (teacher_id) REFERENCES ss_t_teachers(teacher_id),
  CONSTRAINT fk_ts_subject FOREIGN KEY (subject_id) REFERENCES ss_t_subjects(subject_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_teacher_grade_section (
  teacher_grade_section_id INT AUTO_INCREMENT PRIMARY KEY,
  teacher_id INT NOT NULL,
  grade_id INT NOT NULL,
  section_id INT NOT NULL,
  UNIQUE KEY uq_teacher_grsec (teacher_id, grade_id, section_id),
  KEY idx_tgs_teacher (teacher_id),
  KEY idx_tgs_grade_section (grade_id, section_id),
  CONSTRAINT fk_tgs_teacher FOREIGN KEY (teacher_id) REFERENCES ss_t_teachers(teacher_id),
  CONSTRAINT fk_tgs_grade FOREIGN KEY (grade_id) REFERENCES ss_t_grades(grade_id),
  CONSTRAINT fk_tgs_section FOREIGN KEY (section_id) REFERENCES ss_t_sections(section_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_timeslots (
  timeslot_id INT AUTO_INCREMENT PRIMARY KEY,
  day_of_week ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday') NOT NULL,
  period_number INT NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  UNIQUE KEY uq_day_period (day_of_week, period_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_timetable (
  timetable_id INT AUTO_INCREMENT PRIMARY KEY,
  grade_id INT NOT NULL,
  section_id INT NOT NULL,
  timeslot_id INT NOT NULL,
  subject_id INT,
  teacher_id INT,
  room_number VARCHAR(20),
  is_active TINYINT(1) DEFAULT 1,
  KEY idx_tt_grsec (grade_id, section_id),
  KEY idx_tt_timeslot (timeslot_id),
  CONSTRAINT fk_tt_grade FOREIGN KEY (grade_id) REFERENCES ss_t_grades(grade_id),
  CONSTRAINT fk_tt_section FOREIGN KEY (section_id) REFERENCES ss_t_sections(section_id),
  CONSTRAINT fk_tt_timeslot FOREIGN KEY (timeslot_id) REFERENCES ss_t_timeslots(timeslot_id),
  CONSTRAINT fk_tt_subject FOREIGN KEY (subject_id) REFERENCES ss_t_subjects(subject_id),
  CONSTRAINT fk_tt_teacher FOREIGN KEY (teacher_id) REFERENCES ss_t_teachers(teacher_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_attendance (
  attendance_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  attendance_date DATE NOT NULL,
  status ENUM('Present','Absent') NOT NULL,
  rec_created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_att (student_id, attendance_date),
  KEY idx_att_date (attendance_date),
  CONSTRAINT fk_att_student FOREIGN KEY (student_id) REFERENCES ss_t_students(student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_homework_details (
  homework_id INT AUTO_INCREMENT PRIMARY KEY,
  teacher_id INT NOT NULL,
  grade_id INT NOT NULL,
  section_id INT NOT NULL,
  subject_id INT NOT NULL,
  title VARCHAR(150) NOT NULL,
  more_details TEXT,
  assigned_date DATE NOT NULL,
  due_date DATE,
  status ENUM('Pending','Submitted','Completed') DEFAULT 'Pending',
  KEY idx_hw_grsec (grade_id, section_id),
  CONSTRAINT fk_hw_teacher FOREIGN KEY (teacher_id) REFERENCES ss_t_teachers(teacher_id),
  CONSTRAINT fk_hw_grade FOREIGN KEY (grade_id) REFERENCES ss_t_grades(grade_id),
  CONSTRAINT fk_hw_section FOREIGN KEY (section_id) REFERENCES ss_t_sections(section_id),
  CONSTRAINT fk_hw_subject FOREIGN KEY (subject_id) REFERENCES ss_t_subjects(subject_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_class_diary (
  diary_id INT AUTO_INCREMENT PRIMARY KEY,
  teacher_id INT NOT NULL,
  grade_id INT NOT NULL,
  section_id INT NOT NULL,
  subject_id INT NOT NULL,
  entry_date DATE NOT NULL,
  title VARCHAR(150) NOT NULL,
  description TEXT,
  CONSTRAINT fk_cd_teacher FOREIGN KEY (teacher_id) REFERENCES ss_t_teachers(teacher_id),
  CONSTRAINT fk_cd_grade FOREIGN KEY (grade_id) REFERENCES ss_t_grades(grade_id),
  CONSTRAINT fk_cd_section FOREIGN KEY (section_id) REFERENCES ss_t_sections(section_id),
  CONSTRAINT fk_cd_subject FOREIGN KEY (subject_id) REFERENCES ss_t_subjects(subject_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_fees_summary (
  fee_id INT AUTO_INCREMENT PRIMARY KEY,
  student_id INT NOT NULL,
  total_fee DECIMAL(10,2) NOT NULL,
  concession DECIMAL(10,2) DEFAULT 0,
  net_payable DECIMAL(10,2) NOT NULL,
  amount_paid DECIMAL(10,2) DEFAULT 0,
  balance_due DECIMAL(10,2) GENERATED ALWAYS AS (net_payable - amount_paid) STORED,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_fee_student (student_id),
  CONSTRAINT fk_fee_student FOREIGN KEY (student_id) REFERENCES ss_t_students(student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_installments (
  installment_id INT AUTO_INCREMENT PRIMARY KEY,
  fee_id INT NOT NULL,
  installment_no INT NOT NULL,
  amount DECIMAL(10,2) NOT NULL,
  due_date DATE,
  paid_date DATE,
  paid_status ENUM('Pending','Paid','Partial') DEFAULT 'Pending',
  UNIQUE KEY uq_inst (fee_id, installment_no),
  KEY idx_inst_fee (fee_id),
  CONSTRAINT fk_inst_fee FOREIGN KEY (fee_id) REFERENCES ss_t_fees_summary(fee_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_teacher_salary_structure (
  structure_id INT AUTO_INCREMENT PRIMARY KEY,
  teacher_id INT NOT NULL,
  basic_pay DECIMAL(10,2) NOT NULL,
  allowances DECIMAL(10,2) DEFAULT 0,
  deductions DECIMAL(10,2) DEFAULT 0,
  UNIQUE KEY uq_salary_structure (teacher_id),
  CONSTRAINT fk_sal_teacher FOREIGN KEY (teacher_id) REFERENCES ss_t_teachers(teacher_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ss_t_teacher_salary_payslip (
  payslip_id INT AUTO_INCREMENT PRIMARY KEY,
  teacher_id INT NOT NULL,
  year INT NOT NULL,
  month INT NOT NULL,
  basic_pay DECIMAL(10,2) NOT NULL,
  allowances DECIMAL(10,2) DEFAULT 0,
  deductions DECIMAL(10,2) DEFAULT 0,
  net_pay DECIMAL(10,2) NOT NULL,
  UNIQUE KEY uq_payslip (teacher_id, year, month),
  CONSTRAINT fk_payslip_teacher FOREIGN KEY (teacher_id) REFERENCES ss_t_teachers(teacher_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS=1;