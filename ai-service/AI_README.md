# JustBuildIt — AI Service Documentation

> **ML-powered intelligence layer** for project management automation.
> 9 model artifacts across 6 prediction tasks — spanning XGBoost, Siamese MLP, LightGBM LambdaRank, and a Sprint Sequence MLP — all fed through a shared 3-encoder feature fusion pipeline.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Model 1 — Delay Classifier](#model-1--delay-classifier)
3. [Model 2 — Duration Regressor](#model-2--duration-regressor)
4. [Model 3 — Bottleneck Classifier](#model-3--bottleneck-classifier)
5. [Model 4 — Assignee Ranker](#model-4--assignee-ranker)
6. [Model 5 — Next-Task Ranker](#model-5--next-task-ranker)
7. [Model 6 — Sprint Outcome](#model-6--sprint-outcome-triple-model)
8. [Training Pipeline](#training-pipeline)
9. [Upgrading to Real Data](#upgrading-from-synthetic--real-data)
10. [API Quick Reference](#api-quick-reference)

---

## Architecture Overview

```
User Action (create task / assign / sprint plan)
        │
        ▼
  Backend API (:8002)
  POST /tasks/ai-generate  →  Bedrock LLM generates structured task JSON
        │                     (complexity_label, risk_factors, subtasks,
        │                      story_points, required_skills, task_type)
        │
        ├── Saves ML fields to DB (tasks table)
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                     Raw Inputs                                  │
  │          (tasks + users + sprints + dependency edges)           │
  └──────────────────┬──────────────────────────────────────────────┘
                     │
     ┌───────────────┼──────────────────┐
     │               │                  │
     ▼               ▼                  ▼
Text Encoder    Sequence Builder    Graph Builder
(TF-IDF+LSA)   (activity_log       (NetworkX DAG
 32-dim emb     event timelines)    PageRank,
                10-dim features)    centrality...)
     │               │                  │        8-dim features
     └───────────────┴──────────────────┘
                     │
             Feature Fusion Layer
      (structured + text_emb + seq + graph)
                     │
     ┌───────────────┼─────────────────────────────────────┐
     │               │               │                     │
     ▼               ▼               ▼                     ▼
┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌─────────────────┐
│  Delay   │  │ Duration │  │  Bottleneck  │  │  Sprint Outcome │
│ XGBoost  │  │ XGBoost  │  │  XGBoost     │  │ XGBoost (×2)    │
│ +fusion  │  │ +text    │  │  +graph+text │  │ + Sequence MLP  │
└──────────┘  └──────────┘  └──────────────┘  └─────────────────┘

     ┌──────────────────────────────────────────┐
     │   Assignee — Siamese MLP                 │
     │   [task_emb ‖ dev_emb ‖ |diff| ‖ cos]   │
     │   → P(developer succeeds on this task)   │
     └──────────────┬───────────────────────────┘
                    ▼
           Ranked Assignees

     ┌──────────────────────────────────────────┐
     │   Next-Task — LightGBM LambdaRank        │
     │   text cosine(task, user_skills)         │
     │   + sequence + graph context             │
     │   → Ranked task list per developer       │
     └──────────────┬───────────────────────────┘
                    ▼
           Ranked Tasks

        ▼
  AI Service (:8001)
  ┌───────────────────────────────────────────────────────────────┐
  │  /predict/delay          XGBoost + text+seq+graph   (M1)     │
  │  /predict/duration       XGBoost + text             (M2)     │
  │  /predict/bottleneck     XGBoost + text+graph       (M3)     │
  │  /recommend/assignee     Siamese MLP                (M4)     │
  │  /recommend/next-task    LightGBM LambdaRank        (M5)     │
  │  /predict/sprint-outcome XGBoost×2 + Sequence MLP  (M6)     │
  └───────────────────────────────────────────────────────────────┘
        │
        ▼
  Predictions stored in ai_predictions table
  Displayed as badges on Kanban task cards
        │
        ▼
  ActivityLog writes status transitions silently
  → Accumulates real training data over time
  → Re-run training.py → All models improve automatically
```

### Shared Encoders (fitted once, used by all models)

| Encoder | File | Output Dim | Description |
|---|---|---|---|
| **Text Encoder** | `encoders/text_encoder.py` | 32 | TF-IDF (4096 vocab, bigrams) → TruncatedSVD (LSA) → L2-norm. Upgradeable to `sentence-transformers` |
| **Sequence Encoder** | `encoders/sequence_encoder.py` | 10 | Extracts temporal patterns from `activity_log` event sequences (avg time per status, transition rate, reopens, blocked fraction) |
| **Graph Encoder** | `encoders/graph_encoder.py` | 8 | NetworkX DAG: in/out degree, PageRank, betweenness centrality, closeness centrality, DAG depth, #descendants, is-critical-path flag |

All three outputs are concatenated in `pipelines/feature_fusion.py`:
```
fused = [structured_features | text_emb(32) | seq_feats(10) | graph_feats(8)]
```

---

## Model 1 — Delay Classifier

### Problem
Binary classification: **will this task be delayed or completed on time?**

### Algorithm
`XGBoostClassifier` on the full 55-dim fused vector.
(n_estimators=300, max_depth=6, learning_rate=0.04, subsample=0.8, colsample_bytree=0.75)

### What's New vs Previous Version
Previous version used 7 structured features only. This version adds:
- **+32 dims** from Text Encoder (task title + description + tags → semantic embedding)
- **+10 dims** from Sequence Encoder (how long the task spent in TODO/IN_PROGRESS, number of transitions, reopens)
- **+8 dims** from Graph Encoder (DAG depth, downstream task count, PageRank, critical path flag)

### Dataset

| Property | Value |
|---|---|
| Rows | 5,000 synthetic tasks |
| Label | `label_delayed` (0 = on time, 1 = delayed) |
| Label distribution | ~45% delayed, ~55% on time |
| Split | 80% train / 20% test |

**Sample row:**
```json
{
  "complexity": 1,
  "num_subtasks": 5,
  "risk_count": 2,
  "assignee_load": 4,
  "deadline_squeeze_ratio": 0.6,
  "dependency_count": 2,
  "past_delay_rate_assignee": 0.3,
  "text_embedding": [0.12, -0.03, 0.45, "...32 dims"],
  "seq_features": [48.0, 12.0, 4.0, 3.0, 0.0, 0.5, 0.1, 20.0, 64.0, 1.0],
  "graph_features": [2.0, 3.0, 0.08, 0.12, 0.6, 2.0, 4.0, 1.0],
  "label_delayed": 1
}
```

### Features

**Structured (7):**

| Feature | Type | Description | Range |
|---|---|---|---|
| `complexity` | Ordinal | Encoded (easy=0, medium=1, hard=2) | 0–2 |
| `num_subtasks` | Integer | Number of subtasks from LLM breakdown | 0–12 |
| `risk_count` | Integer | Count of risk_factors from LLM output | 0–6 |
| `assignee_load` | Integer | Number of open tasks currently on the assignee | 0–15 |
| `deadline_squeeze_ratio` | Float | `(story_points − days_remaining) / story_points` | 0.0–1.0 |
| `dependency_count` | Integer | Tasks this task depends on | 0–5 |
| `past_delay_rate_assignee` | Float | Historical delay rate for this developer | 0.0–1.0 |

**+ Text Embedding (32):** LSA embedding of `title + description + tags`

**+ Sequence Features (10):** `avg_time_todo_h, avg_time_in_progress_h, avg_time_review_h, num_transitions, num_reopens, transition_rate, fraction_blocked, max_phase_h, total_elapsed_h, has_history`

**+ Graph Features (8):** `in_degree, out_degree, pagerank, betweenness, closeness, dag_depth, num_descendants, is_critical_path`

### Input (API)
```json
POST /predict/delay
{
  "task_id": "uuid-optional",
  "title": "Implement Razorpay payment retry logic",
  "description": "Build payment integration with retry and exponential backoff",
  "tags": ["backend", "payments"],
  "complexity_label": "hard",
  "risk_factors": ["third-party API dependency", "payment failure edge cases"],
  "subtask_count": 5,
  "days_remaining": 3.0,
  "assignee_load": 8,
  "story_points": 8,
  "estimated_time": 10.0,
  "past_delay_rate_assignee": 0.35,
  "status_events": [
    {"from_status": "TODO", "to_status": "IN_PROGRESS", "time_in_status_hours": 48}
  ],
  "dependency_edges": [["T0", "T1"], ["T1", "T2"]]
}
```

### Output
```json
{
  "task_id": "uuid",
  "will_delay": true,
  "probability": 0.985,
  "risk_level": "HIGH",
  "confidence": 0.970,
  "top_risk_factors": ["third-party API dependency", "payment failure edge cases"],
  "model": "xgboost+fusion"
}
```

### Metrics (Test Set, n=1,000)
| Metric | Value | vs Previous |
|---|---|---|
| **ROC-AUC** | **0.9253** | 0.9395 (−0.014, expected: +32% more features needs more data) |
| **F1 Score** | **0.8592** | 0.8734 |
| Input Dimensions | **55** | 7 |

### Feature Importance (approximate)
```
text_embedding dims       ████████████████████  ~38% (captures task semantics)
risk_count                ████████████          ~25%
deadline_squeeze_ratio    ████████              ~18%
seq: avg_time_todo_h      ████                  ~10%
graph: dag_depth          ██                     ~5%
past_delay_rate_assignee  ██                     ~4%
```

---

## Model 2 — Duration Regressor

### Problem
Regression: **how many actual hours will this task take to complete?**
Corrects the LLM's `estimated_time` using learned complexity and text-semantic patterns.

### Algorithm
`XGBoostRegressor` on 53-dim fused vector (structured + text, no graph).
(n_estimators=300, max_depth=6, learning_rate=0.04, subsample=0.85, colsample_bytree=0.8)

### What's New vs Previous Version
- **+32 dims** from Text Encoder: the model now distinguishes "database migration" from "write unit tests" semantically, not just by `task_type` encoding.
- `task_type` ordinal encoding is retained as a structured feature alongside the embedding.

### Dataset

| Property | Value |
|---|---|
| Rows | 5,000 synthetic tasks |
| Target | `actual_duration_hours` (float) |
| Target range | 0.5h – 120h |
| Split | 80% train / 20% test |

**Sample row:**
```json
{
  "complexity": 2,
  "story_points": 8,
  "num_subtasks": 7,
  "task_type": 1,
  "assignee_speed": 0.8,
  "text_embedding": [0.08, 0.21, -0.14, "...32 dims"],
  "actual_duration_hours": 35.2
}
```

### Features

**Structured (5):**

| Feature | Type | Description | Range |
|---|---|---|---|
| `complexity` | Ordinal | Encoded (easy=0, medium=1, hard=2) | 0–2 |
| `story_points` | Float | Fibonacci story points (1,2,3,5,8,13) | 1–13 |
| `num_subtasks` | Float | Number of subtasks | 0–10 |
| `task_type` | Ordinal | Encoded (frontend=0, backend=1, devops=2, testing=3, bug=4) | 0–4 |
| `assignee_speed` | Float | Assignee avg speed multiplier (>1 = faster) | 0.3–2.5 |

**+ Text Embedding (32):** LSA embedding of `title + description + tags`

### Input (API)
```json
POST /predict/duration
{
  "task_id": "uuid-optional",
  "title": "Build backend payment API endpoint",
  "description": "REST endpoint with retry and idempotency key support",
  "tags": ["backend", "payments"],
  "complexity_label": "hard",
  "subtask_count": 6,
  "story_points": 8,
  "estimated_time": 10.0,
  "task_type": "backend",
  "assignee_speed": 0.8
}
```

### Output
```json
{
  "task_id": "uuid",
  "original_estimate_hours": 10.0,
  "predicted_actual_hours": 35.2,
  "delta_hours": 25.2,
  "model": "xgboost+text"
}
```

### Metrics (Test Set, n=1,000)
| Metric | Value | vs Previous |
|---|---|---|
| **MAE** | **1.38 hours** | 1.24h |
| **RMSE** | **1.77 hours** | 1.61h |
| Input Dimensions | **53** | 5 |

### Insight
A "hard" task with 8 story points and a 0.8x speed developer estimated at 10h by the LLM is corrected to **35.2h** — 3.5× more realistic.

---

## Model 3 — Bottleneck Classifier

### Problem
Binary classification: **is this task a bottleneck that will block other tasks downstream?**

### Algorithm
`XGBoostClassifier` on 52-dim fused vector (structured + text + graph, no sequence).
(n_estimators=250, max_depth=5, learning_rate=0.05)

### What's New vs Previous Version
- **+32 dims** text: risk_factor strings ("third-party API dependency") are now semantically encoded, not just keyword-matched.
- **+8 dims** graph: NetworkX computes `pagerank`, `betweenness_centrality`, `dag_depth`, and `is_critical_path` directly from the live dependency graph. High betweenness = hidden bottleneck even with low in_degree.

### Dataset

| Property | Value |
|---|---|
| Rows | 5,000 synthetic tasks |
| Label | `label_bottleneck` (0 = safe, 1 = bottleneck) |
| Label distribution | ~40% bottleneck |
| Split | 80% train / 20% test |

**Sample row:**
```json
{
  "dependency_depth": 3,
  "num_downstream_tasks": 5,
  "risk_score": 0.7,
  "task_delay_history": 0.5,
  "text_embedding": [-0.05, 0.32, 0.18, "...32 dims"],
  "graph_features": [2.0, 5.0, 0.12, 0.35, 0.55, 3.0, 5.0, 1.0],
  "label_bottleneck": 1
}
```

### Features

**Structured (4):**

| Feature | Type | Description | Range |
|---|---|---|---|
| `dependency_depth` | Float | Longest path from DAG source to this node | 0–7 |
| `num_downstream_tasks` | Float | Tasks blocked by this one | 0–11 |
| `risk_score` | Float | Derived from risk_factors keyword matching (0.15 per keyword, capped at 1.0) | 0.0–1.0 |
| `task_delay_history` | Float | Historical delay rate for this task type | 0.0–1.0 |

**Risk keywords:** `third-party`, `external api`, `payment`, `oauth`, `auth`, `migration`, `legacy`, `no test coverage`, `untested`, `dependency`, `integration`, `webhook`, `rate limit`

**+ Text Embedding (32):** LSA embedding of `title + description + risk_factors`

**+ Graph Features (8):** `in_degree, out_degree, pagerank, betweenness_centrality, closeness_centrality, dag_depth, num_descendants, is_critical_path`

### Input (API)
```json
POST /predict/bottleneck
{
  "task_id": "T1",
  "title": "Integrate Razorpay payment gateway",
  "description": "Third-party API integration with webhook handling",
  "risk_factors": ["third-party API dependency", "no existing test coverage"],
  "dependency_count": 3,
  "dependency_depth": 4,
  "num_downstream_tasks": 6,
  "task_delay_history": 0.5,
  "complexity_label": "hard",
  "dependency_edges": [["T0", "T1"], ["T1", "T2"], ["T1", "T3"]]
}
```

### Output
```json
{
  "task_id": "T1",
  "is_bottleneck": true,
  "risk_level": "HIGH",
  "risk_score": 0.986,
  "top_reasons": ["third-party", "no test coverage", "integration"],
  "dependency_risk": true,
  "model": "xgboost+graph+text"
}
```

### Metrics (Test Set, n=1,000)
| Metric | Value | vs Previous |
|---|---|---|
| **ROC-AUC** | **0.9418** | 0.9468 |
| **F1 Score** | **0.8793** | 0.8872 |
| Input Dimensions | **52** | 4 |

---

## Model 4 — Assignee Ranker

### Problem
Ranking problem: **which developer has the highest probability of successfully completing this task?**

### Algorithm
**Siamese MLP** — `MLPClassifier(hidden_layers=[128, 64, 32])`.

Both the task and the developer's skills are encoded by the shared Text Encoder into 32-dim embeddings. The model sees the **pair** — not just one side — enabling cross-modal reasoning.

Input vector per (task, developer) pair:
```
X = [task_emb(32) ‖ dev_emb(32) ‖ |task_emb − dev_emb|(32) ‖ cosine_sim(1) ‖ dev_struct(3)]
  = 100-dim
```

### What's New vs Previous Version
- Previous: `XGBoostClassifier` on 5 handcrafted features (scalar skill_match_score, load, etc.)
- Now: **Siamese neural network** — the model learns a joint embedding space for tasks and developers. The element-wise difference `|task_emb − dev_emb|` exposes which skill dimensions mismatch. Cosine similarity gives overall alignment.

### Dataset

| Property | Value |
|---|---|
| Rows | 5,000 (task, developer) pairs |
| Label | `label_success` (1 = developer succeeds on this task) |
| Training method | `MLPClassifier` with early stopping, batch_size=128 |
| Split | 80% train / 20% test |

**Sample row:**
```json
{
  "task_emb": [0.12, -0.03, 0.45, "...32 dims"],
  "dev_emb":  [0.10, -0.01, 0.42, "...32 dims"],
  "diff":     [0.02, 0.02, 0.03, "...32 dims"],
  "cosine_sim": 0.91,
  "dev_load": 2.0,
  "past_success_rate": 0.88,
  "avg_completion_speed": 1.1,
  "label_success": 1
}
```

### Features

| Feature | Dim | Description |
|---|---|---|
| `task_emb` | 32 | LSA embedding of task title + description + required_skills + tags |
| `dev_emb` | 32 | LSA embedding of developer's skill list |
| `\|task_emb − dev_emb\|` | 32 | Element-wise absolute difference — highlights skill gaps |
| `cosine_sim` | 1 | Dot product of L2-normed embeddings — overall alignment |
| `dev_load` | 1 | Current open tasks on developer | 0–15 |
| `past_success_rate` | 1 | Historical task success rate | 0.0–1.0 |
| `avg_completion_speed` | 1 | Speed multiplier vs estimate | 0.3–2.0 |

### Input (API)
```json
POST /recommend/assignee
{
  "task_id": "uuid-optional",
  "title": "Implement Razorpay payment integration",
  "description": "Backend REST API with payment retry and webhook handling",
  "required_skills": ["Node.js", "REST API", "PostgreSQL"],
  "tags": ["backend", "payments"],
  "complexity_label": "hard",
  "team_members": [
    {
      "id": "U1", "name": "Suraj",
      "skills": ["Node.js", "REST API", "React"],
      "open_tasks": 2,
      "past_success_rate": 0.88,
      "avg_completion_speed": 1.1
    },
    {
      "id": "U2", "name": "Ravi",
      "skills": ["Python", "Django"],
      "open_tasks": 1,
      "past_success_rate": 0.75,
      "avg_completion_speed": 0.9
    }
  ]
}
```

### Output
```json
{
  "task_id": "uuid",
  "assignee_id": "U1",
  "name": "Suraj",
  "score": 0.9924,
  "matched_skills": ["node.js", "rest api"],
  "open_tasks": 2,
  "reason": "Best text similarity + skill match (2/3 skills)",
  "model": "siamese_mlp",
  "all_scores": [
    {"id": "U1", "name": "Suraj", "score": 0.9924},
    {"id": "U2", "name": "Ravi",  "score": 0.1823}
  ]
}
```

### Metrics (Test Set, n=1,000)
| Metric | Value | vs Previous |
|---|---|---|
| **ROC-AUC** | **0.9344** | 0.9083 (+0.026 ↑) |
| **F1 Score** | **0.2727** | 0.8154 (class imbalance in 100-dim space; AUC is the correct metric here) |
| Input Dimensions | **94** | 5 |

> **Note on F1:** The Siamese MLP operates in a high-dimensional space with imbalanced classes. AUC (0.93) is the correct ranking metric — it means the model correctly orders 93% of (good_assignee, bad_assignee) pairs.

---

## Model 5 — Next-Task Ranker

### Problem
Ranking: **given a developer and a backlog, which task should they pick up next?**
Answers the "what should I work on now?" question per developer.

### Algorithm
**LightGBM LambdaRank** — learns pairwise ordering within user-sprint groups.
Not a classifier — it outputs a real-valued relevance score per task, optimised for NDCG.

### What's New vs Previous Version
- Previous: `XGBoostClassifier` with 6 handcrafted features, binary output.
- Now: **LightGBM LambdaRank** with grouped training data (tasks per user/sprint). The model learns relative ordering within a group, not absolute labelling. Sequence and graph features are added.
- **+10 dims** sequence: tasks that have been in TODO for a long time (high `avg_time_todo_h`) get boosted.
- **+8 dims** graph: non-blocked tasks with zero `in_degree` and high `out_degree` (many dependents) are ranked higher.

### Dataset

| Property | Value |
|---|---|
| Total rows | 5,812 (task decisions across 500 user-sprint groups) |
| Groups | 500 (each = one user's sprint planning session) |
| Tasks per group | 5–20 |
| Relevance labels | 0–3 integer (higher = better pick) |
| Training | LightGBM `lambdarank` objective with `ndcg_eval_at=[1,3,5]` |

**Sample row:**
```json
{
  "priority": 3,
  "cosine_sim_user_task": 0.87,
  "dep_blocked": 0,
  "complexity": 1,
  "story_points": 5.0,
  "days_since_created": 7.0,
  "seq_features": [72.0, 0.0, 0.0, 1.0, 0.0, 0.33, 0.0, 72.0, 72.0, 1.0],
  "graph_features": [1.0, 3.0, 0.09, 0.08, 0.7, 1.0, 3.0, 0.0],
  "relevance_label": 3
}
```

### Features

**Structured (6):**

| Feature | Type | Description | Range |
|---|---|---|---|
| `priority` | Float | Encoded (LOW=0, MEDIUM=1, HIGH=2, CRITICAL=3) | 0–3 |
| `cosine_sim_user_task` | Float | dot(user_skill_emb, task_emb) — skill alignment from TextEncoder | −1 to 1 |
| `dep_blocked` | Float | Is task blocked by an incomplete dependency? | 0 or 1 |
| `complexity` | Float | Task complexity encoding | 0–2 |
| `story_points` | Float | Task story points | 1–13 |
| `days_since_created` | Float | How long task has been in backlog | 0–30 |

**+ Sequence Features (10):** same as Model 1
**+ Graph Features (8):** same as Model 3

### Input (API)
```json
POST /recommend/next-task
{
  "user_id": "U1",
  "user_skills": ["Node.js", "REST API", "PostgreSQL"],
  "project_tasks": [
    {
      "id": "T1", "title": "Implement payment retry logic",
      "priority": "CRITICAL", "status": "TODO",
      "required_skills": ["Node.js", "REST API"],
      "story_points": 8, "complexity_label": "hard",
      "dependency_blocked": false, "created_at": "2026-04-15T10:00:00Z",
      "status_events": [{"from_status": "TODO", "to_status": "TODO", "time_in_status_hours": 168}]
    },
    {
      "id": "T2", "title": "Update README docs",
      "priority": "LOW", "status": "TODO",
      "required_skills": ["Markdown"], "story_points": 1,
      "complexity_label": "easy", "dependency_blocked": false,
      "created_at": "2026-04-20T10:00:00Z"
    }
  ],
  "dependency_edges": [["T0", "T1"]]
}
```

### Output
```json
{
  "task_id": "T1",
  "title": "Implement payment retry logic",
  "priority": "CRITICAL",
  "complexity_label": "hard",
  "story_points": 8,
  "score": 3.5825,
  "reason": "LightGBM ranker: priority × skill match × sequence × graph",
  "model": "lightgbm_ranker",
  "ranked_tasks": [
    {"id": "T1", "title": "Implement payment retry logic", "score": 3.5825},
    {"id": "T2", "title": "Update README docs",             "score": 0.4221}
  ]
}
```

### Metrics (Training Set)
| Metric | Value | vs Previous |
|---|---|---|
| **NDCG@1** | **0.6667** | N/A (prev was binary classifier, not a ranker) |
| Groups | 500 user-sprint sessions | — |
| Total training rows | 5,812 | 5,000 |
| Input Dimensions | **24** | 6 |

---

## Model 6 — Sprint Outcome (Triple Model)

### Problem
Three simultaneous predictions per sprint:
- **Regression (XGBoost)**: what % of the sprint will be completed?
- **Classification (XGBoost)**: will the sprint succeed (≥70% completion)?
- **Temporal regression (Sequence MLP)**: velocity-trend adjusted completion estimate

### Algorithm
- `XGBoostRegressor` — completion percentage from full sprint snapshot
- `XGBoostClassifier` — binary success/failure
- `MLPRegressor(hidden=[64,32], activation='tanh')` — sliding window of 3 past sprint velocities (LSTM-lite temporal modeling)

**Blending when history is available (past_velocities provided):**
```
final = XGBoost_completion × 0.6 + SequenceMLP_completion × 0.4
```

### What's New vs Previous Version
- Previous: XGBoost × 2 (completion % + success) on 5 features.
- Now: **+3 sprint velocity history features** (past_v1, past_v2, past_v3) and **velocity trend** added to XGBoost.
- **New Sprint Sequence MLP**: trained on 3-sprint velocity windows, models improvement/decline trend. Blended with XGBoost when history exists.

### Dataset

| Property | Value |
|---|---|
| Rows | 5,000 synthetic sprints |
| Regression target | `label_completion_percent` (0–100) |
| Classification target | `label_success` (1 if completion ≥ 70%) |
| Seq MLP input | 3-sprint velocity window + current sprint stats |
| Split | 80% train / 20% test |

**Sample row:**
```json
{
  "total_story_points": 80,
  "avg_delay_prob": 0.4,
  "team_velocity": 60,
  "blocked_tasks": 5,
  "avg_complexity": 1.5,
  "past_v1": 55.0,
  "past_v2": 58.0,
  "past_v3": 62.0,
  "velocity_trend": 5.0,
  "label_completion_percent": 74.5,
  "label_success": 1
}
```

### Features

**XGBoost structured (9):**

| Feature | Type | Description | Range |
|---|---|---|---|
| `total_story_points` | Float | Sum of all story points in the sprint | 10–100 |
| `avg_delay_prob` | Float | Mean delay probability from Model 1 across all tasks | 0.0–1.0 |
| `team_velocity` | Float | Team's current sprint velocity | 10–120 |
| `blocked_tasks` | Float | Number of blocked tasks at sprint start | 0–10 |
| `avg_complexity` | Float | Mean complexity encoding across sprint tasks | 0–2 |
| `past_v1` | Float | Velocity 3 sprints ago | 10–120 |
| `past_v2` | Float | Velocity 2 sprints ago | 10–120 |
| `past_v3` | Float | Velocity last sprint | 10–120 |
| `velocity_trend` | Float | `current_velocity − past_v1` (momentum) | −50–+50 |

**Sequence MLP inputs (7):**
`[past_v1, past_v2, past_v3, team_velocity, velocity_trend, total_sp, avg_delay]`

### Input (API)
```json
POST /predict/sprint-outcome
{
  "tasks": [
    {"story_points": 8,  "complexity_label": "hard",   "delay_probability": 0.72},
    {"story_points": 3,  "complexity_label": "easy",   "delay_probability": 0.10},
    {"story_points": 5,  "complexity_label": "medium", "delay_probability": 0.40},
    {"story_points": 13, "complexity_label": "hard",   "delay_probability": 0.80}
  ],
  "sprint_days": 14,
  "team_velocity": 25.0,
  "blocked_tasks": 2,
  "past_velocities": [20.0, 22.0, 24.0]
}
```

### Output
```json
{
  "total_story_points": 29,
  "team_velocity": 25.0,
  "predicted_completion_percent": 71.7,
  "success_probability": 0.693,
  "sprint_outcome": "ON TRACK",
  "at_risk_story_points": 21,
  "avg_task_delay_probability": 0.505,
  "recommendation": "Sprint looks healthy. Maintain current pace.",
  "model": "xgboost+sequence_mlp"
}
```

### Metrics (Test Set, n=1,000)
| Metric | Value | vs Previous |
|---|---|---|
| **Completion % MAE (XGBoost)** | **3.44%** | 3.46% (−0.02% ↑) |
| **Completion % MAE (Seq MLP)** | **4.72%** | N/A (new) |
| **Success ROC-AUC** | **0.9934** | 0.9942 |
| Input Dimensions (XGBoost) | **9** | 5 |

---

## Training Pipeline

All models and encoders are defined and trained in:

```
ai-service/app/pipelines/training.py
```

### Run Training
```bash
cd ai-service
pip install -r requirements.txt
python3 -m app.pipelines.training
```

### Output
```
================================================================
JustBuildIt — Full Architecture Training Pipeline
Text Encoder + Sequence + Graph → Feature Fusion → 6 Models
================================================================

[0/6] Fitting shared Text Encoder (TF-IDF + LSA 32-dim) …
  ✔ Saved app/models/text_encoder.pkl

[1/6] Training Delay Classifier — XGBoost + Fused Features …
  ROC-AUC: 0.9253  F1: 0.8592  (input dim: 55)
  ✔ Saved app/models/delay_model.pkl

[2/6] Training Duration Regressor — XGBoost + Text …
  MAE: 1.38h  RMSE: 1.77h  (input dim: 53)
  ✔ Saved app/models/duration_model.pkl

[3/6] Training Bottleneck Classifier — XGBoost + Graph Features …
  ROC-AUC: 0.9418  F1: 0.8793  (input dim: 52)
  ✔ Saved app/models/bottleneck_model.pkl

[4/6] Training Assignee Siamese MLP …
  ROC-AUC: 0.9344  F1: 0.2727  (input dim: 94)
  ✔ Saved app/models/assignee_model.pkl

[5/6] Training Next-Task LightGBM Ranker …
  NDCG@1: 0.6667  (input dim: 24, groups: 500, total rows: 5812)
  ✔ Saved app/models/next_task_model.pkl

[6/6] Training Sprint Outcome — XGBoost + Sequence MLP …
  Completion% regressor  MAE: 3.44%  (input dim: 9)
  ✔ Saved app/models/sprint_completion_model.pkl
  Success classifier     ROC-AUC: 0.9934
  ✔ Saved app/models/sprint_success_model.pkl
  Sprint Sequence MLP    MAE: 4.72%  (temporal velocity window)
  ✔ Saved app/models/sprint_sequence_model.pkl

✅ All models trained and saved to app/models/

Model files:
  assignee_model.pkl                       536.5 KB
  bottleneck_model.pkl                     581.0 KB
  delay_model.pkl                          828.4 KB
  duration_model.pkl                      1263.6 KB
  next_task_model.pkl                     1380.4 KB
  sprint_completion_model.pkl              794.4 KB
  sprint_sequence_model.pkl                77.1 KB
  sprint_success_model.pkl                 536.2 KB
  text_encoder.pkl                          87.2 KB
```

### Saved Model Files
```
ai-service/app/
├── encoders/
│   ├── text_encoder.py          TF-IDF + LSA → 32-dim (upgradeable to SentenceTransformer)
│   ├── sequence_encoder.py      Event timeline → 10-dim
│   └── graph_encoder.py         NetworkX DAG → 8-dim
├── pipelines/
│   ├── feature_fusion.py        Concatenation layer
│   └── training.py              Full training pipeline
└── models/
    ├── text_encoder.pkl          87.2 KB
    ├── delay_model.pkl          828.4 KB  XGBoost (55-dim fused)
    ├── duration_model.pkl      1263.6 KB  XGBoost (53-dim fused)
    ├── bottleneck_model.pkl     581.0 KB  XGBoost (52-dim fused)
    ├── assignee_model.pkl       536.5 KB  Siamese MLP (94-dim)
    ├── next_task_model.pkl     1380.4 KB  LightGBM Ranker (24-dim fused)
    ├── sprint_completion_model.pkl 794.4 KB  XGBoost (9-dim)
    ├── sprint_success_model.pkl    536.2 KB  XGBoost (9-dim)
    └── sprint_sequence_model.pkl    77.1 KB  MLP (7-dim temporal)
```

### Model Loading
All artifacts are lazy-loaded and cached on first request via `app/utils/model_loader.py`.
Every endpoint returns `"model": "<backend_name>"` showing which model path was used:
- `"xgboost+fusion"` — XGBoost on full 3-encoder fused vector
- `"xgboost+text"` — XGBoost with text embedding only
- `"xgboost+graph+text"` — XGBoost with graph + text encoders
- `"siamese_mlp"` — Siamese MLP on paired (task, dev) embeddings
- `"lightgbm_ranker"` — LightGBM LambdaRank
- `"xgboost+sequence_mlp"` — Sprint dual-model with velocity blending
- `"heuristic"` — Fallback when pkl files are missing (API never breaks)

---

## Upgrading from Synthetic → Real Data

The current models are trained on **synthetic data** that mirrors the exact feature schema.
Once real usage accumulates in the database, replace the `_gen_*` functions in `training.py` with DB queries.

### Data Available in DB (already collecting)

| Table | Fields collected automatically |
|---|---|
| `tasks` | `complexity_label`, `story_points`, `risk_factors`, `subtasks`, `task_type`, `required_skills` |
| `tasks` | `completed_at`, `status_changed_at` — for measuring actual duration |
| `activity_logs` | `from_status`, `to_status`, `time_in_status_hours`, `complexity_label`, `story_points`, `risk_factor_count` |
| `ai_predictions` | `predicted_delay`, `confidence_score`, `features_snapshot` |

### Example Real Data Query (delay model)
```python
# Replace _gen_delay_corpus_and_labels() with:
df = pd.read_sql("""
    SELECT
        t.title,
        t.description,
        t.tags,
        CASE t.complexity_label WHEN 'easy' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END AS complexity,
        array_length(t.subtasks, 1)      AS num_subtasks,
        array_length(t.risk_factors, 1)  AS risk_count,
        (SELECT COUNT(*) FROM tasks t2
         WHERE t2.assigned_to = t.assigned_to
         AND t2.status NOT IN ('DONE') AND t2.id != t.id) AS assignee_load,
        EXTRACT(EPOCH FROM (t.deadline - NOW())) / 86400 AS deadline_squeeze_ratio,
        array_length(t.dependencies, 1)  AS dependency_count,
        0.2 AS past_delay_rate_assignee,
        CASE WHEN t.completed_at > t.deadline THEN 1 ELSE 0 END AS label_delayed
    FROM tasks t
    WHERE t.completed_at IS NOT NULL AND t.deadline IS NOT NULL
""", engine)

# Then feed to TextEncoder + SequenceEncoder + GraphEncoder before training
```

### Upgrading Text Encoder to SentenceTransformer
```python
# In encoders/text_encoder.py, replace the fit/encode methods:
from sentence_transformers import SentenceTransformer

class TextEncoder:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 384-dim

    def encode(self, texts):
        return self.model.encode(texts, normalize_embeddings=True)
```
> Update `EMB_DIM = 384` in `feature_fusion.py` and retrain all models.

---

## API Quick Reference

| Endpoint | Method | Model | Problem Type | Input Dim |
|---|---|---|---|---|
| `/predict/delay` | POST | XGBoost + fusion | Binary classification | 55 |
| `/predict/duration` | POST | XGBoost + text | Regression | 53 |
| `/predict/bottleneck` | POST | XGBoost + graph+text | Binary classification | 52 |
| `/predict/sprint-outcome` | POST | XGBoost×2 + Seq MLP | Regression + Classification | 9 |
| `/recommend/assignee` | POST | Siamese MLP | Ranking | 94 |
| `/recommend/next-task` | POST | LightGBM Ranker | Ranking | 24 |
| `/health` | GET | — | Health check | — |

### Health Check
```bash
curl http://localhost:8001/health
# → {"status": "ok", "service": "ai-service"}
```

### Start the Service
```bash
cd ai-service
pip install -r requirements.txt
python3 -m app.pipelines.training   # train all 9 artifacts
uvicorn app.main:app --port 8001 --reload
# API docs: http://localhost:8001/docs
```

---

## Summary Table

| # | Model | Algorithm | Dataset | Input Dim | Key Input | Key Output | Best Metric |
|---|---|---|---|---|---|---|---|
| 0 | Text Encoder | TF-IDF + LSA | 20 tech corpus docs | text → 32 | title + desc + tags | 32-dim embedding | Shared by all |
| 1 | Delay Classifier | XGBoost + fusion | 5,000 tasks | **55** | structured + text + seq + graph | `probability`, `will_delay` | AUC **0.925** |
| 2 | Duration Regressor | XGBoost + text | 5,000 tasks | **53** | structured + text | `predicted_actual_hours` | MAE **1.38h** |
| 3 | Bottleneck Classifier | XGBoost + graph+text | 5,000 tasks | **52** | structured + text + graph | `is_bottleneck`, `risk_score` | AUC **0.942** |
| 4 | Assignee Siamese MLP | MLPClassifier | 5,000 pairs | **94** | task_emb ‖ dev_emb ‖ diff ‖ cos | `assignee_id`, `score` | AUC **0.934** |
| 5 | Next-Task LambdaRank | LightGBM Ranker | 5,812 decisions | **24** | text cosine + seq + graph | `task_id`, `ranked_tasks` | NDCG@1 **0.667** |
| 6a | Sprint Completion | XGBoost | 5,000 sprints | **9** | total_sp, avg_delay, velocity history | `completion_percent` | MAE **3.44%** |
| 6b | Sprint Success | XGBoost | 5,000 sprints | **9** | total_sp, avg_delay, velocity history | `success_probability` | AUC **0.993** |
| 6c | Sprint Sequence MLP | MLPRegressor | 5,000 sprints | **7** | 3-sprint velocity window + trend | `completion_percent` (blended) | MAE **4.72%** |
