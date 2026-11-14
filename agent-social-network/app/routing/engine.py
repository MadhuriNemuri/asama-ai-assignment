import time
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.database import Post, RoutingLog, Agent
from app.routing.stage1_sql_filter import run_stage1_filter
from app.routing.stage2_vector_ann import run_stage2_ann
from app.routing.stage3_reranker import run_stage3_rerank
from app.config import settings

logger = logging.getLogger("routing_engine")

class MultiStageRoutingEngine:
    """
    Coordinates the 3-tier candidate filtering pipeline:
    Stage 1: Fast SQL Metadata Guardrails (< 2 ms)
    Stage 2: Hybrid Dense Vector & Lexical ANN (< 15 ms)
    Stage 3: High-Precision Reranker / Fast LLM Judge (< 100 ms)
    """

    def process_post(self, db: Session, post: Post) -> Dict[str, Any]:
        t0 = time.time()
        
        # --- STAGE 1: Fast SQL Guardrails ---
        t_stage1_start = time.time()
        stage1_candidates = run_stage1_filter(db, post)
        stage1_duration_ms = round((time.time() - t_stage1_start) * 1000, 2)
        
        # --- STAGE 2: Dense Vector ANN Search ---
        t_stage2_start = time.time()
        stage2_top_k = run_stage2_ann(post, stage1_candidates, top_k=settings.STAGE2_TOP_K)
        stage2_duration_ms = round((time.time() - t_stage2_start) * 1000, 2)
        
        # --- STAGE 3: High-Precision Reranker / LLM Judge ---
        t_stage3_start = time.time()
        stage3_results = run_stage3_rerank(post, stage2_top_k, threshold=settings.STAGE3_RERANK_THRESHOLD)
        stage3_duration_ms = round((time.time() - t_stage3_start) * 1000, 2)
        
        total_duration_ms = round((time.time() - t0) * 1000, 2)

        # Log decisions into routing_logs database table
        notified_agents = []
        dropped_agents = []

        for item in stage3_results:
            target_agent: Agent = item["agent"]
            passed: bool = item["passed"]
            status = "NOTIFIED" if passed else "DROPPED"
            
            log_entry = RoutingLog(
                post_id=post.id,
                target_agent_id=target_agent.id,
                stage1_passed=True,
                vector_score=item["vector_score"],
                rerank_score=item["rerank_score"],
                status=status,
                reasoning=item["reasoning"]
            )
            db.add(log_entry)
            
            summary = {
                "agent_id": target_agent.id,
                "company_name": target_agent.company_name,
                "webhook_url": target_agent.webhook_url,
                "vector_score": item["vector_score"],
                "rerank_score": item["rerank_score"],
                "reasoning": item["reasoning"]
            }
            if passed:
                notified_agents.append(summary)
            else:
                dropped_agents.append(summary)

        db.commit()

        return {
            "post_id": post.id,
            "total_registered_agents": db.query(Agent).count(),
            "stage1_eligible_count": len(stage1_candidates),
            "stage2_top_k_count": len(stage2_top_k),
            "stage3_notified_count": len(notified_agents),
            "latencies_ms": {
                "stage1": stage1_duration_ms,
                "stage2": stage2_duration_ms,
                "stage3": stage3_duration_ms,
                "total": total_duration_ms
            },
            "notified_agents": notified_agents,
            "dropped_agents": dropped_agents
        }

routing_engine = MultiStageRoutingEngine()
