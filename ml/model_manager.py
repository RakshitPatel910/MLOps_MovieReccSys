import os
import pickle
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from data_manager import DATA_DIR, MODEL_DIR, data_manager

class ModelManager:
    def __init__(self):
        self.lock = data_manager.lock

    def train_model(self):
        with self.lock:
            # Load all data
            base_df = pd.read_csv(
                os.path.join(DATA_DIR, "u1.base"),
                sep="\t",
                names=["user", "item", "rating", "timestamp"],
                usecols=["user", "item", "rating"]
            )
            
            try:
                feedback_df = pd.read_csv(os.path.join(DATA_DIR, "feedback.csv"))
            except FileNotFoundError:
                feedback_df = pd.DataFrame(columns=["user", "item", "rating"])
            
            combined = pd.concat([base_df, feedback_df])
            
            # ─── Training Logic ─────────────────────────────────────────────
            global_mean = combined["rating"].mean()
            
            pivot = combined.pivot(index="user", columns="item", values="rating").fillna(0)
            user_ids = pivot.index.to_numpy()
            item_ids = pivot.columns.to_numpy()
            R = csr_matrix(pivot.values)
            
            # SVD Decomposition
            svd = TruncatedSVD(n_components=50, random_state=42)
            user_factors = svd.fit_transform(R)
            item_factors = svd.components_.T
            
            # User Metadata
            user_meta = pd.read_csv(
                os.path.join(DATA_DIR, "u.user"),
                sep="|",
                names=["user_id", "age", "gender", "occupation", "zip_code"]
            ).set_index("user_id")
            
            # Handle new users
            new_users = set(user_ids) - set(user_meta.index)
            for uid in new_users:
                user_meta.loc[uid] = [
                    user_meta["age"].mean(),
                    user_meta["gender"].mode()[0],
                    user_meta["occupation"].mode()[0],
                    "00000"  # Default zip
                ]
            
            # Feature Engineering
            ohe_gender = OneHotEncoder(sparse_output=False)
            ohe_occupation = OneHotEncoder(sparse_output=False)
            gender_feats = ohe_gender.fit_transform(user_meta[["gender"]])
            occ_feats = ohe_occupation.fit_transform(user_meta[["occupation"]])
            age_scaled = StandardScaler().fit_transform(user_meta[["age"]])
            
            # Combine Features
            side_info = np.hstack([age_scaled, gender_feats, occ_feats])
            user_profiles = np.hstack([user_factors, side_info])
            
            # NN Model
            nn = NearestNeighbors(n_neighbors=50, metric="cosine")
            nn.fit(user_profiles)
            
            # Save Artifacts
            os.makedirs(MODEL_DIR, exist_ok=True)
            artifacts = {
                "user_ids": user_ids,
                "item_ids": item_ids,
                "item_factors": item_factors,
                "user_profiles": user_profiles,
                "global_mean": global_mean,
                "nn_model": nn
            }
            
            for name, obj in artifacts.items():
                with open(os.path.join(MODEL_DIR, f"{name}.pkl"), "wb") as f:
                    pickle.dump(obj, f)
            
            # Precompute neighbors
            distances, indices = nn.kneighbors(user_profiles)
            data_manager.app_state["models"]["all_neighbors"] = {
                "indices": indices,
                "distances": distances
            }
            
            # Update application state
            data_manager.app_state["models"].update(artifacts)
            data_manager.initialize_state()

model_manager = ModelManager()