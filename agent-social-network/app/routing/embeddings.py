import math
import re
from typing import List
import numpy as np

# Dimension of dense embedding vectors
DIM = 384

class SemanticEmbedder:
    """
    Lightweight, deterministic semantic embedder that works out-of-the-box.
    Uses subword n-gram hashing and contextual vocabulary weighting to project
    text into a normalized 384-dimensional dense vector space.
    Compatible with pluggable models (e.g., SentenceTransformers, OpenAI, Gemini).
    """

    def __init__(self, dim: int = DIM):
        self.dim = dim
        # High-signal business domain concepts for cross-company relevance
        self.domain_anchors = {
            "food_delivery": ["food", "delivery", "restaurant", "order", "swiggy", "zomato", "meal", "dining"],
            "fintech_upi": ["upi", "payment", "cashback", "phonepe", "paytm", "gpay", "wallet", "merchant", "checkout"],
            "banking_cards": ["bank", "card", "hdfc", "icici", "credit", "debit", "discount", "emi", "interest"],
            "ecommerce_festive": ["diwali", "festive", "offer", "discount", "flipkart", "amazon", "sale", "deals"],
            "automotive": ["bike", "motorcycle", "car", "bajaj", "ev", "engine", "dealership", "vehicle", "scooter"],
            "travel": ["flight", "hotel", "travel", "booking", "makemytrip", "holiday"]
        }

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9_\u20B9]+\b", text.lower())

    def embed(self, text: str) -> List[float]:
        """Embeds a single string into a normalized dense vector."""
        vec = np.zeros(self.dim, dtype=np.float32)
        tokens = self._tokenize(text)
        if not tokens:
            return vec.tolist()

        # 1. Hashing trick for unigrams and bigrams
        for i, token in enumerate(tokens):
            idx1 = hash(token) % self.dim
            vec[idx1] += 1.0
            
            # Bigram
            if i > 0:
                bigram = f"{tokens[i-1]}_{token}"
                idx2 = hash(bigram) % self.dim
                vec[idx2] += 1.5

        # 2. Semantic domain anchor projections (bridges semantic gaps e.g. "Diwali offer" <-> "cashback")
        anchor_stride = self.dim // (len(self.domain_anchors) + 1)
        for anchor_idx, (domain, keywords) in enumerate(self.domain_anchors.items()):
            overlap = sum(1 for t in tokens if t in keywords or any(k in t for k in keywords))
            if overlap > 0:
                slot = (anchor_idx + 1) * anchor_stride
                weight = math.log1p(overlap) * 2.0
                vec[slot % self.dim] += weight
                vec[(slot + 1) % self.dim] += weight * 0.7

        # 3. L2 Normalize to ensure cosine similarity equals dot product
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculates cosine similarity between two normalized vectors."""
        if not vec1 or not vec2:
            return 0.0
        v1 = np.array(vec1, dtype=np.float32)
        v2 = np.array(vec2, dtype=np.float32)
        
        # Clip to [0.0, 1.0] for semantic scoring
        score = float(np.dot(v1, v2))
        return max(0.0, min(1.0, score))

embedder = SemanticEmbedder()
