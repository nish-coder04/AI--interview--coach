from flask import Flask, render_template, request
import sqlite3
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
            year TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/save", methods=["POST"])
def save_profile():
    name = request.form["name"]
    degree = request.form["degree"]
    college = request.form["college"]
    year = request.form["year"]

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO profile (name, degree, college, year) VALUES (?, ?, ?, ?)",
                   (name, degree, college, year))
    conn.commit()
    conn.close()

    return "Profile saved!"
if __name__ == "__main__":
    app.run(debug=True)