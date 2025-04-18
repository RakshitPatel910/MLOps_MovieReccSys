import express from 'express';
import bcrypt from 'bcrypt';

import User from '../model/userSchema';

const router = express.Router();
const saltRound = parseInt(process.env.SALTROUND);
const salt = bcrypt.genSaltSync(saltRound);

async function encryption(data) {
  return bcrypt.hash(data, salt);
}


router.post('/signin', async (req, res) => {
  const { email, password } = req.body;

  try {
    const user = await User.findOne({ email });

    if (!user) {
      return res.json({ message: "User does not exist", status: false });
    }

    const isMatch = bcrypt.compareSync(password, user.password);

    if (isMatch) {
      user.password = ""; // Remove password from response

      return res.json({
        message: "Successfully Logged in",
        status: true,
        profile: user
      });
    } else {
      return res.json({ message: "Password is incorrect", status: false });
    }
  } 
  catch (error) {
    console.log(error);
    return res.status(500).json({ message: "Internal server error", status: false });
  }
});

router.post("/signup", async (req, res) => {
  const { userName, email, password } = req.body;

  try {
    const userExist = await User.findOne({ email });

    if (userExist) {
      return res.json({ message: "Email already exists", status: false, profile: userExist });
    }

    const newPassword = await encryption(password);
    const user = new User({ userName, email, password: newPassword });

    await user.save();
    return res.status(201).json({ message: "Signup successfully", status: true, profile: user });

  } 
  catch (error) {
    console.log(error);
    return res.status(500).json({ message: "Failed to register", status: false });
  }
});

export default router;
