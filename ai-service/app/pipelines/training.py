"""
JustBuildIt AI Service — Full Multi-Model Training Pipeline
===========================================================

Architecture:
  Raw inputs → [Text Encoder | Sequence Encoder | Graph Encoder]
                              ↓
                    Feature Fusion Layer
                              ↓
  ┌────────────┬─────────────┬──────────────┬──────────────────────────┐
  │ Delay      │ Duration    │ Bottleneck   │ Sprint (XGB → Seq MLP)   │
  │ XGBoost    │ XGBoost     │ XGBoost      │                          │
  ├────────────┴─────────────┘              ├──────────────────────────┤
  │ Assignee — Siamese MLP                  │ Next Task — LightGBM     │
  │ (cosine text sim + MLP)                 │ Ranker                   │
  └─────────────────────────────────────────┴──────────────────────────┘

Run:
  python3 -m app.pipelines.training
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.metrics import (
    roc_auc_score, f1_score, mean_absolute_error,
)
import xgboost as xgb
import lightgbm as lgb

# ── Local imports ───────────────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.encoders.text_encoder import TextEncoder, build_task_text, build_skill_text
from app.encoders.sequence_encoder import synthesize_sequence_features
from app.encoders.graph_encoder import synthesize_graph_features
from app.pipelines.feature_fusion import fuse_batch

# ── Paths & Config ──────────────────────────────────────────────────────────
MODEL_DIR = "app/models"
os.makedirs(MODEL_DIR, exist_ok=True)

COMPLEXITY_MAP = {"easy": 0, "medium": 1, "hard": 2}
TASK_TYPE_MAP  = {"frontend": 0, "backend": 1, "devops": 2, "testing": 3, "bug": 4}
PRIORITY_MAP   = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

N = 5000        # synthetic rows
np.random.seed(42)
RNG = np.random.default_rng(42)

# ── Vocabulary corpus for Text Encoder ──────────────────────────────────────
_TECH_CORPUS = [
    "implement REST API endpoint authentication oauth JWT",
    "payment integration Razorpay retry logic exponential backoff",
    "database migration schema PostgreSQL indexing foreign key",
    "frontend React TypeScript component state management",
    "devops CI/CD pipeline Docker Kubernetes deployment",
    "testing unit integration coverage pytest jest",
    "bug fix error handling exception logging monitoring",
    "data pipeline ETL transformation aggregation analytics",
    "real-time websocket notification event streaming",
    "third-party API rate limit webhook signature validation",
    "security audit OWASP XSS SQL injection penetration testing",
    "performance optimisation caching Redis CDN lazy loading",
    "mobile responsive design accessibility WCAG",
    "machine learning model training inference feature engineering",
    "async task queue Celery background job scheduling",
    "microservice event-driven architecture message queue RabbitMQ",
    "search full-text indexing Elasticsearch autocomplete",
    "billing subscription pricing SaaS invoice PDF generation",
    "onboarding wizard user flow email verification",
    "reporting dashboard charts analytics Recharts D3",
]

_SKILL_CORPUS = [
    "Python FastAPI SQLAlchemy PostgreSQL",
    "JavaScript TypeScript React Next.js Node.js",
    "DevOps Docker Kubernetes GitHub Actions CI/CD",
    "Java Spring Boot Hibernate MySQL",
    "Go Gin REST gRPC microservices",
    "Machine Learning XGBoost scikit-learn pandas numpy",
    "iOS Swift SwiftUI Xcode",
    "Android Kotlin Jetpack Compose",
    "Security OWASP penetration testing",
    "Data engineering Spark Airflow dbt",
]


def _save(obj, name: str) -> None:
    path = os.path.join(MODEL_DIR, f"{name}.pkl")
    joblib.dump(obj, path)
    print(f"  ✔ Saved {path}")


# ══════════════════════════════════════════════════════════════════════════════
# Step 0 — Fit and Save Shared Text Encoder
# ══════════════════════════════════════════════════════════════════════════════

def fit_text_encoder() -> TextEncoder:
    print("\n[0/6] Fitting shared Text Encoder (TF-IDF + LSA 32-dim) …")
    corpus = _TECH_CORPUS + _SKILL_CORPUS
    enc = TextEncoder()
    enc.fit(corpus)
    enc.save(os.path.join(MODEL_DIR, "text_encoder.pkl"))
    print("  ✔ Saved app/models/text_encoder.pkl")
    return enc


# ══════════════════════════════════════════════════════════════════════════════
# 1. DELAY CLASSIFIER — XGBoost on fused features
#    Structured (7) + Text (32) + Sequence (10) + Graph (8) = 57 features
# ══════════════════════════════════════════════════════════════════════════════

def _gen_delay_corpus_and_labels():
    """Generate synthetic task text + labels for delay prediction."""
    titles = [
        "Implement payment retry logic",
        "Set up CI/CD pipeline",
        "Fix authentication bug",
        "Design database schema",
        "Build REST API endpoint",
        "Write unit tests for service",
        "Deploy to production Kubernetes",
        "Optimise dashboard query performance",
        "Integrate third-party OAuth provider",
        "Migrate legacy database tables",
    ]
    task_texts = [titles[i % len(titles)] for i in range(N)]
    tags_pool = [["backend", "API"], ["devops"], ["bug", "auth"], ["database"],
                 ["backend"], ["testing"], ["devops", "kubernetes"], ["performance"],
                 ["integration", "oauth"], ["migration"]]
    tags_list = [tags_pool[i % len(tags_pool)] for i in range(N)]

    complexity = RNG.choice(list(COMPLEXITY_MAP.keys()), N, p=[0.3, 0.5, 0.2])
    num_subtasks = RNG.integers(0, 12, N)
    risk_count = RNG.integers(0, 6, N)
    assignee_load = RNG.integers(0, 15, N)
    deadline_squeeze = np.clip(RNG.beta(2, 3, N), 0.01, 1.0)
    dependency_count = RNG.integers(0, 5, N)
    past_delay_rate = np.clip(RNG.beta(2, 5, N), 0.0, 1.0)

    c_num = np.array([COMPLEXITY_MAP[c] for c in complexity], dtype=float)
    structured = np.column_stack([
        c_num, num_subtasks, risk_count, assignee_load,
        deadline_squeeze, dependency_count, past_delay_rate
    ])

    # Label: heuristic-seeded (model learns real signal from feature interactions)
    score = (
        c_num / 2 * 0.35
        + risk_count / 5 * 0.30
        + assignee_load / 15 * 0.15
        + deadline_squeeze * 0.10
        + past_delay_rate * 0.10
    ) + RNG.normal(0, 0.08, N)
    labels = (score > 0.42).astype(int)

    return task_texts, tags_list, structured, labels


def train_delay_model(text_enc: TextEncoder) -> None:
    print("\n[1/6] Training Delay Classifier — XGBoost + Fused Features …")
    texts, tags_list, structured, labels = _gen_delay_corpus_and_labels()

    # Text embeddings
    text_emb = np.vstack([
        text_enc.encode(build_task_text(t, tags=tg))
        for t, tg in zip(texts, tags_list)
    ])  # (N, 32)

    # Sequence + Graph synthetic features
    seq_feats   = synthesize_sequence_features(N, RNG)   # (N, 10)
    graph_feats = synthesize_graph_features(N, RNG)      # (N, 8)

    X = fuse_batch(structured, text_emb, seq_feats, graph_feats)  # (N, 57)
    y = labels

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.04,
        subsample=0.8, colsample_bytree=0.75, min_child_weight=3,
        eval_metric="logloss", random_state=42,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

    probs = model.predict_proba(X_te)[:, 1]
    preds = model.predict(X_te)
    print(f"  ROC-AUC: {roc_auc_score(y_te, probs):.4f}  "
          f"F1: {f1_score(y_te, preds):.4f}  "
          f"(input dim: {X.shape[1]})")
    _save(model, "delay_model")


# ══════════════════════════════════════════════════════════════════════════════
# 2. DURATION REGRESSOR — XGBoost + Text Embeddings
#    Structured (5) + Text (32) = 37 features (no graph; temporal = seq)
# ══════════════════════════════════════════════════════════════════════════════

def train_duration_model(text_enc: TextEncoder) -> None:
    print("\n[2/6] Training Duration Regressor — XGBoost + Text …")

    complexity  = RNG.choice(list(COMPLEXITY_MAP.keys()), N, p=[0.3, 0.5, 0.2])
    story_pts   = RNG.choice([1, 2, 3, 5, 8, 13], N)
    num_sub     = RNG.integers(0, 10, N)
    task_type   = RNG.choice(list(TASK_TYPE_MAP.keys()), N)
    speed       = np.clip(RNG.normal(1.0, 0.3, N), 0.3, 2.5)

    c_num  = np.array([COMPLEXITY_MAP[c] for c in complexity], dtype=float)
    tt_num = np.array([TASK_TYPE_MAP[t] for t in task_type], dtype=float)

    structured = np.column_stack([c_num, story_pts.astype(float),
                                   num_sub.astype(float), tt_num, speed])

    base_hours = story_pts * 2.0 * (1 + c_num * 0.3)
    targets    = np.clip(base_hours / speed + num_sub * 0.4 + RNG.normal(0, 1.5, N),
                         0.5, 120.0)

    task_texts = [f"{task_type[i]} task {complexity[i]} complexity" for i in range(N)]
    text_emb   = np.vstack([text_enc.encode(t) for t in task_texts])

    # Duration doesn't need graph (no dependency impact on measuring duration)
    X = fuse_batch(structured, text_emb, seq_feats=None, graph_feats=None)  # (N, 37)

    X_tr, X_te, y_tr, y_te = train_test_split(X, targets, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(
        n_estimators=300, max_depth=6, learning_rate=0.04,
        subsample=0.85, colsample_bytree=0.8, random_state=42,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

    preds = model.predict(X_te)
    mae   = mean_absolute_error(y_te, preds)
    rmse  = float(np.sqrt(np.mean((y_te - preds) ** 2)))
    print(f"  MAE: {mae:.2f}h  RMSE: {rmse:.2f}h  (input dim: {X.shape[1]})")
    _save(model, "duration_model")


# ══════════════════════════════════════════════════════════════════════════════
# 3. BOTTLENECK CLASSIFIER — XGBoost on Graph + Text + Structured
#    Graph(8) + Text(32) + Structured(4) = 44 features
#    (GNN upgrade path: swap GraphEncoder output with PyG GCN embeddings)
# ══════════════════════════════════════════════════════════════════════════════

def train_bottleneck_model(text_enc: TextEncoder) -> None:
    print("\n[3/6] Training Bottleneck Classifier — XGBoost + Graph Features …")

    dep_depth   = RNG.integers(0, 8, N)
    downstream  = RNG.integers(0, 12, N)
    risk_score  = np.clip(RNG.beta(2, 4, N), 0.0, 1.0)
    delay_hist  = np.clip(RNG.beta(2, 5, N), 0.0, 1.0)

    structured = np.column_stack([
        dep_depth.astype(float), downstream.astype(float),
        risk_score, delay_hist
    ])

    score = (dep_depth / 7 * 0.35 + downstream / 11 * 0.25
             + risk_score * 0.25 + delay_hist * 0.15
             + RNG.normal(0, 0.07, N))
    labels = (score > 0.38).astype(int)

    task_texts = [
        f"{'blocked by dependencies' if dep_depth[i] > 3 else 'integration task'} "
        f"{'critical path third-party' if risk_score[i] > 0.5 else 'internal service'}"
        for i in range(N)
    ]
    text_emb    = np.vstack([text_enc.encode(t) for t in task_texts])
    graph_feats = synthesize_graph_features(N, RNG)

    X = fuse_batch(structured, text_emb, seq_feats=None, graph_feats=graph_feats)  # (N, 44)

    X_tr, X_te, y_tr, y_te = train_test_split(X, labels, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(
        n_estimators=250, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        eval_metric="logloss", random_state=42,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

    preds = model.predict(X_te)
    probs = model.predict_proba(X_te)[:, 1]
    print(f"  ROC-AUC: {roc_auc_score(y_te, probs):.4f}  "
          f"F1: {f1_score(y_te, preds):.4f}  (input dim: {X.shape[1]})")
    _save(model, "bottleneck_model")


# ══════════════════════════════════════════════════════════════════════════════
# 4. ASSIGNEE — Siamese MLP (cosine text similarity + structured)
#    Input: [task_emb(32), dev_emb(32), |diff|(32), cosine_sim(1), struct(3)] = 100
#    Architecture: Siamese → shared embedding → MLP → P(success)
# ══════════════════════════════════════════════════════════════════════════════

def train_assignee_model(text_enc: TextEncoder) -> None:
    print("\n[4/6] Training Assignee Siamese MLP …")

    # Generate (task, developer) pairs
    task_texts = [
        build_task_text(
            t,
            tags=RNG.choice(["backend", "API", "database", "frontend",
                              "devops", "testing", "security"], 2).tolist()
        )
        for t in RNG.choice([s.split()[0] for s in _TECH_CORPUS], N)
    ]
    dev_skill_texts = [
        build_skill_text(
            RNG.choice(["Python", "Node.js", "React", "PostgreSQL", "Docker",
                        "TypeScript", "Go", "Java", "Kubernetes", "Redis"],
                       size=RNG.integers(2, 6), replace=False).tolist()
        )
        for _ in range(N)
    ]

    task_embs  = np.vstack([text_enc.encode(t) for t in task_texts])   # (N, 32)
    dev_embs   = np.vstack([text_enc.encode(d) for d in dev_skill_texts])  # (N, 32)
    cosine_sim = np.sum(task_embs * dev_embs, axis=1, keepdims=True)   # (N, 1) — L2-normed
    diff       = np.abs(task_embs - dev_embs)                          # (N, 32) element-wise diff

    dev_load     = RNG.integers(0, 15, N).astype(float)
    past_success = np.clip(RNG.beta(5, 2, N), 0.0, 1.0)
    avg_speed    = np.clip(RNG.normal(1.0, 0.25, N), 0.3, 2.0)

    structured_dev = np.column_stack([dev_load, past_success, avg_speed])  # (N, 3)

    # Siamese feature vector: [task_emb | dev_emb | |diff| | cosine_sim | dev_struct]
    X = np.hstack([task_embs, dev_embs, diff, cosine_sim, structured_dev])  # (N, 100)

    score = (cosine_sim.ravel() * 0.45
             + past_success * 0.30
             + avg_speed / 2 * 0.15
             - dev_load / 15 * 0.20
             + RNG.normal(0, 0.07, N))
    y = (score > 0.45).astype(int)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    model = MLPClassifier(
        hidden_layer_sizes=(128, 64, 32),
        activation="relu",
        max_iter=300,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.1,
        learning_rate_init=0.001,
        batch_size=128,
    )
    model.fit(X_tr, y_tr)

    probs = model.predict_proba(X_te)[:, 1]
    preds = model.predict(X_te)
    print(f"  ROC-AUC: {roc_auc_score(y_te, probs):.4f}  "
          f"F1: {f1_score(y_te, preds):.4f}  (input dim: {X.shape[1]})")
    _save(model, "assignee_model")


# ══════════════════════════════════════════════════════════════════════════════
# 5. NEXT-TASK — LightGBM Ranker (LambdaRank objective)
#    Features: priority, skill_match(text cosine), blocked, complexity,
#              story_points, days_created, seq_feats(10), graph_feats(8) = 20
#    Groups: tasks grouped by (user, sprint) pair
# ══════════════════════════════════════════════════════════════════════════════

def train_next_task_model(text_enc: TextEncoder) -> None:
    print("\n[5/6] Training Next-Task LightGBM Ranker …")

    n_groups = 500          # simulate 500 users × sprint planning sessions
    tasks_per_group = 10    # avg 10 tasks per session

    all_features = []
    all_labels   = []
    group_sizes  = []

    user_skill_texts = [
        build_skill_text(
            RNG.choice(["Python", "React", "Node.js", "PostgreSQL", "Docker",
                        "TypeScript", "Java", "Go"], size=3, replace=False).tolist()
        )
        for _ in range(n_groups)
    ]
    user_embs = np.vstack([text_enc.encode(s) for s in user_skill_texts])  # (n_groups, 32)

    for g_idx in range(n_groups):
        n_tasks = RNG.integers(5, tasks_per_group * 2)
        group_sizes.append(n_tasks)

        task_txts = [
            build_task_text(
                RNG.choice([t.split()[0] for t in _TECH_CORPUS]),
                tags=RNG.choice(["backend","API","database","frontend","devops",
                                  "testing","security"], 2).tolist()
            )
            for _ in range(n_tasks)
        ]
        task_embs    = np.vstack([text_enc.encode(t) for t in task_txts])  # (n_tasks, 32)
        cosine_sims  = task_embs @ user_embs[g_idx]                         # (n_tasks,)

        priority     = RNG.integers(0, 4, n_tasks).astype(float)
        blocked      = RNG.choice([0.0, 1.0], n_tasks, p=[0.8, 0.2])
        complexity   = RNG.integers(0, 3, n_tasks).astype(float)
        story_pts    = RNG.choice([1.,2.,3.,5.,8.,13.], n_tasks)
        days_created = RNG.integers(0, 30, n_tasks).astype(float)

        seq_feats   = synthesize_sequence_features(n_tasks, RNG)
        graph_feats = synthesize_graph_features(n_tasks, RNG)

        struct = np.column_stack([
            priority, cosine_sims, blocked, complexity, story_pts, days_created
        ])
        X_group = np.hstack([struct, seq_feats, graph_feats])   # (n_tasks, 26)
        all_features.append(X_group)

        # Relevance score (higher = better pick)
        rel = (priority / 3 * 3 + cosine_sims * 2 - blocked * 2
               - complexity / 2 * 0.5 + days_created / 30 * 0.5
               + RNG.normal(0, 0.3, n_tasks))
        # Convert to integer relevance labels [0..3]
        rel_labels = np.clip(
            ((rel - rel.min()) / (rel.max() - rel.min() + 1e-6) * 3).astype(int), 0, 3
        )
        all_labels.append(rel_labels)

    X_all  = np.vstack(all_features)
    y_all  = np.concatenate(all_labels)
    groups = np.array(group_sizes)

    # LightGBM Dataset with query groups
    ds = lgb.Dataset(X_all, label=y_all, group=groups)

    params = {
        "objective":      "lambdarank",
        "metric":         "ndcg",
        "ndcg_eval_at":   [1, 3, 5],
        "learning_rate":  0.05,
        "num_leaves":     63,
        "min_data_in_leaf": 5,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq":   5,
        "verbose":        -1,
        "num_threads":    4,
    }

    model = lgb.train(
        params, ds,
        num_boost_round=200,
        valid_sets=[ds],
        callbacks=[lgb.log_evaluation(period=-1)],   # suppress per-round logs
    )

    # NDCG@1 approximation via predict() ranking
    scores   = model.predict(X_all)
    group_offset = 0
    ndcg_sum = 0.0
    for g_sz in group_sizes:
        g_scores = scores[group_offset: group_offset + g_sz]
        g_labels = y_all[group_offset: group_offset + g_sz]
        top1_idx = int(np.argmax(g_scores))
        ndcg_sum += float(g_labels[top1_idx]) / 3.0   # normalised by max label
        group_offset += g_sz

    mean_ndcg1 = ndcg_sum / len(group_sizes)
    print(f"  NDCG@1: {mean_ndcg1:.4f}  (input dim: {X_all.shape[1]}, "
          f"groups: {n_groups}, total rows: {X_all.shape[0]})")
    _save(model, "next_task_model")


# ══════════════════════════════════════════════════════════════════════════════
# 6. SPRINT OUTCOME — XGBoost (baseline) + Sequence MLP (temporal)
#    6a: XGBRegressor  → completion percentage
#    6b: XGBClassifier → success / failure (≥70%)
#    6c: Sequence MLP  → velocity trend from past sprint window
# ══════════════════════════════════════════════════════════════════════════════

def train_sprint_models(text_enc: TextEncoder) -> None:
    print("\n[6/6] Training Sprint Outcome — XGBoost + Sequence MLP …")

    total_sp    = RNG.integers(10, 100, N).astype(float)
    avg_delay   = np.clip(RNG.beta(2, 4, N), 0.0, 1.0)
    velocity    = np.clip(RNG.normal(55, 20, N), 10.0, 120.0)
    blocked     = RNG.integers(0, 10, N).astype(float)
    avg_complex = RNG.uniform(0, 2, N)

    # Sequence window: 3 past sprint velocities (simulates temporal context)
    past_v1 = np.clip(velocity + RNG.normal(0, 8, N), 10, 120)
    past_v2 = np.clip(velocity + RNG.normal(0, 8, N), 10, 120)
    past_v3 = np.clip(velocity + RNG.normal(0, 8, N), 10, 120)
    velocity_trend = velocity - past_v3        # momentum: positive = improving

    struct_features = np.column_stack([
        total_sp, avg_delay, velocity, blocked, avg_complex,
        past_v1, past_v2, past_v3, velocity_trend
    ])

    cap_ratio  = np.clip(velocity / total_sp, 0.1, 2.0)
    comp_pct   = np.clip(
        cap_ratio * 100 * (1 - avg_delay * 0.4)
        - blocked * 2
        + velocity_trend * 0.3
        + RNG.normal(0, 5, N),
        0, 100
    )
    label_success = (comp_pct >= 70).astype(int)

    X_tr, X_te, y_reg_tr, y_reg_te = train_test_split(
        struct_features, comp_pct, test_size=0.2, random_state=42
    )
    _, _, y_cls_tr, y_cls_te = train_test_split(
        struct_features, label_success, test_size=0.2, random_state=42
    )

    # 6a — XGBRegressor (completion %)
    reg = xgb.XGBRegressor(
        n_estimators=300, max_depth=5, learning_rate=0.04,
        subsample=0.85, colsample_bytree=0.8, random_state=42,
    )
    reg.fit(X_tr, y_reg_tr, eval_set=[(X_te, y_reg_te)], verbose=False)
    mae = mean_absolute_error(y_reg_te, reg.predict(X_te))
    print(f"  Completion% regressor  MAE: {mae:.2f}%  (input dim: {X_tr.shape[1]})")
    _save(reg, "sprint_completion_model")

    # 6b — XGBClassifier (success/failure)
    cls = xgb.XGBClassifier(
        n_estimators=250, max_depth=5, learning_rate=0.05,
        eval_metric="logloss", random_state=42,
    )
    cls.fit(X_tr, y_cls_tr, eval_set=[(X_te, y_cls_te)], verbose=False)
    probs = cls.predict_proba(X_te)[:, 1]
    print(f"  Success classifier     ROC-AUC: {roc_auc_score(y_cls_te, probs):.4f}")
    _save(cls, "sprint_success_model")

    # 6c — Sequence MLP (velocity trend window → completion adj.)
    #  Input: [past_v3, past_v2, past_v1, velocity, velocity_trend, total_sp, avg_delay]
    seq_input = np.column_stack([past_v3, past_v2, past_v1, velocity, velocity_trend,
                                  total_sp, avg_delay])
    sq_tr, sq_te, sq_y_tr, sq_y_te = train_test_split(
        seq_input, comp_pct, test_size=0.2, random_state=42
    )
    mlp = MLPRegressor(
        hidden_layer_sizes=(64, 32),
        activation="tanh",
        max_iter=300,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.1,
        learning_rate_init=0.001,
    )
    mlp.fit(sq_tr, sq_y_tr)
    mlp_mae = mean_absolute_error(sq_y_te, mlp.predict(sq_te))
    print(f"  Sprint Sequence MLP    MAE: {mlp_mae:.2f}%  (temporal velocity window)")
    _save(mlp, "sprint_sequence_model")


# ══════════════════════════════════════════════════════════════════════════════
# Entry Point
# ══════════════════════════════════════════════════════════════════════════════

def train_all() -> None:
    print("=" * 64)
    print("JustBuildIt — Full Architecture Training Pipeline")
    print("Text Encoder + Sequence + Graph → Feature Fusion → 6 Models")
    print("=" * 64)

    text_enc = fit_text_encoder()
    train_delay_model(text_enc)
    train_duration_model(text_enc)
    train_bottleneck_model(text_enc)
    train_assignee_model(text_enc)
    train_next_task_model(text_enc)
    train_sprint_models(text_enc)

    print(f"\n✅ All models trained and saved to {MODEL_DIR}/")
    print("\nModel files:")
    for f in sorted(os.listdir(MODEL_DIR)):
        if f.endswith(".pkl"):
            sz = os.path.getsize(os.path.join(MODEL_DIR, f))
            print(f"  {f:<40} {sz/1024:.1f} KB")


if __name__ == "__main__":
    train_all()
