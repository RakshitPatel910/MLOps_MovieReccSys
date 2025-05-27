import os
import pickle
import numpy as np
import pandas as pd
import logging
# import logstash
import sys
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Dict, List, Union
import logging
import logstash
import sys

# ─── Logging Configuration ───────────────────────────────────────
logger = logging.getLogger("MLServiceLogger")
logger.setLevel(logging.INFO)

# Custom filter to handle missing fields
class OptionalFieldsFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'user_id'):
            record.user_id = 'null'
        if not hasattr(record, 'item_id'):
            record.item_id = 'null'
        return True

# Logstash Handler
try:
    logstash_handler = logstash.TCPLogstashHandler(
        host='logstash',
        port=5044,
        version=1
    )
    logstash_handler.addFilter(OptionalFieldsFilter())
    logger.addHandler(logstash_handler)
except Exception as e:
    logger.error(f"Failed to initialize Logstash handler: {str(e)}")

# Console Handler with safe formatting
stream_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
    '"module": "%(module)s", "function": "%(funcName)s", '
    '"message": "%(message)s", "user_id": "%(user_id)s", '
    '"item_id": "%(item_id)s", "service": "ml"}'
)

stream_handler.setFormatter(formatter)
stream_handler.addFilter(OptionalFieldsFilter())
logger.addHandler(stream_handler)

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
    logger.info("Initializing ML service state")
    
    try:
        data_manager.initialize_state()
        if not os.path.exists(os.path.join(MODEL_DIR, "user_ids.pkl")):
            logger.warning("No existing model found, starting initial training")
            model_manager.train_model()

        models = {}
        for name in [
            "user_ids", "item_ids", "item_factors",
            "user_profiles", "nn_model", "global_mean",
            "svd", "scaler_age", "ohe_gender", "ohe_occupation"
        ]:
            path = os.path.join(MODEL_DIR, f"{name}.pkl")
            with open(path, "rb") as f:
                models[name] = pickle.load(f)
                logger.debug(f"Loaded model component: {name}")

        up = models["user_profiles"]
        dists, idxs = models["nn_model"].kneighbors(up)
        models["all_neighbors"] = {"distances": dists, "indices": idxs}
        data_manager.app_state["models"] = models

        logger.info("Service initialization completed successfully",
                  extra={'user_id': 'system', 'item_id': 'system'})
        
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}",
                   extra={'user_id': 'system', 'item_id': 'system'})
        raise RuntimeError(f"Model loading failed: {e}")

    yield

app = FastAPI(lifespan=lifespan)

# ─── Endpoints ─────────────────────────────────────────────────────
@app.get("/ml/users")
async def get_all_users():
    try:
        logger.info("Fetching all users")
        M = data_manager.app_state["models"]
        svd_components = 50
        
        user_meta = []
        for idx, user_id in enumerate(M["user_ids"]):
            profile = M["user_profiles"][idx]
            age = float(profile[svd_components])
            gender = 'M' if profile[svd_components + 1] > 0.5 else 'F'
            occ_features = profile[svd_components + 2:svd_components + 23]
            occupation = str(M["ohe_occupation"].inverse_transform([occ_features])[0][0])

            user_meta.append({
                "user_id": int(user_id),
                "age": age,
                "gender": gender,
                "occupation": occupation
            })
            
        logger.info(f"Returning {len(user_meta)} users")
        return user_meta
        
    except Exception as e:
        logger.error(f"Failed to fetch users: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ml/ratings")
