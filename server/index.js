import express from 'express';
import cors from 'cors';

const app = express();

app.use(app.json());
app.use(cors());

const PORT = '3010';

app.listen(PORT, () => {
    console.log("server is running at port 3010");
  });