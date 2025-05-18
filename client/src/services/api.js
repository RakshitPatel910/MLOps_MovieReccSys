import axios from "axios";

// const SERVER_URL =
  // process.env.REACT_APP_SERVER_URL ||
  // "http://movie-recc-server:3000";
  
  // const SERVER_URL = "http://localhost:3000/api";     //local
  const SERVER_URL = '/api';                       // k8s and compose
  // const SERVER_URL = '';


  export const login = async (email, password) => {
    try {
      const response = await axios.post(`${SERVER_URL}/auth/signin`, {
        email,
        password
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Login failed');
    }
  }

  export const signup = async (userData) => {
    try {
      const response = await axios.post(`${SERVER_URL}/auth/signup`, {
        userName: userData.username,
        email: userData.email,
        password: userData.password,
        age: userData.age,
        gender: userData.gender,
        occupation: userData.occupation,
        zipCode: userData.zipCode
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.message || 'Registration failed');
    }
  }

  export const fetchRecommendations = async (userId) => {
    if (!userId) return [];
    const response = await axios.post(
      `${SERVER_URL}/getRecommendation`,            //compose
      // `/api/getRecommendation`,                          //k8s
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
      `${SERVER_URL}/feedback`,
      payload,
      { headers: { 'Content-Type': 'application/json' } }
    );
    return data;  // e.g. { status: "feedback recorded" }
  };