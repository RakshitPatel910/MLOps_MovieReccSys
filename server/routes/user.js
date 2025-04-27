import express from 'express';
import mongoose from 'mongoose';
// const User = require("../model/userSchema.js");
import User from "../model/userSchema.js";
import { fetchRecommendation, addFeedback } from "../services/mlClient.js";

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
})

router.post('/feedback', async (req, res) => {
    const { id, feedback } = req.body;

    console.log(feedback)

    try {
        // const user = await User.findOne({ "uid" : id });

        // let wl = user.watchlist;

        // wl.forEach((movie) => {
        //     if( movie.mid === feedback.mid ) movie.rating = feedback.rating;
        // })

        // user.watchlist = wl;

        // await User.findOneAndUpdate({ "uid" : id }, user);

        const fres = await addFeedback(feedback);

        console.log(fres);

        res.json(fres);
    } 
    catch (err) {
        res.json({error: err});
    }
})

export default router;