"""
JustBuildIt AI Service — XGBoost Training Pipeline
Trains all 6 ML models from synthetic data that mirrors the real schema.
Run:  python3 -m app.pipelines.training
"""
import os
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder
from sklearn.metrics import (
    roc_auc_score, f1_score, mean_absolute_error,
    precision_score, classification_report,
)
import xgboost as xgb

# ── Paths ──────────────────────────────────────────────────────────────────────
MODEL_DIR = "app/models"
os.makedirs(MODEL_DIR, exist_ok=True)

COMPLEXITY_MAP = {"easy": 0, "medium": 1, "hard": 2}
TASK_TYPE_MAP = {"frontend": 0, "backend": 1, "devops": 2, "testing": 3, "bug": 4}
N = 5000  # synthetic rows per model
np.random.seed(42)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _complexity_numeric(arr):
    return np.vectorize(COMPLEXITY_MAP.get)(arr, 1)


def _task_type_numeric(arr):
    return np.vectorize(TASK_TYPE_MAP.get)(arr, 1)


def _save(model, name: str):
    path = os.path.join(MODEL_DIR, f"{name}.pkl")
    joblib.dump(model, path)
    print(f"  ✔ Saved {path}")


# ══════════════════════════════════════════════════════════════════════════════
# 1. DELAY CLASSIFIER  (XGBoostClassifier)
#    Features: complexity, num_subtasks, risk_count, assignee_load,
#              deadline_squeeze_ratio, dependency_count, past_delay_rate_assignee
# ══════════════════════════════════════════════════════════════════════════════

def _gen_delay_data():
    complexity = np.random.choice(["easy", "medium", "hard"], N, p=[0.3, 0.5, 0.2])
    num_subtasks = np.random.randint(0, 12, N)
    risk_count = np.random.randint(0, 6, N)
    assignee_load = np.random.randint(0, 15, N)
    deadline_squeeze = np.clip(np.random.beta(2, 3, N), 0.01, 1.0)
    dependency_count = np.random.randint(0, 5, N)
    past_delay_rate = np.clip(np.random.beta(2, 5, N), 0.0, 1.0)

    c_num = _complexity_numeric(complexity)
    # Heuristic-informed label (noisy)
    score = (
        c_num / 2 * 0.35
        + risk_count / 5 * 0.30
        + assignee_load / 15 * 0.15
        + deadline_squeeze * 0.10
        + past_delay_rate * 0.10
    ) + np.random.normal(0, 0.08, N)
    label = (score > 0.42).astype(int)

    return pd.DataFrame({
        "complexity": c_num,
        "num_subtasks": num_subtasks,
        "risk_count": risk_count,
        "assignee_load": assignee_load,
        "deadline_squeeze_ratio": deadline_squeeze,
        "dependency_count": dependency_count,
        "past_delay_rate_assignee": past_delay_rate,
        "label_delayed": label,
    })


