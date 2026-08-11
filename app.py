from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import json
import markdown
import time
from datetime import datetime
from anthropic import Anthropic
from google import genai
from google.genai import types
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

load_dotenv(override=True)
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
app = Flask(__name__)
app.secret_key = "mysecretkey123"
ADMIN_EMAIL = "nishthas615@gmail.com" 


def init_db():
    os.makedirs("resumes", exist_ok=True)
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT,
        degree TEXT,
        college TEXT,
        year TEXT,
        resume TEXT
    )
""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        candidate_name TEXT,
        company TEXT,
        role TEXT,
        round_type TEXT,
        score INTEGER,
        overview TEXT,
        strengths TEXT,
        weak_points TEXT,
        suggestions TEXT,
        date TEXT
    )
""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rating INTEGER,
        comments TEXT,
        date TEXT
    )
""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
""")
    conn.commit()
    conn.close()


init_db()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
@login_required
def home():
    return render_template("index.html")


@app.route("/interview")
@login_required
def interview():
    questions = session.get("questions")
    current_index = session.get("current_index")
    round_type = session.get("round_type")
    current_question = questions[current_index]
    total_questions = len(questions)
    elapsed = time.time() - session.get("start_time")
    if round_type == "technical":
        total_duration = 3600  # 60 minutes
    else:
        total_duration = 1200  # 20 minutes
    time_remaining = total_duration - elapsed
    if time_remaining < 0:
        time_remaining = 0
    return render_template(
        "interview.html",
        question=current_question,
        current_number=current_index + 1,
        total=total_questions,
        round_type=round_type,
        time_remaining=int(time_remaining),
    )


@app.route("/next", methods=["GET", "POST"])
@login_required
def next_question():
    if request.method == "POST":
        answer = request.form.get("answer", "")
        answers_list = session.get("answers")
        answers_list.append(answer)
        round_type = session.get("round_type")
        questions = session.get("questions")
        MAX_QUESTIONS = 5
        if (
            round_type in ["hr", "managerial"]
            and answer.strip() != ""
            and len(questions) < MAX_QUESTIONS
        ):
            followup_response = gemini_client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=f"The candidate answered: {answer}\n\nBased on this answer, generate exactly 1 relevant follow-up interview question. Return ONLY the question text, nothing else.",
                config=types.GenerateContentConfig(
                    system_instruction=f"You are a professional interviewer conducting a {round_type} round."
                ),
            )
            followup_question = followup_response.text.strip()
            questions.append(followup_question)
            session["questions"] = questions

    session["current_index"] += 1
    questions = session.get("questions")
    if session["current_index"] >= len(questions):
        answers = session.get("answers")
        feedback_data = generate_overall_feedback(questions, answers)
        return render_template(
            "feedback.html",
            status="Interview Complete! 🎉",
            score=feedback_data["score"],
            strengths=feedback_data["strengths"],
            weak_points=feedback_data["weak_points"],
            suggestions=feedback_data["suggestions"],
            summary=feedback_data["summary"],
            candidate_name=session.get("candidate_name"),
            company=session.get("company"),
            role=session.get("role"),
            round_type=session.get("round_type"),
        )

    return redirect("/interview")


@app.route("/previous")
@login_required
def previous_question():
    if session["current_index"] > 0:
        session["current_index"] -= 1
    return redirect("/interview")


@app.route("/timeup")
@login_required
def timeup():
    questions = session.get("questions")
    answers = session.get("answers")
    feedback_data = generate_overall_feedback(questions, answers)
    return render_template(
        "feedback.html",
        status="Time's Up! ⏰",
        score=feedback_data["score"],
        strengths=feedback_data["strengths"],
        weak_points=feedback_data["weak_points"],
        suggestions=feedback_data["suggestions"],
        summary=feedback_data["summary"],
        candidate_name=session.get("candidate_name"),
        company=session.get("company"),
        role=session.get("role"),
        round_type=session.get("round_type"),
    )


@app.route("/company")
@login_required
def company():
    return render_template("company.html")


@app.route("/select/<company>")
@login_required
def select_company(company):
    return render_template("role.html", company=company)


@app.route("/start", methods=["POST"])
@login_required
def start():
    company = request.form["company"]
    role = request.form["role"]
    difficulty = request.form["difficulty"]

    return render_template(
        "round.html", company=company, role=role, difficulty=difficulty
    )


def generate_overall_feedback(questions, answers):
    if session.get("feedback_cache"):
        return session.get("feedback_cache")
    qa_pairs = ""
    for i in range(len(answers)):
        qa_pairs = qa_pairs + f"Q{i+1}: {questions[i]}\nA{i+1}: {answers[i]}\n\n"
    feedback_response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=f'Here is a partial or full interview transcript:\n\n{qa_pairs}\n\nAnalyze the candidate\'s performance in detail. Even if the candidate performed well overall, always find at least 2 genuine areas for improvement, no matter how minor. Also give a realistic overall performance score out of 100, based on how a real interviewer would score this — IMPORTANT: heavily penalize the score if many questions were left unanswered or skipped, since incomplete answers are a major red flag in a real interview, regardless of how good the answered questions were. Also give 2-3 practical, actionable suggestions the candidate can practice before their next interview, based on their specific weak points. Do not include any external links or URLs. Return ONLY a JSON object in this exact format, nothing else: {{"score": 75, "strengths": ["a detailed 1-2 sentence point with specific examples from their answers", "another detailed point"], "weak_points": ["a detailed 1-2 sentence point with specific, actionable advice", "another detailed point"], "suggestions": ["a specific practice tip or exercise", "another practical suggestion"], "summary": "a 2-3 sentence overall summary"}}',
        config=types.GenerateContentConfig(
            system_instruction="You are a supportive but honest interview coach reviewing a candidate's mock interview."
        ),
    )
    feedback_data = json.loads(feedback_response.text)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO interview_history (user_id, candidate_name, company, role, round_type, score, overview, strengths, weak_points, suggestions, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            session.get("user_id"),
            session.get("candidate_name"),
            session.get("company"),
            session.get("role"),
            session.get("round_type"),
            feedback_data["score"],
            feedback_data["summary"],
            json.dumps(feedback_data["strengths"]),
            json.dumps(feedback_data["weak_points"]),
            json.dumps(feedback_data["suggestions"]),
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ),
    )
    conn.commit()
    conn.close()

    session["feedback_cache"] = feedback_data
    return feedback_data


@app.route("/begin", methods=["POST"])
@login_required
def begin():
    company = request.form["company"]
    role = request.form["role"]
    difficulty = request.form["difficulty"]
    round_type = request.form["round"]
    if round_type == "technical":
        tone = "challenging and detail-oriented, focusing on problem-solving skills"
    elif round_type == "hr":
        tone = "friendly and conversational, focusing on personality and cultural fit"
    else:
        tone = "focused on leadership, decision-making, and past experience"
    num_questions = 2 if round_type == "technical" else 3
    response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=f'Generate exactly {num_questions} interview questions for a {difficulty} {role} candidate in the {round_type} round. Return ONLY a JSON object in this exact format, nothing else: {{"questions": ["question 1", ...]}}',
        config=types.GenerateContentConfig(
            system_instruction=f"You are a professional interviewer conducting interviews for {company}. Be {tone}."
        ),
    )
    data = json.loads(response.text)
    questions = data["questions"]
    session["questions"] = questions
    session["answers"] = []
    session["current_index"] = 0
    session["round_type"] = round_type
    session["company"] = company
    session["role"] = role
    session["start_time"] = time.time()
    session["feedback_cache"] = None
    return redirect("/interview")


@app.route("/profile")
@login_required
def profile():
    return redirect("/")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        password_hash = generate_password_hash(password)

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("signup.html", error="Email already registered!")
        conn.close()

        return redirect("/login")

    return render_template("signup.html", error=None)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["user_email"] = email
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid email or password!")

    return render_template("login.html", error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/feedback")
@login_required
def feedback():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT rating, comments, date FROM app_feedback ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return render_template("feedback_list.html", feedbacks=rows)


@app.route("/feedback/give", methods=["GET", "POST"])
@login_required
def give_feedback():
    if request.method == "POST":
        rating = request.form["rating"]
        comments = request.form.get("comments", "")
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO app_feedback (rating, comments, date) VALUES (?, ?, ?)",
            (rating, comments, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()
        conn.close()
        return render_template("app_feedback.html", submitted=True)

    return render_template("app_feedback.html", submitted=False)


@app.route("/save", methods=["POST"])
@login_required
def save_profile():
    name = request.form["name"]
    degree = request.form["degree"]
    college = request.form["college"]
    year = request.form["year"]
    resume = request.files["resume"]
    resume_path = os.path.join("resumes", resume.filename)
    resume.save(resume_path)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO profile (user_id, name, degree, college, year, resume) VALUES (?, ?, ?, ?, ?, ?)",
        (session.get("user_id"), name, degree, college, year, resume_path),
    )
    conn.commit()
    conn.close()
    session["candidate_name"] = name

    return redirect("/company")


@app.route("/history")
@login_required
def history():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, date, company, role, round_type, score FROM interview_history WHERE user_id = ? ORDER BY id DESC",
        (session.get("user_id"),),
    )
    rows = cursor.fetchall()
    conn.close()

    return render_template("history.html", interviews=rows)


@app.route("/history/<interview_id>")
@login_required
def history_detail(interview_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM interview_history WHERE id = ? AND user_id = ?",
        (interview_id, session.get("user_id")),
    )
    row = cursor.fetchone()
    if row is None:
        return "Interview not found or access denied.", 404
    conn.close()

    strengths = json.loads(row[7])
    weak_points = json.loads(row[8])
    suggestions = json.loads(row[9])

    return render_template(
        "feedback.html",
        status="Past Interview Report",
        score=row[5],
        strengths=strengths,
        weak_points=weak_points,
        suggestions=suggestions,
        summary=row[6],
        candidate_name=row[1],
        company=row[2],
        role=row[3],
        round_type=row[4],
    )


@app.route("/progress")
@login_required
def progress():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, score FROM interview_history WHERE user_id = ? ORDER BY id ASC",
        (session.get("user_id"),),
    )
    rows = cursor.fetchall()
    conn.close()

    scores = [row[1] for row in rows]
    dates = [row[0] for row in rows]
    total_interviews = len(scores)

    if total_interviews > 0:
        average_score = round(sum(scores) / total_interviews)
        best_score = max(scores)
    else:
        average_score = 0
        best_score = 0

    return render_template(
        "progress.html",
        total_interviews=total_interviews,
        average_score=average_score,
        best_score=best_score,
        dates=dates,
        scores=scores,
    )
    


@app.route("/admin")
@login_required
def admin():
    if session.get("user_email") != ADMIN_EMAIL:
        return "Access Denied — Admins only.", 403

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, degree, college, year, resume FROM profile ORDER BY id DESC"
    )
    profiles = cursor.fetchall()
    conn.close()

    return render_template("admin.html", profiles=profiles)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
