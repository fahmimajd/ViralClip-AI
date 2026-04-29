"""
Multi-Modal Scoring Service
Combines LLM analysis with audio and visual features
"""
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger

from app.core.config import settings


class MultiModalScoringService:
    """
    Service for multi-modal viral clip scoring
    
    Combines:
    - LLM virality analysis (60%)
    - Audio energy peaks (20%)
    - Visual scene changes (20%)
    """
    
    def __init__(self):
        self.weights = {
            "llm": settings.LLM_WEIGHT,
            "audio": settings.AUDIO_WEIGHT,
            "visual": settings.VISUAL_WEIGHT
        }
    
    def calculate_audio_score(
        self, 
        audio_path: str, 
        start: float, 
        end: float
    ) -> float:
        """
        Calculate audio-based virality score
        
        Analyzes:
        - Energy peaks (louder = more emotional)
        - Speech rate variation
        - Silence patterns
        
        Args:
            audio_path: Path to audio file
            start: Segment start time
            end: Segment end time
            
        Returns:
            Audio score 0-100
        """
        try:
            import librosa
            
            # Load audio segment
            y, sr = librosa.load(audio_path, offset=start, duration=end-start, sr=None)
            
            if len(y) == 0:
                return 0.0
            
            # Calculate RMS energy (loudness)
            rms = librosa.feature.rms(y=y)[0]
            
            # Normalize energy
            if len(rms) > 0:
                avg_energy = np.mean(rms)
                max_energy = np.max(rms)
                energy_variation = np.std(rms) / (avg_energy + 1e-8)
                
                # Score based on energy characteristics
                energy_score = min(avg_energy * 100, 50)  # Up to 50 points
                variation_score = min(energy_variation * 100, 30)  # Up to 30 points
                
                # Detect speech rate (zero crossing rate as proxy)
                zcr = librosa.feature.zero_crossing_rate(y)[0]
                speech_rate_score = min(np.mean(zcr) * 1000, 20)  # Up to 20 points
                
                total_score = energy_score + variation_score + speech_rate_score
                return min(100, max(0, total_score))
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Audio scoring error: {e}")
            return 50.0  # Neutral fallback
    
    def calculate_visual_score(
        self, 
        video_path: str, 
        start: float, 
        end: float
    ) -> float:
        """
        Calculate visual-based virality score
        
        Analyzes:
        - Scene change frequency (more changes = more dynamic)
        - Motion detection
        - Face presence (optional)
        
        Args:
            video_path: Path to video file
            start: Segment start time
            end: Segment end time
            
        Returns:
            Visual score 0-100
        """
        try:
            import cv2
            
            # Open video
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if fps <= 0:
                cap.release()
                return 50.0
            
            # Calculate frame range
            start_frame = int(start * fps)
            end_frame = int(end * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # Read frames and detect scene changes
            prev_frame = None
            scene_changes = 0
            motion_scores = []
            total_frames = 0
            
            while cap.isOpened() and total_frames < (end_frame - start_frame):
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert to grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                if prev_frame is not None:
                    # Calculate frame difference
                    diff = cv2.absdiff(prev_frame, gray)
                    diff_mean = np.mean(diff)
                    
                    # Detect scene change (large difference)
                    if diff_mean > 30:  # Threshold for scene change
                        scene_changes += 1
                    
                    # Calculate motion score
                    motion_scores.append(diff_mean)
                
                prev_frame = gray
                total_frames += 1
            
            cap.release()
            
            if total_frames == 0:
                return 50.0
            
            # Calculate scores
            duration = end - start
            
            # Scene change score (optimal: 1-3 changes per 10 seconds)
            change_rate = (scene_changes / duration) * 10
            scene_score = min(change_rate * 20, 50)  # Up to 50 points
            
            # Motion score
            if motion_scores:
                avg_motion = np.mean(motion_scores)
                motion_score = min(avg_motion * 2, 50)  # Up to 50 points
            else:
                motion_score = 0
            
            total_score = scene_score + motion_score
            return min(100, max(0, total_score))
            
        except Exception as e:
            logger.error(f"Visual scoring error: {e}")
            return 50.0  # Neutral fallback
    
    def calculate_final_score(
        self,
        llm_score: float,
        audio_score: float,
        visual_score: float
    ) -> Dict[str, float]:
        """
        Calculate weighted final score
        
        Args:
            llm_score: LLM virality score (0-100)
            audio_score: Audio feature score (0-100)
            visual_score: Visual feature score (0-100)
            
        Returns:
            Dictionary with individual and final scores
        """
        final_score = (
            llm_score * self.weights["llm"] +
            audio_score * self.weights["audio"] +
            visual_score * self.weights["visual"]
        )
        
        return {
            "llm_score": llm_score,
            "audio_score": audio_score,
            "visual_score": visual_score,
            "final_score": final_score,
            "weights": self.weights.copy()
        }
    
    async def score_segment(
        self,
        video_path: str,
        audio_path: str,
        segment: Dict[str, Any],
        llm_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate complete multi-modal score for a segment
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            segment: Segment dictionary with start/end times
            llm_analysis: Pre-computed LLM analysis (optional)
            
        Returns:
            Complete scoring result
        """
        start = segment.get("start", 0)
        end = segment.get("end", 0)
        
        # Get LLM score
        llm_score = llm_analysis.get("score", 50) if llm_analysis else 50
        
        # Calculate audio score
        audio_score = self.calculate_audio_score(audio_path, start, end)
        
        # Calculate visual score
        visual_score = self.calculate_visual_score(video_path, start, end)
        
        # Calculate final score
        scores = self.calculate_final_score(llm_score, audio_score, visual_score)
        
        logger.info(
            f"Segment {start:.1f}-{end:.1f}s scored: "
            f"LLM={llm_score:.1f}, Audio={audio_score:.1f}, Visual={visual_score:.1f}, "
            f"Final={scores['final_score']:.1f}"
        )
        
        return scores


# Singleton instance
_scoring_service: Optional[MultiModalScoringService] = None


def get_scoring_service() -> MultiModalScoringService:
    """Get or create scoring service singleton"""
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = MultiModalScoringService()
    return _scoring_service
