"""
Video Processing Service
Handles video downloading, cropping, captioning, and rendering
"""
import os
import subprocess
import json
import shutil
import html
import urllib.request
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import timedelta
from loguru import logger

from app.core.config import settings


class VideoProcessingService:
    """
    Service for video processing operations
    
    Features:
    - YouTube download via yt-dlp
    - Smart vertical cropping (9:16)
    - Animated caption overlay
    - Clip extraction and rendering
    """
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.temp_dir = Path(settings.TEMP_DIR)
        self.ffmpeg_bin = self._resolve_ffmpeg()
        self.ffprobe_bin = shutil.which("ffprobe")
        
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_ffmpeg(self) -> str:
        """Prefer system FFmpeg, fallback to imageio-ffmpeg's bundled binary."""
        if ffmpeg_bin := shutil.which("ffmpeg"):
            return ffmpeg_bin

        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return "ffmpeg"
    
    def download_youtube_video(
        self, 
        url: str, 
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Download YouTube video using yt-dlp
        
        Args:
            url: YouTube video URL
            output_path: Optional custom output path
            
        Returns:
            Dictionary with download info
        """
        import yt_dlp
        
        if output_path is None:
            video_id = url.split('v=')[-1].split('&')[0]
            output_path = str(self.upload_dir / f"{video_id}.mp4")
        
        ydl_opts = {
            'format': 'bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4]/best',
            'outtmpl': output_path,
            'merge_output_format': 'mp4',
            'ffmpeg_location': str(Path(self.ffmpeg_bin).parent),
            'progress_hooks': [self._download_progress_hook],
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'retries': 10,
            'fragment_retries': 10,
            'extractor_retries': 3,
            'js_runtimes': {
                'node': {'path': '/usr/bin/node'},
            },
            'http_headers': {
                'User-Agent': (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/124.0.0.0 Safari/537.36'
                ),
                'Accept-Language': 'en-US,en;q=0.9',
            },
        }

        cookies_file = settings.YTDLP_COOKIES_FILE
        if cookies_file:
            ydl_opts['cookiefile'] = cookies_file
        
        logger.info(f"Downloading YouTube video: {url}")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Get actual filename after download
                actual_path = ydl.prepare_filename(info)
                if actual_path.endswith('.webm'):
                    actual_path = actual_path[:-5] + '.mp4'
                elif actual_path.endswith('.mkv'):
                    actual_path = actual_path[:-4] + '.mp4'
                
                result = {
                    "success": True,
                    "file_path": actual_path,
                    "title": info.get('title', 'Unknown'),
                    "duration": info.get('duration', 0),
                    "resolution": f"{info.get('width', 0)}x{info.get('height', 0)}",
                    "thumbnail": info.get('thumbnail', ''),
                    "author": info.get('uploader', 'Unknown'),
                    "transcript": self.get_youtube_transcript(info),
                }
                
                logger.info(f"Downloaded: {result['title']} ({result['duration']}s)")
                return result
                
        except Exception as e:
            logger.error(f"YouTube download error: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": None
            }

    def get_youtube_transcript(self, info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract YouTube subtitles/auto-captions from yt-dlp metadata when available."""
        preferred_langs = [
            lang.strip()
            for lang in settings.YOUTUBE_TRANSCRIPT_LANGS.split(",")
            if lang.strip()
        ]
        subtitle_sources = [
            ("manual", info.get("subtitles") or {}),
            ("automatic", info.get("automatic_captions") or {}),
        ]

        for source_name, subtitles in subtitle_sources:
            for lang in preferred_langs:
                caption_formats = subtitles.get(lang) or subtitles.get(f"{lang}-orig")
                if not caption_formats:
                    continue

                caption = self._select_caption_format(caption_formats)
                if not caption:
                    continue

                transcript = self._download_caption_transcript(caption, lang, source_name)
                if transcript and transcript["segments"]:
                    logger.info(
                        f"Using YouTube {source_name} transcript: "
                        f"{lang} ({len(transcript['segments'])} segments)"
                    )
                    return transcript

        return None

    def _select_caption_format(self, caption_formats: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Prefer YouTube json3 captions because they preserve timing cleanly."""
        for ext in ("json3", "srv3", "vtt"):
            for caption in caption_formats:
                if caption.get("ext") == ext and caption.get("url"):
                    return caption
        return next((caption for caption in caption_formats if caption.get("url")), None)

    def _download_caption_transcript(
        self,
        caption: Dict[str, Any],
        language: str,
        source: str
    ) -> Optional[Dict[str, Any]]:
        try:
            request = urllib.request.Request(
                caption["url"],
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                content = response.read().decode("utf-8", errors="replace")

            if caption.get("ext") == "json3":
                data = json.loads(content)
                segments = self._parse_json3_captions(data)
            else:
                segments = self._parse_vtt_captions(content)

            if not segments:
                return None

            return {
                "segments": segments,
                "language": language,
                "duration": max(segment["end"] for segment in segments),
                "source": f"youtube_{source}",
            }
        except Exception as e:
            logger.warning(f"Failed to load YouTube transcript: {e}")
            return None

    def _parse_json3_captions(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        segments = []
        for event in data.get("events", []):
            if "segs" not in event:
                continue

            text = "".join(seg.get("utf8", "") for seg in event.get("segs", []))
            text = html.unescape(" ".join(text.split()))
            if not text:
                continue

            start = event.get("tStartMs", 0) / 1000
            duration = event.get("dDurationMs", 0) / 1000
            if duration <= 0:
                duration = 2.0

            segments.append({
                "start": start,
                "end": start + duration,
                "text": text,
                "speaker": None,
                "confidence": 1.0,
            })

        return segments

    def _parse_vtt_captions(self, content: str) -> List[Dict[str, Any]]:
        segments = []
        blocks = content.replace("\r\n", "\n").split("\n\n")
        for block in blocks:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            timing_line = next((line for line in lines if "-->" in line), None)
            if not timing_line:
                continue

            start_raw, end_raw = [part.strip().split(" ")[0] for part in timing_line.split("-->", 1)]
            text_lines = lines[lines.index(timing_line) + 1:]
            text = html.unescape(" ".join(" ".join(text_lines).split()))
            if not text:
                continue

            segments.append({
                "start": self._vtt_time_to_seconds(start_raw),
                "end": self._vtt_time_to_seconds(end_raw),
                "text": text,
                "speaker": None,
                "confidence": 1.0,
            })

        return segments

    def _vtt_time_to_seconds(self, value: str) -> float:
        value = value.replace(",", ".")
        parts = value.split(":")
        seconds = float(parts[-1])
        minutes = int(parts[-2]) if len(parts) >= 2 else 0
        hours = int(parts[-3]) if len(parts) >= 3 else 0
        return hours * 3600 + minutes * 60 + seconds
    
    def _download_progress_hook(self, d: Dict):
        """Progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            if total > 0:
                progress = (downloaded / total) * 100
                logger.debug(f"Download progress: {progress:.1f}%")
    
    def extract_audio(self, video_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract audio from video file
        
        Args:
            video_path: Path to video file
            output_path: Optional output path
            
        Returns:
            Path to extracted audio file
        """
        if output_path is None:
            output_path = str(self.temp_dir / f"{Path(video_path).stem}.wav")
        
        cmd = [
            self.ffmpeg_bin, '-i', video_path,
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # PCM audio
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',  # Mono
            '-y',  # Overwrite
            output_path
        ]
        
        logger.info(f"Extracting audio from: {video_path}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Audio extracted to: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio extraction error: {e}")
            raise
    
    def create_vertical_clip(
        self,
        input_path: str,
        output_path: str,
        start_time: float,
        end_time: float,
        resolution: str = "1080x1920",
        crop_mode: str = "center"
    ) -> bool:
        """
        Create vertical 9:16 clip from video
        
        Args:
            input_path: Source video path
            output_path: Output clip path
            start_time: Start time in seconds
            end_time: End time in seconds
            resolution: Target resolution (default: 1080x1920)
            crop_mode: Crop mode (center, face, smart)
            
        Returns:
            True if successful
        """
        duration = end_time - start_time
        
        # Build FFmpeg command for vertical crop
        width, height = map(int, resolution.split('x'))
        
        # Smart crop filter based on mode
        if crop_mode == "center":
            crop_filter = f"crop=ih*(9/16):ih:(iw-ih*(9/16))/2:0,scale={width}:{height}"
        elif crop_mode == "smart":
            # Use dynamic crop tracking (simplified)
            crop_filter = f"crop=ih*(9/16):ih:(iw-ih*(9/16))/2:0,scale={width}:{height}"
        else:
            crop_filter = f"scale={width}:{height},crop={width}:{height}"
        
        cmd = [
            self.ffmpeg_bin,
            '-i', input_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-vf', crop_filter,
            '-c:v', settings.VIDEO_CODEC,
            '-b:v', settings.VIDEO_BITRATE,
            '-c:a', settings.AUDIO_CODEC,
            '-b:a', settings.AUDIO_BITRATE,
            '-r', str(settings.FPS),
            '-y',
            output_path
        ]
        
        logger.info(f"Creating vertical clip: {start_time:.1f}s - {end_time:.1f}s")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Clip created: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Clip creation error: {e.stderr.decode() if e.stderr else str(e)}")
            return False
    
    def add_animated_captions(
        self,
        input_path: str,
        output_path: str,
        captions: List[Dict[str, Any]],
        style: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add animated captions to video
        
        Args:
            input_path: Input video path
            output_path: Output video path
            captions: List of caption segments with timing
            style: Caption styling options
            
        Returns:
            True if successful
        """
        # Default style
        if style is None:
            style = {
                "font": settings.CAPTION_FONT,
                "fontsize": settings.CAPTION_FONT_SIZE,
                "color": settings.CAPTION_COLOR,
                "bg_color": settings.CAPTION_BG_COLOR,
                "position": settings.CAPTION_POSITION
            }
        
        # Generate ASS subtitle file for advanced styling
        ass_path = str(self.temp_dir / f"{Path(input_path).stem}_captions.ass")
        self._generate_ass_file(captions, ass_path, style)
        
        # FFmpeg command with subtitle overlay
        cmd = [
            self.ffmpeg_bin,
            '-i', input_path,
            '-vf', f"ass={ass_path}",
            '-c:v', settings.VIDEO_CODEC,
            '-b:v', settings.VIDEO_BITRATE,
            '-c:a', settings.AUDIO_CODEC,
            '-b:a', settings.AUDIO_BITRATE,
            '-y',
            output_path
        ]
        
        logger.info(f"Adding animated captions to: {input_path}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Captions added: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Caption overlay error: {e.stderr.decode() if e.stderr else str(e)}")
            return False
    
    def _generate_ass_file(
        self,
        captions: List[Dict[str, Any]],
        output_path: str,
        style: Dict[str, Any]
    ):
        """
        Generate ASS subtitle file with styling
        
        ASS format allows for advanced text styling and animations
        """
        font = style.get("font", "Arial")
        fontsize = style.get("fontsize", 48)
        color = style.get("color", "white")
        bgcolor = style.get("bg_color", "&H80000000")
        
        # Convert color names to ASS format
        color_hex = self._color_to_ass(color)
        
        ass_content = f"""[Script Info]
Title: ViralClip AI Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{fontsize},&H00{color_hex[2:]},&H00FFFFFF,&H00000000,{bgcolor},1,0,0,0,100,100,0,0,1,2,0,2,10,10,140,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        for caption in captions:
            start = self._seconds_to_ass_time(caption["start"])
            end = self._seconds_to_ass_time(caption["end"])
            text = caption["text"].replace("\n", "\\N")
            
            # Add word-by-word animation effect (simplified)
            ass_content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{{\\fad(200,200)}}{text}\n"
        
        Path(output_path).write_text(ass_content, encoding='utf-8')
        logger.debug(f"ASS file generated: {output_path}")
    
    def _seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS.cc)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centiseconds = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"
    
    def _color_to_ass(self, color: str) -> str:
        """Convert color name/hex to ASS format"""
        color_map = {
            "white": "00FFFFFF",
            "black": "00000000",
            "yellow": "0000FFFF",
            "red": "000000FF",
            "green": "0000FF00",
            "blue": "00FF0000"
        }
        return color_map.get(color.lower(), "00FFFFFF")
    
    def generate_thumbnail(
        self,
        video_path: str,
        output_path: str,
        timestamp: Optional[float] = None
    ) -> bool:
        """
        Generate thumbnail from video
        
        Args:
            video_path: Source video path
            output_path: Output thumbnail path
            timestamp: Timestamp to capture (default: middle of video)
            
        Returns:
            True if successful
        """
        if timestamp is None:
            # Get video duration
            if self.ffprobe_bin:
                cmd = [
                    self.ffprobe_bin, '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    video_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                duration = float(result.stdout.strip())
                timestamp = duration / 3  # Take frame at 1/3 point
            else:
                timestamp = 1.0
        
        cmd = [
            self.ffmpeg_bin,
            '-i', video_path,
            '-ss', str(timestamp),
            '-vframes', '1',
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920',
            '-y',
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Thumbnail generated: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Thumbnail generation error: {e}")
            return False
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get video metadata using ffprobe"""
        if not self.ffprobe_bin:
            try:
                import cv2
                capture = cv2.VideoCapture(video_path)
                fps = capture.get(cv2.CAP_PROP_FPS) or 0
                frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0
                width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
                height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
                capture.release()

                return {
                    "duration": frame_count / fps if fps else 0,
                    "width": width,
                    "height": height,
                    "fps": fps,
                    "has_audio": True,
                    "file_size": Path(video_path).stat().st_size
                }
            except Exception as e:
                logger.error(f"Video info error: {e}")
                return {}

        cmd = [
            self.ffprobe_bin, '-v', 'quiet',
            '-print_format', 'json',
            '-show_format', '-show_streams',
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            
            video_stream = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
            audio_stream = next((s for s in info['streams'] if s['codec_type'] == 'audio'), None)
            
            return {
                "duration": float(info['format']['duration']),
                "width": int(video_stream.get('width', 0)) if video_stream else 0,
                "height": int(video_stream.get('height', 0)) if video_stream else 0,
                "fps": eval(video_stream.get('r_frame_rate', '0/1')) if video_stream else 0,
                "has_audio": audio_stream is not None,
                "file_size": int(info['format']['size'])
            }
        except Exception as e:
            logger.error(f"Video info error: {e}")
            return {}


# Singleton instance
_video_service: Optional[VideoProcessingService] = None


def get_video_service() -> VideoProcessingService:
    """Get or create video processing service singleton"""
    global _video_service
    if _video_service is None:
        _video_service = VideoProcessingService()
    return _video_service
