"""
Database models using SQLAlchemy
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum


Base = declarative_base()


class JobStatusEnum(enum.Enum):
    """Job status enumeration"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    ANALYZING = "analyzing"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoSource(Base):
    """Video source table"""
    __tablename__ = "video_sources"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)  # youtube, upload
    url = Column(String, nullable=True)
    filename = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    resolution = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = relationship("ProcessingJob", back_populates="source")


class ProcessingJob(Base):
    """Processing job table"""
    __tablename__ = "processing_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)
    source_id = Column(String, ForeignKey("video_sources.id"), nullable=False)
    status = Column(SQLEnum(JobStatusEnum), default=JobStatusEnum.PENDING)
    progress = Column(Integer, default=0)
    options = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    source = relationship("VideoSource", back_populates="jobs")
    clips = relationship("GeneratedClip", back_populates="job")


class GeneratedClip(Base):
    """Generated clip table"""
    __tablename__ = "generated_clips"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("processing_jobs.id"), nullable=False)
    file_path = Column(String, nullable=False)
    file_url = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    duration = Column(Float, nullable=False)
    resolution = Column(String, nullable=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    virality_score = Column(Float, nullable=False)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("ProcessingJob", back_populates="clips")


class TranscriptSegment(Base):
    """Transcript segment table"""
    __tablename__ = "transcript_segments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("processing_jobs.id"), nullable=False)
    start = Column(Float, nullable=False)
    end = Column(Float, nullable=False)
    text = Column(Text, nullable=False)
    speaker = Column(String, nullable=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
