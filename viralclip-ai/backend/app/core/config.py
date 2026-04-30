"""
Configuration settings for ViralClip AI Backend
"""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "ViralClip AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/viralclip"
    
    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./outputs"
    TEMP_DIR: str = "./temp"
    MAX_UPLOAD_SIZE: int = 2 * 1024 * 1024 * 1024  # 2GB
    
    # LLM Providers
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "groq"  # groq or openai
    LLM_MODEL: str = "llama3-70b-8192"  # Groq default
    
    # Embedding Model for Semantic Search
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Whisper Models
    WHISPER_MODEL: str = "large-v3"
    WHISPER_DEVICE: str = "auto"  # auto, cuda, cpu
    WHISPER_COMPUTE_TYPE: str = "float16"  # float16, int8, int8_float16
    WHISPER_CPU_THREADS: int = 12
    WHISPER_NUM_WORKERS: int = 1
    YOUTUBE_TRANSCRIPT_LANGS: str = "id,en"
    
    # Diarization
    PYANNOTE_TOKEN: Optional[str] = None
    YTDLP_COOKIES_FILE: Optional[str] = None
    
    # Processing Mode
    PROCESSING_MODE: str = "general"  # general, podcast, interview, monologue
    MAX_CONCURRENT_LLM_TASKS: int = 5  # For parallel LLM analysis
    
    # Video Processing
    VIDEO_CODEC: str = "libx264"
    AUDIO_CODEC: str = "aac"
    VIDEO_BITRATE: str = "2M"
    AUDIO_BITRATE: str = "128k"
    FPS: int = 30
    
    # Clip Settings
    CLIP_MIN_DURATION: float = 15.0
    CLIP_MAX_DURATION: float = 60.0
    CLIP_BUFFER: float = 0.5  # seconds before/after
    TOP_CLIPS: int = 10
    
    # Scoring Weights
    LLM_WEIGHT: float = 0.6
    AUDIO_WEIGHT: float = 0.2
    VISUAL_WEIGHT: float = 0.2
    
    # Caption Styling
    CAPTION_FONT: str = "Arial"
    CAPTION_FONT_SIZE: int = 48
    CAPTION_COLOR: str = "white"
    CAPTION_BG_COLOR: str = "black@0.7"
    CAPTION_POSITION: str = "bottom"  # bottom, center, top
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://yourdomain.com"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get global settings instance"""
    return settings
