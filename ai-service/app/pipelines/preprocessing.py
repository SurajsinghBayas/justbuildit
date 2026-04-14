import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Tuple


def preprocess(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Clean and normalize raw task feature data.

    Returns:
        Processed dataframe and a dict of fitted transformers for reuse.
    """
    df = df.copy()
    transformers = {}

    # Drop nulls
    df = df.dropna()

    # Normalize numeric columns
    numeric_cols = ["assignee_load", "days_remaining", "team_velocity"]
    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    transformers["scaler"] = scaler

    # Clip outliers
    df["complexity"] = df["complexity"].clip(1, 5)
    df["open_blockers"] = df["open_blockers"].clip(0, 10)

    return df, transformers