async def get_all_ratings():
    try:
        logger.info("Fetching all ratings")
        base_path = os.path.join(DATA_DIR, "u1.base")
        feedback_path = os.path.join(DATA_DIR, "feedback.csv")

        base_df = pd.read_csv(
            base_path,
            sep='\t',
            names=["user_id", "item_id", "rating", "timestamp"],
            dtype={'user_id': 'int32', 'item_id': 'int32', 
                   'rating': 'float32', 'timestamp': 'int64'}
        )

        try:
            feedback_df = pd.read_csv(
                feedback_path,
                header=0,
                names=["user_id", "item_id", "rating"],
                dtype={'user_id': 'int32', 'item_id': 'int32', 'rating': 'float32'}
            )
            current_ts = int(pd.Timestamp.now().timestamp())
            feedback_df = feedback_df.assign(timestamp=current_ts)
            
        except FileNotFoundError:
            feedback_df = pd.DataFrame(columns=["user_id", "item_id", "rating", "timestamp"])
            logger.warning("No feedback file found")

        combined = pd.concat([base_df, feedback_df], ignore_index=True)
        combined = combined.astype({
            'user_id': 'int32',
            'item_id': 'int32',
            'rating': 'float32',
            'timestamp': 'int64'
        }, errors='ignore')

        combined = combined.dropna(subset=['user_id', 'item_id', 'rating'])
        logger.info(f"Returning {len(combined)} ratings")
        return combined.to_dict(orient="records")
        
    except Exception as e:
        logger.error(f"Failed to fetch ratings: {str(e)}")
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
            
        logger.info("User created", extra={
            "user_id": new_id,
            "age": user_data.age,
            "gender": user_data.gender,
            "occupation": user_data.occupation
        })
        return {"user_id": new_id}
    except Exception as e:
        logger.error("User creation failed", extra={
            "error": str(e),
            "user_data": user_data.dict()
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/feedback")
async def submit_feedback(feedback: FeedbackIn):
    try:
        logger.info("Receiving feedback", extra={
            "user_id": feedback.user_id,
            "item_id": feedback.item_id,
            "rating": feedback.rating
        })
        data_manager.add_feedback(feedback.user_id, feedback.item_id, feedback.rating)
        
        if data_manager.check_retrain_needed(threshold=2):
            logger.info("Initiating model retraining")
            model_manager.train_model()
            
        return {"status": "feedback recorded"}
    except Exception as e:
        logger.error("Feedback processing failed", extra={
            "user_id": feedback.user_id,
            "item_id": feedback.item_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ml/recommend/{user_id}")
async def get_recommendations(user_id: int):
    try:
        logger.info("Recommendation request received", extra={"user_id": user_id})
        
        M = data_manager.app_state["models"]
        ratings = data_manager.app_state["data"]["ratings"]
        user_history = data_manager.app_state["data"]["user_history"]
        item_titles = data_manager.app_state["data"]["item_titles"]

        def neighbors_from(profile: np.ndarray):
            d, i = M["nn_model"].kneighbors(profile)
            neigh = i[0][1:]
            w = 1 / (d[0][1:] + 1e-6)
            return M["user_ids"][neigh], w

        if user_id not in M["user_ids"]:
            logger.info("Handling cold-start user", extra={"user_id": user_id})
            try:
                meta = pd.read_csv(
                    os.path.join(DATA_DIR, "u.user"),
                    sep="|",
                    names=["user_id","age","gender","occupation","zip_code"]
                ).set_index("user_id")
                
                if user_id not in meta.index:
                    logger.warning("Unknown cold-start user", extra={"user_id": user_id})
                    return {"recommended_items": []}

                row = meta.loc[user_id]
                age_v = M["scaler_age"].transform(pd.DataFrame([[row.age]], columns=["age"]))
                gender_v = M["ohe_gender"].transform(pd.DataFrame([[row.gender]], columns=["gender"]))
                occ_v = M["ohe_occupation"].transform(pd.DataFrame([[row.occupation]], columns=["occupation"]))
                profile = np.hstack([np.zeros((1, M["svd"].n_components)), age_v, gender_v, occ_v])
                neighbors, weights = neighbors_from(profile)
            except Exception as e:
                logger.error("Cold-start processing failed", extra={"user_id": user_id, "error": str(e)})
                raise HTTPException(status_code=500, detail=f"Cold-start processing failed: {str(e)}")
        else:
            idxs = np.where(M["user_ids"] == user_id)[0]
            if not idxs.size:
                logger.warning("User not found in model", extra={"user_id": user_id})
                return {"recommended_items": []}
                
            uprof = M["user_profiles"][idxs[0]].reshape(1, -1)
            neighbors, weights = neighbors_from(uprof)

        nbr_df = ratings[ratings["user"].isin(neighbors)]
        if nbr_df.empty:
            logger.warning("No neighbors found for user", extra={"user_id": user_id})
            return {"recommended_items": []}

        wr = nbr_df.merge(pd.Series(weights, index=neighbors).rename("w"), left_on="user", right_index=True)
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

        logger.info("Recommendation generated", extra={
            "user_id": user_id,
            "num_items": len(top)
        })
        return {
            "recommended_items": [
                {"item_id": i, "title": item_titles.get(i, "Unknown")}
                for i in top
            ]
        }

    except Exception as e:
        logger.error("Recommendation failed", extra={
            "user_id": user_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ml/retrain")
async def trigger_retraining():
    try:
        logger.info("Starting model retraining")
        model_manager.train_model()
        logger.info("Model retraining completed successfully")
        return {"status": "retraining completed"}
    except Exception as e:
        logger.error("Model retraining failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)