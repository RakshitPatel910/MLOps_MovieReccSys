import os
import pickle
import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors

# ─── Configuration ─────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "ml-100k")
MODEL_DIR = os.path.join(BASE_DIR, "model_data")

def train_model():
    # 1) Load ratings
    ratings_df = pd.read_csv(
        os.path.join(DATA_DIR, "u1.base"),
        sep="\t",
        names=["user", "item", "rating", "timestamp"],
        usecols=["user", "item", "rating"]
    )

    # 2) Global mean
    global_mean = ratings_df["rating"].mean()

    # 3) Build user-item matrix
    pivot   = ratings_df.pivot(index="user", columns="item", values="rating").fillna(0)
    user_ids= pivot.index.to_numpy()
    item_ids= pivot.columns.to_numpy()
    R       = csr_matrix(pivot.values)

    # 4) SVD latent factors
    svd         = TruncatedSVD(n_components=50, random_state=42)
    user_factors= svd.fit_transform(R)
    item_factors= svd.components_.T

    # 5) Load user metadata and fit side-info transformers
    user_meta = pd.read_csv(
        os.path.join(DATA_DIR, "u.user"),
        sep="|",
        names=["user_id", "age", "gender", "occupation", "zip_code"]
    ).set_index("user_id").loc[user_ids]

    # 5a) Scaler for age
    scaler_age = StandardScaler().fit(user_meta[["age"]])

    # 5b) One-hot for gender & occupation
    ohe_gender     = OneHotEncoder(sparse_output=False).fit(user_meta[["gender"]])
    ohe_occupation = OneHotEncoder(sparse_output=False).fit(user_meta[["occupation"]])

    # 6) Build full user profile (latent ∥ side-info)
    age_feats      = scaler_age.transform(user_meta[["age"]])
    gender_feats   = ohe_gender.transform(user_meta[["gender"]])
    occupation_feats = ohe_occupation.transform(user_meta[["occupation"]])
    side_info      = np.hstack([age_feats, gender_feats, occupation_feats])
    user_profiles  = np.hstack([user_factors, side_info])

    # 7) Fit neighbor model
    nn_model = NearestNeighbors(n_neighbors=50, metric="cosine").fit(user_profiles)

    # 8) Save artifacts
    os.makedirs(MODEL_DIR, exist_ok=True)
    artifacts = {
        "user_ids":       user_ids,
        "item_ids":       item_ids,
        "item_factors":   item_factors,
        "user_profiles":  user_profiles,
        "global_mean":    global_mean,
        "nn_model":       nn_model,
        "svd":            svd,
        "scaler_age":     scaler_age,
        "ohe_gender":     ohe_gender,
        "ohe_occupation": ohe_occupation,
    }
    for name, obj in artifacts.items():
        with open(os.path.join(MODEL_DIR, f"{name}.pkl"), "wb") as f:
            pickle.dump(obj, f)

    print(f"✅ Model artifacts saved to {MODEL_DIR}/")


if __name__ == "__main__":
    train_model()
