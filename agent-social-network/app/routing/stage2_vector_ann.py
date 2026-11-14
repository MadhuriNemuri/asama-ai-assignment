from typing import List, Tuple
from app.models.database import Agent, Post
from app.routing.embeddings import embedder
from app.config import settings

def run_stage2_ann(post: Post, candidates: List[Agent], top_k: int = settings.STAGE2_TOP_K) -> List[Tuple[Agent, float]]:
    """
    Stage 2: Hybrid Dense Vector & Lexical Retrieval (ANN Search)
    - Compares incoming post text embedding with agent interest vectors using Cosine Distance.
    - Returns top K = 50 candidates ordered by vector similarity score.
    - Metric: S_dense in [0, 1]
    - Latency: < 15 ms
    """
    if not post.post_embedding or not candidates:
        return []

    scored_candidates = []
    for agent in candidates:
        if not agent.interest_embedding:
            continue
        sim = embedder.cosine_similarity(post.post_embedding, agent.interest_embedding)
        scored_candidates.append((agent, sim))

    # Sort descending by vector similarity score
    scored_candidates.sort(key=lambda x: x[1], reverse=True)

    return scored_candidates[:top_k]
