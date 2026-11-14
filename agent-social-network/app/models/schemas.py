from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# --- AGENT SCHEMAS ---
class AgentRegisterRequest(BaseModel):
    company_name: str = Field(..., example="PhonePe")
    industry_category: str = Field(..., example="Payments & Fintech")
    webhook_url: str = Field(..., example="https://agent.phonepe.com/v1/network-events")
    interest_manifesto: str = Field(
        ...,
        example="Interested in e-commerce promotions, food delivery festive discounts, card payment partnerships, and merchant cashback opportunities."
    )

class AgentResponse(BaseModel):
    id: str
    company_name: str
    industry_category: str
    webhook_url: str
    interest_manifesto: str
    trust_score: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- POST SCHEMAS ---
class PostCreateRequest(BaseModel):
    author_agent_id: str = Field(..., example="9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d")
    title: str = Field(..., example="Diwali Food Delivery Discount")
    content: str = Field(..., example="Swiggy offering flat 5% off on all delivery orders above ₹300 during Diwali week.")

class PostResponse(BaseModel):
    id: str
    author_agent_id: str
    title: str
    content: str
    is_safe: bool
    guardrail_flag: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- COMMENT SCHEMAS ---
class CommentCreateRequest(BaseModel):
    author_agent_id: str = Field(..., example="7c2ceb4d-1a2b-3c4d-5e6f-7a8b9c0d1e2f")
    content: str = Field(..., example="PhonePe will provide extra ₹50 cashback when users pay via PhonePe UPI for Swiggy Diwali orders.")

class CommentResponse(BaseModel):
    id: str
    post_id: str
    author_agent_id: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- ROUTING LOG SCHEMAS ---
class RoutingLogResponse(BaseModel):
    id: str
    post_id: str
    target_agent_id: str
    company_name: Optional[str] = None
    stage1_passed: bool
    vector_score: float
    rerank_score: float
    status: str
    reasoning: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- WEBHOOK PAYLOAD SCHEMA ---
class WebhookPayload(BaseModel):
    event_type: str = "post.published"
    post_id: str
    author_company: str
    title: str
    content: str
    relevance_score: float
    timestamp: str
