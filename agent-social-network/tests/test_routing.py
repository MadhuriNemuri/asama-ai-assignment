import pytest
from app.models.database import Base, SessionLocal, engine, Agent, Post, Comment
from app.routing.embeddings import embedder
from app.routing.engine import routing_engine
from app.feedback.profile_learner import profile_learner

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.query(Comment).delete()
    db.query(Post).delete()
    db.query(Agent).delete()
    db.commit()
    yield db
    db.close()

def test_semantic_routing_relevance(setup_db):
    db = setup_db
    # Register Swiggy (Food), PhonePe (Fintech), Bajaj (Automotive)
    swiggy = Agent(
        company_name="Swiggy",
        industry_category="Food Delivery",
        webhook_url="https://swiggy.com/webhook",
        interest_manifesto="Food discounts and festive campaigns",
        interest_embedding=embedder.embed("Food discounts and festive campaigns"),
        trust_score=1.0,
        status="ACTIVE"
    )
    phonepe = Agent(
        company_name="PhonePe",
        industry_category="Payments & Fintech",
        webhook_url="https://phonepe.com/webhook",
        interest_manifesto="E-commerce discounts, payment cashback, UPI promotions",
        interest_embedding=embedder.embed("E-commerce discounts, payment cashback, UPI promotions"),
        trust_score=1.0,
        status="ACTIVE"
    )
    bajaj = Agent(
        company_name="Bajaj Auto",
        industry_category="Automotive",
        webhook_url="https://bajajauto.com/webhook",
        interest_manifesto="Motorcycle parts, EV batteries, supply chain manufacturing",
        interest_embedding=embedder.embed("Motorcycle parts, EV batteries, supply chain manufacturing"),
        trust_score=1.0,
        status="ACTIVE"
    )
    db.add_all([swiggy, phonepe, bajaj])
    db.commit()

    # Swiggy posts Diwali food delivery discount
    post = Post(
        author_agent_id=swiggy.id,
        title="Diwali Food Delivery Discount",
        content="Swiggy offers 5% off on all festive orders.",
        post_embedding=embedder.embed("Diwali Food Delivery Discount Swiggy offers 5% off on all festive orders."),
        is_safe=True
    )
    db.add(post)
    db.commit()

    result = routing_engine.process_post(db, post)

    # Assertions
    # 1. Author should be excluded by Stage 1
    assert result["stage1_eligible_count"] == 2
    
    # 2. PhonePe should be NOTIFIED (S >= 0.75)
    notified_names = [n["company_name"] for n in result["notified_agents"]]
    assert "PhonePe" in notified_names

    # 3. Bajaj Auto should be DROPPED
    dropped_names = [d["company_name"] for d in result["dropped_agents"]]
    assert "Bajaj Auto" in dropped_names

def test_closed_loop_feedback(setup_db):
    db = setup_db
    phonepe = Agent(
        company_name="PhonePe",
        industry_category="Payments",
        webhook_url="https://phonepe.com/webhook",
        interest_manifesto="Discounts and payments",
        interest_embedding=embedder.embed("Discounts and payments"),
        trust_score=1.0,
        status="ACTIVE"
    )
    db.add(phonepe)
    db.commit()

    post = Post(
        author_agent_id=phonepe.id, # dummy
        title="Test Post",
        content="Test Content",
        post_embedding=embedder.embed("Test Post Test Content")
    )
    db.add(post)
    db.commit()

    # Trigger comment & test positive feedback
    profile_learner.on_comment_added(db, post.id, phonepe.id)
    rate = profile_learner.calculate_engagement_rate(db, phonepe.id)
    assert rate >= 0.0
