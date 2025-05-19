import axios from "axios";

// const ML_URL = process.env.ML_URL || "http://localhost:8000";        //local
const ML_URL = process.env.ML_URL || "http://ml-service:8000";        //k8s and compose
// const ML_URL = process.env.ML_URL || "http://movie-recc-ml-service:8000";   //compose

export const getAllUsers = async () => {
    const res = await axios.get(`${ML_URL}/ml/users`);

    return res.data;
}

export const getAllRatings = async () => {
    const res = await axios.get(`${ML_URL}/ml/ratings`);

    return res.data;
}

export const addUser = async (user) => {
    try {
        const res = await axios.post(`${ML_URL}/ml/users/create`, user);

        return res.data;
    } catch (error) {
        return res.status(500).json({message: `ML Service Error: ${error.response?.data?.detail || error.message}`});
    }
}

export const fetchRecommendation = async ( uid ) => {
    // const res = await axios.get(`${ML_URL}/recommend/${uid}`);   //k0s
    const res = await axios.get(`${ML_URL}/ml/recommend/${uid}`);   //compose

    return res.data;
}

export const addFeedback = async (feedback) => {
    const res = await axios.post(`${ML_URL}/ml/feedback`, {
        user_id: feedback.uid,
        item_id: feedback.iid,
        rating: feedback.rating
    });

    return res.data; 
}


// module.exports = { fetchRecommendation };