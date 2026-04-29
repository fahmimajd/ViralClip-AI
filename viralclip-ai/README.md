# ViralClip AI - Production-Ready Architecture

## 📁 Project Structure

```
viralclip-ai/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # Config, security
│   │   ├── models/           # Pydantic & DB models
│   │   ├── services/         # Business logic
│   │   ├── utils/            # Helpers
│   │   └── main.py           # App entry point
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   ├── lib/              # Utilities
│   │   └── styles/           # Tailwind CSS
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── database/
│   ├── schema.prisma
│   └── migrations/
├── docker/
│   ├── docker-compose.yml
│   └── .env.example
├── scripts/
│   └── setup.sh
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- FFmpeg installed
- GPU recommended for Whisper (optional)

### Setup Steps

1. **Clone and navigate**
```bash
cd viralclip-ai
```

2. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
cd frontend
npm install
```

4. **Database Setup**
```bash
cd database
npx prisma generate
npx prisma migrate dev
```

5. **Environment Variables**
```bash
cp docker/.env.example .env
# Edit .env with your API keys
```

6. **Run with Docker**
```bash
docker-compose up --build
```

Or run services individually:
```bash
# Backend
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm run dev
```

## 📡 API Endpoints

- `POST /api/v1/upload` - Upload video file
- `POST /api/v1/process/youtube` - Process YouTube URL
- `GET /api/v1/clips/{job_id}` - Get processed clips
- `GET /api/v1/jobs` - List all jobs
- `POST /api/v1/search` - Search clips by prompt

## 🧠 Processing Pipeline

1. **Input** → YouTube URL or file upload
2. **Download** → yt-dlp extracts video/audio
3. **Transcribe** → Faster-Whisper + Pyannote diarization
4. **Segment** → Split into 30-60s semantic segments
5. **Analyze** → LLM virality scoring
6. **Score** → Multi-modal fusion (LLM + audio + visual)
7. **Select** → Top 5-15 non-overlapping clips
8. **Render** → FFmpeg vertical crop + captions
9. **Output** → MP4 clips + metadata JSON

## 🔑 Features

- ✅ YouTube URL & file upload support
- ✅ Speaker diarization
- ✅ LLM-powered virality analysis
- ✅ Multi-modal scoring (audio peaks, scene changes)
- ✅ Smart vertical cropping (face tracking)
- ✅ Animated TikTok-style captions
- ✅ Metadata generation (titles, hashtags)
- ✅ Prompt-based clip search
- ✅ Batch processing
- ✅ Async job queue (Celery/Redis)

## 🛠️ Tech Stack

**Backend:** Python 3.10, FastAPI, Celery, Redis
**AI:** Faster-Whisper, Pyannote, Groq/OpenAI LLM
**Video:** FFmpeg, MoviePy, OpenCV
**Frontend:** Next.js 14, Tailwind CSS, TypeScript
**Database:** PostgreSQL, Prisma ORM
**Deployment:** Docker, Docker Compose

## 📝 License

MIT License - See LICENSE file
