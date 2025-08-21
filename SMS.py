from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DECIMAL, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
import os
import pandas as pd

# --- ENV CONFIG ---
load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASS}@localhost/{DB_NAME}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="Student Result Management API")

# --- DB MODELS ---
class Student(Base):
    __tablename__ = "students"
    student_id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String(100), nullable=False)
    class_name = Column(String(10), nullable=False)
    gender = Column(String(1), nullable=False)
    date_of_birth = Column(String(20), nullable=False)
    scores = relationship("Score", back_populates="student")

class Subject(Base):
    __tablename__ = "subjects"
    subject_id = Column(Integer, primary_key=True, index=True)
    subject_name = Column(String(100), nullable=False)
    scores = relationship("Score", back_populates="subject")

class Score(Base):
    __tablename__ = "scores"
    score_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"))
    subject_id = Column(Integer, ForeignKey("subjects.subject_id", ondelete="CASCADE"))
    term = Column(String(20), nullable=False)
    session_year = Column(String(20), nullable=True)
    score = Column(DECIMAL(5,2), nullable=False)

    student = relationship("Student", back_populates="scores")
    subject = relationship("Subject", back_populates="scores")

Base.metadata.create_all(bind=engine)

# --- DEPENDENCY ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SCHEMAS ---
class StudentCreate(BaseModel):
    student_name: str
    class_name: str
    gender: str
    date_of_birth: str

class SubjectCreate(BaseModel):
    subject_name: str

class ScoreCreate(BaseModel):
    student_id: int
    subject_id: int
    term: str
    session_year: str
    score: float

# --- STUDENT ENDPOINTS ---
@app.post("/students")
def add_student(student: StudentCreate, db: Session = Depends(get_db)):
    db_student = Student(**student.dict())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return {"message": "Student added successfully", "student_id": db_student.student_id}

@app.get("/students")
def list_students(db: Session = Depends(get_db)):
    return db.query(Student).all()

# --- SUBJECT ENDPOINTS ---
@app.post("/subjects")
def add_subject(subject: SubjectCreate, db: Session = Depends(get_db)):
    db_subject = Subject(**subject.dict())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return {"message": "Subject added successfully", "subject_id": db_subject.subject_id}

@app.get("/subjects")
def list_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()

# --- SCORE ENDPOINTS ---
@app.post("/scores")
def add_score(score: ScoreCreate, db: Session = Depends(get_db)):
    # Validate score range
    if score.score < 0 or score.score > 100:
        raise HTTPException(status_code=400, detail="Score must be between 0 and 100")

    db_score = Score(**score.dict())
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    return {"message": "Score added successfully", "score_id": db_score.score_id}

@app.get("/scores/student/{student_id}")
def get_student_scores(student_id: int, db: Session = Depends(get_db)):
    scores = db.query(Score).filter(Score.student_id == student_id).all()
    if not scores:
        raise HTTPException(status_code=404, detail="No scores found for this student")
    return scores

@app.get("/scores/top/{n}")
def get_top_students(n: int, db: Session = Depends(get_db)):
    result = db.query(
        Score.student_id,
        func.avg(Score.score).label("average_score")
    ).group_by(Score.student_id).order_by(func.avg(Score.score).desc()).limit(n).all()
    return result

# --- PANDAS POWERED ANALYTICS ---
@app.get("/scores/stats/class/{class_name}")
def class_stats(class_name: str, db: Session = Depends(get_db)):
    result = db.query(
        func.avg(Score.score).label("average_score"),
        func.max(Score.score).label("highest_score"),
        func.min(Score.score).label("lowest_score")
    ).join(Student).filter(Student.class_name == class_name).first()

    if not result or all(v is None for v in result):
        raise HTTPException(status_code=404, detail="No scores found for this class")

    return {
        "class_name": class_name,
        "average_score": float(result.average_score) if result.average_score else None,
        "highest_score": float(result.highest_score) if result.highest_score else None,
        "lowest_score": float(result.lowest_score) if result.lowest_score else None,
    }

@app.get("/analytics/student-rank/{term}")
def student_ranking(term: str, db: Session = Depends(get_db)):
    query = db.query(
        Student.student_id, Student.student_name, Score.term, Score.score
    ).join(Score).filter(Score.term == term)

    df = pd.read_sql(query.statement, db.bind)

    if df.empty:
        raise HTTPException(status_code=404, detail="No data available for this term")

    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df = df.dropna(subset=["score"])
    df = df[(df["score"] >= 0) & (df["score"] <= 100)]

    student_avg = df.groupby(["student_id", "student_name"])["score"].mean().reset_index()
    student_avg["rank"] = student_avg["score"].rank(method="dense", ascending=False)

    return student_avg.sort_values(by="score", ascending=False).to_dict(orient="records")
