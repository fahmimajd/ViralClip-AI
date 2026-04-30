# ViralClip AI Backend - Refactored Architecture

## Struktur Direktori Baru

```
backend/app/
├── api/                    # API Routes dan endpoints
│   ├── __init__.py
│   └── routes.py          # FastAPI router definitions
│
├── core/                   # Konfigurasi inti
│   ├── __init__.py
│   └── config.py          # Settings dan environment variables
│
├── models/                 # Data models dan schemas
│   ├── __init__.py
│   ├── database.py        # Database connection & models
│   └── schemas.py         # Pydantic models untuk request/response
│
├── services/               # Business logic services
│   ├── __init__.py
│   ├── analyzers/         # Modular analyzers (NEW)
│   │   ├── __init__.py
│   │   └── base.py        # Base analyzer interface
│   ├── renderers/         # Modular renderers (NEW)
│   │   └── __init__.py
│   ├── pipeline.py        # Main orchestration pipeline
│   ├── llm_analysis.py    # LLM virality analysis
│   ├── scoring.py         # Multi-modal scoring system
│   ├── semantic_search.py # Semantic search with embeddings
│   ├── transcription.py   # Whisper transcription service
│   ├── video_processing.py # Video processing & captioning
│   └── clip_selection.py  # Clip selection logic
│
├── utils/                  # Utility functions (NEW)
│   ├── __init__.py
│   └── helpers.py         # Common helper functions
│
├── celery.py              # Celery worker configuration
└── main.py                # FastAPI application entry point
```

## Fitur yang Direfactor

### 1. **Modular Analyzer System** (`services/analyzers/`)
- Interface base class untuk semua analyzer
- Memudahkan penambahan analyzer baru untuk tipe konten berbeda
- Support untuk:
  - General content analyzer
  - Podcast analyzer  
  - Interview analyzer
  - Monologue analyzer

### 2. **Utility Functions** (`utils/helpers.py`)
Fungsi-fungsi umum yang digunakan di seluruh aplikasi:
- `sanitize_filename()` - Sanitasi nama file
- `format_duration()` - Format durasi human-readable
- `extract_hashtags()` - Ekstrak hashtag dari teks
- `truncate_text()` - Truncate text dengan suffix
- `calculate_reading_speed()` - Hitung kecepatan baca (WPM)
- `is_optimal_reading_speed()` - Cek optimalitas WPM untuk caption

### 3. **Enhanced LLM Analysis** (`services/llm_analysis.py`)
- Parallel batch processing dengan semaphore
- Mode-specific prompts (general, podcast, interview)
- Advanced viral scoring dengan 6 kriteria
- Fallback heuristic analysis

### 4. **Multi-Modal Scoring** (`services/scoring.py`)
Weighted scoring system:
- LLM analysis: 50%
- Audio features: 15%
- Visual features: 15%
- Viral components: 20%
  - Hook strength
  - Emotional diversity
  - Question engagement
  - Call-to-action presence
  - Controversy potential

### 5. **Semantic Search** (`services/semantic_search.py`)
- Sentence embeddings untuk pencarian natural language
- Cache embeddings untuk performa
- Fallback ke keyword search
- Mirip dengan fitur Clip-Anything

### 6. **Enhanced Video Processing** (`services/video_processing.py`)
- YouTube transcript extraction (prioritized over Whisper)
- ASS subtitle generation dengan:
  - Word-by-word animation
  - Keyword highlighting (numbers, emotions, actions)
  - Fade in/out effects
- Smart vertical cropping (9:16)

### 7. **Configuration Updates** (`core/config.py`)
New settings:
- `EMBEDDING_MODEL` - Model untuk semantic search
- `PROCESSING_MODE` - general/podcast/interview/monologue
- `MAX_CONCURRENT_LLM_TASKS` - Control parallelism
- `YOUTUBE_TRANSCRIPT_LANGS` - Prioritas bahasa transcript

## Cara Menggunakan

### Menjalankan Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables
```bash
# LLM Providers
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
LLM_PROVIDER=groq

# Processing
PROCESSING_MODE=general  # atau: podcast, interview, monologue
MAX_CONCURRENT_LLM_TASKS=5

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# YouTube
YOUTUBE_TRANSCRIPT_LANGS=id,en
YTDLP_COOKIES_FILE=/path/to/cookies.txt
```

### API Endpoints Utama

#### Process YouTube Video
```bash
POST /api/v1/process/youtube
{
  "url": "https://youtube.com/watch?v=...",
  "top_clips": 10,
  "add_captions": true,
  "search_query": "find emotional moments"  // Optional semantic search
}
```

#### Search Clips by Prompt
```bash
POST /api/v1/search
{
  "query": "controversial opinions",
  "job_id": "optional-job-id",
  "limit": 10
}
```

## Keunggulan Refactoring

1. **Separation of Concerns** - Setiap modul punya tanggung jawab jelas
2. **Extensibility** - Mudah menambah analyzer/renderer baru
3. **Reusability** - Utility functions dapat dipakai di mana saja
4. **Testability** - Modul terpisah memudahkan unit testing
5. **Performance** - Parallel processing dan caching
6. **Flexibility** - Mode-specific processing untuk berbagai tipe konten

## Next Steps

1. Tambahkan unit tests untuk setiap modul
2. Implementasi face detection untuk smart cropping
3. Tambahkan WebSocket untuk real-time progress updates
4. Integrasi database untuk persistent storage
5. Tambahkan authentication & user management
