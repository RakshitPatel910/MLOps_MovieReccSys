import express from 'express';
import mongoose from 'mongoose';
// const User = require("../model/userSchema.js");
import User from "../model/userSchema.js";
import { fetchRecommendation, addFeedback } from "../services/mlClient.js";
import { movieDB } from '../serverdata/movieDB.js';

const router = express.Router();

router.post('/getRecommendation', async (req, res) => {
    const { id } = req.body;

    try {
        const data = await fetchRecommendation(id);

        res.json(data);
    } 
    catch (err) {
        res.status(502).json({error: err});
    }   
});


router.post('/feedback', async (req, res) => {
    const { id, feedback } = req.body;

    try {
        // Validate movie ID exists in database
        const movieIdString = feedback.iid.toString();
        if (!movieDB[movieIdString]) {
            return res.status(400).json({ 
                error: `Invalid movie ID: ${feedback.iid}` 
            });
        }

        // Update user's watchlist in MongoDB
        const user = await User.findOne({ ml_user_id: id });

        if (!user) {
            return res.status(404).json({ error: 'User not found' });
        }

        // Find existing movie in watchlist
        const existingMovieIndex = user.watchlist.findIndex(
            movie => movie.movie_id === feedback.iid
        );

        if (existingMovieIndex !== -1) {
            // Update existing rating
            user.watchlist[existingMovieIndex].rating = feedback.rating;
        } else {
            // Add new entry to watchlist
            user.watchlist.push({
                movie_id: feedback.iid,
                rating: feedback.rating,
                // timestamp added automatically by schema
            });
        }

        await user.save();

        // Send feedback to ML service
        const fres = await addFeedback(feedback);
        res.json(fres);
    } 
    catch (err) {
        console.error('Feedback error:', err);
        res.status(500).json({ 
            error: err.response?.data?.message || err.message 
        });
    }
});

export default router;