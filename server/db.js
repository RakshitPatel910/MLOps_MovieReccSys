import mongoose from "mongoose";

export const connectDB = async () => {
  try {
    await mongoose.connect("mongodb+srv://rakshitpatel910:3At0jkIMdjPzhegb@movie-cluster.ksqkwri.mongodb.net/?retryWrites=true&w=majority&appName=movie-cluster");
    console.log('MongoDB connected');
  } catch (err) {
    console.error('Connection error:', err);
    process.exit(1);
  }
};