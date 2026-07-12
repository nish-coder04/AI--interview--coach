from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import json
import time
from anthropic import Anthropic
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(override=True)
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
app = Flask(__name__)
app.secret_key = "mysecretkey123"


def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            degree TEXT,
            college TEXT,
            year TEXT,
            resume TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/interview")
def interview():
    questions = session.get("questions")
    current_index = session.get("current_index")
    round_type = session.get("round_type")
    current_question = questions[current_index]
    total_questions = len(questions)
    elapsed = time.time() - session.get("start_time")
    total_duration = 120  # 2 minutes for testing
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


@app.route("/next")
def next_question():
    session["current_index"] += 1
    questions = session.get("questions")
    if session["current_index"] >= len(questions):
        return "<h2>Interview Complete! 🎉</h2><p>You have answered all questions.</p>"
    return redirect("/interview")


@app.route("/previous")
def previous_question():
    if session["current_index"] > 0:
        session["current_index"] -= 1
    return redirect("/interview")


@app.route("/timeup")
def timeup():
    return "<h2>Time's Up! ⏰</h2><p>Your interview round has ended.</p>"


@app.route("/company")
def company():
    return render_template("company.html")


@app.route("/select/<company>")
def select_company(company):
    return render_template("role.html", company=company)


@app.route("/start", methods=["POST"])
def start():
    company = request.form["company"]
    role = request.form["role"]
    difficulty = request.form["difficulty"]

    return render_template(
        "round.html", company=company, role=role, difficulty=difficulty
    )


@app.route("/begin", methods=["POST"])
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
    response = gemini_client.models.generate_content(
        model="gemini-3.5-flash",
        contents=f'Generate exactly 3 interview questions for a {difficulty} {role} candidate in the {round_type} round. Return ONLY a JSON object in this exact format, nothing else: {{"questions": ["question 1", "question 2", "question 3"]}}',
        config=types.GenerateContentConfig(
            system_instruction=f"You are a professional interviewer conducting interviews for {company}. Be {tone}."
        ),
    )
    data = json.loads(response.text)
    questions = data["questions"]
    session["questions"] = questions
    session["current_index"] = 0
    session["round_type"] = round_type
    session["start_time"] = time.time()
    return redirect("/interview")


@app.route("/save", methods=["POST"])
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
        "INSERT INTO profile (name, degree, college, year, resume) VALUES (?, ?, ?, ?, ?)",
        (name, degree, college, year, resume_path),
    )
    conn.commit()
    conn.close()

    return redirect("/company")


if __name__ == "__main__":
    app.run(debug=True)
