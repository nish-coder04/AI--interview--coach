from flask import Flask, render_template, request, redirect
import sqlite3
import os
from anthropic import Anthropic
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(override=True)
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
app = Flask(__name__)


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
        contents=f"Generate 1 interview question for a {difficulty} {role} candidate in the {round_type} round. Just the question, nothing else.",
        config=types.GenerateContentConfig(
            system_instruction=f"You are a professional interviewer conducting interviews for {company}. Be {tone}."
        ),
    )
    question = response.text
    return (
        f"<h2>{round_type.capitalize()} Round — First Question:</h2><p>{question}</p>"
    )


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
