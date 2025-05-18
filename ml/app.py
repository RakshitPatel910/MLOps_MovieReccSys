import os
import pickle
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Dict, List, Union

from data_manager import data_manager, DATA_DIR, MODEL_DIR
from model_manager import model_manager

# ─── Pydantic schemas ─────────────────────────────────────────────
class UserCreate(BaseModel):
    age: int
    gender: str
    occupation: str
    zip_code: str = "00000"

class FeedbackIn(BaseModel):
    user_id: int
    item_id: int
    rating: float

# ─── FastAPI app with lifespan ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize data state
    data_manager.initialize_state()

    # Retrain if no model yet
    if not os.path.exists(os.path.join(MODEL_DIR, "user_ids.pkl")):
        model_manager.train_model()

    # Load all model artifacts + transformers
    try:
        models = {}
        for name in [
            "user_ids", "item_ids", "item_factors",
            "user_profiles", "nn_model", "global_mean",
            "svd", "scaler_age", "ohe_gender", "ohe_occupation"
        ]:
            path = os.path.join(MODEL_DIR, f"{name}.pkl")
            with open(path, "rb") as f:
                models[name] = pickle.load(f)

        # Precompute neighbor lists for existing users
        up = models["user_profiles"]
        dists, idxs = models["nn_model"].kneighbors(up)
        models["all_neighbors"] = {"distances": dists, "indices": idxs}

        data_manager.app_state["models"] = models

    except Exception as e:
        raise RuntimeError(f"Model loading failed: {e}")

    yield

app = FastAPI(lifespan=lifespan)

# ─── Endpoints ─────────────────────────────────────────────────────
@app.get("/ml/users")
async def get_all_users():
    try:
        M = data_manager.app_state["models"]
        svd_components = 50  # Match your TruncatedSVD configuration
        
        user_meta = []
        for idx, user_id in enumerate(M["user_ids"]):
            profile = M["user_profiles"][idx]
            
            # Convert numpy types to native Python types
            age = float(profile[svd_components])
            gender = 'M' if profile[svd_components + 1] > 0.5 else 'F'
            
            # Handle occupation one-hot encoding
            occ_features = profile[svd_components + 2:svd_components + 23]
            occupation = str(M["ohe_occupation"].inverse_transform([occ_features])[0][0])

            user_meta.append({
                "user_id": int(user_id),  # Convert numpy.int64 to Python int
                "age": age,
                "gender": gender,
                "occupation": occupation
            })
            
        return user_meta
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ml/ratings")
async def get_all_ratings():
    try:
        base_path = os.path.join(DATA_DIR, "u1.base")
        feedback_path = os.path.join(DATA_DIR, "feedback.csv")

        # Read base ratings with proper typing
        base_df = pd.read_csv(
            base_path,
            sep='\t',
            names=["user_id", "item_id", "rating", "timestamp"],
            dtype={
                'user_id': 'int32',
                'item_id': 'int32', 
                'rating': 'float32',
                'timestamp': 'int64'
            }
        )

        # Handle feedback with safe type conversion
        try:
            feedback_df = pd.read_csv(
                feedback_path,
                header=0,
                names=["user_id", "item_id", "rating"],
                dtype={
                    'user_id': 'int32',
                    'item_id': 'int32',
                    'rating': 'float32'
                }
            )
            # Convert timestamp properly
            current_ts = int(pd.Timestamp.now().timestamp())
            feedback_df = feedback_df.assign(timestamp=current_ts)
            
        except FileNotFoundError:
            feedback_df = pd.DataFrame(columns=["user_id", "item_id", "rating", "timestamp"])

        # Combine and clean data
        combined = pd.concat([base_df, feedback_df], ignore_index=True)
        
        # Convert dtypes safely
        combined = combined.astype({
            'user_id': 'int32',
            'item_id': 'int32',
            'rating': 'float32',
            'timestamp': 'int64'
        }, errors='ignore')

        # Remove invalid rows
        combined = combined.dropna(subset=['user_id', 'item_id', 'rating'])
        
        return combined.to_dict(orient="records")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/users/create")
