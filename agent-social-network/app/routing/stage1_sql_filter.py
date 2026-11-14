from typing import List
from sqlalchemy.orm import Session
from app.models.database import Agent, Post

def run_stage1_filter(db: Session, post: Post) -> List[Agent]:
    """
    Stage 1: Fast SQL Metadata Guardrails
    - Exclude deactivated or suspended agents
    - Exclude the publishing agent itself
    - Exclude agents with 0 trust score
    - Latency: < 2 ms
    """
    eligible_agents = (
        db.query(Agent)
        .filter(
            Agent.id != post.author_agent_id,
            Agent.status == "ACTIVE",
            Agent.trust_score > 0.0,
            Agent.interest_embedding.isnot(None)
        )
        .all()
    )
    return eligible_agents
