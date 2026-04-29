"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job processing status"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


# Request Models
class YouTubeProcessRequest(BaseModel):
    """Request to process a YouTube video"""
    url: HttpUrl
    clip_duration_min: int = Field(default=15, ge=10, le=30)
    clip_duration_max: int = Field(default=60, ge=30, le=120)
    top_clips: int = Field(default=10, ge=1, le=20)
    add_captions: bool = True
    add_music: bool = False
    search_query: Optional[str] = None  # Bonus: prompt-based search


class UploadResponse(BaseModel):
    """Response after file upload"""
    job_id: str
    filename: str
    file_size: int
    status: str
    message: str


class ProcessRequest(BaseModel):
    """Generic process request"""
    source_type: str  # youtube, upload
    source_url: Optional[str] = None
    file_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


# Response Models
class TranscriptSegment(BaseModel):
    """Transcript segment with timing"""
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    confidence: float = 1.0


class ViralityAnalysis(BaseModel):
    """LLM virality analysis result"""
    start: float
    end: float
    score: float = Field(ge=0, le=100)
    reason: str
    hook: str
    suggested_title: str
    hashtags: List[str]
    emotional_peaks: List[str] = []
    quotable_lines: List[str] = []


class MultiModalScore(BaseModel):
    """Combined multi-modal score"""
    llm_score: float
    audio_score: float
    visual_score: float
    final_score: float
    weights: Dict[str, float]


class ClipMetadata(BaseModel):
    """Metadata for generated clip"""
    clip_id: str
    title: str
    description: str
    hashtags: List[str]
    start_time: float
    end_time: float
    duration: float
    original_timestamp: str
    virality_score: float
    thumbnail_path: Optional[str] = None


class GeneratedClip(BaseModel):
    """Generated clip information"""
    clip_id: str
    file_path: str
    file_url: str
    file_size: int
    duration: float
    resolution: str
    metadata: ClipMetadata
    created_at: datetime


class JobResponse(BaseModel):
    """Job status and results"""
    job_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    message: Optional[str] = None
    error: Optional[str] = None
    input_source: str
    clips: List[GeneratedClip] = []
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class SearchResult(BaseModel):
    """Search result for prompt-based clip search"""
    clip_id: str
    relevance_score: float
    matched_text: str
    timestamp: str
    preview_url: Optional[str] = None


class SearchRequest(BaseModel):
    """Search request with prompt"""
    query: str
    job_id: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    services: Dict[str, bool]


# Database Models (for Prisma/SQLAlchemy)
class VideoSource(BaseModel):
    """Video source information"""
    id: str
    type: str  # youtube, upload
    url: Optional[str]
    filename: Optional[str]
    file_path: Optional[str]
    duration: float
    resolution: str
    file_size: int
    created_at: datetime


class ProcessingJob(BaseModel):
    """Processing job record"""
    id: str
    user_id: Optional[str]
    source_id: str
    status: JobStatus
    progress: int
    options: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
