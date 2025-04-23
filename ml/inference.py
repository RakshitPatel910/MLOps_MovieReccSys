import os
import pickle
import numpy as np
import pandas as pd
from typing import List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model_data")
RATINGS_FILE = os.path.join(BASE_DIR, "ml-100k", "u1.base")
FEEDBACK_FILE = os.path.join(BASE_DIR, "ml-100k", "feedback.csv")

def load_model_components():
    components = {}
    for component in ["user_ids", "item_ids", "item_factors", 
                     "user_profiles", "nn_model", "global_mean"]:
        with open(os.path.join(MODEL_DIR, f"{component}.pkl"), "rb") as f:
            components[component] = pickle.load(f)
    return components

def recommend(user_id: int, top_n: int = 10) -> List[int]:
    # Load trained models
    model = load_model_components()
    
    # Find user index
    try:
        user_idx = np.where(model["user_ids"] == user_id)[0][0]
    except IndexError:
        return []
    
    # Find similar users
    distances, indices = model["nn_model"].kneighbors(
        [model["user_profiles"][user_idx]]
    )
    neighbor_indices = indices[0][1:]  # Exclude self
    neighbor_weights = 1 / (distances[0][1:] + 1e-6)
    
    # Load rating data
    try:
        feedback_df = pd.read_csv(FEEDBACK_FILE, names=["user", "item", "rating"])
    except FileNotFoundError:
        feedback_df = pd.DataFrame(columns=["user", "item", "rating"])
        
    base_df = pd.read_csv(
        RATINGS_FILE,
        sep="\t",
        names=["user", "item", "rating", "timestamp"],
        usecols=["user", "item", "rating"]
    )
    combined_ratings = pd.concat([base_df, feedback_df])
    
    # Calculate weighted scores
    neighbor_users = model["user_ids"][neighbor_indices]
    neighbor_ratings = combined_ratings[combined_ratings["user"].isin(neighbor_users)]
    
    if neighbor_ratings.empty:
        return []
    
    # Score calculation
    score_map = {}
    weight_map = dict(zip(neighbor_users, neighbor_weights))
    
    for _, row in neighbor_ratings.iterrows():
        item = row["item"]
        score = weight_map[row["user"]] * row["rating"]
        if item in score_map:
            score_map[item].append(score)
        else:
            score_map[item] = [score]
    
    # Generate predictions
    predictions = {}
    for item, scores in score_map.items():
        total_weight = sum(weight_map[u] for u in neighbor_users if u in neighbor_ratings[neighbor_ratings["item"] == item]["user"].values)
        predictions[item] = (sum(scores) / total_weight) + model["global_mean"]
    
    # Filter seen items
    user_history = combined_ratings[combined_ratings["user"] == user_id]["item"].unique()
    recommendations = [
        (item, score)
        for item, score in predictions.items()
        if item not in user_history
    ]
    
    # Return top N items as native Python integers
    return [
        int(item[0]) 
        for item in sorted(recommendations, key=lambda x: x[1], reverse=True)[:top_n]
    ]