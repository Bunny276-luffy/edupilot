# EduPilot 🎓

> **From Classroom to NAAC — Automated.**

EduPilot is a full-stack AI-powered academic agent designed for Indian engineering colleges. It uses **Gemini 1.5 Pro** to automate NAAC/NBA accreditation workflows for faculty and provides a **Socratic tutoring experience** for students.

---

## 🧩 Problem Statement

Indian engineering colleges spend hundreds of faculty hours manually:
- Classifying exam questions by Bloom's taxonomy
- Creating CO-PO attainment matrices for NBA accreditation
- Writing NAAC-formatted PDF reports every semester

Students, meanwhile, often memorise instead of understanding — because AI tools give them direct answers.

**EduPilot solves both problems** with one platform.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  EduPilot Architecture                  │
└─────────────────────────────────────────────────────────┘

  [Browser]
      │  React + Vite + Tailwind
      │
      ▼
  [Vercel CDN]  ─────────────────────────────────────────┐
      │                                                   │
      │ HTTP/REST                                         │
      ▼                                                   │
  [Cloud Run]                                             │
  FastAPI Backend                                         │
      │                                                   │
      ├── Gemini 1.5 Pro API ←── Bloom's / Socratic       │
      │                                                   │
      ├── MongoDB Atlas ←── questions, sessions, students │
      │   └── Vector Search Index (embeddings)            │
      │                                                   │
      ├── Elasticsearch ←── past papers full-text search  │
      │                                                   │
      ├── Arize Phoenix ←── Gemini call tracing           │
      │                                                   │
      └── ReportLab ←── CO-PO & NAAC PDF generation      │
                                                          │
  [Agent Layer]                                           │
  4 Tool Functions (classify_bloom, map_copo,             │
                    search_papers, socratic_tutor)        │
```

---

## ✨ Features

| Feature | Who | What |
|---|---|---|
| **Bloom's Analyzer** | Faculty | Classifies questions into 6 cognitive levels with NBA warning |
| **CO-PO Matrix** | Faculty | Auto-generates attainment matrix from MongoDB vector search |
| **NAAC Report** | Faculty | One-click PDF with AI executive summary |
| **Socratic Tutor** | Student | Gemini never gives answers; guides through questions |
| **Past Paper Search** | Student | Elasticsearch full-text search with highlights |
| **AI Tracing** | Admin | Arize Phoenix logs all Gemini calls |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + Tailwind CSS + Recharts |
| Backend | FastAPI (Python 3.11) |
| AI Engine | Gemini 1.5 Pro (Google) |
| Primary DB | MongoDB Atlas (+ Vector Search) |
| Search | Elasticsearch 8 (Elastic Cloud) |
| Tracing | Arize Phoenix |
| PDF | ReportLab |
| Deployment | Vercel (frontend) + Cloud Run (backend) |

---

## 🚀 Local Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- MongoDB Atlas account (free tier works)
- Google AI Studio API key (Gemini)

### 1. Clone and configure

```bash
git clone <repo-url>
cd edupilot
cp backend/.env.example backend/.env
# Fill in your API keys in backend/.env
```

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

> [!TIP]
> If using mock/in-memory fallback modes (e.g. without live MongoDB or Elastic Cloud), run the backend with a single worker process (default when using `--reload` or without the `--workers` flag) to ensure in-memory stores are shared consistently.

Backend will be available at http://localhost:8000
API docs at http://localhost:8000/docs

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:5173

### 4. (Optional) Docker Compose

```bash
docker-compose up --build
```

---

## ⚡ Quick Demo (No API Keys)

```bash
# Backend
cd backend
cp .env.example .env
# Ensure LLM_PROVIDER=mock is set (it is by default)
python seed_demo.py
uvicorn main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173** — everything works offline with zero API keys.

---

## ☁️ Deployment

### Backend → Google Cloud Run

```bash
cd backend
gcloud run deploy edupilot-backend \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars "LLM_PROVIDER=mock,MONGODB_URI=$MONGODB_URI,MONGODB_DB_NAME=edupilot"
```

### Frontend → Vercel

```bash
cd frontend
vercel --prod
# Set VITE_API_URL in Vercel project settings to your Cloud Run URL
```

---

## 🤝 Partner Integrations

| Service | Purpose | Fallback |
|---|---|---|
| **MongoDB Atlas** | Primary database + vector search | In-memory dict store |
| **Elastic Cloud** | Past paper search | Local keyword search |
| **Arize Phoenix** | LLM tracing | Local JSON file logs |

### MongoDB Atlas
- Stores questions, students, sessions, and courses
- Vector Search index (`embedding_index`) enables semantic CO mapping
- Free tier M0 cluster sufficient for development

### Elastic Cloud / Elasticsearch
- Indexes past question papers with `edu_analyzer` (stop-word aware)
- Full-text search with term highlighting
- Falls back to demo data when not configured

### Arize Phoenix
- Every Gemini call is recorded: prompt, response, latency, token count, model
- In-memory store always active; cloud push requires API keys
- View traces at `/faculty` → AI Traces tab

---

## 🏆 Datathon Judging Notes

✅ Runs 100% locally with `LLM_PROVIDER=mock`  
✅ No credit card / API key required for demo  
✅ In-memory fallback warns about single-worker uvicorn use  
✅ All endpoints tested and verified  
✅ Frontend tries backend first; transparent Gemini direct fallback  

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/faculty/upload-questions` | Upload + classify questions |
| `POST` | `/api/faculty/generate-copo` | Generate CO-PO matrix |
| `GET` | `/api/faculty/naac-report/{id}` | Download NAAC PDF |
| `GET` | `/api/faculty/copo-pdf/{id}` | Download CO-PO PDF |
| `POST` | `/api/student/register` | Register student |
| `POST` | `/api/student/chat` | Socratic tutor chat |
| `GET` | `/api/student/progress/{id}` | Student progress |
| `POST` | `/api/search/papers` | Search past papers |
| `GET` | `/api/admin/traces` | AI trace logs |
| `GET` | `/docs` | Swagger UI |

---

## 📸 Screenshots

![Home](_screenshots/home.png)
![Faculty Dashboard](_screenshots/faculty-dashboard.png)
![Student Chat](_screenshots/student-chat.png)

---

## 📝 MongoDB Schema

```json
// questions
{
  "_id": ObjectId,
  "course_id": "CS301",
  "question_text": "Explain quicksort.",
  "blooms_level": "Understand",
  "co_mapping": ["CO1", "CO2"],
  "po_mapping": ["PO1"],
  "embedding": [0.12, ...],
  "uploaded_by": "faculty_001",
  "created_at": ISODate
}

// students
{
  "_id": ObjectId,
  "name": "Ravi Kumar",
  "roll_number": "21CS001",
  "college": "VIT Chennai",
  "topics_progress": [
    { "topic": "Binary Trees", "level": "Getting It", "last_session": ISODate }
  ]
}

// sessions
{
  "_id": ObjectId,
  "student_id": ObjectId,
  "topic": "Normalization",
  "messages": [{ "role": "user", "content": "..." }],
  "understanding_level": "Mastered",
  "exchange_count": 5,
  "created_at": ISODate
}
```

---

## 📄 License

MIT License — Copyright 2024 EduPilot Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software.