def train_delay_model():
    print("\n[1/6] Training delay classifier …")
    df = _gen_delay_data()
    X = df.drop("label_delayed", axis=1)
    y = df["label_delayed"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        use_label_encoder=False, eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

    preds = model.predict(X_te)
    probs = model.predict_proba(X_te)[:, 1]
    print(f"  ROC-AUC: {roc_auc_score(y_te, probs):.4f}  F1: {f1_score(y_te, preds):.4f}")
    _save(model, "delay_model")


# ══════════════════════════════════════════════════════════════════════════════
# 2. DURATION REGRESSOR  (XGBoostRegressor)
#    Features: complexity, story_points, num_subtasks, task_type, assignee_speed
#    Target: actual_duration_hours
# ══════════════════════════════════════════════════════════════════════════════

def _gen_duration_data():
    complexity = np.random.choice(["easy", "medium", "hard"], N, p=[0.3, 0.5, 0.2])
    story_points = np.random.choice([1, 2, 3, 5, 8, 13], N)
    num_subtasks = np.random.randint(0, 10, N)
    task_type = np.random.choice(list(TASK_TYPE_MAP.keys()), N)
    assignee_speed = np.clip(np.random.normal(1.0, 0.3, N), 0.3, 2.5)  # multiplier

    c_num = _complexity_numeric(complexity)
    tt_num = _task_type_numeric(task_type)

    base_hours = story_points * 2.0 * (1 + c_num * 0.3)
    actual = base_hours / assignee_speed + num_subtasks * 0.4 + np.random.normal(0, 1.5, N)
    actual = np.clip(actual, 0.5, 120)

    return pd.DataFrame({
        "complexity": c_num,
        "story_points": story_points.astype(float),
        "num_subtasks": num_subtasks.astype(float),
        "task_type": tt_num.astype(float),
        "assignee_speed": assignee_speed,
        "actual_duration_hours": actual,
    })


def train_duration_model():
    print("\n[2/6] Training duration regressor …")
    df = _gen_duration_data()
    X = df.drop("actual_duration_hours", axis=1)
    y = df["actual_duration_hours"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(
        n_estimators=250, max_depth=5, learning_rate=0.04,
        subsample=0.85, colsample_bytree=0.8,
        random_state=42,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

    preds = model.predict(X_te)
    mae = mean_absolute_error(y_te, preds)
    rmse = np.sqrt(np.mean((y_te - preds) ** 2))
    print(f"  MAE: {mae:.2f}h  RMSE: {rmse:.2f}h")
    _save(model, "duration_model")


# ══════════════════════════════════════════════════════════════════════════════
# 3. BOTTLENECK CLASSIFIER  (XGBoostClassifier)
#    Features: dependency_depth, num_downstream_tasks, risk_score,
#              task_delay_history
# ══════════════════════════════════════════════════════════════════════════════

def _gen_bottleneck_data():
    dep_depth = np.random.randint(0, 8, N)
    downstream = np.random.randint(0, 12, N)
    risk_score = np.clip(np.random.beta(2, 4, N), 0.0, 1.0)
    delay_history = np.clip(np.random.beta(2, 5, N), 0.0, 1.0)

    score = (
        dep_depth / 7 * 0.35
        + downstream / 11 * 0.25
        + risk_score * 0.25
        + delay_history * 0.15
    ) + np.random.normal(0, 0.07, N)
    label = (score > 0.38).astype(int)

    return pd.DataFrame({
        "dependency_depth": dep_depth.astype(float),
        "num_downstream_tasks": downstream.astype(float),
        "risk_score": risk_score,
        "task_delay_history": delay_history,
        "label_bottleneck": label,
    })


def train_bottleneck_model():
    print("\n[3/6] Training bottleneck classifier …")
    df = _gen_bottleneck_data()
    X = df.drop("label_bottleneck", axis=1)
    y = df["label_bottleneck"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.06,
        subsample=0.8, colsample_bytree=0.8,
        use_label_encoder=False, eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

    preds = model.predict(X_te)
    probs = model.predict_proba(X_te)[:, 1]
    print(f"  ROC-AUC: {roc_auc_score(y_te, probs):.4f}  F1: {f1_score(y_te, preds):.4f}")
    _save(model, "bottleneck_model")


# ══════════════════════════════════════════════════════════════════════════════
# 4. ASSIGNEE RANKER  (XGBoostClassifier — pairwise success prediction)
#    Features: skill_match_score, dev_load, dev_past_success_rate,
#              avg_completion_speed, complexity
# ══════════════════════════════════════════════════════════════════════════════

def _gen_assignee_data():
    skill_match = np.clip(np.random.beta(4, 2, N), 0.0, 1.0)
    dev_load = np.random.randint(0, 15, N)
    past_success = np.clip(np.random.beta(5, 2, N), 0.0, 1.0)
    avg_speed = np.clip(np.random.normal(1.0, 0.25, N), 0.3, 2.0)
    complexity = np.random.randint(0, 3, N)

    score = (
        skill_match * 0.45
        + past_success * 0.30
        + avg_speed / 2 * 0.15
        - dev_load / 15 * 0.20
        - complexity / 2 * 0.10
    ) + np.random.normal(0, 0.07, N)
    label = (score > 0.45).astype(int)

    return pd.DataFrame({
        "skill_match_score": skill_match,
        "dev_load": dev_load.astype(float),
        "past_success_rate": past_success,
        "avg_completion_speed": avg_speed,
        "complexity": complexity.astype(float),
        "label_success": label,
    })


def train_assignee_model():
    print("\n[4/6] Training assignee success classifier …")
    df = _gen_assignee_data()
    X = df.drop("label_success", axis=1)
    y = df["label_success"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        use_label_encoder=False, eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

    preds = model.predict(X_te)
    probs = model.predict_proba(X_te)[:, 1]
    print(f"  ROC-AUC: {roc_auc_score(y_te, probs):.4f}  F1: {f1_score(y_te, preds):.4f}")
    _save(model, "assignee_model")


# ══════════════════════════════════════════════════════════════════════════════
# 5. NEXT-TASK RANKER  (XGBoostClassifier — task selection score)
#    Features: priority, skill_match, dependency_blocked, complexity,
#              story_points, days_since_created
# ══════════════════════════════════════════════════════════════════════════════

PRIORITY_MAP = {"CRITICAL": 3, "HIGH": 2, "MEDIUM": 1, "LOW": 0}


def _gen_next_task_data():
    priority = np.random.randint(0, 4, N)           # 0=LOW..3=CRITICAL
    skill_match = np.clip(np.random.beta(3, 2, N), 0.0, 1.0)
    dep_blocked = np.random.binomial(1, 0.2, N)     # 1=blocked
    complexity = np.random.randint(0, 3, N)
    story_points = np.random.choice([1, 2, 3, 5, 8, 13], N).astype(float)
    days_created = np.random.randint(0, 30, N).astype(float)

    score = (
        priority / 3 * 0.40
        + skill_match * 0.30
        - dep_blocked * 0.20
        - complexity / 2 * 0.05
        + days_created / 30 * 0.05  # older tasks get slight boost
    ) + np.random.normal(0, 0.06, N)
    label = (score > 0.35).astype(int)

    return pd.DataFrame({
        "priority": priority.astype(float),
        "skill_match": skill_match,
        "dep_blocked": dep_blocked.astype(float),
        "complexity": complexity.astype(float),
        "story_points": story_points,
        "days_since_created": days_created,
        "label_should_pick": label,
    })


def train_next_task_model():
    print("\n[5/6] Training next-task ranker …")
    df = _gen_next_task_data()
    X = df.drop("label_should_pick", axis=1)
    y = df["label_should_pick"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.75,
        use_label_encoder=False, eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

    preds = model.predict(X_te)
    probs = model.predict_proba(X_te)[:, 1]
    print(f"  ROC-AUC: {roc_auc_score(y_te, probs):.4f}  F1: {f1_score(y_te, preds):.4f}")
    _save(model, "next_task_model")


# ══════════════════════════════════════════════════════════════════════════════
# 6. SPRINT OUTCOME  (XGBoostClassifier + XGBoostRegressor)
#    Classification: will sprint succeed?
#    Regression: completion percentage
# ══════════════════════════════════════════════════════════════════════════════

def _gen_sprint_data():
    total_sp = np.random.randint(10, 100, N).astype(float)
    avg_delay_prob = np.clip(np.random.beta(2, 4, N), 0.0, 1.0)
    team_velocity = np.clip(np.random.normal(55, 20, N), 10, 120).astype(float)
    blocked_tasks = np.random.randint(0, 10, N).astype(float)
    avg_complexity = np.random.uniform(0, 2, N)

    capacity_ratio = np.clip(team_velocity / total_sp, 0.1, 2.0)

    completion_pct = np.clip(
        capacity_ratio * 100 * (1 - avg_delay_prob * 0.4)
        - blocked_tasks * 2
        + np.random.normal(0, 5, N),
        0, 100
    )
    label_success = (completion_pct >= 70).astype(int)

    return pd.DataFrame({
        "total_story_points": total_sp,
        "avg_delay_prob": avg_delay_prob,
        "team_velocity": team_velocity,
        "blocked_tasks": blocked_tasks,
        "avg_complexity": avg_complexity,
        "label_completion_percent": completion_pct,
        "label_success": label_success,
    })


def train_sprint_model():
    print("\n[6/6] Training sprint outcome models …")
    df = _gen_sprint_data()
    features = ["total_story_points", "avg_delay_prob", "team_velocity", "blocked_tasks", "avg_complexity"]
    X = df[features]

    # 6a — Regression: completion %
    y_reg = df["label_completion_percent"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y_reg, test_size=0.2, random_state=42)
    reg_model = xgb.XGBRegressor(
        n_estimators=250, max_depth=5, learning_rate=0.04,
        subsample=0.85, colsample_bytree=0.8, random_state=42,
    )
    reg_model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)
    mae = mean_absolute_error(y_te, reg_model.predict(X_te))
    print(f"  Completion% regressor  MAE: {mae:.2f}%")
    _save(reg_model, "sprint_completion_model")

    # 6b — Classification: success/failure
    y_cls = df["label_success"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y_cls, test_size=0.2, random_state=42)
    cls_model = xgb.XGBClassifier(
        n_estimators=200, max_depth=4, learning_rate=0.05,
        use_label_encoder=False, eval_metric="logloss", random_state=42,
    )
    cls_model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)
    probs = cls_model.predict_proba(X_te)[:, 1]
    print(f"  Success classifier     ROC-AUC: {roc_auc_score(y_te, probs):.4f}")
    _save(cls_model, "sprint_success_model")


# ── Entry point ────────────────────────────────────────────────────────────────

def train_all():
    print("=" * 60)
    print("JustBuildIt — Training all 6 XGBoost ML models")
    print("=" * 60)
    train_delay_model()
    train_duration_model()
    train_bottleneck_model()
    train_assignee_model()
    train_next_task_model()
    train_sprint_model()
    print("\n✅ All models trained and saved to", MODEL_DIR)


if __name__ == "__main__":
    train_all()
