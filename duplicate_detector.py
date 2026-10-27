"""
CivicFlow - Duplicate Complaint Detector (duplicate_detector.py)
Uses TF-IDF Vectorization and Cosine Similarity to compare incoming complaint descriptions
against active municipal records and flag potential duplicates.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def find_duplicates(new_text: str, existing_complaints: list[dict], threshold: float = 0.60, top_k: int = 3) -> dict:
    """
    Compares new_text against description + title of existing_complaints.
    Returns:
    {
        'is_duplicate': bool,
        'top_similarity': float,
        'parent_id': str or None,
        'matches': list[dict]
    }
    """
    if not existing_complaints or not new_text.strip():
        return {
            "is_duplicate": False,
            "top_similarity": 0.0,
            "parent_id": None,
            "matches": []
        }

    corpus = []
    metadata = []

    for c in existing_complaints:
        # Combine title and description for richer semantic matching
        full_text = f"{c.get('title', '')} {c.get('description', '')}".strip()
        if full_text:
            corpus.append(full_text)
            metadata.append(c)

    if not corpus:
        return {
            "is_duplicate": False,
            "top_similarity": 0.0,
            "parent_id": None,
            "matches": []
        }

    # Include new_text in the TF-IDF vectorizer fit
    all_docs = [new_text] + corpus
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words='english', min_df=1)
    tfidf_matrix = vectorizer.fit_transform(all_docs)

    # Compute cosine similarity between the new query (index 0) and all existing docs (indices 1..N)
    query_vector = tfidf_matrix[0:1]
    corpus_vectors = tfidf_matrix[1:]

    sim_scores = cosine_similarity(query_vector, corpus_vectors)[0]

    # Find highest similarity indices
    sorted_indices = np.argsort(sim_scores)[::-1]

    matches = []
    top_sim = 0.0
    parent_id = None

    for idx in sorted_indices[:top_k]:
        score = float(sim_scores[idx])
        if score > 0.15:  # Only capture non-trivial similarity
            match_data = metadata[idx]
            match_entry = {
                "id": match_data["id"],
                "title": match_data["title"],
                "category": match_data.get("category", "Unknown"),
                "status": match_data.get("status", "Unknown"),
                "location": match_data.get("location", "Unknown"),
                "similarity_score": round(score, 3),
                "created_at": match_data.get("created_at", "")
            }
            matches.append(match_entry)

    if matches and matches[0]["similarity_score"] >= threshold:
        top_sim = matches[0]["similarity_score"]
        parent_id = matches[0]["id"]
        is_duplicate = True
    else:
        top_sim = matches[0]["similarity_score"] if matches else 0.0
        is_duplicate = False

    return {
        "is_duplicate": is_duplicate,
        "top_similarity": top_sim,
        "parent_id": parent_id,
        "matches": matches
    }
