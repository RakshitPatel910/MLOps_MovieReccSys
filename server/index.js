import express from 'express';
import cors from 'cors';
import { CronJob } from 'cron';
import { connectDB } from './db.js';
import userRouter from './routes/user.js';
import authRouter from './routes/auth.js';
import { fullSync } from './services/syncServices.js';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(cors());

// Database Connection
const startServer = async () => {
  try {
    const dbConnection = await connectDB();
    app.locals.db = dbConnection;

    // Routes
    app.use('/api', userRouter);
    app.use('/api/auth', authRouter);

    // Manual sync endpoint
    app.post('/api/admin/sync', async (req, res) => {
      try {
        const result = await fullSync();
        res.json(result);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Start server
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`);
      
      // Start sync processes
      scheduleRecurringSync();
      initialSync();
    });

  } catch (error) {
    console.error("Failed to initialize server:", error);
    process.exit(1);
  }
};

// Sync Functions
const initialSync = async () => {
  console.log('[SYNC] Running initial sync...');
  try {
    const result = await fullSync();
    console.log(`[SYNC] Initial sync completed. Users: ${result.users}, Ratings: ${result.ratings}`);
  } catch (error) {
    console.error('[SYNC] Initial sync failed:', error);
  }
};

const scheduleRecurringSync = () => {
  // Every 6 hours at minute 0
  new CronJob(
    '0 */6 * * *',
    async () => {
      console.log('[SYNC] Starting scheduled sync...');
      try {
        const result = await fullSync();
        console.log(`[SYNC] Scheduled sync completed. Users: ${result.users}, Ratings: ${result.ratings}`);
      } catch (error) {
        console.error('[SYNC] Scheduled sync failed:', error);
      }
    },
    null,
    true,
    'UTC'
  );
};

// Start the application
startServer();