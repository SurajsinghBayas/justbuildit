# JustBuildIt — AI Service Documentation

> **ML-powered intelligence layer** for project management automation.
> 6 XGBoost models that predict delays, estimate duration, detect bottlenecks, recommend assignees, suggest next tasks, and forecast sprint outcomes.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Model 1 — Delay Classifier](#model-1--delay-classifier)
3. [Model 2 — Duration Regressor](#model-2--duration-regressor)
4. [Model 3 — Bottleneck Classifier](#model-3--bottleneck-classifier)
5. [Model 4 — Assignee Ranker](#model-4--assignee-ranker)
6. [Model 5 — Next-Task Ranker](#model-5--next-task-ranker)
7. [Model 6 — Sprint Outcome](#model-6--sprint-outcome-dual-model)
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
  AI Service (:8001)  ←  Receives structured task features
  ┌───────────────────────────────────────────────────────┐
  │  /predict/delay          XGBoostClassifier   (M1)     │
  │  /predict/duration       XGBoostRegressor    (M2)     │
  │  /predict/bottleneck     XGBoostClassifier   (M3)     │
  │  /recommend/assignee     XGBoostClassifier   (M4)     │
  │  /recommend/next-task    XGBoostClassifier   (M5)     │
  │  /predict/sprint-outcome XGBoost × 2         (M6)     │
  └───────────────────────────────────────────────────────┘
        │
        ▼
  Predictions stored in ai_predictions table
  Displayed as badges on Kanban task cards
        │
        ▼
  ActivityLog writes status transitions silently
  → Accumulates real training data over time
  → Re-run training.py → Models improve automatically
```

All models are trained on **5,000 synthetic rows** that mirror the exact feature schema produced by the Bedrock LLM generation prompt. They fall back to calibrated heuristics if `.pkl` files are missing (so the API never breaks).

---

## Model 1 — Delay Classifier

### Problem
Binary classification: **will this task be delayed or completed on time?**

### Algorithm
`XGBoostClassifier` (n_estimators=200, max_depth=5, learning_rate=0.05, subsample=0.8)

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
  "label_delayed": 1
}
```

### Features

| Feature | Type | Description | Range |
|---|---|---|---|
| `complexity` | Ordinal | Encoded from complexity_label (easy=0, medium=1, hard=2) | 0–2 |
| `num_subtasks` | Integer | Number of subtasks from LLM breakdown | 0–12 |
| `risk_count` | Integer | Count of risk_factors from LLM output | 0–6 |
| `assignee_load` | Integer | Number of open tasks currently on the assignee | 0–15 |
| `deadline_squeeze_ratio` | Float | `(story_points - days_remaining) / story_points` | 0.0–1.0 |
| `dependency_count` | Integer | Tasks this task depends on | 0–5 |
| `past_delay_rate_assignee` | Float | Historical delay rate for this developer | 0.0–1.0 |

### Input (API)
```json
POST /predict/delay
{
  "task_id": "uuid-optional",
  "complexity_label": "hard",
  "risk_factors": ["third-party API dependency", "payment failure edge cases"],
  "subtask_count": 5,
  "days_remaining": 3.0,
  "assignee_load": 8,
  "story_points": 8,
  "estimated_time": 10.0,
  "past_delay_rate_assignee": 0.35
}
```

### Output
```json
{
  "task_id": "uuid",
  "will_delay": true,
  "probability": 0.9963,
  "risk_level": "HIGH",
  "confidence": 0.9926,
  "model": "xgboost",
  "top_risk_factors": ["third-party API dependency", "payment failure edge cases"]
}
```

### Metrics (Test Set, n=1,000)
| Metric | Value |
|---|---|
| **ROC-AUC** | **0.9395** |
| **F1 Score** | **0.8734** |
| Precision | 0.87 |
| Recall | 0.88 |

### Feature Importance (approximate)
```
risk_count                ████████████████████  35%
deadline_squeeze_ratio    ███████████████       30%
past_delay_rate_assignee  ████████              15%
complexity                ██████                12%
assignee_load             ████                   8%
```

---

## Model 2 — Duration Regressor

### Problem
Regression: **how many actual hours will this task take to complete?**
Corrects the LLM's estimated_time using learned complexity and assignee speed patterns.

### Algorithm
`XGBoostRegressor` (n_estimators=250, max_depth=5, learning_rate=0.04, subsample=0.85)

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
  "actual_duration_hours": 35.1
}
```

### Features

| Feature | Type | Description | Range |
|---|---|---|---|
| `complexity` | Ordinal | Encoded (easy=0, medium=1, hard=2) | 0–2 |
| `story_points` | Float | Fibonacci story points (1,2,3,5,8,13) | 1–13 |
| `num_subtasks` | Float | Number of subtasks | 0–10 |
| `task_type` | Ordinal | Encoded (frontend=0, backend=1, devops=2, testing=3, bug=4) | 0–4 |
| `assignee_speed` | Float | Assignee avg speed multiplier (>1 = faster) | 0.3–2.5 |

### Input (API)
```json
POST /predict/duration
{
  "task_id": "uuid-optional",
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
  "predicted_actual_hours": 35.1,
  "delta_hours": 25.1,
  "model": "xgboost"
}
```

### Metrics (Test Set, n=1,000)
| Metric | Value |
|---|---|
| **MAE** | **1.24 hours** |
| **RMSE** | **1.61 hours** |

### Insight
A "hard" task with 8 story points and a 0.8x speed developer is estimated at 10h by the LLM but the model corrects it to **35.1h** — closer to reality.

---

## Model 3 — Bottleneck Classifier

### Problem
Binary classification: **is this task a bottleneck that will block other tasks?**

### Algorithm
`XGBoostClassifier` (n_estimators=200, max_depth=4, learning_rate=0.06)

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
  "label_bottleneck": 1
}
```

### Features

| Feature | Type | Description | Range |
|---|---|---|---|
| `dependency_depth` | Float | How deep in the dependency chain | 0–7 |
| `num_downstream_tasks` | Float | How many tasks are blocked by this one | 0–11 |
| `risk_score` | Float | Derived from risk_factors keyword matching | 0.0–1.0 |
| `task_delay_history` | Float | Historical delay rate for this task type | 0.0–1.0 |

**risk_score derivation** — matches against high-risk keywords:
`third-party`, `external api`, `payment`, `oauth`, `auth`, `migration`, `legacy`, `no test coverage`, `untested`, `dependency`, `integration`, `webhook`, `rate limit`

### Input (API)
```json
POST /predict/bottleneck
{
  "task_id": "uuid-optional",
  "risk_factors": ["third-party API dependency", "no existing test coverage"],
  "dependency_count": 3,
  "dependency_depth": 4,
  "num_downstream_tasks": 6,
  "task_delay_history": 0.5,
  "complexity_label": "hard",
  "subtask_count": 5
}
```

### Output
```json
{
  "task_id": "uuid",
  "is_bottleneck": true,
  "risk_level": "HIGH",
  "risk_score": 0.9893,
  "top_reasons": ["third-party", "no test coverage"],
  "dependency_risk": true,
  "model": "xgboost"
}
```

### Metrics (Test Set, n=1,000)
| Metric | Value |
|---|---|
| **ROC-AUC** | **0.9468** |
| **F1 Score** | **0.8872** |

---

## Model 4 — Assignee Ranker

### Problem
Ranking problem: **which developer has the highest probability of successfully completing this task?**

### Algorithm
`XGBoostClassifier` scoring P(success) for each candidate, then ranking by score.

### Dataset

| Property | Value |
|---|---|
| Rows | 5,000 (task, developer) pairs |
| Label | `label_success` (1 = developer completed similar task well) |
| Split | 80% train / 20% test |

**Sample row:**
```json
{
  "skill_match_score": 0.8,
  "dev_load": 3,
  "past_success_rate": 0.9,
  "avg_completion_speed": 1.2,
  "complexity": 1,
  "label_success": 1
}
```

### Features

| Feature | Type | Description | Range |
|---|---|---|---|
| `skill_match_score` | Float | `|dev_skills ∩ required_skills| / |required_skills|` | 0.0–1.0 |
| `dev_load` | Float | Current open tasks on developer | 0–15 |
| `past_success_rate` | Float | Historical task success rate | 0.0–1.0 |
| `avg_completion_speed` | Float | Average speed vs estimate (>1 = faster) | 0.3–2.0 |
| `complexity` | Float | Task complexity encoding | 0–2 |

### Input (API)
```json
POST /recommend/assignee
{
  "task_id": "uuid-optional",
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
  "matched_skills": ["Node.js", "REST API"],
  "open_tasks": 2,
  "reason": "Best skill match (2/3 skills: node.js, rest api)",
  "model": "xgboost",
  "all_scores": [
    {"id": "U1", "name": "Suraj", "score": 0.9924},
    {"id": "U2", "name": "Ravi",  "score": 0.1823}
  ]
}
```

### Metrics (Test Set, n=1,000)
| Metric | Value |
|---|---|
| **ROC-AUC** | **0.9083** |
| **F1 Score** | **0.8154** |

---

## Model 5 — Next-Task Ranker

### Problem
Ranking: **given a developer and a backlog of tasks, which single task should they pick up next?**
Answers the "what should I work on?" question intelligently.

### Algorithm
`XGBoostClassifier` scoring P(should_pick) for each candidate task, ranked descending.

### Dataset

| Property | Value |
|---|---|
| Rows | 5,000 (user, task) scoring decisions |
| Label | `label_should_pick` (1 = this is the right task to pick next) |
| Split | 80% train / 20% test |

**Sample row:**
```json
{
  "priority": 3,
  "skill_match": 0.9,
  "dep_blocked": 0,
  "complexity": 1,
  "story_points": 5.0,
  "days_since_created": 7.0,
  "label_should_pick": 1
}
```

### Features

| Feature | Type | Description | Range |
|---|---|---|---|
| `priority` | Float | Encoded (LOW=0, MEDIUM=1, HIGH=2, CRITICAL=3) | 0–3 |
| `skill_match` | Float | `|user_skills ∩ task.required_skills| / |required_skills|` | 0.0–1.0 |
| `dep_blocked` | Float | Is this task blocked by a dependency? (1=yes) | 0 or 1 |
| `complexity` | Float | Task complexity encoding | 0–2 |
| `story_points` | Float | Task story points | 1–13 |
| `days_since_created` | Float | How long has the task been in TODO | 0–30 |

### Input (API)
```json
POST /recommend/next-task
{
  "user_id": "U1",
  "user_skills": ["Node.js", "REST API"],
  "project_tasks": [
    {
      "id": "T1", "title": "Implement payment retry logic",
      "priority": "CRITICAL", "status": "TODO",
      "required_skills": ["Node.js", "REST API"],
      "story_points": 8, "complexity_label": "hard",
      "dependency_blocked": false, "created_at": "2026-04-15T10:00:00Z"
    },
    {
      "id": "T2", "title": "Update README docs",
      "priority": "LOW", "status": "TODO",
      "required_skills": ["Markdown"], "story_points": 1,
      "complexity_label": "easy", "dependency_blocked": false,
      "created_at": "2026-04-20T10:00:00Z"
    }
  ]
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
  "score": 0.9974,
  "reason": "Highest ML pick-probability based on priority, skill match, and dependencies",
  "model": "xgboost",
  "ranked_tasks": [
    {"id": "T1", "title": "Implement payment retry logic", "score": 0.9974},
    {"id": "T2", "title": "Update README docs",             "score": 0.0832}
  ]
}
```

### Metrics (Test Set, n=1,000)
| Metric | Value |
|---|---|
| **ROC-AUC** | **0.9711** |
| **F1 Score** | **0.8836** |

---

## Model 6 — Sprint Outcome (Dual Model)

### Problem
Two simultaneous predictions:
- **Regression**: what % of the sprint will be completed?
- **Classification**: will the sprint succeed (≥70% completion)?

### Algorithm
- `XGBoostRegressor` for completion percentage
- `XGBoostClassifier` for binary success/failure

### Dataset

| Property | Value |
|---|---|
| Rows | 5,000 synthetic sprints |
| Regression target | `label_completion_percent` (0–100) |
| Classification target | `label_success` (1 if completion ≥ 70%) |
| Split | 80% train / 20% test |

**Sample row:**
```json
{
  "total_story_points": 80,
  "avg_delay_prob": 0.4,
  "team_velocity": 60,
  "blocked_tasks": 5,
  "avg_complexity": 1.5,
  "label_completion_percent": 62.5,
  "label_success": 0
}
```

### Features

| Feature | Type | Description | Range |
|---|---|---|---|
| `total_story_points` | Float | Sum of all story points in the sprint | 10–100 |
| `avg_delay_prob` | Float | Mean delay probability from Model 1 across all tasks | 0.0–1.0 |
| `team_velocity` | Float | Team's historical avg story points per sprint | 10–120 |
| `blocked_tasks` | Float | Number of blocked tasks at sprint start | 0–10 |
| `avg_complexity` | Float | Mean complexity encoding across sprint tasks | 0–2 |

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
  "blocked_tasks": 2
}
```

### Output
```json
{
  "total_story_points": 29,
  "team_velocity": 25.0,
  "predicted_completion_percent": 72.4,
  "success_probability": 0.7092,
  "sprint_outcome": "ON TRACK",
  "at_risk_story_points": 21,
  "avg_task_delay_probability": 0.505,
  "recommendation": "Sprint looks healthy. Maintain current pace.",
  "model": "xgboost"
}
```

### Metrics (Test Set, n=1,000)
| Metric | Value |
|---|---|
| **Completion % MAE** | **3.46%** |
| **Success ROC-AUC** | **0.9942** |

---

## Training Pipeline

All models are defined and trained in a single file:

```
ai-service/app/pipelines/training.py
```

### Run Training
```bash
cd ai-service
python3 -m app.pipelines.training
```

### Output
```
============================================================
JustBuildIt — Training all 6 XGBoost ML models
============================================================

[1/6] Training delay classifier …
  ROC-AUC: 0.9395  F1: 0.8734
  ✔ Saved app/models/delay_model.pkl

[2/6] Training duration regressor …
  MAE: 1.24h  RMSE: 1.61h
  ✔ Saved app/models/duration_model.pkl

[3/6] Training bottleneck classifier …
  ROC-AUC: 0.9468  F1: 0.8872
  ✔ Saved app/models/bottleneck_model.pkl

[4/6] Training assignee success classifier …
  ROC-AUC: 0.9083  F1: 0.8154
  ✔ Saved app/models/assignee_model.pkl

[5/6] Training next-task ranker …
  ROC-AUC: 0.9711  F1: 0.8836
  ✔ Saved app/models/next_task_model.pkl

[6/6] Training sprint outcome models …
  Completion% regressor  MAE: 3.46%
  ✔ Saved app/models/sprint_completion_model.pkl
  Success classifier     ROC-AUC: 0.9942
  ✔ Saved app/models/sprint_success_model.pkl

✅ All models trained and saved to app/models
```

### Saved Model Files
```
ai-service/app/models/
├── delay_model.pkl
├── duration_model.pkl
├── bottleneck_model.pkl
├── assignee_model.pkl
├── next_task_model.pkl
├── sprint_completion_model.pkl
└── sprint_success_model.pkl
```

### Model Loading
Models are lazy-loaded and cached at first request via `app/utils/model_loader.py`.
Every endpoint prints `"model": "xgboost"` on success or `"model": "heuristic"` if pkl file is missing.

---

## Upgrading from Synthetic → Real Data

The current models are trained on **synthetic data** that mirrors the exact feature schema.
Once real usage accumulates in the database, replace the `_gen_*_data()` functions in `training.py` with DB queries.

### Data Available in DB (already collecting)

| Table | Fields collected automatically |
|---|---|
| `tasks` | `complexity_label`, `story_points`, `risk_factors`, `subtasks`, `task_type`, `required_skills` |
| `tasks` | `completed_at`, `status_changed_at` — for measuring actual duration |
| `activity_logs` | `from_status`, `to_status`, `time_in_status_hours`, `complexity_label`, `story_points` |
| `ai_predictions` | `predicted_delay`, `confidence_score`, `features_snapshot` |

### Example Real Data Query (delay model)
```python
# Replace _gen_delay_data() with:
df = pd.read_sql("""
    SELECT
        CASE complexity_label WHEN 'easy' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END AS complexity,
        array_length(subtasks, 1) AS num_subtasks,
        array_length(risk_factors, 1) AS risk_count,
        (SELECT COUNT(*) FROM tasks t2 WHERE t2.assigned_to = t.assigned_to
         AND t2.status NOT IN ('DONE') AND t2.id != t.id) AS assignee_load,
        EXTRACT(EPOCH FROM (deadline - NOW())) / 86400 AS days_remaining,
        story_points,
        0.2 AS past_delay_rate_assignee,
        CASE WHEN completed_at > deadline THEN 1 ELSE 0 END AS label_delayed
    FROM tasks t
    WHERE completed_at IS NOT NULL AND deadline IS NOT NULL
""", engine)
```

---

## API Quick Reference

| Endpoint | Method | Model | Problem Type |
|---|---|---|---|
| `/predict/delay` | POST | XGBClassifier | Binary classification |
| `/predict/duration` | POST | XGBRegressor | Regression |
| `/predict/bottleneck` | POST | XGBClassifier | Binary classification |
| `/predict/sprint-outcome` | POST | XGB × 2 | Regression + Classification |
| `/recommend/assignee` | POST | XGBClassifier (ranked) | Ranking |
| `/recommend/next-task` | POST | XGBClassifier (ranked) | Ranking |
| `/health` | GET | — | Health check |

### Health Check
```bash
curl http://localhost:8001/health
# → {"status": "ok", "service": "ai-service"}
```

### Start the Service
```bash
cd ai-service
pip install -r requirements.txt
python3 -m app.pipelines.training   # train models first
uvicorn app.main:app --port 8001 --reload
# API docs: http://localhost:8001/docs
```

---

## Summary Table

| # | Model | Algorithm | Dataset Size | Key Input Fields | Key Output | Best Metric |
|---|---|---|---|---|---|---|
| 1 | Delay Classifier | XGBClassifier | 5,000 tasks | complexity, risk_count, assignee_load, deadline_squeeze | `probability`, `will_delay` | AUC **0.94** |
| 2 | Duration Regressor | XGBRegressor | 5,000 tasks | complexity, story_points, subtasks, task_type, speed | `predicted_actual_hours` | MAE **1.24h** |
| 3 | Bottleneck Classifier | XGBClassifier | 5,000 tasks | dep_depth, downstream_count, risk_score, delay_history | `is_bottleneck`, `risk_score` | AUC **0.95** |
| 4 | Assignee Ranker | XGBClassifier | 5,000 pairs | skill_match, dev_load, past_success, speed | `assignee_id`, `score` | AUC **0.91** |
| 5 | Next-Task Ranker | XGBClassifier | 5,000 decisions | priority, skill_match, blocked, story_points | `task_id`, `ranked_tasks` | AUC **0.97** |
| 6a | Sprint Completion | XGBRegressor | 5,000 sprints | total_sp, avg_delay_prob, velocity, blocked | `completion_percent` | MAE **3.46%** |
| 6b | Sprint Success | XGBClassifier | 5,000 sprints | total_sp, avg_delay_prob, velocity, blocked | `success_probability` | AUC **0.99** |
