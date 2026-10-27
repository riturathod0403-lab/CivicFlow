"""
CivicFlow - Model Training Pipeline (train_model.py)
Trains a lightweight Scikit-learn text classifier using TF-IDF and Logistic Regression / Multinomial Naive Bayes.
Saves model artifacts via Joblib and prints real classification evaluation metrics.
NOTE: Uses synthetic demonstration data. Limitations documented in README.md.
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score, f1_score
import joblib

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.joblib")
DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sample_complaints.csv")

def train_and_save():
    print("=" * 60)
    print("CivicFlow: Training Municipal Complaint Classifier")
    print("Data Source: Synthetic demonstration dataset (data/sample_complaints.csv)")
    print("=" * 60)

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} labelled complaint records across {df['category'].nunique()} categories.")
    print("Class distribution:")
    print(df['category'].value_counts())

    X = df["text"].values
    y = df["category"].values

    # Stratified split with reproducible random state
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # Scikit-learn Pipeline: TF-IDF Vectorizer + Multinomial Naive Bayes
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words='english', min_df=1, sublinear_tf=True)),
        ('clf', MultinomialNB(alpha=0.5))
    ])

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

    print("\n--- Model Evaluation Results (Test Set) ---")
    print(f"Accuracy:  {acc:.4f} ({acc*100:.2f}%)")
    print(f"F1-Score:  {f1:.4f} (Weighted)")
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # Save model and metadata
    artifact = {
        "pipeline": pipeline,
        "classes": list(pipeline.classes_),
        "accuracy": float(acc),
        "f1_score": float(f1),
        "dataset_size": len(df)
    }

    joblib.dump(artifact, MODEL_PATH)
    print(f"Model saved successfully to: {MODEL_PATH}")
    return artifact

if __name__ == "__main__":
    train_and_save()
