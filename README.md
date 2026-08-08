# 🎯 AI Interview Academy

An AI-powered mock interview platform that helps students and job-seekers practice real interview scenarios — company-specific questions, round-based practice (Technical / HR / Managerial), instant AI feedback, and progress tracking over time.

**🔗 Live Demo:** [web-production-2c2da0.up.railway.app](https://web-production-2c2da0.up.railway.app)

---

## ✨ Features

- **Profile Setup** — Save your name, degree, college, academic year, and resume before you begin.
- **35+ Companies to Choose From** — Organized into Product/Tech MNCs, Indian IT Services, Indian Startups/Unicorns, and Finance/Consulting, with a live search bar. Can't find your target company? Just type its name and start the interview anyway — the backend generates questions for *any* company.
- **Role & Difficulty Selection** — Choose your target role (SDE, Data Analyst, PM, ML Engineer) and experience level (Fresher / Experienced).
- **Three Interview Rounds:**
  - 💻 **Technical** — 2 in-depth questions, 60-minute session, LeetCode-style split-screen editor (Python/Java/C++/C/JavaScript).
  - 🗣️ **HR** — 3 conversational questions with AI-generated follow-ups based on your answers, 20-minute session, voice input supported.
  - 📊 **Managerial** — 3 leadership/decision-making focused questions with follow-ups, 20-minute session, voice input supported.
- **Real-Time Timer** — Server-side elapsed-time tracking that survives page reloads and question navigation.
- **AI-Generated Feedback Report** — After every interview:
  - Overall performance score (0–100%), realistically penalized for incomplete answers
  - Written overview/summary
  - Strengths
  - Areas to improve
  - Actionable suggestions for next time
- **Interview History** — Every completed interview is saved permanently. Browse past sessions and revisit any full feedback report.
- **Progress Tracking** — Total interviews, average score, best score, and a score-trend line graph (Chart.js) so you can see yourself improve over time.
- **App Feedback System** — Users can rate the app and leave comments; all feedback is visible on a public feedback wall.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Database | SQLite |
| AI | Google Gemini API (`gemini-3.1-flash-lite`) |
| Charts | Chart.js |
| Voice Input | Web Speech API |
| Deployment | Railway |

---

## 📸 Screenshots

### Profile Setup
![Profile](screenshots/profile.png)

### Company Selection
![Company Selection](screenshots/company.png)

### Live Interview
![Interview](screenshots/interview.png)

### AI Feedback Report
![Feedback Report](screenshots/feedback.png)

### Progress Tracking
![Progress](screenshots/progress.png)

---

## 🚀 Running Locally

1. **Clone the repo**
   ```bash
   git clone https://github.com/nish-coder04/AI--interview--coach.git
   cd AI--interview--coach
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Run the app**
   ```bash
   python app.py
   ```

   Visit `http://127.0.0.1:5000` in your browser.

---

## 📂 Project Structure

```
AI--interview--coach/
├── app.py                 # Flask app — all routes and logic
├── requirements.txt
├── Procfile                # Railway deployment config
├── templates/
│   ├── index.html          # Profile setup
│   ├── company.html        # Company selection + search
│   ├── role.html            # Role & difficulty selection
│   ├── round.html           # Round selection
│   ├── interview.html       # Live interview (question + answer panel)
│   ├── feedback.html        # AI feedback report
│   ├── history.html         # Past interview list
│   ├── feedback_list.html   # App feedback wall
│   ├── app_feedback.html    # App feedback submission form
│   └── progress.html        # Stats + score trend graph
├── resumes/                 # Uploaded resume files
└── database.db              # SQLite database
```

---

## 🗺️ Roadmap / Planned Enhancements

- [ ] Multi-resume support — save up to 4 resumes per user (for different roles/companies)
- [ ] Company-specific round structures (e.g. Amazon Bar Raiser + Leadership Principles, Google System Design + Googleyness)
- [ ] Real code execution for Technical round (via a sandboxed judge API)
- [ ] Video-call style UI for HR/Managerial rounds

---

## 👩‍💻 Author

**Nishtha Shukla**
B.Tech CSE, JECRC University, Jaipur

---

## 📄 License

See [LICENSE](LICENSE) for details.