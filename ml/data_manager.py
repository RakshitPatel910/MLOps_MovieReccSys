import os
import pandas as pd
from fastapi import HTTPException
from typing import Dict, Any
import numpy as np
import pickle
from filelock import FileLock

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "ml-100k")
MODEL_DIR = os.path.join(BASE_DIR, "model_data")

class DataManager:
    def __init__(self):
        self.app_state = {
            "models": {},
            "data": {
                "ratings": None,
                "user_history": dict,
                "all_neighbors": None,
                "feedback_count": 0,
                "next_user_id": None
            }
        }
        self.lock = FileLock(os.path.join(DATA_DIR, "data.lock"))

    def initialize_state(self):
        with self.lock:
            # Load base data
            base_df = pd.read_csv(
                os.path.join(DATA_DIR, "u1.base"),
                sep="\t",
                names=["user", "item", "rating", "timestamp"],
                usecols=["user", "item", "rating"]
            )
            
            # Load feedback data
            feedback_path = os.path.join(DATA_DIR, "feedback.csv")
            try:
                feedback_df = pd.read_csv(feedback_path)
            except FileNotFoundError:
                feedback_df = pd.DataFrame(columns=["user", "item", "rating"])
            
            # Combine data
            combined = pd.concat([base_df, feedback_df])
            self.app_state["data"]["ratings"] = combined
            self.app_state["data"]["user_history"] = combined.groupby("user")["item"].apply(set).to_dict()
            
            # Initialize next user ID
            max_existing = combined["user"].max() if not combined.empty else 0
            user_ids = self.load_user_ids()
            self.app_state["data"]["next_user_id"] = max(max_existing, (user_ids.max() if user_ids.size > 0 else 0)) + 1
            
            # Initialize feedback counter
            self.app_state["data"]["feedback_count"] = len(feedback_df)

    def load_user_ids(self):
        try:
            with open(os.path.join(MODEL_DIR, "user_ids.pkl"), "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return np.array([])

    def get_next_user_id(self):
        with self.lock:
            next_id = self.app_state["data"]["next_user_id"]
            self.app_state["data"]["next_user_id"] += 1
            return next_id

    def add_feedback(self, user_id: int, item_id: int, rating: float):
        feedback_path = os.path.join(DATA_DIR, "feedback.csv")
        with self.lock:
            # load or create feedback.csv
            existing = pd.read_csv(feedback_path) \
                    if os.path.exists(feedback_path) else pd.DataFrame(columns=["user","item","rating"])
            mask = (existing["user"] == user_id) & (existing["item"] == item_id)

            if mask.any():
                existing.loc[mask, "rating"] = rating
            else:
                new_row = pd.DataFrame([[user_id, item_id, rating]], columns=["user", "item", "rating"])
                existing = pd.concat([existing, new_row], ignore_index=True)

            # persist every single feedback
            existing.to_csv(feedback_path, index=False)

            # just count it—no in-RAM cache touch here
            self.app_state["data"]["feedback_count"] += 1


    def _merge_feedback_into_base(self):
        """Load u1.base + feedback.csv → merge/update → overwrite u1.base → delete feedback.csv."""
        base_path = os.path.join(DATA_DIR, "u1.base")
        fb_path   = os.path.join(DATA_DIR, "feedback.csv")

        # 1) read the original base
        base_df = pd.read_csv(
            base_path,
            sep="\t",
            names=["user","item","rating","timestamp"],
            usecols=["user","item","rating"]
        )

        # 2) read every buffered feedback
        fb_df = pd.read_csv(fb_path)

        # 3) for each (user,item) in fb_df, update or append
        for u,i,r in fb_df.itertuples(index=False):
            mask = (base_df["user"] == u) & (base_df["item"] == i)
            if mask.any():
                base_df.loc[mask, "rating"] = r
            else:
                base_df = pd.concat([
                    base_df,
                    pd.DataFrame([[u,i,r]], columns=["user","item","rating"])
                ], ignore_index=True)

        # 4) overwrite u1.base (tab-sep, no header)
        base_df.to_csv(base_path, sep="\t", header=False, index=False)

        # 5) clear out feedback.csv
        os.remove(fb_path)

    # def check_retrain_needed(self, threshold: int = 100):
    #     with self.lock:
    #         if self.app_state["data"]["feedback_count"] >= threshold:
    #             self.app_state["data"]["feedback_count"] = 0
    #             return True
    #         return False

    def check_retrain_needed(self, threshold: int = 100) -> bool:
        """
        Once feedback_count ≥ threshold:
        • merge ALL feedback into u1.base
        • clear the CSV buffer
        • reset the counter + re-init in-RAM data
        • return True so caller can retrain
        """
        if self.app_state["data"]["feedback_count"] >= threshold:
            with self.lock:
                self._merge_feedback_into_base()
                # reload everything off the newly updated base
                self.initialize_state()
                # reset
                self.app_state["data"]["feedback_count"] = 0
            return True
        return False


data_manager = DataManager()