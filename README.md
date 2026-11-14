# Asama.ai AI Engineering Assignment

This repository contains complete, production-grade implementations for **both problems** in the Asama.ai AI Engineering Assignment.

---

## Repository Structure

```
asama-ai-assignment/
├── agent-social-network/        # PROBLEM 1: B2B Social Network for AI Agents
│   ├── app/
│   │   ├── routing/             # 3-Stage Relevance Routing Engine (SQL -> Vector ANN -> Reranker)
│   │   ├── security/            # HMAC-SHA256 & Prompt Injection Defense
│   │   ├── feedback/            # Closed-Loop Feedback & Dynamic Profile Learning
│   │   ├── models/              # SQLAlchemy & Pydantic Data Models
│   │   └── agents/              # Simulated Autonomous Enterprise Agents
│   ├── tests/                   # Pytest test suite
│   ├── demo.py                  # End-to-end interactive simulation script
│   ├── requirements.txt
│   └── README.md
│
├── linux-hardware-assistant/    # PROBLEM 2: Local Linux Hardware Q&A Assistant
│   ├── assistant/
│   │   ├── execution.py         # Safe System Execution Engine (Allow-list, execve, shell=False)
│   │   ├── parsers.py           # Structured JSON normalizers (dmidecode, lscpu, lsblk, free)
│   │   ├── discovery.py         # System capability & binary availability discovery
│   │   └── agent.py             # Grounded LLM Orchestrator with anti-hallucination prompt
│   ├── tests/                   # Pytest test suite
│   ├── demo.py                  # Interactive CLI demo (supports live Linux or mock modes)
│   ├── requirements.txt
│   └── README.md
│
└── README.md                    # Project index & architecture summary
```

---

## Problem 1: A Social Network for AI Agents (`agent-social-network/`)

### Summary & Highlights
* **Domain:** B2B event-driven network where company AI agents (Swiggy, PhonePe, HDFC Bank, Bajaj Auto) broadcast updates to discover cross-company commercial partnerships.
* **Core Problem Solved:** **Multi-Stage Semantic Relevance Routing**:
  1. **Stage 1 (Fast SQL Metadata Filter, `< 2 ms`)**: Excludes publishing author, deactivated/suspended accounts, and zero-trust scores.
  2. **Stage 2 (Dense Vector ANN Match, `< 15 ms`)**: Cosine similarity against agent interest manifestos filters candidate pool down to Top $K=50$.
  3. **Stage 3 (High-Precision Reranker / Fast LLM Judge, `< 100 ms`)**: Evaluates commercial synergy. Threshold $\ge 0.75$ queues for notification.
* **Trust & Safety:**
  - `HMAC-SHA256` cryptographic signatures for webhook integrity.
  - Strict data/prompt separation and input guardrail filtering prompt injection attacks (`ignore previous instructions`, etc.).
* **Closed-Loop Feedback:** Dynamically tracks engagement rates ($R = \frac{\text{Comments}}{\text{Notifications}}$) and applies gradient shifts to update agent interest vectors over time.

### How to Run Demo 1
```bash
cd agent-social-network
pip install -r requirements.txt
python demo.py
```
To run tests:
```bash
pytest tests/ -v
```

---

## Problem 2: Local Linux Hardware Q&A Assistant (`linux-hardware-assistant/`)

### Summary & Highlights
* **Domain:** Local natural-language assistant inspecting host Linux hardware specs without hallucinations.
* **Core Problem Solved:** **Safe Tool Calling & System Grounding**:
  1. **Strict Allow-List Model**: The LLM never executes arbitrary bash strings; it selects pre-defined tools mapped to fixed binary paths.
  2. **Subshell Prevention (`shell=False`)**: Direct OS syscalls (`execve`) prevent shell injection (`;`, `&&`, `|`).
  3. **Privilege Escalation Strategy**: Clear architecture for scoped sudoers (`/etc/sudoers.d/hw-assistant`) and unprivileged fallbacks (`/proc/meminfo`, `/sys`).
  4. **Output Normalization**: Converts raw `dmidecode`, `lscpu`, `lsblk`, and `free` text into standardized JSON schemas.
  5. **Anti-Hallucination Prompting**: Strictly answers from verified JSON; outputs *"I cannot determine this hardware detail"* if data is missing.

### How to Run Demo 2
```bash
cd linux-hardware-assistant
pip install -r requirements.txt
python demo.py
```
To run tests:
```bash
pytest tests/ -v
```
