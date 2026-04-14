import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os


def generate_synthetic_data(n: int = 1000) -> pd.DataFrame:
    """Generate synthetic training data for task delay prediction."""
    np.random.seed(42)
    df = pd.DataFrame({
        "complexity": np.random.randint(1, 6, n),
        "assignee_load": np.random.randint(1, 20, n),
        "days_remaining": np.random.randint(0, 30, n),
        "open_blockers": np.random.randint(0, 5, n),
        "team_velocity": np.random.uniform(5, 20, n),
    })
    # Heuristic label: delayed if complex + overloaded + few days remaining
    df["delayed"] = (
        (df["complexity"] >= 4) |
        (df["assignee_load"] >= 15) |
        (df["days_remaining"] <= 2)
    ).astype(int)
    return df


def train_model(output_path: str = "app/models/delay_model.pkl"):
    df = generate_synthetic_data()
    X = df.drop("delayed", axis=1)
    y = df["delayed"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)
    model.fit(X_train, y_train)

    print(classification_report(y_test, model.predict(X_test)))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    joblib.dump(model, output_path)
    print(f"Model saved to {output_path}")


if __name__ == "__main__":
    train_model()
