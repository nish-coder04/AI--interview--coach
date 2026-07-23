# AI Interview Coach 🎯

An AI-powered mock interview app built with Python and Flask.

## Features (Week 1 - Complete)
- Profile setup with education details
- Resume upload (PDF/DOC/JPG)
- SQLite database integration
- Bottom navigation bar

## Features (Week 2 - Complete)
- Company selection screen — 6 companies with logos
- Role + Difficulty selection
- Round Selection screen (Technical/HR/Managerial)
- Responsive design fixes (mobile + desktop)

## Features (Week 3 - Complete)
- AI Interviewer Persona — round-specific tone (Technical/HR/Managerial)
- JSON-based question generation (3 questions per round)
- LeetCode-style Interview Chat UI — split-screen with code editor
- Overall round timer with Previous/Next navigation
- AI-generated follow-up questions (HR/Managerial rounds)
- Voice input for HR/Managerial rounds (Web Speech API)

## Features (Week 4 - Complete)
- AI-generated overall feedback report — structured JSON output from Gemini
- Overall performance score (0-100%) with realistic scoring, including penalty for incomplete answers
- Strengths and Weak Points sections with specific, detailed feedback
- Practical, actionable suggestions for improvement (no external links, AI-generated tips only)
- Personalized final report — candidate name, company, role, and round context
- "Try Another Interview" button for quick restart
- Feedback caching to avoid redundant API calls on refresh

## Tech Stack
- Python + Flask (Backend)
- HTML + CSS + JavaScript (Frontend)
- SQLite (Database)
- Google Gemini API (AI question generation + feedback)
- Markdown library (formatting AI responses)

## Coming Soon
- History + PDF Report (Week 5)
- Deployment (Week 6)

## How to Run
pip install flask
python app.py