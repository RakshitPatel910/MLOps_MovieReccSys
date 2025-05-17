import axios from "axios";

const ML_URL = process.env.ML_URL || "http://ml-service:8000";        //k8s
// const ML_URL = process.env.ML_URL || "http://movie-recc-ml-service:8000";   //compose

export const addUser = async (user) => {
    const res = await axios.post(`${ML_URL}/users/create`, user);

    return res.data
}

export const fetchRecommendation = async ( uid ) => {
    // const res = await axios.get(`${ML_URL}/recommend/${uid}`);   //k0s
    const res = await axios.get(`${ML_URL}/ml/recommend/${uid}`);   //compose

    return res.data
}

export const addFeedback = async (feedback) => {
    const res = await axios.post(`${ML_URL}/feedback`, {
        user_id: feedback.uid,
        item_id: feedback.iid,
        rating: feedback.rating
    });

    return res.data; 
}


// module.exports = { fetchRecommendation };