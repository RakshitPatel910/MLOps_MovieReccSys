import axios from "axios";

// const SERVER_URL =
  // process.env.REACT_APP_SERVER_URL ||
  // "http://movie-recc-server:3000";
  
  const SERVER_URL = "http://localhost:3000";

export const fetchRecommendations = async (userId) => {
  if (!userId) return [];

  try {
    const response = await axios.post(
      `${SERVER_URL}/backend/getRecommendation`,
      { id: userId },
      {
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
    // your Express returns whatever mlClient.fetchRecommendation() returns,
    // which should include .recommended_items
    return response.data.recommended_items || [];
  } catch (error) {
    throw new Error(
      `Error fetching recommendations: ${error.response?.data?.error || error.message}`
    );
  }
};
