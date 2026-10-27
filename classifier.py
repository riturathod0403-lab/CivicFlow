"""
CivicFlow - Complaint Classifier (classifier.py)
Loads trained Scikit-learn model, provides category prediction, confidence scoring,
department recommendations, and triggers manual review for low confidence (<60%).
"""

import os
import joblib
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.joblib")

CATEGORY_DEPARTMENT_MAP = {
    "potholes": "Roads & Infrastructure",
    "garbage": "Solid Waste Management",
    "streetlights": "Electrical & Lighting",
    "drainage": "Drainage & Stormwater",
    "water_supply": "Water Works & Supply",
    "sanitation": "Public Health & Sanitation",
    "other": "General Administration"
}

CATEGORY_FRIENDLY_NAMES = {
    "potholes": "Potholes & Road Damage",
    "garbage": "Garbage & Waste Dump",
    "streetlights": "Streetlights & Electricity",
    "drainage": "Drainage & Sewerage",
    "water_supply": "Drinking Water Supply",
    "sanitation": "Sanitation & Public Health",
    "other": "Other Municipal Issues"
}

_MODEL_CACHE = None

def load_classifier():
    """Loads saved model artifact or trains if not yet present."""
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    if os.path.exists(MODEL_PATH):
        try:
            _MODEL_CACHE = joblib.load(MODEL_PATH)
            return _MODEL_CACHE
        except Exception as e:
            print(f"Warning: Failed to load {MODEL_PATH}: {e}. Retraining...")

    from train_model import train_and_save
    _MODEL_CACHE = train_and_save()
    return _MODEL_CACHE

def classify_complaint(text: str, confidence_threshold: float = 0.60) -> dict:
    """
    Classifies complaint text.
    Returns:
    {
        'category': str,
        'friendly_category': str,
        'department': str,
        'confidence': float,
        'needs_review': bool,
        'all_probabilities': dict[str, float]
    }
    """
    if not text or not text.strip():
        return {
            "category": "other",
            "friendly_category": CATEGORY_FRIENDLY_NAMES["other"],
            "department": CATEGORY_DEPARTMENT_MAP["other"],
            "confidence": 0.0,
            "needs_review": True,
            "all_probabilities": {}
        }

    artifact = load_classifier()
    pipeline = artifact["pipeline"]
    classes = pipeline.classes_

    # Predict probabilities
    probs = pipeline.predict_proba([text])[0]
    best_idx = np.argmax(probs)
    predicted_category = classes[best_idx]
    confidence = float(probs[best_idx])

    all_probs = {cls: round(float(p), 3) for cls, p in zip(classes, probs)}

    # Recommend department based on category
    department = CATEGORY_DEPARTMENT_MAP.get(predicted_category, "General Administration")

    # Flag for manual administrative review if confidence is under threshold
    needs_review = bool(confidence < confidence_threshold)

    return {
        "category": predicted_category,
        "friendly_category": CATEGORY_FRIENDLY_NAMES.get(predicted_category, predicted_category),
        "department": department,
        "confidence": round(confidence, 3),
        "needs_review": needs_review,
        "all_probabilities": all_probs
    }
