"""
Base Analyzer Module
Abstract base class for all analyzers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAnalyzer(ABC):
    """Abstract base class for segment analyzers"""
    
    @abstractmethod
    async def analyze(self, segment: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a segment and return analysis results
        
        Args:
            segment: Segment dictionary with text and timing
            context: Optional additional context
            
        Returns:
            Dictionary with analysis results
        """
        pass
    
    @abstractmethod
    async def analyze_batch(
        self, 
        segments: list[Dict[str, Any]], 
        context: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Analyze multiple segments in batch
        
        Args:
            segments: List of segments to analyze
            context: Optional video context
            
        Returns:
            List of analysis results
        """
        pass
