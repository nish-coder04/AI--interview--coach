from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import json
import markdown
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


@app.route("/next", methods=["GET", "POST"])
def next_question():
    if request.method == "POST":
        answer = request.form.get("answer", "")
        answers_list = session.get("answers")
        answers_list.append(answer)
        session["answers"] = answers_list
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
        )

    return redirect("/interview")


@app.route("/previous")
def previous_question():
    if session["current_index"] > 0:
        session["current_index"] -= 1
    return redirect("/interview")


@app.route("/timeup")
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
    )


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


def generate_overall_feedback(questions, answers):
    if session.get("feedback_cache"):
        return session.get("feedback_cache")
    qa_pairs = ""
    for i in range(len(answers)):
        qa_pairs = qa_pairs + f"Q{i+1}: {questions[i]}\nA{i+1}: {answers[i]}\n\n"
    feedback_response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=f'Here is a partial or full interview transcript:\n\n{qa_pairs}\n\nAnalyze the candidate\'s performance in detail. Even if the candidate performed well overall, always find at least 2 genuine areas for improvement, no matter how minor. Also give a realistic overall performance score out of 100, based on how a real interviewer would score this. Also give 2-3 practical, actionable suggestions the candidate can practice before their next interview, based on their specific weak points. Do not include any external links or URLs. Return ONLY a JSON object in this exact format, nothing else: {{"score": 75, "strengths": ["a detailed 1-2 sentence point with specific examples from their answers", "another detailed point"], "weak_points": ["a detailed 1-2 sentence point with specific, actionable advice", "another detailed point"], "suggestions": ["a specific practice tip or exercise", "another practical suggestion"], "summary": "a 2-3 sentence overall summary"}}',
        config=types.GenerateContentConfig(
            system_instruction="You are a supportive but honest interview coach reviewing a candidate's mock interview."
        ),
    )
    feedback_data = json.loads(feedback_response.text)
    print("DEBUG weak_points:", feedback_data.get("weak_points"))
    session["feedback_cache"] = feedback_data
    return feedback_data


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
        model="gemini-3.1-flash-lite",
        contents=f'Generate exactly 3 interview questions for a {difficulty} {role} candidate in the {round_type} round. Return ONLY a JSON object in this exact format, nothing else: {{"questions": ["question 1", "question 2", "question 3"]}}',
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
    session["start_time"] = time.time()
    session["feedback_cache"] = None
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
