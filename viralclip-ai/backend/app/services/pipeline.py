"""
Main Processing Pipeline Orchestrator
Coordinates all services for end-to-end clip generation
"""
import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import uuid
from loguru import logger

from app.core.config import settings
from app.services.transcription import get_transcription_service
from app.services.llm_analysis import get_llm_service
from app.services.scoring import get_scoring_service
from app.services.video_processing import get_video_service
from app.services.clip_selection import get_selection_service


class ProcessingPipeline:
    """
    Main orchestration pipeline for viral clip generation
    
    Coordinates:
    1. Video download/upload
    2. Audio extraction
    3. Transcription + diarization
    4. Segment creation
    5. LLM virality analysis
    6. Multi-modal scoring
    7. Top clip selection
    8. Clip rendering with captions
    """
    
    def __init__(self):
        self.transcription = get_transcription_service()
        self.llm = get_llm_service()
        self.scoring = get_scoring_service()
        self.video = get_video_service()
        self.selection = get_selection_service()
        
        # Progress tracking
        self.progress_callbacks = {}
    
    def register_progress_callback(self, job_id: str, callback):
        """Register a callback for progress updates"""
        self.progress_callbacks[job_id] = callback
    
    def _update_progress(self, job_id: str, progress: int, message: str):
        """Update job progress"""
        logger.info(f"Job {job_id}: {progress}% - {message}")
        if job_id in self.progress_callbacks:
            try:
                asyncio.create_task(self.progress_callbacks[job_id](progress, message))
            except RuntimeError:
                # No event loop running, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.progress_callbacks[job_id](progress, message))
                loop.close()
    
    async def process_youtube_video(
        self,
        url: str,
        job_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a YouTube video end-to-end
        
        Args:
            url: YouTube video URL
            job_id: Unique job identifier
            options: Processing options
            
        Returns:
            Result dictionary with clips and metadata
        """
        options = options or {}
        result = {
            "job_id": job_id,
            "success": False,
            "clips": [],
            "metadata": {},
            "error": None
        }
        
        try:
            # Step 1: Download video
            self._update_progress(job_id, 5, "Downloading YouTube video...")
            download_result = self.video.download_youtube_video(url)
            
            if not download_result.get("success"):
                raise Exception(f"Download failed: {download_result.get('error', 'Unknown error')}")
            
            video_path = download_result["file_path"]
            video_info = {
                "title": download_result.get("title", ""),
                "author": download_result.get("author", ""),
                "duration": download_result.get("duration", 0),
                "resolution": download_result.get("resolution", "")
            }
            
            result["metadata"]["video_info"] = video_info
            
            # Step 2: Extract audio
            self._update_progress(job_id, 15, "Extracting audio...")
            audio_path = self.video.extract_audio(video_path)
            
            # Step 3: Transcribe with diarization
            self._update_progress(job_id, 25, "Transcribing audio...")
            transcript = await self.transcription.transcribe(audio_path)
            
            # Save transcript
            transcript_path = str(Path(settings.OUTPUT_DIR) / f"{job_id}_transcript.json")
            self.transcription.save_transcript(transcript, transcript_path)
            result["metadata"]["transcript_path"] = transcript_path
            
            # Step 4: Segment transcript
            self._update_progress(job_id, 40, "Creating segments...")
            segments = self.selection.segment_transcript(
                transcript["segments"],
                target_duration=options.get("target_duration", 45.0)
            )
            
            if not segments:
                raise Exception("No valid segments created from transcript")
            
            # Step 5: LLM virality analysis
            self._update_progress(job_id, 50, "Analyzing virality...")
            llm_analyses = await self.llm.analyze_batch(
                segments,
                context=f"Video: {video_info['title']} by {video_info['author']}"
            )
            
            # Step 6: Multi-modal scoring
            self._update_progress(job_id, 65, "Calculating multi-modal scores...")
            scored_segments = []
            for segment, llm_analysis in zip(segments, llm_analyses):
                scores = await self.scoring.score_segment(
                    video_path=video_path,
                    audio_path=audio_path,
                    segment=segment,
                    llm_analysis=llm_analysis
                )
                
                # Combine all data
                combined = {**segment, **llm_analysis, **scores}
                scored_segments.append(combined)
            
            # Step 7: Select top clips
            self._update_progress(job_id, 75, "Selecting best clips...")
            top_clips = self.selection.select_top_clips(
                scored_segments,
                top_n=options.get("top_clips", settings.TOP_CLIPS),
                min_score=options.get("min_score", 40.0)
            )
            
            # Step 8: Render clips
            self._update_progress(job_id, 80, "Rendering clips...")
            rendered_clips = []
            
            for i, clip in enumerate(top_clips):
                clip_num = i + 1
                self._update_progress(
                    job_id, 
                    80 + int((i / len(top_clips)) * 15),
                    f"Rendering clip {clip_num}/{len(top_clips)}..."
                )
                
                rendered = await self._render_clip(
                    video_path=video_path,
                    clip=clip,
                    job_id=job_id,
                    clip_index=i,
                    options=options
                )
                
                if rendered:
                    rendered_clips.append(rendered)
            
            # Finalize
            self._update_progress(job_id, 100, "Processing complete!")
            
            result["success"] = True
            result["clips"] = rendered_clips
            result["metadata"]["total_clips"] = len(rendered_clips)
            result["metadata"]["output_dir"] = str(Path(settings.OUTPUT_DIR) / job_id)
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            result["error"] = str(e)
            self._update_progress(job_id, 0, f"Failed: {str(e)}")
        
        return result
    
    async def _render_clip(
        self,
        video_path: str,
        clip: Dict[str, Any],
        job_id: str,
        clip_index: int,
        options: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Render a single clip with captions"""
        try:
            output_dir = Path(settings.OUTPUT_DIR) / job_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            start = clip.get("buffered_start", clip.get("start", 0))
            end = clip.get("buffered_end", clip.get("end", 0))
            
            # Create vertical clip
            clip_path = str(output_dir / f"clip_{clip_index:03d}.mp4")
            
            success = self.video.create_vertical_clip(
                input_path=video_path,
                output_path=clip_path,
                start_time=start,
                end_time=end,
                crop_mode="center"
            )
            
            if not success:
                logger.warning(f"Failed to create clip {clip_index}")
                return None
            
            # Add captions if enabled
            if options.get("add_captions", True):
                captioned_path = str(output_dir / f"clip_{clip_index:03d}_captioned.mp4")
                
                # Get captions for this time range
                captions = self._get_captions_for_range(clip, start, end)
                
                if captions:
                    self.video.add_animated_captions(
                        input_path=clip_path,
                        output_path=captioned_path,
                        captions=captions
                    )
                    final_path = captioned_path
                else:
                    final_path = clip_path
            else:
                final_path = clip_path
            
            # Generate thumbnail
            thumbnail_path = str(output_dir / f"clip_{clip_index:03d}_thumb.jpg")
            self.video.generate_thumbnail(final_path, thumbnail_path)
            
            # Generate metadata
            metadata = self.selection.generate_clip_metadata(
                clip=clip,
                video_title=options.get("video_title", ""),
                author=options.get("author", "")
            )
            
            # Save metadata
            metadata_path = str(output_dir / f"clip_{clip_index:03d}_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Get file info
            video_info = self.video.get_video_info(final_path)
            
            return {
                "clip_id": metadata["clip_id"],
                "index": clip_index,
                "file_path": final_path,
                "file_url": f"/outputs/{job_id}/clip_{clip_index:03d}.mp4",
                "thumbnail_path": thumbnail_path,
                "thumbnail_url": f"/outputs/{job_id}/clip_{clip_index:03d}_thumb.jpg",
                "metadata": metadata,
                "duration": metadata["duration"],
                "resolution": f"{video_info.get('width', 0)}x{video_info.get('height', 0)}",
                "file_size": video_info.get("file_size", 0),
                "virality_score": clip.get("final_score", 0)
            }
            
        except Exception as e:
            logger.error(f"Clip render error: {e}")
            return None
    
    def _get_captions_for_range(
        self,
        clip: Dict[str, Any],
        start: float,
        end: float
    ) -> List[Dict[str, Any]]:
        """Extract captions for a specific time range"""
        subsegments = clip.get("subsegments", [])
        
        captions = []
        for seg in subsegments:
            seg_start = seg.get("start", 0)
            seg_end = seg.get("end", 0)
            
            # Adjust timing relative to clip start
            adjusted_start = max(0, seg_start - start)
            adjusted_end = min(end - start, seg_end - start)
            
            if adjusted_end > adjusted_start:
                captions.append({
                    "start": adjusted_start,
                    "end": adjusted_end,
                    "text": seg.get("text", "")
                })
        
        return captions
    
    async def process_uploaded_file(
        self,
        file_path: str,
        job_id: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an uploaded video file
        
        Similar to YouTube processing but skips download step
        """
        options = options or {}
        
        # Get video info
        video_info = self.video.get_video_info(file_path)
        options["video_title"] = Path(file_path).stem
        options["video_duration"] = video_info.get("duration", 0)
        
        # Reuse YouTube processing logic
        return await self.process_youtube_video(
            url="",  # Not used for uploads
            job_id=job_id,
            options=options
        )


# Singleton instance
_pipeline: Optional[ProcessingPipeline] = None


def get_processing_pipeline() -> ProcessingPipeline:
    """Get or create processing pipeline singleton"""
    global _pipeline
    if _pipeline is None:
        _pipeline = ProcessingPipeline()
    return _pipeline
