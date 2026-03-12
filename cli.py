import numpy as np
import torch
import pandas as pd


def predict_embedding(model, hsqc):
    """Compute embedding vector from HSQC numpy array using the SMART model."""
    hsqc = torch.FloatTensor(hsqc)
    if len(hsqc.size()) == 2:
        hsqc = hsqc.unsqueeze(0)
    embedding = model.compute_image(hsqc.unsqueeze(1))
    return embedding.squeeze(0).numpy()


def search_database(db, embedding_matrix, query_embedding, topk=100):
    """Search the database by cosine similarity and return top-k results as a DataFrame."""
    query_norm = np.sqrt(np.dot(query_embedding, query_embedding))
    normed_query = query_embedding / query_norm

    # Cosine similarities via dot product (embeddings are already normalized)
    similarities = embedding_matrix.dot(normed_query)

    top_indices = np.argsort(similarities)[::-1][:topk]

    results = []
    for idx in top_indices:
        entry = db[idx]
        results.append({
            "DBID": entry["ID"],
            "Name": entry.get("Compound_name", ""),
            "SMILES": entry.get("SMILES", ""),
            "MW": entry.get("MW", 0),
            "From": entry.get("From", ""),
            "Cosine score": float(similarities[idx]),
        })

    return pd.DataFrame(results)
