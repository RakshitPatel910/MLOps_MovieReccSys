import mongoose from 'mongoose';
import User from '../model/userSchema.js';
import { getAllUsers, getAllRatings } from './mlClient.js'; // Changed import

const validOccupations = [
  'administrator', 'artist', 'doctor', 'educator', 'engineer',
  'entertainment', 'executive', 'healthcare', 'homemaker', 'lawyer',
  'librarian', 'marketing', 'none', 'other', 'programmer', 'retired',
  'salesman', 'scientist', 'student', 'technician', 'writer'
];

export async function syncUsers() {
  try {
    const mlUsers = await getAllUsers(); // Directly use imported function
    const operations = mlUsers.map(mlUser => ({
      updateOne: {
        filter: { ml_user_id: mlUser.user_id },
        update: {
          $setOnInsert: {
            username: `user${mlUser.user_id}`,
            email: `user${mlUser.user_id}@gmail.com`,
            password: `pass${mlUser.user_id}`
          },
          $set: {
            age: parseInt(mlUser.age) || 25,
            gender: mlUser.gender === 'M' ? 'M' : 'F',
            occupation: validOccupations.includes(mlUser.occupation.toLowerCase()) 
              ? mlUser.occupation 
              : 'other',
            zip_code: '00000'
          }
        },
        upsert: true
      }
    }));

    if (operations.length > 0) {
      await User.bulkWrite(operations, { ordered: false });
    }
    return { users: operations.length };
  } catch (error) {
    console.error('User sync error:', error);
    throw error;
  }
}

export async function syncRatings() {
  try {
    const mlRatings = await getAllRatings(); // Directly use imported function
    const userMap = new Map();

    mlRatings.forEach(rating => {
      if (!userMap.has(rating.user_id)) {
        userMap.set(rating.user_id, new Map());
      }
      userMap.get(rating.user_id).set(rating.item_id, {
        movie_id: rating.item_id,
        rating: rating.rating,
        timestamp: new Date(rating.timestamp * 1000 || Date.now())
      });
    });

    const operations = [];
    for (const [userId, ratings] of userMap) {
      operations.push({
        updateOne: {
          filter: { ml_user_id: parseInt(userId) },
          update: {
            $addToSet: {
              watchlist: {
                $each: Array.from(ratings.values())
              }
            }
          }
        }
      });
    }

    if (operations.length > 0) {
      await User.bulkWrite(operations, { ordered: false });
    }
    return { ratings: operations.length };
  } catch (error) {
    console.error('Rating sync error:', error);
    throw error;
  }
}

export async function fullSync() {
  try {
    const userResult = await syncUsers();
    const ratingResult = await syncRatings();
    return {
      success: true,
      users: userResult.users,
      ratings: ratingResult.ratings
    };
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}