# PromptEnhancer: Multi-Agent Prompt Enrichment System

PromptEnhancer is a secure, self-correcting multi-agent system built on the **Google Agent Development Kit (ADK 2.0)**. It automates high-fidelity prompt expansion using Chain-of-Thought (CoT) reasoning, enforces layout hierarchies, and applies enterprise security filters before images are generated.

---

## 🚀 Features

*   **Decoupled Multi-Agent Loop**: Coordinates a refinement cycle between the **CoT Rewriter** and **AlignEvaluator** agents, terminating early when the alignment quality score is $\ge 4/5$.
*   **Descriptive Hierarchy**: Guides the CoT model to write expanded prompts using a strict 4-level structure:
    1.  *Opening Statement* (focal point summary)
    2.  *Spatially Organized Body* (foreground/background layout)
    3.  *Hierarchical Object Description* (shapes, colors, textures)
    4.  *Concluding Stylistic Identification* (lighting, camera style)
*   **Enterprise Security Checkpoint**: Scrub SSNs and credit cards from prompts before they reach external APIs, and detect/quarantine prompt injection attacks.
*   **Semantic Circuit Breaker**: Utilizes `text-embedding-004` to compare input and output similarity. Sessions with similarity $< 0.65$ are quarantined.
*   **FastAPI Dashboard UI**: A dark glassmorphism dashboard providing session monitoring, CoT logging, and pending approval management.

---

## 📁 Directory Structure

```
prompt-enhancer/
├── app/
│   ├── agent.py               # Root Orchestrator and Agent definitions
│   ├── instructions.py        # System instructions and prompt templates
│   ├── security.py            # PII scrubbing and injection defenses
│   ├── tools.py               # HITL vibe-diff tool and image generator
│   └── mock_mcp_server.py     # Local FastMCP stdio server
├── dashboard/
│   ├── main.py                # FastAPI dashboard app
│   └── templates/             # Dashboard HTML template
├── tests/
│   ├── unit/                  # Pytest unit tests
│   └── eval/                  # Evaluation datasets & configs
├── pyproject.toml             # Python dependencies
└── deployment.yaml            # Cloud Run Knative configurations
```

---

## 🛠️ Setup & Local Run

### Prerequisites
*   Install **uv**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
*   Install **agents-cli**: `uv tool install google-agents-cli`

### 1. Install Dependencies
```bash
agents-cli install
```

### 2. Run Unit Tests
```bash
uv run pytest tests/unit/test_agent.py
```

### 3. Run Evaluation Suite
Run inference and grading over the capstone dataset:
```bash
agents-cli eval run --dataset tests/eval/datasets/eval-dataset.json --config tests/eval/eval_config.yaml
```

### 4. Run Web Dashboard
```bash
uv run uvicorn dashboard.main:app --reload --port 8080
```
Open `http://localhost:8080` to view the active sessions and manage pending approvals.

---

## 📊 Evaluation Results

| Metric Name | Value / Score |
|:---|:---|
| **`final_response_quality_v1`** | **0.8472** |
| **`safety_v1`** | **1.0000** |
| **`hierarchy_compliance` (Custom)** | **5.0000 / 5** |
| **`keypoint_alignment` (Custom)** | **5.0000 / 5** |
| **`semantic_drift_check` (Custom)** | **5.0000 / 5** |
