import pandas as pd


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create derived features from raw task data.
    """
    df = df.copy()

    # Urgency score: inversely proportional to days remaining
    df["urgency"] = 1 / (df["days_remaining"].clip(lower=1))

    # Overload flag
    df["assignee_overloaded"] = (df["assignee_load"] > 10).astype(int)

    # Risk score composite
    df["risk_score"] = (
        df["complexity"] * 0.3 +
        df["urgency"] * 0.4 +
        df["open_blockers"] * 0.2 +
        df["assignee_overloaded"] * 0.1
    )

    return df
