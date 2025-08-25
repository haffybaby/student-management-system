# 🎓 Student Result Management System (SRMS)

A modern, full-stack solution for managing **student records, subjects, scores, and analytics**.  
Built with **FastAPI** (backend REST API), **MySQL** (database), and **Streamlit** (dashboard UI).

---

## 🚀 Quickstart

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/srms.git
cd srms
```

### 2. Set Up Python Environment
```bash
python -m venv venv
venv\Scripts\activate      # On Windows
# Or
source venv/bin/activate   # On Mac/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:

```ini
DB_USER=root
DB_PASS=your_mysql_password
DB_NAME=student_db
DB_HOST=localhost
```

### 5. Set Up MySQL Database
Run the following SQL in MySQL:
```sql
CREATE DATABASE student_db;
CREATE USER 'root'@'localhost' IDENTIFIED BY 'your_mysql_password';
GRANT ALL PRIVILEGES ON student_db.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

### 6. Run the FastAPI Backend
```bash
uvicorn SMS:app --reload
```
API docs will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 7. Run the Streamlit Dashboard
```bash
streamlit run app.py
```
Dashboard will be available at: [http://localhost:8501](http://localhost:8501)

---

## 🏗️ Architecture

- **Backend**: FastAPI REST API (`SMS.py`)  
- **Database**: MySQL (tables auto-created by SQLAlchemy models)  
- **Frontend**: Streamlit dashboard (`app.py`)  
- **ORM**: SQLAlchemy  
- **Config**: `.env` file for DB credentials  

---

## 📚 Data Model

### Student
| Field        | Type   | Description          |
|--------------|--------|----------------------|
| student_id   | int    | Primary Key          |
| student_name | string | Student's name       |
| class_name   | string | Class (e.g., JSS1)   |
| gender       | string | 'M' or 'F'           |
| date_of_birth| string | Date of birth        |

### Subject
| Field       | Type   | Description    |
|-------------|--------|----------------|
| subject_id  | int    | Primary Key    |
| subject_name| string | Subject name   |

### Score
| Field       | Type   | Description                     |
|-------------|--------|---------------------------------|
| score_id    | int    | Primary Key                     |
| student_id  | int    | Foreign Key (Student)           |
| subject_id  | int    | Foreign Key (Subject)           |
| term        | string | e.g., "FirstTerm"               |
| session_year| string | Academic session                |
| score       | float  | Score (0–100)                   |

---

## 🔌 API Endpoints

### Students
- `POST /students` — Add student  
- `GET /students` — List students  

### Subjects
- `POST /subjects` — Add subject  
- `GET /subjects` — List subjects  

### Scores
- `POST /scores` — Add score  
- `GET /scores/student/{student_id}` — Get scores for a student  

### Analytics
- `GET /analytics/top-students` — Top N students (optionally by class/term)  
- `GET /analytics/class-summary/{class_name}/{term}` — Class stats per subject  
- `GET /analytics/transcript/{student_id}` — Student transcript  
- `GET /analytics/export` — Export report to Excel  
- `GET /analytics/configurable-report` — Custom report (min subjects, etc.)  

---

## 📊 Streamlit Dashboard Features

- **Dashboard**: Key metrics, top students, quick charts  
- **Students**: Add/list students  
- **Subjects**: Add/list subjects  
- **Scores**: Add scores, view by student  
- **Analytics**: Class stats, student ranking, quick charts, CSV export  

---

## 🧑‍💻 Contributing

### How to Contribute
1. Fork the repo and create your branch:
   ```bash
   git checkout -b feature/my-feature
   ```
2. Commit your changes:
   ```bash
   git commit -am "Add new feature"
   ```
3. Push to the branch:
   ```bash
   git push origin feature/my-feature
   ```
4. Open a Pull Request on GitHub.

### Code Style
- Use **Black**, **isort**, and **flake8** for formatting/linting.  
- Type annotations are encouraged.  
- Write tests for new features.  

---

## 🧪 Running Tests
```bash
pytest
```

---

## 📂 File Structure
*(You can expand this with a `tree` view of your repo later)*

---

## 📝 License
MIT License. See [LICENSE](./LICENSE) for details.

---

## 🙋 FAQ

**Q: I get "Access denied for user" errors?**  
A: Check your `.env` file for correct DB credentials and ensure no quotes around values.

**Q: How do I reset the database?**  
A: Drop and recreate the database in MySQL, then restart the FastAPI app.

**Q: How do I add new analytics or endpoints?**  
A: Add new routes to `SMS.py` and corresponding UI in `app.py`.

---

## 📬 Support
Open an issue or start a discussion for help or feature requests.

---

✨ Happy coding! 🎓
