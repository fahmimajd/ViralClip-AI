"""
Semantic Search Service using Sentence Embeddings
Enables natural language prompt-based clip search
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from loguru import logger

from app.core.config import settings


class SemanticSearchService:
    """
    Service for semantic search using sentence embeddings
    
    Features:
    - Convert transcript segments to embeddings
    - Search with natural language queries
    - Find clips by theme, emotion, or topic
    - Similar to Clip-Anything's prompt search
    """
    
    def __init__(self):
        self.model = None
        self.index = None
        self.embeddings_cache = {}
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize sentence transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"Loading sentence embedding model: {settings.EMBEDDING_MODEL}")
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")
            
        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback keyword search")
            self.model = None
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            self.model = None
    
    def generate_embeddings(
        self, 
        segments: List[Dict[str, Any]],
        job_id: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate embeddings for transcript segments
        
        Args:
            segments: List of transcript segments with text
            job_id: Optional job ID for caching
            
        Returns:
            Numpy array of embeddings
        """
        if not segments:
            return np.array([])
        
        # Check cache
        if job_id and job_id in self.embeddings_cache:
            logger.info(f"Using cached embeddings for job {job_id}")
            return self.embeddings_cache[job_id]
        
        texts = [seg.get("text", "") for seg in segments]
        
        if self.model is not None:
            try:
                embeddings = self.model.encode(texts, show_progress_bar=True)
                
                # Cache embeddings
                if job_id:
                    self.embeddings_cache[job_id] = embeddings
                
                logger.info(f"Generated {len(embeddings)} embeddings")
                return embeddings
                
            except Exception as e:
                logger.error(f"Embedding generation error: {e}")
        
        # Fallback: use TF-IDF-like approach
        logger.info("Using fallback keyword-based embeddings")
        return self._fallback_embeddings(texts)
    
    def _fallback_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate simple bag-of-words embeddings as fallback"""
        # Simple word frequency vectors
        all_words = set()
        for text in texts:
            all_words.update(text.lower().split())
        
        word_to_idx = {word: idx for idx, word in enumerate(all_words)}
        embeddings = []
        
        for text in texts:
            vec = np.zeros(len(all_words))
            words = text.lower().split()
            for word in words:
                if word in word_to_idx:
                    vec[word_to_idx[word]] += 1
            # Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            embeddings.append(vec)
        
        return np.array(embeddings)
    
    def search_by_prompt(
        self,
        query: str,
        segments: List[Dict[str, Any]],
        embeddings: np.ndarray,
        limit: int = 10,
        min_relevance: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Search for clips using natural language query
        
        Args:
            query: Natural language search query (e.g., "find emotional reactions")
            segments: List of transcript segments
            embeddings: Pre-computed segment embeddings
            limit: Maximum results to return
            min_relevance: Minimum relevance threshold
            
        Returns:
            List of matching segments with relevance scores
        """
        if len(segments) == 0 or len(embeddings) == 0:
            return []
        
        # Generate query embedding
        if self.model is not None:
            try:
                query_embedding = self.model.encode([query])[0]
            except Exception as e:
                logger.error(f"Query embedding error: {e}")
                query_embedding = self._fallback_query_embedding(query)
        else:
            query_embedding = self._fallback_query_embedding(query)
        
        # Calculate cosine similarity
        similarities = self._cosine_similarity(query_embedding, embeddings)
        
        # Filter by minimum relevance
        valid_indices = np.where(similarities >= min_relevance)[0]
        
        if len(valid_indices) == 0:
            logger.info(f"No segments found above relevance threshold {min_relevance}")
            return []
        
        # Sort by relevance
        sorted_indices = valid_indices[np.argsort(similarities[valid_indices])[::-1]]
        
        # Get top results
        results = []
        for idx in sorted_indices[:limit]:
            result = segments[idx].copy()
            result["relevance_score"] = float(similarities[idx]) * 100
            result["matched_query"] = query
            results.append(result)
        
        logger.info(f"Found {len(results)} relevant clips for query: '{query}'")
        return results
    
    def _fallback_query_embedding(self, query: str) -> np.ndarray:
        """Generate simple query embedding as fallback"""
        # This will be expanded to match fallback_embeddings dimensionality
        return np.zeros(100)  # Placeholder
    
    def _cosine_similarity(self, query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
        """Calculate cosine similarity between query and documents"""
        # Normalize query vector
        query_norm = np.linalg.norm(query_vec)
        if query_norm > 0:
            query_vec = query_vec / query_norm
        
        # Calculate dot product (already normalized docs)
        similarities = np.dot(doc_vecs, query_vec)
        
        return similarities
    
    def find_similar_clips(
        self,
        segment_index: int,
        segments: List[Dict[str, Any]],
        embeddings: np.ndarray,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find clips similar to a given segment
        
        Args:
            segment_index: Index of the reference segment
            segments: List of transcript segments
            embeddings: Pre-computed embeddings
            limit: Number of similar clips to find
            
        Returns:
            List of similar segments
        """
        if segment_index >= len(embeddings):
            return []
        
        query_embedding = embeddings[segment_index]
        
        # Calculate similarities to all other segments
        similarities = self._cosine_similarity(query_embedding, embeddings)
        
        # Exclude the reference segment itself
        similarities[segment_index] = -1
        
        # Get top similar
        top_indices = np.argsort(similarities)[::-1][:limit]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:
                result = segments[idx].copy()
                result["similarity_score"] = float(similarities[idx]) * 100
                results.append(result)
        
        return results
    
    def clear_cache(self, job_id: Optional[str] = None):
        """Clear embedding cache"""
        if job_id:
            self.embeddings_cache.pop(job_id, None)
        else:
            self.embeddings_cache.clear()
        logger.info("Embedding cache cleared")


# Singleton instance
_search_service: Optional[SemanticSearchService] = None


def get_semantic_search_service() -> SemanticSearchService:
    """Get or create semantic search service singleton"""
    global _search_service
    if _search_service is None:
        _search_service = SemanticSearchService()
    return _search_service
