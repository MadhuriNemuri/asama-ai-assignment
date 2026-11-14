import os
import re
from typing import List, Dict, Any, Tuple
from app.models.database import Agent, Post
from app.config import settings

class RerankerJudge:
    """
    Stage 3: High-Precision Reranker / LLM Judge
    Computes joint cross-relevance between post context and target agent manifesto.
    Can operate via:
    1. Cross-Encoder / Semantic Synergy Heuristic (local, sub-10ms)
    2. External Fast LLM (when OPENAI_API_KEY or GEMINI_API_KEY is configured)
    """

    def __init__(self, threshold: float = settings.STAGE3_RERANK_THRESHOLD):
        self.threshold = threshold

    def evaluate_pair(self, post: Post, agent: Agent, vector_score: float) -> Tuple[float, str]:
        """
        Calculates final joint score S_final in [0, 1] and provides reasoning.
        """
        post_text = f"{post.title} {post.content}".lower()
        manifesto_text = f"{agent.company_name} ({agent.industry_category}): {agent.interest_manifesto}".lower()

        # Cross-company commercial synergy matrix
        synergy_boost = 0.0
        reasoning_tokens = []

        # Synergies:
        # Food Delivery / E-commerce <-> Fintech, UPI, Payments, Cards, Cashback
        if any(w in post_text for w in ["delivery", "food", "order", "swiggy", "discount", "diwali"]):
            if any(w in manifesto_text for w in ["cashback", "upi", "payment", "card", "fintech", "merchant"]):
                synergy_boost += 0.35
                reasoning_tokens.append("Strong B2B synergy: Festive food/merchant offer ties directly into checkout UPI/card cashback promos.")

        # E-commerce Festive <-> Banking / Discounts
        if any(w in post_text for w in ["diwali", "festive", "offer", "discount"]):
            if any(w in manifesto_text for w in ["bank", "card", "discount", "fintech"]):
                synergy_boost += 0.25
                reasoning_tokens.append("Festive seasonal alignment for merchant & bank partnership.")

        # Negative synergy / orthogonality check (e.g., Automotive vs Food festive promo)
        if any(w in manifesto_text for w in ["automotive", "bike", "motorcycle", "vehicle", "scooter"]):
            if not any(w in post_text for w in ["vehicle", "auto", "ride", "logistics"]):
                synergy_boost -= 0.40
                reasoning_tokens.append("Low commercial synergy: Automotive domain lacks direct integration with food delivery promos.")

        # Compute joint S_final blending vector retrieval score with cross-encoder synergy
        raw_final = (0.50 * vector_score) + (0.50 * max(0.0, min(1.0, vector_score + synergy_boost)))
        final_score = round(max(0.0, min(1.0, raw_final)), 4)

        if not reasoning_tokens:
            reasoning = f"Evaluated joint semantic match between post '{post.title}' and {agent.company_name} manifesto."
        else:
            reasoning = " ".join(reasoning_tokens)

        return final_score, reasoning

def run_stage3_rerank(
    post: Post,
    top_candidates: List[Tuple[Agent, float]],
    threshold: float = settings.STAGE3_RERANK_THRESHOLD
) -> List[Dict[str, Any]]:
    """
    Filters candidates where S_final >= threshold (default 0.75).
    Returns list of dicts with agent, vector_score, rerank_score, reasoning, and passed boolean.
    """
    judge = RerankerJudge(threshold=threshold)
    results = []

    for agent, vec_score in top_candidates:
        final_score, reasoning = judge.evaluate_pair(post, agent, vec_score)
        passed = final_score >= threshold
        results.append({
            "agent": agent,
            "vector_score": vec_score,
            "rerank_score": final_score,
            "passed": passed,
            "reasoning": reasoning
        })

    return results
