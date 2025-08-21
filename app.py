# app.py
import os
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

# --------------- CONFIG / THEME ---------------
st.set_page_config(
    page_title="Student Result Management",
    page_icon="🎓",
    layout="wide",
    menu_items={"Get help": "https://fastapi.tiangolo.com", "About": "SRMS Frontend • Streamlit + FastAPI"},
)

# Subtle custom CSS for polished UI
st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    .stMetric { text-align: center; }
    .metric-card { border-radius: 16px; padding: 16px; box-shadow: 0 4px 18px rgba(0,0,0,.08); }
    .pill { display:inline-block; padding:2px 8px; border-radius:999px; background: #eef2ff; color:#4338ca; font-size:12px; }
    .good { color:#16a34a; }
    .bad { color:#dc2626; }
    .warn { color:#d97706; }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------- ENV / BASE URL ---------------
load_dotenv()
DEFAULT_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

with st.sidebar:
    st.title("🎓 SRMS")
    st.caption("Streamlit UI for your FastAPI")
    base_url = st.text_input("API Base URL", value=DEFAULT_BASE_URL, help="e.g. http://127.0.0.1:8000")
    st.divider()
    st.markdown("**Quick Links**")
    col = st.columns(2)
    with col[0]:
        if st.button("Open Swagger", use_container_width=True):
            st.markdown(f"[Open Swagger UI]({urljoin(base_url, '/docs')})")
    with col[1]:
        if st.button("Open ReDoc", use_container_width=True):
            st.markdown(f"[Open ReDoc]({urljoin(base_url, '/redoc')})")
    st.divider()
    st.caption("Tip: Keep FastAPI running → `uvicorn main:app --reload`")


# --------------- HELPERS ---------------
def api_get(path: str, params: Optional[Dict[str, Any]] = None) -> Any:
    url = urljoin(base_url, path)
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code >= 400:
            raise RuntimeError(f"{r.status_code}: {r.text}")
        return r.json()
    except Exception as e:
        st.error(f"GET {url} failed: {e}")
        return None


def api_post(path: str, payload: Dict[str, Any]) -> Any:
    url = urljoin(base_url, path)
    try:
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code >= 400:
            raise RuntimeError(f"{r.status_code}: {r.text}")
        return r.json()
    except Exception as e:
        st.error(f"POST {url} failed: {e}")
        return None


@st.cache_data(ttl=30)
def get_students_df() -> pd.DataFrame:
    data = api_get("/students") or []
    return pd.DataFrame(data)


@st.cache_data(ttl=30)
def get_subjects_df() -> pd.DataFrame:
    data = api_get("/subjects") or []
    return pd.DataFrame(data)


def show_df(df: pd.DataFrame, caption: str = ""):
    if df is None or df.empty:
        st.info("No data to display yet.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        if caption:
            st.caption(caption)


def download_df_button(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    if df is None or df.empty:
        return
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv, file_name=filename, mime="text/csv")


# --------------- TABS / PAGES ---------------
tab_dashboard, tab_students, tab_subjects, tab_scores, tab_analytics = st.tabs(
    ["🏠 Dashboard", "👩‍🎓 Students", "📚 Subjects", "📝 Scores", "📊 Analytics"]
)

# ---------- DASHBOARD ----------
with tab_dashboard:
    st.subheader("Overview")

    students_df = get_students_df()
    subjects_df = get_subjects_df()

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    total_students = 0 if students_df is None or students_df.empty else len(students_df)
    total_subjects = 0 if subjects_df is None or subjects_df.empty else len(subjects_df)

    with c1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Students", total_students)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Subjects", total_subjects)
        st.markdown("</div>", unsafe_allow_html=True)

    # Top N students (API: /scores/top/{n})
    st.markdown("### 🏆 Top Students")
    col_top = st.columns([1, 3])
    with col_top[0]:
        top_n = st.number_input("How many?", min_value=1, max_value=50, value=5, step=1)
        if st.button("Fetch Top Students", type="primary", use_container_width=True):
            top_raw = api_get(f"/scores/top/{int(top_n)}") or []
            # Enrich with student names if possible
            if students_df is not None and not students_df.empty:
                id_to_name = dict(zip(students_df["student_id"], students_df["student_name"]))
                for row in top_raw:
                    row["student_name"] = id_to_name.get(row.get("student_id"), "Unknown")
            top_df = pd.DataFrame(top_raw)
            if not top_df.empty and "average_score" in top_df.columns:
                top_df["average_score"] = pd.to_numeric(top_df["average_score"], errors="coerce").round(2)
            show_df(top_df, caption="Ordered by average score (descending).")
            download_df_button(top_df, "top_students.csv")
    with col_top[1]:
        st.info("Use this section to quickly see top performers across the database.")

# ---------- STUDENTS ----------
with tab_students:
    st.subheader("Manage Students")

    with st.expander("➕ Add Student", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            student_name = st.text_input("Full Name *")
            class_name = st.text_input("Class (e.g., JSS1, SS2) *")
        with c2:
            gender = st.selectbox("Gender *", options=["M", "F"])
            date_of_birth = st.text_input("Date of Birth (YYYY-MM-DD) *")

        if st.button("Create Student", type="primary"):
            if not student_name or not class_name or not gender or not date_of_birth:
                st.warning("Please fill all required fields.")
            else:
                payload = {
                    "student_name": student_name.strip(),
                    "class_name": class_name.strip(),
                    "gender": gender,
                    "date_of_birth": date_of_birth.strip(),
                }
                res = api_post("/students", payload)
                if res:
                    st.success(f"✅ {res.get('message')} (ID: {res.get('student_id')})")
                    st.cache_data.clear()

    st.markdown("### All Students")
    students_df = get_students_df()
    show_df(students_df)
    download_df_button(students_df, "students.csv")

# ---------- SUBJECTS ----------
with tab_subjects:
    st.subheader("Manage Subjects")

    with st.expander("➕ Add Subject", expanded=True):
        subject_name = st.text_input("Subject Name *")
        if st.button("Create Subject", type="primary"):
            if not subject_name:
                st.warning("Please provide a subject name.")
            else:
                res = api_post("/subjects", {"subject_name": subject_name.strip()})
                if res:
                    st.success(f"✅ {res.get('message')} (ID: {res.get('subject_id')})")
                    st.cache_data.clear()

    st.markdown("### All Subjects")
    subjects_df = get_subjects_df()
    show_df(subjects_df)
    download_df_button(subjects_df, "subjects.csv")

# ---------- SCORES ----------
with tab_scores:
    st.subheader("Manage Scores")

    students_df = get_students_df()
    subjects_df = get_subjects_df()

    with st.expander("➕ Add Score", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            sid = None
            if students_df is not None and not students_df.empty:
                sid = st.selectbox(
                    "Student *",
                    options=students_df["student_id"],
                    format_func=lambda i: f"{int(i)} — {students_df.loc[students_df['student_id']==i, 'student_name'].values[0]}",
                )
            term = st.text_input("Term *", value="FirstTerm")
            session_year = st.text_input("Session Year *", value="2024/2025")
        with col2:
            subid = None
            if subjects_df is not None and not subjects_df.empty:
                subid = st.selectbox(
                    "Subject *",
                    options=subjects_df["subject_id"],
                    format_func=lambda i: f"{int(i)} — {subjects_df.loc[subjects_df['subject_id']==i, 'subject_name'].values[0]}",
                )
            score_val = st.number_input("Score (0–100) *", min_value=0.0, max_value=100.0, step=0.5)

        if st.button("Submit Score", type="primary"):
            if sid is None or subid is None or not term or not session_year:
                st.warning("Please complete all fields.")
            else:
                payload = {
                    "student_id": int(sid),
                    "subject_id": int(subid),
                    "term": term.strip(),
                    "session_year": session_year.strip(),
                    "score": float(score_val),
                }
                res = api_post("/scores", payload)
                if res:
                    st.success(f"✅ {res.get('message')} (ID: {res.get('score_id')})")

    st.markdown("### Lookup Scores by Student")
    if students_df is not None and not students_df.empty:
        pick_sid = st.selectbox(
            "Select Student",
            options=students_df["student_id"],
            format_func=lambda i: f"{int(i)} — {students_df.loc[students_df['student_id']==i, 'student_name'].values[0]}",
        )
        if st.button("Fetch Student Scores"):
            scores = api_get(f"/scores/student/{int(pick_sid)}") or []
            s_df = pd.DataFrame(scores)
            if not s_df.empty:
                # map subject names if available
                if subjects_df is not None and not subjects_df.empty:
                    sub_map = dict(zip(subjects_df["subject_id"], subjects_df["subject_name"]))
                    s_df["subject_name"] = s_df.get("subject_id", pd.Series(dtype=int)).map(sub_map)
            show_df(s_df)
            download_df_button(s_df, "student_scores.csv")

# ---------- ANALYTICS ----------
with tab_analytics:
    st.subheader("Analytics & Reports")

    students_df = get_students_df()

    left, right = st.columns(2)
    # --- Class Stats (avg/min/max) per subject & term ---
    with left:
        st.markdown("#### 📈 Class Stats (per Subject & Term)")
        # Build class options from students
        class_options = sorted(students_df["class_name"].unique()) if students_df is not None and not students_df.empty else []
        selected_class = st.selectbox("Class", options=class_options if class_options else ["JSS1"], index=0)
        selected_term = st.text_input("Term", value="FirstTerm")
        if st.button("Compute Class Stats", type="primary"):
            stats = api_get(f"/scores/stats/class/{selected_class}")
            # Your endpoint /scores/stats/class/{class_name} doesn’t take term in params.
            # If you use the analytics endpoint that includes term, change to:
            # stats = api_get(f"/analytics/class-stats/{selected_class}/{selected_term}")
            if stats is None:
                st.stop()
            # Normalize to DataFrame
            if isinstance(stats, dict) and "average_score" in stats:
                # Simple avg/min/max result
                df_stats = pd.DataFrame([stats])
            else:
                df_stats = pd.DataFrame(stats)
            show_df(df_stats)
            download_df_button(df_stats, "class_stats.csv")

    # --- Student Ranking for a Term ---
    with right:
        st.markdown("#### 🏅 Student Ranking (by Term)")
        term_rank = st.text_input("Term", value="FirstTerm", key="rankTerm")
        if st.button("Rank Students", type="primary"):
            ranks = api_get(f"/analytics/student-rank/{term_rank}") or []
            r_df = pd.DataFrame(ranks)
            if not r_df.empty:
                r_df.rename(columns={"score": "average_score"}, inplace=True)
                r_df["average_score"] = pd.to_numeric(r_df["average_score"], errors="coerce").round(2)
                r_df["rank"] = pd.to_numeric(r_df["rank"], errors="coerce").astype("Int64")
            show_df(r_df, caption="Dense ranking (ties share same rank; next rank increments by 1).")
            download_df_button(r_df, "student_ranking.csv")

    st.divider()

    # Optional: pretty charts if data available
    st.markdown("#### 📊 Quick Charts")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.caption("Average Scores by Student (from Top-N)")
        # Reuse the last fetched top_n if available by requesting again (cached on server side if you add it)
        top_df = pd.DataFrame(api_get("/scores/top/5") or [])
        if not top_df.empty:
            # Enrich with names
            if students_df is not None and not students_df.empty:
                id_to_name = dict(zip(students_df["student_id"], students_df["student_name"]))
                top_df["student_name"] = top_df["student_id"].map(id_to_name)
            st.bar_chart(top_df.set_index("student_name")["average_score"])
    with chart_col2:
        st.caption("Class Distribution")
        if students_df is not None and not students_df.empty:
            counts = students_df["class_name"].value_counts().rename_axis("class").reset_index(name="count")
            counts = counts.set_index("class")
            st.bar_chart(counts["count"])