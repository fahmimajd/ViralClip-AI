"""
FastAPI Routes for ViralClip AI
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional, Dict, Any
import uuid
import asyncio
import shutil
import json
from pathlib import Path
from loguru import logger
from datetime import datetime, timezone

from app.core.config import settings
from app.models.schemas import (
    YouTubeProcessRequest,
    UploadResponse,
    JobResponse,
    JobStatus,
    SearchRequest,
    SearchResult,
    HealthResponse,
    GeneratedClip,
)
from app.services.pipeline import get_processing_pipeline
from app.services.clip_selection import get_selection_service

router = APIRouter(prefix=settings.API_PREFIX, tags=["main"])

# In-memory job storage (use database in production)
jobs_db: Dict[str, Dict[str, Any]] = {}


def utc_now() -> datetime:
    """Return timezone-aware UTC timestamps for API responses."""
    return datetime.now(timezone.utc)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "services": {
            "api": True,
            "database": True,  # Should check actual DB connection
            "redis": True  # Should check actual Redis connection
        }
    }


@router.post("/upload", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...), background_tasks: BackgroundTasks = None) -> UploadResponse:
    """
    Upload a video file for processing
    
    Accepts: mp4, mkv, mov, avi
    Max size: Configured in settings (default 2GB)
    """
    try:
        # Validate file type
        allowed_types = ["video/mp4", "video/x-matroska", "video/quicktime", "video/x-msvideo"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
            )
        
        # Generate job ID and save path
        job_id = str(uuid.uuid4())
        upload_dir = Path(settings.UPLOAD_DIR) / job_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / file.filename
        
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Store job info
        jobs_db[job_id] = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "progress": 0,
            "source_type": "upload",
            "file_path": str(file_path),
            "filename": file.filename,
            "file_size": len(content),
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "clips": [],
            "error": None
        }
        
        logger.info(f"Uploaded file: {file.filename} ({len(content)} bytes) - Job ID: {job_id}")
        
        return {
            "job_id": job_id,
            "filename": file.filename,
            "file_size": len(content),
            "status": "uploaded",
            "message": "File uploaded successfully. Call /process to start processing."
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/youtube", response_model=JobResponse)
async def process_youtube(
    request: YouTubeProcessRequest,
    background_tasks: BackgroundTasks = None
):
    """
    Process a YouTube video URL
    
    Downloads the video, transcribes, analyzes virality, and generates clips
    """
    try:
        job_id = str(uuid.uuid4())
        
        # Initialize job
        jobs_db[job_id] = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "progress": 0,
            "source_type": "youtube",
            "source_url": str(request.url),
            "options": {
                "clip_duration_min": request.clip_duration_min,
                "clip_duration_max": request.clip_duration_max,
                "top_clips": request.top_clips,
                "add_captions": request.add_captions,
                "add_music": request.add_music,
                "search_query": request.search_query
            },
            "created_at": utc_now(),
            "updated_at": utc_now(),
            "clips": [],
            "error": None
        }
        
        # Start processing in background
        async def progress_callback(progress: int, message: str):
            if job_id in jobs_db:
                jobs_db[job_id]["progress"] = progress
                jobs_db[job_id]["updated_at"] = utc_now()
                
                # Update status based on progress
                if progress == 0:
                    jobs_db[job_id]["status"] = JobStatus.FAILED
                elif progress < 25:
                    jobs_db[job_id]["status"] = JobStatus.DOWNLOADING
                elif progress < 50:
                    jobs_db[job_id]["status"] = JobStatus.TRANSCRIBING
                elif progress < 75:
                    jobs_db[job_id]["status"] = JobStatus.ANALYZING
                elif progress < 100:
                    jobs_db[job_id]["status"] = JobStatus.RENDERING
                else:
                    jobs_db[job_id]["status"] = JobStatus.COMPLETED
                    jobs_db[job_id]["completed_at"] = utc_now()
        
        async def process_task():
            pipeline = get_processing_pipeline()
            pipeline.register_progress_callback(job_id, progress_callback)
            
            result = await pipeline.process_youtube_video(
                url=str(request.url),
                job_id=job_id,
                options=jobs_db[job_id]["options"]
            )
            
            # Update job with results
            if job_id in jobs_db:
                if result["success"]:
                    jobs_db[job_id]["clips"] = result["clips"]
                    jobs_db[job_id]["metadata"] = result["metadata"]
                    jobs_db[job_id]["status"] = JobStatus.COMPLETED
                    jobs_db[job_id]["completed_at"] = utc_now()
                else:
                    jobs_db[job_id]["error"] = result["error"]
                    jobs_db[job_id]["status"] = JobStatus.FAILED
        
        # Run in background
        if background_tasks:
            background_tasks.add_task(process_task)
        else:
            asyncio.create_task(process_task)
        
        logger.info(f"YouTube processing started: {request.url} - Job ID: {job_id}")
        
        return _get_job_response(jobs_db[job_id])
        
    except Exception as e:
        logger.error(f"YouTube processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process/upload/{job_id}", response_model=JobResponse)
async def process_upload(
    job_id: str,
    top_clips: int = 10,
    add_captions: bool = True,
    background_tasks: BackgroundTasks = None
):
    """
    Process an uploaded video file
    
    Call this after uploading a file via /upload
    """
    try:
        if job_id not in jobs_db:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = jobs_db[job_id]
        
        if job["source_type"] != "upload":
            raise HTTPException(status_code=400, detail="Job is not an upload job")
        
        # Update job status
        job["status"] = JobStatus.PENDING
        job["progress"] = 0
        job["options"] = {
            "top_clips": top_clips,
            "add_captions": add_captions
        }
        job["updated_at"] = utc_now()
        
        # Start processing
        async def progress_callback(progress: int, message: str):
            if job_id in jobs_db:
                jobs_db[job_id]["progress"] = progress
                jobs_db[job_id]["updated_at"] = utc_now()
                
                if progress == 0:
                    jobs_db[job_id]["status"] = JobStatus.FAILED
                elif progress < 25:
                    jobs_db[job_id]["status"] = JobStatus.TRANSCRIBING
                elif progress < 50:
                    jobs_db[job_id]["status"] = JobStatus.ANALYZING
                elif progress < 75:
                    jobs_db[job_id]["status"] = JobStatus.RENDERING
                else:
                    jobs_db[job_id]["status"] = JobStatus.COMPLETED
                    jobs_db[job_id]["completed_at"] = utc_now()
        
        async def process_task():
            pipeline = get_processing_pipeline()
            pipeline.register_progress_callback(job_id, progress_callback)
            
            result = await pipeline.process_uploaded_file(
                file_path=job["file_path"],
                job_id=job_id,
                options=job["options"]
            )
            
            if job_id in jobs_db:
                if result["success"]:
                    jobs_db[job_id]["clips"] = result["clips"]
                    jobs_db[job_id]["metadata"] = result["metadata"]
                    jobs_db[job_id]["status"] = JobStatus.COMPLETED
                    jobs_db[job_id]["completed_at"] = utc_now()
                else:
                    jobs_db[job_id]["error"] = result["error"]
                    jobs_db[job_id]["status"] = JobStatus.FAILED
        
        if background_tasks:
            background_tasks.add_task(process_task)
        else:
            asyncio.create_task(process_task)
        
        logger.info(f"Upload processing started: {job['filename']} - Job ID: {job_id}")
        
        return _get_job_response(job)
        
    except Exception as e:
        logger.error(f"Upload processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[JobStatus] = None,
    limit: int = 20,
    offset: int = 0
):
    """List all processing jobs with optional filtering"""
    jobs = list(jobs_db.values())
    
    # Filter by status if provided
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    
    # Sort by created_at descending
    jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    # Paginate
    paginated = jobs[offset:offset + limit]
    
    return [_get_job_response(job) for job in paginated]


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get job status and results"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return _get_job_response(jobs_db[job_id])


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job and its associated files"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete output files
    output_dir = Path(settings.OUTPUT_DIR) / job_id
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    
    # Delete from database
    del jobs_db[job_id]
    
    return {"message": f"Job {job_id} deleted successfully"}


@router.post("/search", response_model=List[SearchResult])
async def search_clips(request: SearchRequest):
    """
    Search for clips by text query (Bonus feature)
    
    Searches through transcript segments to find relevant clips
    """
    try:
        selection = get_selection_service()
        
        # If job_id provided, search only that job's transcript
        if request.job_id:
            if request.job_id not in jobs_db:
                raise HTTPException(status_code=404, detail="Job not found")
            
            job = jobs_db[request.job_id]
            transcript_path = job.get("metadata", {}).get("transcript_path")
            
            if not transcript_path or not Path(transcript_path).exists():
                raise HTTPException(status_code=404, detail="Transcript not found")
            
            # Load transcript
            import json
            with open(transcript_path, 'r') as f:
                transcript = json.load(f)
            
            results = selection.search_clips_by_prompt(
                transcript_segments=transcript.get("segments", []),
                query=request.query,
                limit=request.limit
            )
            
            # Convert to SearchResult format
            search_results = []
            for r in results:
                search_results.append(SearchResult(
                    clip_id=r.get("speaker", "unknown"),
                    relevance_score=r["relevance_score"],
                    matched_text=r["text"][:200],
                    timestamp=f"{r['start']:.1f}s - {r['end']:.1f}s",
                    preview_url=None
                ))
            
            return search_results
        else:
            # Search all jobs (simplified - in production use database)
            all_results = []
            
            for job_id, job in jobs_db.items():
                transcript_path = job.get("metadata", {}).get("transcript_path")
                if transcript_path and Path(transcript_path).exists():
                    import json
                    with open(transcript_path, 'r') as f:
                        transcript = json.load(f)
                    
                    results = selection.search_clips_by_prompt(
                        transcript_segments=transcript.get("segments", []),
                        query=request.query,
                        limit=request.limit
                    )
                    
                    for r in results:
                        all_results.append(SearchResult(
                            clip_id=f"{job_id}_{r.get('speaker', 'unknown')}",
                            relevance_score=r["relevance_score"],
                            matched_text=r["text"][:200],
                            timestamp=f"{r['start']:.1f}s - {r['end']:.1f}s",
                            preview_url=f"/jobs/{job_id}"
                        ))
            
            # Sort by relevance and limit
            all_results.sort(key=lambda x: x.relevance_score, reverse=True)
            return all_results[:request.limit]
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clips/{job_id}/download/{clip_index}")
async def download_clip(job_id: str, clip_index: int):
    """Download a specific clip file"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    # Find clip
    clip = None
    for c in job.get("clips", []):
        if c.get("index") == clip_index:
            clip = c
            break
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    file_path = clip.get("file_path")
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="Clip file not found")
    
    return FileResponse(
        path=file_path,
        filename=f"clip_{clip_index}.mp4",
        media_type="video/mp4"
    )


def _get_job_response(job: Dict[str, Any]) -> JobResponse:
    """Convert internal job dict to JobResponse model"""
    return JobResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        message=f"Progress: {job['progress']}%",
        error=job.get("error"),
        input_source=job.get("source_url") or job.get("filename", ""),
        clips=job.get("clips", []),
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        completed_at=job.get("completed_at")
    )