async def create_user(user_data: UserCreate):
    try:
        raw = data_manager.get_next_user_id()
        new_id = int(raw)
        path = os.path.join(DATA_DIR, "u.user")
        with open(path, "a") as f:
            f.write(f"{new_id}|{user_data.age}|{user_data.gender}|"
                    f"{user_data.occupation}|{user_data.zip_code}\n")
            
        print(new_id)
        return {"user_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/feedback")
async def submit_feedback(feedback: FeedbackIn):
    try:
        data_manager.add_feedback(feedback.user_id, feedback.item_id, feedback.rating)
        if data_manager.check_retrain_needed(threshold=100):
            model_manager.train_model()
        return {"status": "feedback recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(
    "/ml/recommend/{user_id}",
    response_model=Dict[str, List[Dict[str, Union[int, str]]]]
)
async def get_recommendations(user_id: int):
    try:
        M            = data_manager.app_state["models"]
        ratings      = data_manager.app_state["data"]["ratings"]
        user_history = data_manager.app_state["data"]["user_history"]
        item_titles  = data_manager.app_state["data"]["item_titles"]

        # helper for any profile → neighbor users & weights
        def neighbors_from(profile: np.ndarray):
            d, i = M["nn_model"].kneighbors(profile)
            neigh = i[0][1:]
            w     = 1 / (d[0][1:] + 1e-6)
            return M["user_ids"][neigh], w

        # ─── Cold-start branch ───────────────────────────────────
        if user_id not in M["user_ids"]:
            try:
                meta = pd.read_csv(
                    os.path.join(DATA_DIR, "u.user"),
                    sep="|",
                    names=["user_id","age","gender","occupation","zip_code"]
                ).set_index("user_id")
                if user_id not in meta.index:
                    return {"recommended_items": []}

                row = meta.loc[user_id]
                # Transform using DataFrames to include feature names
                age_df = pd.DataFrame([[row.age]], columns=["age"])
                age_v = M["scaler_age"].transform(age_df)

                gender_df = pd.DataFrame([[row.gender]], columns=["gender"])
                gender_v = M["ohe_gender"].transform(gender_df)

                occupation_df = pd.DataFrame([[row.occupation]], columns=["occupation"])
                occ_v = M["ohe_occupation"].transform(occupation_df)

                zeros = np.zeros((1, M["svd"].n_components))
                profile = np.hstack([zeros, age_v, gender_v, occ_v])
                neighbors, weights = neighbors_from(profile)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Cold-start processing failed: {str(e)}")

        # ─── Existing-user branch ───────────────────────────────
        else:
            idxs = np.where(M["user_ids"] == user_id)[0]
            if not idxs.size:
                return {"recommended_items": []}
            uprof = M["user_profiles"][idxs[0]].reshape(1, -1)
            neighbors, weights = neighbors_from(uprof)

        # ─── Score & rank ───────────────────────────────────────
        nbr_df = ratings[ratings["user"].isin(neighbors)]
        if nbr_df.empty:
            return {"recommended_items": []}

        w_series = pd.Series(weights, index=neighbors)
        wr = nbr_df.merge(w_series.rename("w"), left_on="user", right_index=True)
        wr["ws"] = wr["rating"] * wr["w"]

        agg = wr.groupby("item").agg(
            total_score  = ("ws", "sum"),
            total_weight = ("w",  "sum")
        )
        gm = float(M["global_mean"])
        agg["pred"] = agg["total_score"] / (agg["total_weight"] + 1e-9) + gm

        seen = user_history.get(user_id, set())
        cand = agg[~agg.index.isin(seen)]
        top = cand.nlargest(10, "pred").index.astype(int)

        return {
            "recommended_items": [
                {"item_id": i, "title": item_titles.get(i, "Unknown")}
                for i in top
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/retrain")
async def trigger_retraining():
    try:
        model_manager.train_model()
        return {"status": "retraining completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
