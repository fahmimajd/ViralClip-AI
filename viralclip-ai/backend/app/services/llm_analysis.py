"""
LLM Service for Virality Analysis
Uses Groq or OpenAI to analyze video segments for viral potential
"""
import json
from typing import List, Dict, Any, Optional
from loguru import logger

from app.core.config import settings


class LLMViralityService:
    """
    Service for analyzing video segments using LLM
    
    Evaluates segments based on virality criteria:
    - Strong hook in first 3 seconds
    - Emotional peaks (surprise, humor, anger, curiosity)
    - Insights/value/advice
    - Controversy or opinion
    - Quotable lines
    - Storytelling/reveal moments
    """
    
    def __init__(self):
        self.client = None
        self.provider = settings.LLM_PROVIDER
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize LLM client based on provider"""
        try:
            if self.provider == "groq":
                from groq import Groq
                
                if not settings.GROQ_API_KEY:
                    raise ValueError("GROQ_API_KEY not set")
                
                self.client = Groq(api_key=settings.GROQ_API_KEY)
                self.model = settings.LLM_MODEL
                logger.info(f"Initialized Groq client with model: {self.model}")
                
            elif self.provider == "openai":
                from openai import OpenAI
                
                if not settings.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY not set")
                
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.model = "gpt-4o"
                logger.info(f"Initialized OpenAI client with model: {self.model}")
            else:
                raise ValueError(f"Unknown LLM provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Error initializing LLM client: {e}")
            raise
    
    async def analyze_segment(
        self, 
        segment_text: str,
        start_time: float,
        end_time: float,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a video segment for virality
        
        Args:
            segment_text: Transcript text for the segment
            start_time: Start time in seconds
            end_time: End time in seconds
            context: Optional additional context about the video
            
        Returns:
            Dictionary with virality analysis
        """
        duration = end_time - start_time
        
        # Build the prompt
        system_prompt = self._get_system_prompt()
        user_prompt = self._build_user_prompt(segment_text, duration, context)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Add timing information
            result["start"] = start_time
            result["end"] = end_time
            
            # Validate and normalize
            result = self._validate_analysis(result, duration)
            
            logger.info(f"Analyzed segment ({start_time:.1f}-{end_time:.1f}s): score={result['score']}")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            # Return fallback analysis
            return self._fallback_analysis(segment_text, start_time, end_time)
    
    async def analyze_batch(
        self, 
        segments: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple segments in batch
        
        Args:
            segments: List of segment dictionaries with text and timing
            context: Optional video context
            
        Returns:
            List of virality analyses
        """
        results = []
        
        for i, segment in enumerate(segments):
            logger.info(f"Analyzing segment {i+1}/{len(segments)}")
            
            analysis = await self.analyze_segment(
                segment_text=segment.get("text", ""),
                start_time=segment.get("start", 0),
                end_time=segment.get("end", 0),
                context=context
            )
            
            results.append(analysis)
        
        return results
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for virality analysis"""
        return """You are an expert video content analyst specializing in identifying viral-worthy clips for social media platforms like TikTok, Instagram Reels, and YouTube Shorts.

Your task is to analyze video transcripts and identify segments with high viral potential.

Evaluate each segment based on these criteria:
1. **Hook Strength** (0-10): Does it grab attention in the first 3 seconds?
2. **Emotional Impact** (0-10): Does it evoke surprise, humor, anger, or curiosity?
3. **Value/Insight** (0-10): Does it provide useful advice, knowledge, or perspective?
4. **Controversy/Opinion** (0-10): Does it present a bold or controversial take?
5. **Quotability** (0-10): Are there memorable, shareable lines?
6. **Storytelling** (0-10): Does it have a narrative arc or reveal moment?

Calculate an overall virality score (0-100) based on these factors.

Respond ONLY with valid JSON in this exact format:
{
    "score": <number 0-100>,
    "reason": "<brief explanation of why this segment is viral-worthy>",
    "hook": "<the opening hook line or description>",
    "suggested_title": "<catchy title for social media>",
    "hashtags": ["<hashtag1>", "<hashtag2>", "<hashtag3>", "<hashtag4>", "<hashtag5>"],
    "emotional_peaks": ["<emotion1>", "<emotion2>"],
    "quotable_lines": ["<quote1>", "<quote2>"]
}"""
    
    def _build_user_prompt(
        self, 
        text: str, 
        duration: float,
        context: Optional[str] = None
    ) -> str:
        """Build the user prompt for analysis"""
        prompt = f"""Analyze this video segment for viral potential:

**Duration**: {duration:.1f} seconds

**Transcript**:
{text}
"""
        
        if context:
            prompt += f"\n**Video Context**: {context}\n"
        
        prompt += "\nProvide your analysis in the specified JSON format."
        
        return prompt
    
    def _validate_analysis(self, result: Dict, duration: float) -> Dict:
        """Validate and normalize the analysis result"""
        # Ensure score is in valid range
        score = result.get("score", 0)
        result["score"] = max(0, min(100, float(score)))
        
        # Ensure required fields exist
        result.setdefault("reason", "Segment analyzed for viral potential")
        result.setdefault("hook", "")
        result.setdefault("suggested_title", "Viral Clip")
        result.setdefault("hashtags", ["viral", "trending", "fyp", "explore", "content"])
        result.setdefault("emotional_peaks", [])
        result.setdefault("quotable_lines", [])
        
        # Ensure hashtags is a list
        if not isinstance(result["hashtags"], list):
            result["hashtags"] = ["viral", "trending", "fyp"]
        
        # Limit hashtags to 5
        result["hashtags"] = result["hashtags"][:5]
        
        return result
    
    def _fallback_analysis(
        self, 
        text: str, 
        start: float, 
        end: float
    ) -> Dict:
        """Generate fallback analysis when LLM fails"""
        # Simple heuristic-based scoring
        word_count = len(text.split())
        question_marks = text.count("?")
        exclamation_marks = text.count("!")
        
        # Basic scoring
        score = 50  # Base score
        score += min(question_marks * 5, 15)  # Questions engage
        score += min(exclamation_marks * 5, 15)  # Exclamations show emotion
        score += min(word_count / 10, 20)  # Longer content can be better
        
        score = min(100, score)
        
        return {
            "start": start,
            "end": end,
            "score": score,
            "reason": "Automated analysis based on text patterns",
            "hook": text[:100] + "..." if len(text) > 100 else text,
            "suggested_title": "Interesting Clip",
            "hashtags": ["viral", "trending", "fyp", "explore", "content"],
            "emotional_peaks": [],
            "quotable_lines": []
        }


# Singleton instance
_llm_service: Optional[LLMViralityService] = None


def get_llm_service() -> LLMViralityService:
    """Get or create LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMViralityService()
    return _llm_service
