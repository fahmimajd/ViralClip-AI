"""
Transcription Service using Faster-Whisper and Pyannote
Handles speech-to-text and speaker diarization
"""
import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import numpy as np
from loguru import logger

from app.core.config import settings


class TranscriptionService:
    """
    Service for transcribing audio with speaker diarization
    
    Uses Faster-Whisper for efficient speech-to-text
    and Pyannote for speaker diarization
    """
    
    def __init__(self):
        self.whisper_model = None
        self.diarization_model = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize Whisper and Pyannote models"""
        try:
            # Initialize Faster-Whisper
            from faster_whisper import WhisperModel
            
            logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL}")
            self.whisper_model = WhisperModel(
                settings.WHISPER_MODEL,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE_TYPE,
                cpu_threads=settings.WHISPER_CPU_THREADS,
                num_workers=settings.WHISPER_NUM_WORKERS
            )
            logger.info("Whisper model loaded successfully")
            
            # Initialize Pyannote for diarization (if token available)
            if settings.PYANNOTE_TOKEN:
                from pyannote.audio import Pipeline
                
                logger.info("Loading Pyannote diarization pipeline")
                self.diarization_model = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=settings.PYANNOTE_TOKEN
                )
                
                if hasattr(self.diarization_model, 'to'):
                    import torch
                    self.diarization_model.to(torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
                
                logger.info("Pyannote model loaded successfully")
            else:
                logger.warning("Pyannote token not provided, skipping diarization")
                
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise
    
    async def transcribe(
        self, 
        audio_path: str, 
        language: str = "en",
        enable_diarization: bool = True
    ) -> Dict[str, Any]:
        """
        Transcribe audio file with optional speaker diarization
        
        Args:
            audio_path: Path to audio file
            language: Language code (default: en)
            enable_diarization: Whether to perform speaker diarization
            
        Returns:
            Dictionary containing segments with timing, text, and speaker info
        """
        logger.info(f"Starting transcription for: {audio_path}")
        
        result = {
            "segments": [],
            "language": language,
            "duration": 0
        }
        
        try:
            # Get audio duration
            import librosa
            y, sr = librosa.load(audio_path, sr=None)
            result["duration"] = len(y) / sr
            
            # Run Whisper transcription
            segments, info = self.whisper_model.transcribe(
                audio_path,
                language=language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            logger.info(f"Detected language: {info.language} with probability {info.language_probability}")
            result["language"] = info.language
            
            # Process segments
            whisper_segments = []
            for segment in segments:
                whisper_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "confidence": getattr(segment, 'avg_logprob', 0.0)
                })
            
            # Perform diarization if enabled and available
            if enable_diarization and self.diarization_model:
                logger.info("Performing speaker diarization")
                diarization = self.diarization_model(audio_path)
                
                # Merge Whisper segments with diarization
                result["segments"] = self._merge_diarization(
                    whisper_segments, 
                    diarization
                )
            else:
                result["segments"] = whisper_segments
            
            logger.info(f"Transcription complete: {len(result['segments'])} segments")
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
        
        return result
    
    def _merge_diarization(
        self, 
        segments: List[Dict], 
        diarization
    ) -> List[Dict]:
        """
        Merge Whisper transcription segments with Pyannote diarization
        
        Args:
            segments: List of Whisper segments
            diarization: Pyannote diarization result
            
        Returns:
            List of segments with speaker information
        """
        merged_segments = []
        
        # Convert diarization to list of (start, end, speaker) tuples
        diarization_segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            diarization_segments.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })
        
        # For each Whisper segment, find overlapping speaker
        for segment in segments:
            segment_start = segment["start"]
            segment_end = segment["end"]
            
            # Find speakers in this segment
            speakers_in_segment = {}
            for diag in diarization_segments:
                # Check for overlap
                if diag["start"] < segment_end and diag["end"] > segment_start:
                    overlap_start = max(segment_start, diag["start"])
                    overlap_end = min(segment_end, diag["end"])
                    overlap_duration = overlap_end - overlap_start
                    
                    speaker = diag["speaker"]
                    if speaker not in speakers_in_segment:
                        speakers_in_segment[speaker] = 0
                    speakers_in_segment[speaker] += overlap_duration
            
            # Assign dominant speaker
            dominant_speaker = None
            if speakers_in_segment:
                dominant_speaker = max(speakers_in_segment, key=speakers_in_segment.get)
            
            merged_segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"],
                "speaker": dominant_speaker,
                "confidence": segment.get("confidence", 0.0)
            })
        
        return merged_segments
    
    def save_transcript(self, transcript: Dict[str, Any], output_path: str):
        """Save transcript to JSON file"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Transcript saved to: {output_path}")
    
    def load_transcript(self, input_path: str) -> Dict[str, Any]:
        """Load transcript from JSON file"""
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)


# Singleton instance
_transcription_service: Optional[TranscriptionService] = None


def get_transcription_service() -> TranscriptionService:
    """Get or create transcription service singleton"""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service
