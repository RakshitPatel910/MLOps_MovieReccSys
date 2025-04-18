import axios from "axios";

const ML_URL = process.env.ML_URL || "http://ml-service:5000";

export const addUser = async (user) => {
    const res = await axios.post(`${ML_URL}/adduser`, {user : user});
}

export const fetchRecommendation = async ( uid ) => {
    const res = await axios.get(`${ML_URL}/recommend/${uid}`);

    return res.data
}

export const feedback = async ( uid, feedback ) => {
    const res = await axios.post(`${ML_URL}/feedback`, {feedback: feedback});
}

// module.exports = { fetchRecommendation };