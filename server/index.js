import express from 'express';
import cors from 'cors';

import userRouter from './routes/user.js';
import authRouter from './routes/auth.js';
const app = express();

app.use(express.json());
app.use(cors());

app.use('/', userRouter);
app.use('/auth/', authRouter);

const PORT = '3010';

app.listen(PORT, () => {
    console.log("server is running at port 3010");
  });