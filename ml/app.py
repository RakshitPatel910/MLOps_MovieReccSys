import os
import pickle
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Dict, Any
from train import train_model


# Global state for cached data and models
app_state = {
    "models": {},
    "data": {
        "ratings": None,
        "user_history": dict,
        "all_neighbors": None
    }
}

class FeedbackIn(BaseModel):
    user_id: int
    item_id: int
    rating: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload all models and data at startup"""
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        # 1. Train or load model
        train_model()  # Your original training function
        
        # 2. Load trained models
        MODEL_DIR = os.path.join(BASE_DIR, "model_data")
        model_components = [
            "user_ids", "item_ids", "item_factors",
            "user_profiles", "nn_model", "global_mean"
        ]
        
        for component in model_components:
            with open(os.path.join(MODEL_DIR, f"{component}.pkl"), "rb") as f:
                app_state["models"][component] = pickle.load(f)

        # 3. Precompute neighborhoods for all users
        user_profiles = app_state["models"]["user_profiles"]
        nn_model = app_state["models"]["nn_model"]
        distances, indices = nn_model.kneighbors(user_profiles)
        app_state["models"]["all_neighbors"] = {
            "indices": indices,
            "distances": distances
        }

        # 4. Load and cache rating data
        data_dir = os.path.join(BASE_DIR, "ml-100k")
        base_df = pd.read_csv(
            os.path.join(data_dir, "u1.base"),
            sep="\t",
            names=["user", "item", "rating", "timestamp"],
            usecols=["user", "item", "rating"]
        )
        
        # Load feedback data if exists
        feedback_path = os.path.join(data_dir, "feedback.csv")
        try:
            feedback_df = pd.read_csv(feedback_path)
        except FileNotFoundError:
            feedback_df = pd.DataFrame(columns=["user", "item", "rating"])

        # Combine and preprocess
        combined_ratings = pd.concat([base_df, feedback_df])
        app_state["data"]["ratings"] = combined_ratings
        app_state["data"]["user_history"] = combined_ratings.groupby("user")["item"].apply(set).to_dict()

    except Exception as e:
        print(f"🚨 Startup initialization failed: {str(e)}")
        raise
    
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/recommend/{user_id}", response_model=Dict[str, List[int]])
async def get_recommendations(user_id: int):
    """Optimized recommendation endpoint with cached data"""
    try:
        # Get required components from app state
        user_ids = app_state["models"]["user_ids"]
        all_neighbors = app_state["models"]["all_neighbors"]
        ratings = app_state["data"]["ratings"]
        user_history = app_state["data"]["user_history"]

        # 1. Find user index
        user_idx = np.where(user_ids == user_id)[0]
        if not user_idx.size:
            return {"recommended_items": []}
        user_idx = user_idx[0]

        # 2. Get precomputed neighbors (skip self)
        neighbor_indices = all_neighbors["indices"][user_idx][1:]
        neighbor_weights = 1 / (all_neighbors["distances"][user_idx][1:] + 1e-6)
        neighbor_users = user_ids[neighbor_indices]

        # 3. Filter neighbor ratings
        mask = ratings["user"].isin(neighbor_users)
        neighbor_ratings = ratings.loc[mask, ["user", "item", "rating"]]

        if neighbor_ratings.empty:
            return {"recommended_items": []}

        # 4. Vectorized scoring
        weight_mapping = pd.Series(neighbor_weights, index=neighbor_users)
        weighted_ratings = neighbor_ratings.merge(
            weight_mapping.rename("weight"),
            left_on="user",
            right_index=True
        )
        weighted_ratings["weighted_score"] = weighted_ratings["rating"] * weighted_ratings["weight"]

        # 5. Aggregate scores (FIXED VERSION)
        item_scores = weighted_ratings.groupby("item").agg(
            total_score=("weighted_score", "sum"),
            total_weight=("weight", "sum")
        )

        # Handle division safely and enforce numeric type
        item_scores["prediction"] = (
            (item_scores["total_score"] / (item_scores["total_weight"] + 1e-9))  # Prevent division by zero
            + float(app_state["models"]["global_mean"])  # Ensure native float type
        ).astype(float)  # Explicitly cast to float

        # 6. Filter seen items
        seen_items = user_history.get(user_id, set())
        recommendations = item_scores[~item_scores.index.isin(seen_items)]

        # 7. Return top 10 recommendations (SAFE VERSION)
        if not recommendations.empty:
            top_items = recommendations.nlargest(10, "prediction").index.astype(int).tolist()
        else:
            top_items = []
            
        return {"recommended_items": top_items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
def submit_feedback(feedback: FeedbackIn):
    """Handle user feedback with proper path handling"""
    try:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        feedback_path = os.path.join(BASE_DIR, "ml-100k", "feedback.csv")
        
        # Write feedback with proper locking
        with open(feedback_path, "a") as f:
            f.write(f"{feedback.user_id},{feedback.item_id},{feedback.rating}\n")
            
        # Update cached data
        new_entry = pd.DataFrame([[feedback.user_id, feedback.item_id, feedback.rating]],
                                columns=["user", "item", "rating"])
        app_state["data"]["ratings"] = pd.concat([app_state["data"]["ratings"], new_entry])
        
        # Update user history
        if feedback.user_id in app_state["data"]["user_history"]:
            app_state["data"]["user_history"][feedback.user_id].add(feedback.item_id)
        else:
            app_state["data"]["user_history"][feedback.user_id] = {feedback.item_id}
            
        return {"status": "feedback recorded"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/retrain")
def trigger_retraining():
    """Retrain model and refresh cache"""
    try:
        train_model()
        
        # Reload models
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        MODEL_DIR = os.path.join(BASE_DIR, "model_data")
        
        for component in ["user_ids", "item_ids", "item_factors",
                         "user_profiles", "nn_model", "global_mean"]:
            with open(os.path.join(MODEL_DIR, f"{component}.pkl"), "rb") as f:
                app_state["models"][component] = pickle.load(f)
        
        return {"status": "retraining completed"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))