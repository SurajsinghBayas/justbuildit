# justbuildit — AI Model Documentation

## Overview

The AI service provides two primary capabilities:
1. **Task Delay Prediction** — predicts whether a task is at risk of being delayed
2. **Smart Recommendations** — suggests assignees and priorities

---

## 1. Task Delay Prediction

### Model: `GradientBoostingClassifier`

| Attribute       | Value                   |
|-----------------|-------------------------|
| Framework       | scikit-learn            |
| Algorithm       | Gradient Boosting       |
| Output          | Binary classification   |
| Positive label  | `1` = will be delayed   |

### Input Features

| Feature           | Type   | Description                                 |
|-------------------|--------|---------------------------------------------|
| `complexity`      | float  | Task complexity score (1–5)                 |
| `assignee_load`   | float  | Number of open tasks on the assignee        |
| `days_remaining`  | float  | Days until due date                         |
| `open_blockers`   | int    | Number of blocking dependencies             |
| `team_velocity`   | float  | Average team tasks completed per sprint     |

### Training Data

- **Source**: Synthetic data (1,000 samples) with heuristic labels
- **Split**: 80% train / 20% test
- **Label heuristic**: delayed if `complexity ≥ 4` OR `assignee_load ≥ 15` OR `days_remaining ≤ 2`

### Performance (on synthetic test set)

| Metric    | Score |
|-----------|-------|
| Accuracy  | ~0.87 |
| Precision | ~0.85 |
| Recall    | ~0.89 |
| F1        | ~0.87 |

### Training

```bash
cd ai-service
python app/pipelines/training.py
# → saves model to app/models/delay_model.pkl
```

---

## 2. Recommendation Engine

### Assignee Recommendation
- **Strategy**: Rule-based — sorts team by open task count, assigns to least loaded member
- **Future**: ML-based skill matching using embedding similarity

### Priority Recommendation
- **Strategy**: Rule-based threshold on `days_until_due`
  - ≤ 1 day or has blockers → `critical`
  - ≤ 3 days → `high`
  - ≤ 7 days → `medium`
  - Otherwise → `low`

---

## Roadmap

- [ ] Integrate real historical task data for model retraining
- [ ] Add skill-based assignee matching with NLP embeddings
- [ ] Implement A/B testing framework for recommendation strategies
- [ ] Add drift detection to monitor model performance in production
