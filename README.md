# 🎓 Ruia Pulse — Student AI Companion

> An intelligent, proactive academic companion built with Streamlit and Google Gemini to help students manage exams, generate study plans, practice with targeted quizzes, and learn with an AI-powered tutor.

---

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B?logo=streamlit)
![Gemini AI](https://img.shields.io/badge/AI-Google%20Gemini-8E75C2?logo=googlegemini)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📖 Overview

**Ruia Pulse** is an all-in-one academic productivity platform tailored for students. Going beyond basic to-do lists, Ruia Pulse leverages the Google Gemini API to analyze student strengths and weaknesses, generate adaptive study schedules, construct personalized quizzes, and serve as an always-available subject tutor.

The application features a modern, clean, glassmorphic UI built in Streamlit with smooth animations, custom cards, and interactive visualizations.

---

## ✨ Features

### 📊 1. Centralized Dashboard
- **Interactive Overview:** Quick metrics on your current study streak, upcoming deadlines, and average quiz scores.
- **Urgent Deadlines:** Highlights impending exams prioritized by urgency and confidence score.
- **Weakness Tracker:** Automatically flags topics needing review based on quiz mistakes.
- **Quick Actions:** Instant one-click navigation across all platform tools.

### 📅 2. AI-Powered Study Planner
- **7-Day Dynamic Schedules:** Generates customized study calendars considering available daily study hours, exam timelines, and known weak areas.
- **Interactive Weekly Grid:** Visual weekly schedule displaying focus areas and daily action items.
- **Export & Archive:** Download generated study plans directly as Markdown files and browse past plans from your library.

### 📝 3. Exam Tracker & Revision Priority Engine
- **Confidence Tracking:** Log exams with subject, date, and personal confidence levels (1–10).
- **AI-Driven Priority Ordering:** Leverages LLM reasoning and heuristic fallbacks to suggest optimal revision schedules based on exam proximity and confidence.
- **Status Management:** Track upcoming and completed exams seamlessly.

### 🎯 4. Interactive Quiz Generator
- **Custom Topic Quizzes:** Generate multiple-choice question (MCQ) assessments on any subject or topic at an undergraduate level.
- **Instant Grading & Feedback:** Detailed breakdowns of correct answers, your answers, and missed topics.
- **Adaptive Memory:** Missed quiz topics automatically feed into the student memory to inform future study plans and tutoring sessions.

### 💬 5. Context-Aware AI Tutor
- **Personalized Help:** A dedicated conversational assistant that references your saved study plans, upcoming exams, and past quiz mistakes to provide targeted help.
- **Clean Chat Interface:** Chat history persistence with the ability to clear history on demand.

### 📈 6. Progress Analytics & History
- **Interactive Charts (Altair):** 
  - Bar charts of quiz score history.
  - Timeline tracking of score progression.
  - Exam confidence comparison across subjects.
  - Horizontal bar breakdown of frequent weak topics.
  - Activity breakdown donut chart.
- **Full Data Export:** Download all historical plans, exams, quizzes, and chat transcripts in a consolidated Markdown report.

---

## 🛠️ Architecture & Tech Stack

- **Frontend & App Framework:** [Streamlit](https://streamlit.io/) with custom HTML5/CSS3 glassmorphic design and animations.
- **Charts & Data Visualization:** [Altair](https://altair-viz.github.io/), [Pandas](https://pandas.pydata.org/).
- **AI & Language Models:** Google Gemini API (`gemini-2.5-flash` / `gemini-1.5-flash`), with multi-key rotation and rate-limiting resilience.
- **Database:** SQLite3 for lightweight, zero-configuration local persistence.
- **Testing:** Python `unittest` suite covering data access, AI fallbacks, and security utilities.

---

## 📁 Repository Structure

```
├── app.py                  # Main Streamlit web application & routing
├── ui_components.py        # UI design system, custom CSS, HTML components
├── ai_service.py           # Gemini API integration, prompt templates & key rotation
├── ai.py                   # Alternate/secondary AI client utilities
├── exam_scorer.py          # Heuristic and AI-based exam urgency scoring
├── db.py                   # SQLite storage (tasks, exams, quizzes, chat, context)
├── analytics.py            # Analytics and dashboard data aggregation
├── security.py             # Rate-limiting, input sanitization, safe filename utils
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment variable template
├── tests/                  # Test suites
│   └── test_core.py
├── test_ai.py              # Test suite for AI features
└── test_exam_scorer.py     # Test suite for exam scoring logic
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- [Google AI Studio API Key](https://aistudio.google.com/)

### 1. Clone the Repository
```bash
git clone https://github.com/RishabhDev676/student-AI-companion.git
cd student-AI-companion
```

### 2. Set Up a Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env.local` (or `.env`):
```bash
cp .env.example .env.local
```
Add your Google Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Optional) You can specify multiple keys (`API_KEY_1`, `API_KEY_2`, etc.) for round-robin rotation.*

### 5. Run the Application
```bash
streamlit run app.py
```
The app will open automatically in your default browser at `http://localhost:8501`.

---

## 🧪 Running Tests

Execute the unit test suite with:
```bash
python -m unittest discover -s .
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
