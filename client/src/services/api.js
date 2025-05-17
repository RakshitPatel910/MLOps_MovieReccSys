import axios from "axios";

// const SERVER_URL =
  // process.env.REACT_APP_SERVER_URL ||
  // "http://movie-recc-server:3000";
  
  const SERVER_URL = "http://localhost:3000";

  export const fetchRecommendations = async (userId) => {
    if (!userId) return [];
    const response = await axios.post(
      // `${SERVER_URL}/backend/getRecommendation`,
      `/api/getRecommendation`,
      { id: userId },
      { headers: { "Content-Type": "application/json" } }
    );
    return response.data.recommended_items || [];
  };
  
  // **New**: postFeedback wraps user, item, rating into the shape your Express expects
  export const postFeedback = async ({ uid, iid, rating }) => {
    const payload = {
      id: uid,
      feedback: { uid, iid, rating }
    };
    const { data } = await axios.post(
      `${SERVER_URL}/backend/feedback`,
      payload,
      { headers: { 'Content-Type': 'application/json' } }
    );
    return data;  // e.g. { status: "feedback recorded" }
  };