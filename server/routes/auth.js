import express from 'express';
import bcrypt from 'bcrypt';

import User from '../model/userSchema.js';
import { addUser } from '../services/mlClient.js';
import { enhanceWatchlist } from '../helpers/movieHelpers.js';

const router = express.Router();
const saltRound = parseInt(process.env.SALTROUND);
const salt = bcrypt.genSaltSync(saltRound);

async function encryption(data) {
  return bcrypt.hash(data, salt);
}


router.post('/signin', async (req, res) => {
  const { email, password } = req.body;

  try {
      const user = await User.findOne({ email }).select('+password');
      
      console.log(await user.comparePassword(password))

      if (!user || !(await user.comparePassword(password))) {
          return res.status(401).json({
              message: "Invalid credentials",
              status: false
          });
      }

      const userProfile = user.toObject();
      delete userProfile.password;

      const enhancedProfile = {
        ...userProfile,
        watchlist: enhanceWatchlist(userProfile.watchlist || [])
      };

      return res.json({
          message: "Login successful",
          status: true,
          profile: enhancedProfile
      });
  } 
  catch (error) {
      console.log(error);
      return res.status(500).json({ message: "Internal server error", status: false });
  }
});

router.post("/signup", async (req, res) => {
  const { userName, email, password, age, gender, occupation, zipCode } = req.body;

  try {
    // const mlres = await addUser({
    //     age: age,
    //     gender: gender,
    //     occupation: occupation,
    //     zip_code: zipCode
    // })

    // const uid = mlres.data;

    const userExist = await User.findOne({ $or: [{ email }, { userName }] });

    if (userExist) {
      return res.status(409).json({
        message: "Username/email already exists",
        status: false
      });
    }


    const mlres = await addUser({
        age: age,
        gender: gender,
        occupation: occupation,
        zip_code: zipCode
    })

    console.log(mlres)

    const uid = mlres.user_id;


     const user = new User({
        ml_user_id: uid, // From ML service response
        username: userName,
        email,
        password, // Will be hashed by schema pre-save hook
        age: Number(age),
        gender,
        occupation,
        zip_code: zipCode
    });

    await user.save();

    const userProfile = user.toObject();
    delete userProfile.password;

    const enhancedProfile = {
      ...userProfile,
      watchlist: enhanceWatchlist(userProfile.watchlist || [])
    };

    return res.status(201).json({
        message: "Signup successful",
        status: true,
        profile: enhancedProfile
    });
  } 
  catch (error) {
    console.log(error);
    return res.status(500).json({ message: "Failed to register", status: false });
  }
});

export default router;
