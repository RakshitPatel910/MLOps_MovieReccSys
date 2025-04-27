# app.py
import os
import pickle
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Dict, List

from data_manager import data_manager, DATA_DIR, MODEL_DIR
from model_manager import model_manager

class UserCreate(BaseModel):
    age: int
    gender: str
    occupation: str
    zip_code: str = "00000"

class FeedbackIn(BaseModel):
    user_id: int
    item_id: int
    rating: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize data structures and load or train models
    data_manager.initialize_state()
    # Check for existing model artifacts
    user_ids_path = os.path.join(MODEL_DIR, "user_ids.pkl")
    if not os.path.exists(user_ids_path):
        model_manager.train_model()
    else:
        try:
            for component in [
                "user_ids", "item_ids", "item_factors",
                "user_profiles", "nn_model", "global_mean"
            ]:
                path = os.path.join(MODEL_DIR, f"{component}.pkl")
                with open(path, "rb") as f:
                    data_manager.app_state["models"][component] = pickle.load(f)

            # Precompute user–user neighbors
            user_profiles = data_manager.app_state["models"]["user_profiles"]
            nn_model = data_manager.app_state["models"]["nn_model"]
            distances, indices = nn_model.kneighbors(user_profiles)
            data_manager.app_state["models"]["all_neighbors"] = {
                "indices": indices,
                "distances": distances
            }
        except Exception as e:
            raise RuntimeError(f"Model loading failed: {e}")
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/users/create")
async def create_user(user_data: UserCreate):
    try:
        new_id = data_manager.get_next_user_id()
        user_meta_path = os.path.join(DATA_DIR, "u.user")
        with open(user_meta_path, "a") as f:
            f.write(
                f"{new_id}|{user_data.age}|{user_data.gender}|"
                f"{user_data.occupation}|{user_data.zip_code}\n"
            )
        return {"user_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackIn):
    try:
        data_manager.add_feedback(feedback.user_id, feedback.item_id, feedback.rating)
        # Retrain if we've collected 100 new feedbacks
        if data_manager.check_retrain_needed(threshold=100):
            model_manager.train_model()
        return {"status": "feedback recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommend/{user_id}", response_model=Dict[str, List[int]])
async def get_recommendations(user_id: int):
    try:
        user_ids     = data_manager.app_state["models"]["user_ids"]
        all_neighbors= data_manager.app_state["models"]["all_neighbors"]
        ratings      = data_manager.app_state["data"]["ratings"]
        user_history = data_manager.app_state["data"]["user_history"]

        # 1. Find internal index
        idx_array = np.where(user_ids == user_id)[0]
        if not idx_array.size:
            return {"recommended_items": []}
        user_idx = idx_array[0]

        # 2. Precomputed neighbors (skip self)
        neighbor_idx     = all_neighbors["indices"][user_idx][1:]
        neighbor_weights = 1 / (all_neighbors["distances"][user_idx][1:] + 1e-6)
        neighbor_users   = user_ids[neighbor_idx]

        # 3. Filter ratings from neighbors
        mask        = ratings["user"].isin(neighbor_users)
        nbr_ratings = ratings.loc[mask, ["user", "item", "rating"]]
        if nbr_ratings.empty:
            return {"recommended_items": []}

        # 4. Weight & score
        weight_map = pd.Series(neighbor_weights, index=neighbor_users)
        wr = nbr_ratings.merge(
            weight_map.rename("weight"),
            left_on="user", right_index=True
        )
        wr["weighted_score"] = wr["rating"] * wr["weight"]

        # 5. Aggregate
        item_scores = wr.groupby("item").agg(
            total_score = ("weighted_score", "sum"),
            total_weight= ("weight", "sum")
        )
        global_mean = float(data_manager.app_state["models"]["global_mean"])
        item_scores["prediction"] = (
            item_scores["total_score"] / (item_scores["total_weight"] + 1e-9)
        ) + global_mean
        item_scores["prediction"] = item_scores["prediction"].astype(float)

        # 6. Remove seen items
        seen       = user_history.get(user_id, set())
        candidates = item_scores[~item_scores.index.isin(seen)]

        # 7. Return top-10
        top_n = candidates.nlargest(10, "prediction").index.astype(int).tolist()
        return {"recommended_items": top_n}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/retrain")
async def trigger_retraining():
    try:
        model_manager.train_model()
        return {"status": "retraining completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
