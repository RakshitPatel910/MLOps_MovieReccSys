import mongoose from 'mongoose';
import bcrypt from 'bcryptjs';

const validOccupations = [
  'administrator', 'artist', 'doctor', 'educator', 
  'engineer', 'entertainment', 'executive', 'healthcare',
  'homemaker', 'lawyer', 'librarian', 'marketing',
  'none', 'other', 'programmer', 'retired',
  'salesman', 'scientist', 'student', 'technician',
  'writer'
];

const userSchema = new mongoose.Schema({
  // From ML dataset
  ml_user_id: {
    type: Number,  // Matches u.user's user IDs
    required: true,
    unique: true
  },
  age: {
    type: Number,
    min: 1,
    max: 120
  },
  gender: {
    type: String,
    enum: ['M', 'F']
  },
  occupation: {
    type: String,
    enum: validOccupations,
    default: 'other'
  },
  zip_code: {
    type: String,
    validate: {
        validator: function(v) {
        // Allow both 5-digit ZIPs and Canadian postal codes
        return /(^\d{5}$)|(^[A-Za-z]\d[A-Za-z] ?\d[A-Za-z]\d$)/.test(v);
        },
        message: props => `${props.value} is not a valid postal code!`
    },
    default: '00000'
    },
  
  // Application-specific fields
  username: {
    type: String,
    required: true,
    unique: true,
    trim: true
  },
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    match: [/\S+@\S+\.\S+/, 'is invalid']
  },
  password: {
    type: String,
    required: true,
    select: false
  },
  watchlist: [{
    movie_id: Number,  // Matches u.item IDs
    rating: {
      type: Number,
      min: 1,
      max: 5
    },
    timestamp: {
      type: Date,
      default: Date.now
    }
  }]
}, { timestamps: true });


// Password hashing middleware
userSchema.pre('save', async function(next) {
  // Only hash if password is modified (or new)
  if (!this.isModified('password')) return next();
  
  try {
    const salt = await bcrypt.genSalt(12);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (error) {
    next(error);
  }
});

// Password comparison method
userSchema.methods.comparePassword = async function(candidatePassword) {
  return await bcrypt.compare(candidatePassword, this.password);
};


export default mongoose.model('User', userSchema);