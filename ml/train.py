import os
import pickle
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

# ─── Configuration ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "ml-100k")
MODEL_DIR = os.path.join(BASE_DIR, "model_data")

def train_model():
    # Load ratings data
    ratings_df = pd.read_csv(
        os.path.join(DATA_DIR, "u1.base"),
        sep="\t",
        names=["user", "item", "rating", "timestamp"],
        usecols=["user", "item", "rating"]
    )
    
    # Calculate global average rating
    global_mean = ratings_df["rating"].mean()
    
    # Create user-item matrix
    pivot = ratings_df.pivot(index="user", columns="item", values="rating").fillna(0)
    user_ids = pivot.index.to_numpy()
    item_ids = pivot.columns.to_numpy()
    R = csr_matrix(pivot.values)
    
    # Perform SVD decomposition
    svd = TruncatedSVD(n_components=50, random_state=42)
    user_factors = svd.fit_transform(R)
    item_factors = svd.components_.T
    
    # Process user metadata
    user_meta = pd.read_csv(
        os.path.join(DATA_DIR, "u.user"),
        sep="|",
        names=["user_id", "age", "gender", "occupation", "zip_code"]
    ).set_index("user_id").loc[user_ids]
    
    # Feature engineering
    ohe_gender = OneHotEncoder(sparse_output=False)
    ohe_occupation = OneHotEncoder(sparse_output=False)
    gender_feats = ohe_gender.fit_transform(user_meta[["gender"]])
    occ_feats = ohe_occupation.fit_transform(user_meta[["occupation"]])
    age_scaled = StandardScaler().fit_transform(user_meta[["age"]])
    
    # Combine features
    side_info = np.hstack([age_scaled, gender_feats, occ_feats])
    user_profiles = np.hstack([user_factors, side_info])
    
    # Build neighbor model
    nn = NearestNeighbors(n_neighbors=50, metric="cosine")
    nn.fit(user_profiles)
    
    # Ensure output directory exists
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Save all components
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
    
    print(f"✅ Model artifacts saved to {MODEL_DIR}/")

if __name__ == "__main__":
    train_model()