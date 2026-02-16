"""
Semantic Critic for the Long-Form Video Reliability Engine.

This module provides semantic similarity-based quality evaluation
for generated prompts against scene content.
"""

import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class SemanticCritic:
    """
    Evaluates semantic alignment between scene content and prompts.
    
    Uses sentence transformers to encode text into embeddings and
    measures cosine similarity to determine quality.
    """
    
    def __init__(self):
        """Initialize the semantic critic with the embedding model."""
        print("[CRITIC INIT] Loading sentence transformer model...")
        
        # Set cache directory to local project folder to avoid permission issues
        cache_dir = os.path.join(os.getcwd(), ".model_cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        self.model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=cache_dir)
        print("[CRITIC INIT] ✓ Model loaded successfully")
    
    def evaluate_shot(self, script_text: str, prompt_text: str) -> float:
        """
        Evaluate semantic similarity between scene content and prompt.
        
        Args:
            script_text: The original scene content from the screenplay
            prompt_text: The generated positive prompt for the shot
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Encode both texts into embeddings
        embeddings = self.model.encode([script_text, prompt_text])
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity([embeddings[0]], [embeddings[1]])
        score = float(similarity_matrix[0][0])
        
        return score
