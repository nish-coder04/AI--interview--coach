from flask import Flask, render_template, request, redirect
import sqlite3
import os
app = Flask(__name__)
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            degree TEXT,
            college TEXT,
            year TEXT,
            resume TEXT
        )
    ''')
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
    return f"Company: {company} | Role: {role} | Difficulty: {difficulty}"

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
    cursor.execute("INSERT INTO profile (name, degree, college, year, resume) VALUES (?, ?, ?, ?, ?)",
                   (name, degree, college, year, resume_path))
    conn.commit()
    conn.close()

    return redirect("/company")
if __name__ == "__main__":
    app.run(debug=True)