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
            # Load and prepare data
            base_df = pd.read_csv(
                os.path.join(DATA_DIR, "u1.base"),
                sep="\t",
                names=["user", "item", "rating"],
                usecols=["user", "item", "rating"]
            )
            
            try:
                feedback_df = pd.read_csv(
                    os.path.join(DATA_DIR, "feedback.csv"),
                    usecols=["user", "item", "rating"]
                )
            except FileNotFoundError:
                feedback_df = pd.DataFrame(columns=["user", "item", "rating"])
            
            combined = pd.concat([base_df, feedback_df], ignore_index=True)
            combined = combined.groupby(["user", "item"], as_index=False)["rating"].mean()
            
            # Create pivot matrix
            pivot = combined.pivot(index="user", columns="item", values="rating").fillna(0)
            user_ids = pivot.index.to_numpy()
            
            # SVD decomposition
            svd = TruncatedSVD(n_components=50, random_state=42)
            user_factors = svd.fit_transform(csr_matrix(pivot.values))

            # Load and align user metadata
            user_meta = pd.read_csv(
                os.path.join(DATA_DIR, "u.user"),
                sep="|",
                names=["user_id", "age", "gender", "occupation", "zip_code"]
            ).set_index("user_id")
            
            # Add missing users and reindex
            missing_users = set(user_ids) - set(user_meta.index)
            default_age = user_meta["age"].mean()
            default_gender = user_meta["gender"].mode()[0]
            default_occupation = user_meta["occupation"].mode()[0]
            
            for uid in missing_users:
                user_meta.loc[uid] = [default_age, default_gender, default_occupation, "00000"]
            
            # Ensure metadata alignment with pivot users
            user_meta = user_meta.reindex(user_ids)

            # Feature engineering
            ohe_gender = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
            ohe_occupation = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
            
            gender_feats = ohe_gender.fit_transform(user_meta[["gender"]])
            occ_feats = ohe_occupation.fit_transform(user_meta[["occupation"]])
            age_scaled = StandardScaler().fit_transform(user_meta[["age"]])
            
            # Ensure dimensional alignment
            user_profiles = np.hstack([
                user_factors,
                age_scaled,
                gender_feats,
                occ_feats
            ])

            # Model training
            nn = NearestNeighbors(n_neighbors=50, metric="cosine")
            nn.fit(user_profiles)

            # Save artifacts
            os.makedirs(MODEL_DIR, exist_ok=True)
            artifacts = {
                "user_ids": user_ids,
                "item_ids": pivot.columns.to_numpy(),
                "item_factors": svd.components_.T,
                "user_profiles": user_profiles,
                "global_mean": combined["rating"].mean(),
                "nn_model": nn
            }
            
            for name, obj in artifacts.items():
                with open(os.path.join(MODEL_DIR, f"{name}.pkl"), "wb") as f:
                    pickle.dump(obj, f)

            # Update application state
            distances, indices = nn.kneighbors(user_profiles)
            data_manager.app_state["models"].update({
                "all_neighbors": {"indices": indices, "distances": distances},
                **artifacts
            })
            data_manager.initialize_state()

model_manager = ModelManager()