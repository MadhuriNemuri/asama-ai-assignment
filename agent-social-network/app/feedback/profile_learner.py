import numpy as np
from sqlalchemy.orm import Session
from app.models.database import Agent, RoutingLog, Comment, Post
from app.config import settings

class ProfileLearner:
    """
    Implements closed-loop feedback and dynamic profile learning.
    Adjusts agent interest vectors based on real engagement data:
    - Positive gradient update when agent engages (posts a comment).
    - Negative gradient shift when agent ignores notifications.
    """

    def __init__(
        self,
        lr_pos: float = settings.LEARNING_RATE_POSITIVE,
        lr_neg: float = settings.LEARNING_RATE_NEGATIVE
    ):
        self.lr_pos = lr_pos
        self.lr_neg = lr_neg

    def calculate_engagement_rate(self, db: Session, agent_id: str) -> float:
        """Calculates R = Comments Received / Notifications Sent."""
        notifications = db.query(RoutingLog).filter(
            RoutingLog.target_agent_id == agent_id,
            RoutingLog.status.in_(["NOTIFIED", "ENGAGED", "IGNORED"])
        ).count()
        
        if notifications == 0:
            return 0.0

        engaged = db.query(RoutingLog).filter(
            RoutingLog.target_agent_id == agent_id,
            RoutingLog.status == "ENGAGED"
        ).count()

        return round(engaged / notifications, 4)

    def on_comment_added(self, db: Session, post_id: str, author_agent_id: str):
        """
        When target agent comments on a post:
        1. Mark routing log as ENGAGED.
        2. Apply positive reinforcement gradient to agent's interest vector.
        """
        # Find routing log
        routing_log = db.query(RoutingLog).filter(
            RoutingLog.post_id == post_id,
            RoutingLog.target_agent_id == author_agent_id
        ).first()

        if routing_log:
            routing_log.status = "ENGAGED"

        post = db.query(Post).filter(Post.id == post_id).first()
        agent = db.query(Agent).filter(Agent.id == author_agent_id).first()

        if post and agent and post.post_embedding and agent.interest_embedding:
            # Positive gradient update: V_new = Normalize(V_current + lr_pos * V_post)
            v_curr = np.array(agent.interest_embedding, dtype=np.float32)
            v_post = np.array(post.post_embedding, dtype=np.float32)
            v_new = v_curr + (self.lr_pos * v_post)
            norm = np.linalg.norm(v_new)
            if norm > 0:
                v_new = v_new / norm
            agent.interest_embedding = v_new.tolist()

        db.commit()

    def penalize_unengaged_notifications(self, db: Session, post_id: str):
        """
        For agents notified about a post who did not engage after expiration/timeout:
        Apply negative gradient shift away from unengaged post embedding.
        """
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post or not post.post_embedding:
            return

        unengaged_logs = db.query(RoutingLog).filter(
            RoutingLog.post_id == post_id,
            RoutingLog.status == "NOTIFIED"
        ).all()

        v_post = np.array(post.post_embedding, dtype=np.float32)

        for log in unengaged_logs:
            log.status = "IGNORED"
            agent = db.query(Agent).filter(Agent.id == log.target_agent_id).first()
            if agent and agent.interest_embedding:
                v_curr = np.array(agent.interest_embedding, dtype=np.float32)
                # Negative gradient shift: V_new = Normalize(V_current - lr_neg * V_post)
                v_new = v_curr - (self.lr_neg * v_post)
                norm = np.linalg.norm(v_new)
                if norm > 0:
                    v_new = v_new / norm
                agent.interest_embedding = v_new.tolist()

        db.commit()

profile_learner = ProfileLearner()
