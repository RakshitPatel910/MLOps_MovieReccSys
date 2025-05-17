import pandas as pd
import os

FEEDBACK_PATH = "./ml-100k/feedback.csv"

def write_feedback(user_id, item_id, rating):
    """
    Append a new user rating to feedback.csv.
    """
    new_entry = pd.DataFrame([[user_id, item_id, rating]], columns=["user", "item", "rating"])
    
    if not os.path.exists(FEEDBACK_PATH):
        new_entry.to_csv(FEEDBACK_PATH, index=False, header=False)
    else:
        new_entry.to_csv(FEEDBACK_PATH, mode='a', index=False, header=False)
    
    print(f"✅ Feedback saved: User {user_id} rated Item {item_id} with {rating}")
