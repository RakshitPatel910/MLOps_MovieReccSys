import os
import pickle
import numpy as np
import pandas as pd
from typing import List

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR     = os.path.join(BASE_DIR, "model_data")
RATINGS_FILE  = os.path.join(BASE_DIR, "ml-100k", "u1.base")
FEEDBACK_FILE = os.path.join(BASE_DIR, "ml-100k", "feedback.csv")
USER_META     = os.path.join(BASE_DIR, "ml-100k", "u.user")

def load_model_components():
    names = [
        "user_ids", "item_ids", "item_factors",
        "user_profiles", "nn_model", "global_mean",
        "svd", "scaler", "ohe_gender", "ohe_occupation"
    ]
    components = {}
    for name in names:
        path = os.path.join(MODEL_DIR, f"{name}.pkl")
        with open(path, "rb") as f:
            components[name] = pickle.load(f)
    return components

def recommend(user_id: int, top_n: int = 10) -> List[int]:
    # Load all model artifacts + transformers
    model = load_model_components()

    # Load & combine base + feedback ratings
    try:
        fb = pd.read_csv(FEEDBACK_FILE, names=["user", "item", "rating"])
    except FileNotFoundError:
        fb = pd.DataFrame(columns=["user", "item", "rating"])
    base = pd.read_csv(
        RATINGS_FILE,
        sep="\t",
        names=["user", "item", "rating", "timestamp"],
        usecols=["user", "item", "rating"]
    )
    ratings = pd.concat([base, fb], ignore_index=True)

    # Helper to compute neighbors & weights given a profile vector
    def get_neighbors(profile: np.ndarray):
        dists, idxs = model["nn_model"].kneighbors([profile])
        neigh_i = idxs[0][1:]  # skip self
        w = 1 / (dists[0][1:] + 1e-6)
        users = model["user_ids"][neigh_i]
        return users, w

    # ─── Cold-start branch ─────────────────────────────────────────────────────────
    if user_id not in model["user_ids"]:
        # 1. load this user's metadata
        meta = pd.read_csv(
            USER_META,
            sep="|",
            names=["user_id","age","gender","occupation","zip_code"]
        ).set_index("user_id")
        if user_id not in meta.index:
            return []  # no metadata → no recs

        row = meta.loc[user_id]
        # 2. transform side-info
        age_scaled      = model["scaler"].transform([[row.age]])
        gender_feat     = model["ohe_gender"].transform([[row.gender]])
        occupation_feat = model["ohe_occupation"].transform([[row.occupation]])
        # 3. zero-vector for latent factors
        zeros = np.zeros(model["svd"].n_components)
        profile = np.hstack([zeros, age_scaled, gender_feat, occupation_feat])

        neighbor_users, neighbor_weights = get_neighbors(profile)

    # ─── Existing-user branch ───────────────────────────────────────────────────────
    else:
        # locate index in the trained user_profiles
        uidx = np.where(model["user_ids"] == user_id)[0][0]
        profile = model["user_profiles"][uidx]
        neighbor_users, neighbor_weights = get_neighbors(profile)

    # ─── Scoring ────────────────────────────────────────────────────────────────────
    # Filter neighbors' ratings
    nbr_r = ratings[ratings["user"].isin(neighbor_users)]
    if nbr_r.empty:
        return []

    # Compute weighted scores per item
    weight_map = dict(zip(neighbor_users, neighbor_weights))
    item_accum = {}  # item_id -> [weighted_scores...]

    for _, row in nbr_r.iterrows():
        item = row.item
        score = weight_map[row.user] * row.rating
        item_accum.setdefault(item, []).append(score)

    # Build final predictions
    preds = {}
    for item, scores in item_accum.items():
        # total weight of neighbors who rated this item
        users_who_rated = nbr_r[nbr_r["item"] == item]["user"]
        total_w = sum(weight_map[u] for u in users_who_rated if u in weight_map)
        preds[item] = (sum(scores) / total_w) + model["global_mean"]

    # Exclude items the user has already seen
    seen = set(ratings[ratings["user"] == user_id]["item"].unique())
    candidates = [(it, sc) for it, sc in preds.items() if it not in seen]

    # Return top-N item IDs
    top_items = sorted(candidates, key=lambda x: x[1], reverse=True)[:top_n]
    return [int(item) for item, _ in top_items]
