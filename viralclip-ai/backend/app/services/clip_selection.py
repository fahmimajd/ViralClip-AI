"""
Clip Selection and Segmentation Service
Handles intelligent segment creation and top clip selection
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from app.core.config import settings


class ClipSelectionService:
    """
    Service for segmenting transcripts and selecting best clips
    
    Features:
    - Semantic segmentation (don't cut mid-sentence)
    - Non-overlapping clip selection
    - Buffer addition for smooth transitions
    - Top-N scoring with diversity
    """
    
    def __init__(self):
        self.min_duration = settings.CLIP_MIN_DURATION
        self.max_duration = settings.CLIP_MAX_DURATION
        self.buffer = settings.CLIP_BUFFER
        self.top_clips = settings.TOP_CLIPS
    
    def segment_transcript(
        self,
        transcript_segments: List[Dict[str, Any]],
        target_duration: float = 45.0
    ) -> List[Dict[str, Any]]:
        """
        Segment transcript into viral-clip-sized chunks
        
        Args:
            transcript_segments: List of transcript segments with timing
            target_duration: Target duration for each segment
            
        Returns:
            List of segmented clips with combined text and timing
        """
        if not transcript_segments:
            return []
        
        segments = []
        current_segment = {
            "start": transcript_segments[0]["start"],
            "end": transcript_segments[0]["end"],
            "text": transcript_segments[0]["text"],
            "subsegments": [transcript_segments[0]]
        }
        
        for i in range(1, len(transcript_segments)):
            seg = transcript_segments[i]
            current_duration = current_segment["end"] - current_segment["start"]
            
            # Check if adding this segment would exceed target duration
            new_duration = seg["end"] - current_segment["start"]
            
            if new_duration <= self.max_duration:
                # Add to current segment
                current_segment["end"] = seg["end"]
                current_segment["text"] += " " + seg["text"]
                current_segment["subsegments"].append(seg)
            else:
                # Save current segment if it's long enough
                if current_duration >= self.min_duration:
                    segments.append(current_segment)
                
                # Start new segment
                current_segment = {
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "subsegments": [seg]
                }
        
        # Don't forget the last segment
        if current_segment["end"] - current_segment["start"] >= self.min_duration:
            segments.append(current_segment)
        
        logger.info(f"Created {len(segments)} segments from {len(transcript_segments)} transcript parts")
        
        return segments
    
    def select_top_clips(
        self,
        scored_segments: List[Dict[str, Any]],
        top_n: Optional[int] = None,
        min_score: float = 40.0,
        avoid_overlap: bool = True,
        overlap_buffer: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Select top viral clips avoiding overlaps
        
        Args:
            scored_segments: List of segments with scores
            top_n: Number of clips to select (default: settings.TOP_CLIPS)
            min_score: Minimum score threshold
            avoid_overlap: Whether to avoid overlapping clips
            overlap_buffer: Minimum gap between clips
            
        Returns:
            List of selected top clips
        """
        if not scored_segments:
            return []
        
        top_n = top_n or self.top_clips
        
        # Sort by final score descending
        sorted_segments = sorted(
            scored_segments,
            key=lambda x: x.get("final_score", 0),
            reverse=True
        )
        
        selected = []
        selected_ranges = []  # Track time ranges to avoid overlaps
        
        for segment in sorted_segments:
            if len(selected) >= top_n:
                break
            
            start = segment.get("start", 0)
            end = segment.get("end", 0)
            score = segment.get("final_score", 0)
            
            # Skip if below minimum score
            if score < min_score:
                continue
            
            # Check for overlaps
            if avoid_overlap:
                has_overlap = False
                for sel_start, sel_end in selected_ranges:
                    # Check if ranges overlap (with buffer)
                    if not (end + overlap_buffer < sel_start or start > sel_end + overlap_buffer):
                        has_overlap = True
                        break
                
                if has_overlap:
                    continue
            
            # Add buffer times
            buffered_start = max(0, start - self.buffer)
            buffered_end = end + self.buffer
            
            # Create selected clip entry
            clip = segment.copy()
            clip["buffered_start"] = buffered_start
            clip["buffered_end"] = buffered_end
            clip["duration"] = buffered_end - buffered_start
            
            selected.append(clip)
            selected_ranges.append((buffered_start, buffered_end))
        
        logger.info(f"Selected {len(selected)} top clips from {len(scored_segments)} candidates")
        
        return selected
    
    def search_clips_by_prompt(
        self,
        transcript_segments: List[Dict[str, Any]],
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant clips based on text query
        
        Uses simple keyword matching (can be enhanced with embeddings)
        
        Args:
            transcript_segments: List of transcript segments
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching segments with relevance scores
        """
        query_words = set(query.lower().split())
        
        results = []
        
        for segment in transcript_segments:
            text = segment.get("text", "").lower()
            text_words = set(text.split())
            
            # Calculate word overlap
            overlap = len(query_words & text_words)
            relevance = overlap / len(query_words) if query_words else 0
            
            if relevance > 0:
                result = segment.copy()
                result["relevance_score"] = relevance * 100
                result["matched_query"] = query
                results.append(result)
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results[:limit]
    
    def optimize_clip_boundaries(
        self,
        segment: Dict[str, Any],
        transcript_segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Optimize clip boundaries to avoid cutting mid-sentence
        
        Args:
            segment: Segment to optimize
            transcript_segments: Original transcript segments
            
        Returns:
            Optimized segment with adjusted boundaries
        """
        start = segment.get("start", 0)
        end = segment.get("end", 0)
        
        # Find the transcript segment that contains or is closest to start
        best_start = start
        for ts in transcript_segments:
            ts_start = ts.get("start", 0)
            ts_end = ts.get("end", 0)
            
            # If this segment starts near our target start, use its start
            if abs(ts_start - start) < 1.0:
                best_start = ts_start
                break
        
        # Find the transcript segment that contains or is closest to end
        best_end = end
        for ts in transcript_segments:
            ts_start = ts.get("start", 0)
            ts_end = ts.get("end", 0)
            
            # If this segment ends near our target end, use its end
            if abs(ts_end - end) < 1.0:
                best_end = ts_end
                break
        
        # Ensure we don't exceed max duration
        if best_end - best_start > self.max_duration:
            best_end = best_start + self.max_duration
        
        optimized = segment.copy()
        optimized["start"] = best_start
        optimized["end"] = best_end
        optimized["duration"] = best_end - best_start
        
        return optimized
    
    def generate_clip_metadata(
        self,
        clip: Dict[str, Any],
        video_title: str = "",
        author: str = ""
    ) -> Dict[str, Any]:
        """
        Generate metadata for a clip
        
        Args:
            clip: Selected clip with analysis
            video_title: Original video title
            author: Video author
            
        Returns:
            Metadata dictionary
        """
        import uuid
        from datetime import datetime
        
        start = clip.get("start", 0)
        end = clip.get("end", 0)
        duration = end - start
        
        # Format timestamp
        hours = int(start // 3600)
        minutes = int((start % 3600) // 60)
        secs = int(start % 60)
        timestamp = f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours > 0 else f"{minutes:02d}:{secs:02d}"
        
        # Generate description
        hook = clip.get("hook", "")
        reason = clip.get("reason", "")
        
        description = f"{hook}\n\n{reason}"
        if video_title:
            description += f"\n\nFrom: {video_title}"
        if author:
            description += f"\nBy: {author}"
        
        metadata = {
            "clip_id": str(uuid.uuid4()),
            "title": clip.get("suggested_title", "Viral Clip"),
            "description": description,
            "hashtags": clip.get("hashtags", ["viral", "trending"]),
            "start_time": start,
            "end_time": end,
            "duration": duration,
            "original_timestamp": timestamp,
            "virality_score": clip.get("final_score", 0),
            "emotional_peaks": clip.get("emotional_peaks", []),
            "quotable_lines": clip.get("quotable_lines", []),
            "created_at": datetime.utcnow().isoformat()
        }
        
        return metadata


# Singleton instance
_selection_service: Optional[ClipSelectionService] = None


def get_selection_service() -> ClipSelectionService:
    """Get or create clip selection service singleton"""
    global _selection_service
    if _selection_service is None:
        _selection_service = ClipSelectionService()
    return _selection_service
