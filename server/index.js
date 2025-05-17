// import express from 'express';
// import cors from 'cors';

// import userRouter from './routes/user.js';
// import authRouter from './routes/auth.js';
// import { connectDB } from './db.js'; 
// const app = express();
// const PORT = 3000;

// app.use(express.json());
// app.use(cors());

// // Connect to MongoDB and start the server
// connectDB().then((db) => {
//   app.locals.db = db; // optionally store DB in app context

//   app.use('/backend/', userRouter);
//   app.use('/backend/auth/', authRouter);

//   app.listen(PORT, () => {
//     console.log(`Server is running at port ${PORT}`);
//   });
// }).catch(err => {
//   console.error("Failed to connect to MongoDB, server not started:", err);
// });


import express from 'express';
import cors from 'cors';

import userRouter from './routes/user.js';
import authRouter from './routes/auth.js';
const app = express();

app.use(express.json());
app.use(cors());

app.use('/api/', userRouter);
app.use('/api/auth/', authRouter);

const PORT = '3000';

app.listen(PORT, () => {
    console.log("server is running at port 3010");
  });


// const MINIKUBE_IP = '192.168.49.2';
// const FRONTEND_ORIGIN = `http://${MINIKUBE_IP}:30073`;
// app.use(express.json());

// app.use(cors({
//   origin: FRONTEND_ORIGIN,
// }));

// app.use('/', userRouter);
// app.use('/backend/auth/', authRouter);

// const PORT = 3000;

// app.listen(PORT, () => {
//   console.log(`server is running at port ${PORT}`);
// });