# 🚀 ViralClip AI - Setup Guide

Complete step-by-step instructions to run ViralClip AI locally or with Docker.

---

## 📋 Prerequisites

### Required Software
- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **FFmpeg** - [Download](https://ffmpeg.org/download.html)
- **Git** - [Download](https://git-scm.com/)

### Optional (for GPU acceleration)
- **NVIDIA GPU** with CUDA support
- **NVIDIA Container Toolkit** (for Docker)

### API Keys (Required for full functionality)
- **Groq API Key** - Get free at [console.groq.com](https://console.groq.com)
- **Hugging Face Token** (for Pyannote diarization) - Get at [huggingface.co](https://huggingface.co/settings/tokens)

---

## 🐳 Option 1: Quick Start with Docker (Recommended)

### Step 1: Clone the Repository
```bash
cd viralclip-ai
```

### Step 2: Configure Environment Variables
```bash
cp docker/.env.example .env
```

Edit `.env` and add your API keys:
```bash
GROQ_API_KEY=gsk_your_key_here
PYANNOTE_TOKEN=hf_your_token_here
```

### Step 3: Start All Services
```bash
cd docker
docker-compose up --build
```

### Step 4: Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 💻 Option 2: Manual Setup (Development)

### Backend Setup

#### Step 1: Navigate to Backend Directory
```bash
cd backend
```

#### Step 2: Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Mac/Linux
source venv/bin/activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Configure Environment
```bash
cp ../docker/.env.example .env
```

Edit `.env` with your API keys.

#### Step 5: Initialize Database (Optional)
```bash
# If using PostgreSQL
createdb viralclip

# Or use SQLite for development (update DATABASE_URL in .env)
DATABASE_URL=sqlite:///./viralclip.db
```

#### Step 6: Run Backend Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

---

### Frontend Setup

#### Step 1: Navigate to Frontend Directory
```bash
cd frontend
```

#### Step 2: Install Dependencies
```bash
npm install
```

#### Step 3: Configure Environment
Create `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Step 4: Run Development Server
```bash
npm run dev
```

Frontend will be available at: http://localhost:3000

---

## 🔧 System Dependencies Installation

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y ffmpeg python3-dev build-essential
```

### macOS
```bash
brew install ffmpeg python
```

### Windows
```powershell
# Using Chocolatey
choco install ffmpeg python

# Or download from official websites
```

---

## 🧪 Testing the Application

### Test with a YouTube Video

1. Open http://localhost:3000
2. Enter a YouTube URL (e.g., a podcast or interview)
3. Click "Generate Clips"
4. Wait for processing (check progress in the UI)
5. Download your viral clips!

### Test with File Upload

1. Switch to "Upload Video" tab
2. Drag & drop or select a video file
3. Click "Upload & Process"
4. Wait for processing to complete

---

## 🎛️ Configuration Options

### Adjust Clip Settings
In `.env`, modify:
```bash
CLIP_MIN_DURATION=15      # Minimum clip length (seconds)
CLIP_MAX_DURATION=60      # Maximum clip length (seconds)
TOP_CLIPS=10              # Number of clips to generate
```

### Change Scoring Weights
```bash
LLM_WEIGHT=0.6            # LLM analysis importance
AUDIO_WEIGHT=0.2          # Audio features importance
VISUAL_WEIGHT=0.2         # Visual features importance
```

### Customize Captions
```bash
CAPTION_FONT_SIZE=48
CAPTION_COLOR=white
CAPTION_BG_COLOR=black@0.7
```

---

## 🐛 Troubleshooting

### Common Issues

**1. FFmpeg not found**
```bash
# Verify installation
ffmpeg -version

# Reinstall if needed
# Ubuntu/Debian: sudo apt install ffmpeg
# macOS: brew install ffmpeg
```

**2. Out of memory during transcription**
```bash
# Use smaller Whisper model in .env
WHISPER_MODEL=base  # or small, medium
```

**3. Groq API errors**
- Check your API key is correct
- Verify you have credits/quota remaining
- Check network connectivity

**4. Port already in use**
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in .env
PORT=8001
```

**5. Docker permission issues**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

---

## 📊 Performance Tips

### For Faster Processing

1. **Use GPU for Whisper**
   ```bash
   WHISPER_DEVICE=cuda
   WHISPER_COMPUTE_TYPE=float16
   ```

2. **Reduce clip count**
   ```bash
   TOP_CLIPS=5  # Generate fewer clips
   ```

3. **Use faster Whisper model**
   ```bash
   WHISPER_MODEL=small  # Instead of large-v3
   ```

### For Better Quality

1. **Use best models**
   ```bash
   WHISPER_MODEL=large-v3
   LLM_MODEL=llama3-70b-8192
   ```

2. **Enable diarization**
   ```bash
   PYANNOTE_TOKEN=your_token
   ```

3. **Increase clip duration range**
   ```bash
   CLIP_MIN_DURATION=30
   CLIP_MAX_DURATION=90
   ```

---

## 📱 API Usage Examples

### Process YouTube Video
```bash
curl -X POST http://localhost:8000/api/v1/process/youtube \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=VIDEO_ID",
    "top_clips": 10,
    "add_captions": true
  }'
```

### Check Job Status
```bash
curl http://localhost:8000/api/v1/jobs/JOB_ID
```

### Search Clips
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "money advice",
    "limit": 5
  }'
```

---

## 🎯 Next Steps

1. **Customize branding** - Update logo and colors in frontend
2. **Add authentication** - Implement user login/signup
3. **Deploy to production** - Use Railway, Render, or your VPS
4. **Integrate auto-upload** - Connect TikTok/YouTube APIs
5. **Add more AI features** - Emotion detection, B-roll suggestions

---

## 📞 Support

- **Documentation**: Check README.md in project root
- **API Docs**: http://localhost:8000/docs
- **Issues**: Report bugs via GitHub Issues

---

## 🎉 You're Ready!

Your ViralClip AI system is now running. Start creating viral content! 🚀

For production deployment guides, see `DEPLOYMENT.md`.
