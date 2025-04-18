import mongoose from 'mongoose';

const userSchema = new mongoose.Schema({
  // _id:String,
  userName: {
    type: String,
    required: true,
  },

  name: {
    type: String,
    default: null,
  },

  age: {
    type: Date,
    default: null,
  },

  email: {
    type: String,
    required: true,
  },

  password: {
    type: String,
    required: true,
  },
  watchlist: [
    {
      movieId: String,
      isWatching: Boolean,
      isWatched: Boolean,
      genre: [
        {
          genreId: String,
        },
      ],
      date: Date,
    },
  ],
}); 

const  User = mongoose.model('User', userSchema);

module.exports = User;