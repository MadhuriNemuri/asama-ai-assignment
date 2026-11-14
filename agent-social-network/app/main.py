import json
import logging
from typing import List, Dict, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Header
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database import init_db, get_db, Agent, Post, Comment, RoutingLog
from app.models.schemas import (
    AgentRegisterRequest, AgentResponse,
    PostCreateRequest, PostResponse,
    CommentCreateRequest, CommentResponse,
    RoutingLogResponse, WebhookPayload
)
from app.routing.embeddings import embedder
from app.routing.engine import routing_engine
from app.security.hmac_signer import generate_hmac_signature, verify_hmac_signature
from app.security.guardrails import sanitize_and_check_guardrails
from app.feedback.profile_learner import profile_learner
from app.agents.mock_agents import mock_agents_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_network_api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    init_db()
    logger.info("Database initialized successfully.")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="A B2B Event-Driven Social Network for Autonomous AI Agents with Multi-Stage Semantic Relevance Routing",
    lifespan=lifespan
)

# -------------------------------------------------------------
# 1. AGENTS API
# -------------------------------------------------------------
@app.post("/api/v1/agents/register", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
def register_agent(agent_in: AgentRegisterRequest, db: Session = Depends(get_db)):
    """
    Registers an enterprise agent, stores its interest manifesto,
    and computes its initial dense semantic embedding vector.
    """
    # Compute dense vector for manifesto
    embedding = embedder.embed(f"{agent_in.company_name} ({agent_in.industry_category}): {agent_in.interest_manifesto}")

    agent = Agent(
        company_name=agent_in.company_name,
        industry_category=agent_in.industry_category,
        webhook_url=agent_in.webhook_url,
        interest_manifesto=agent_in.interest_manifesto,
        interest_embedding=embedding,
        trust_score=1.0,
        status="ACTIVE"
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

@app.get("/api/v1/agents", response_model=List[AgentResponse])
def list_agents(db: Session = Depends(get_db)):
    return db.query(Agent).all()

# -------------------------------------------------------------
# 2. POSTS API & ROUTING PIPELINE
# -------------------------------------------------------------
@app.post("/api/v1/posts", status_code=status.HTTP_201_CREATED)
def publish_post(post_in: PostCreateRequest, db: Session = Depends(get_db)):
    """
    Publishes an update from an agent.
    1. Validates author agent.
    2. Runs Security & Prompt Injection Guardrails.
    3. Generates dense post embedding vector.
    4. Triggers 3-Stage Relevance Routing Engine (SQL -> Vector ANN -> Reranker).
    """
    author = db.query(Agent).filter(Agent.id == post_in.author_agent_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author agent not registered.")

    # Security check: prompt injection guardrail
    is_safe, reason = sanitize_and_check_guardrails(post_in.title, post_in.content)
    
    post_embedding = embedder.embed(f"{post_in.title} {post_in.content}")

    post = Post(
        author_agent_id=post_in.author_agent_id,
        title=post_in.title,
        content=post_in.content,
        post_embedding=post_embedding,
        is_safe=is_safe,
        guardrail_flag=reason if not is_safe else None
    )
    db.add(post)
    db.commit()
    db.refresh(post)

    # If the post violates security guardrails, halt routing immediately
    if not is_safe:
        return {
            "post_id": post.id,
            "status": "BLOCKED_BY_GUARDRAIL",
            "security_reason": reason,
            "routing_summary": None
        }

    # Execute 3-Stage Relevance Routing Engine
    routing_result = routing_engine.process_post(db, post)

    return {
        "post_id": post.id,
        "title": post.title,
        "author": author.company_name,
        "status": "PUBLISHED_AND_ROUTED",
        "routing_result": routing_result
    }

@app.get("/api/v1/posts/{post_id}")
def get_post(post_id: str, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    
    comments = db.query(Comment).filter(Comment.post_id == post_id).all()
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author_id": post.author_agent_id,
        "author_company": post.author.company_name if post.author else "Unknown",
        "is_safe": post.is_safe,
        "created_at": post.created_at,
        "comments": [
            {
                "id": c.id,
                "author_id": c.author_agent_id,
                "author_company": c.author.company_name if c.author else "Unknown",
                "content": c.content,
                "created_at": c.created_at
            }
            for c in comments
        ]
    }

# -------------------------------------------------------------
# 3. COMMENTS & CLOSED-LOOP FEEDBACK API
# -------------------------------------------------------------
@app.post("/api/v1/posts/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def post_comment(post_id: str, comment_in: CommentCreateRequest, db: Session = Depends(get_db)):
    """
    Autonomous response from a notified agent.
    Updates routing logs to ENGAGED and adjusts the target agent's dynamic preference vector.
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    author = db.query(Agent).filter(Agent.id == comment_in.author_agent_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Commenting agent not found.")

    comment = Comment(
        post_id=post_id,
        author_agent_id=comment_in.author_agent_id,
        content=comment_in.content
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # Trigger Closed-Loop Feedback
    profile_learner.on_comment_added(db, post_id, comment_in.author_agent_id)

    return comment

# -------------------------------------------------------------
# 4. OBSERVABILITY & ROUTING LOGS
# -------------------------------------------------------------
@app.get("/api/v1/posts/{post_id}/routing-logs", response_model=List[RoutingLogResponse])
def get_routing_logs(post_id: str, db: Session = Depends(get_db)):
    logs = db.query(RoutingLog).filter(RoutingLog.post_id == post_id).all()
    results = []
    for log in logs:
        results.append(
            RoutingLogResponse(
                id=log.id,
                post_id=log.post_id,
                target_agent_id=log.target_agent_id,
                company_name=log.target_agent.company_name if log.target_agent else None,
                stage1_passed=log.stage1_passed,
                vector_score=log.vector_score,
                rerank_score=log.rerank_score,
                status=log.status,
                reasoning=log.reasoning,
                created_at=log.created_at
            )
        )
    return results

# -------------------------------------------------------------
# 5. SIMULATION / DEMO RUNNER
# -------------------------------------------------------------
@app.post("/api/v1/posts/{post_id}/simulate-responses")
def simulate_agent_responses(post_id: str, db: Session = Depends(get_db)):
    """
    Simulates webhook dispatch and autonomous responses for all NOTIFIED agents.
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    notified_logs = db.query(RoutingLog).filter(
        RoutingLog.post_id == post_id,
        RoutingLog.status == "NOTIFIED"
    ).all()

    responses = []
    for log in notified_logs:
        agent = log.target_agent
        if not agent:
            continue

        mock_runner = mock_agents_registry.get(agent.company_name)
        if not mock_runner:
            continue

        payload = {
            "post_id": post.id,
            "author_company": post.author.company_name if post.author else "Unknown",
            "title": post.title,
            "content": post.content
        }
        signature = generate_hmac_signature(str(payload))

        reply_text = mock_runner.handle_webhook(payload, signature)
        if reply_text:
            comment = Comment(
                post_id=post.id,
                author_agent_id=agent.id,
                content=reply_text
            )
            db.add(comment)
            profile_learner.on_comment_added(db, post.id, agent.id)
            responses.append({
                "agent": agent.company_name,
                "comment": reply_text
            })

    db.commit()
    return {"simulated_responses": responses}
