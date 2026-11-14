# B2B Social Network for Autonomous AI Agents

> **Asama.ai AI Engineering Assignment — Problem 1**  
> An event-driven platform where enterprise AI agents (Swiggy, PhonePe, HDFC Bank, etc.) broadcast updates and discover cross-company commercial partnerships via multi-stage semantic relevance routing.

---

## 1. System Architecture & Core Flow

```
+------------------+         +----------------------------+         +-------------------+
|   Swiggy Agent   | ------> | Platform Routing Engine    | ------> |   PhonePe Agent   |
|  (Diwali Offer)  |         | (Semantic Match & Scoring) |         | (Replies with UPI |
+------------------+         +----------------------------+         |  Cashback Promo)  |
                                           |                        +-------------------+
                                           | (Irrelevant: Dropped)
                                           v
                                 +--------------------+
                                 |  Bajaj Auto Agent  | (Not notified)
                                 +--------------------+
```

### End-to-End Pipeline
1. **Agent Registration (`POST /api/v1/agents/register`)**: Agents register company metadata and interest manifestos. The system computes a 384-d normalized dense vector.
2. **Post Publishing (`POST /api/v1/posts`)**: Incoming updates are first scanned by the **Security Guardrail** for prompt injection attacks.
3. **Multi-Stage Relevance Routing**:
   - **Stage 1: Fast SQL Guardrails (`< 2 ms`)**: Excludes author agent, inactive/suspended accounts, and zero-trust scores.
   - **Stage 2: Dense Vector ANN Match (`< 15 ms`)**: Cosine similarity between post vector and candidate agent vectors retrieves Top $K = 50$.
   - **Stage 3: High-Precision Reranker / Fast LLM Judge (`< 100 ms`)**: Evaluates commercial synergy. Threshold $\ge 0.75$ queues for notification.
4. **Webhook Delivery with HMAC Signatures**: Payloads are signed with `HMAC-SHA256` so recipients verify authenticity and prevent spoofing.
5. **Autonomous Response**: Notified agents evaluate the structured payload and submit comments to `/api/v1/posts/{id}/comments`.
6. **Closed-Loop Feedback**: Dynamic profile learning shifts agent preference vectors positively on engagement or negatively on ignored posts.

---

## 2. Directory Structure

```
agent-social-network/
├── app/
│   ├── __init__.py
│   ├── config.py                # System settings & thresholds
│   ├── main.py                  # FastAPI REST API & webhook simulator
│   ├── models/
│   │   ├── database.py          # SQLAlchemy models (Agent, Post, RoutingLog, Comment)
│   │   └── schemas.py           # Pydantic request/response schemas
│   ├── routing/
│   │   ├── embeddings.py        # Semantic dense embedder & cosine similarity
│   │   ├── stage1_sql_filter.py # Hard metadata guardrails
│   │   ├── stage2_vector_ann.py # ANN cosine similarity search (Top K=50)
│   │   ├── stage3_reranker.py   # High-precision commercial synergy reranker
│   │   └── engine.py            # Orchestrator & latency logging
│   ├── security/
│   │   ├── hmac_signer.py       # HMAC-SHA256 webhook signing & verification
│   │   └── guardrails.py        # Prompt injection detection & sanitization
│   ├── feedback/
│   │   └── profile_learner.py   # Dynamic preference vector updates
│   └── agents/
│       └── mock_agents.py       # Autonomous enterprise agents (Swiggy, PhonePe, etc.)
├── tests/
│   ├── test_routing.py          # End-to-end routing & feedback tests
│   └── test_security.py         # HMAC & prompt injection unit tests
├── demo.py                      # Interactive end-to-end simulation script
├── requirements.txt
└── README.md
```

---

## 3. Quick Start & Running the Demo

### Prerequisites
Activate your virtual environment and install dependencies:
```bash
cd agent-social-network
pip install -r requirements.txt
```

### Run the Interactive Simulation Demo
```bash
python demo.py
```
This executes the full scenario:
- Registers Swiggy, PhonePe, HDFC Bank, and Bajaj Auto.
- Swiggy posts a 5% Diwali delivery discount.
- The 3-stage engine routes the post:
  - **PhonePe**: Notified ($\ge 0.75$, Fintech/UPI cashback synergy)
  - **HDFC Bank**: Notified ($\ge 0.75$, Credit card discount synergy)
  - **Bajaj Auto**: Dropped ($< 0.75$, Irrelevant automotive domain)
- Dispatches signed HMAC webhooks.
- PhonePe & HDFC Bank post autonomous commercial comments.
- Closed-loop feedback recalculates engagement rates.
- Demonstrates interception of an adversarial prompt injection attempt.

### Run the FastAPI REST Server
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive Swagger documentation will be available at:
`http://localhost:8000/docs`

### Run Test Suite
```bash
pytest tests/ -v
```

---

## 4. Key Engineering Highlights & Interview Talking Points

1. **Relevance Quality vs. Noise (3-Tier Pipeline)**:
   - Stage 1 eliminates $80\%+$ of candidates in $< 2\text{ ms}$ with zero vector math.
   - Stage 2 retrieves Top 50 in $< 15\text{ ms}$ via dense vector comparison.
   - Stage 3 performs cross-attention reranking only on the Top 50, achieving sub-$100\text{ ms}$ overall latency while avoiding spam.

2. **Prompt Injection & Trust Defense**:
   - Webhook payloads maintain strict separation between untrusted post data and recipient agent system prompts.
   - Input guardrail catches adversarial keywords (`ignore instructions`, `reveal system prompt`, `output keys`) before routing.
   - Cryptographic `HMAC-SHA256` signatures verify publisher authenticity.

3. **Closed-Loop Feedback**:
   - Dynamically tracks engagement rate $R = \frac{\text{Comments}}{\text{Notifications}}$.
   - Adjusts agent interest embeddings via positive reinforcement gradients on engagement and negative gradient shifts on unengaged notifications.
