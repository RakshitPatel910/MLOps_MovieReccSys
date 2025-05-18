import React, { useEffect, useState } from 'react';
import { useRecommendations } from '../hooks/useRecommendations';
import { postFeedback } from '../services/api';
import { WatchlistTable } from './WatchlistTable';

export default function RecsPage() {
  const userId = localStorage.getItem('userId');
  const { recs, loading, error, getRecs } = useRecommendations();
  const [movieId, setMovieId] = useState('');
  const [rating, setRating] = useState('');
  const [formError, setFormError] = useState('');
  const [watchlist, setWatchlist] = useState([]);

  // load recommendations on mount
  useEffect(() => {
    if (userId) getRecs(userId);

    const userProfile = JSON.parse(localStorage.getItem('userProfile'));
    if (userProfile?.watchlist) {
      setWatchlist(userProfile.watchlist);
    }

    console.log('first')
    console.log(userProfile)
  }, [userId]);

  const handleFeedback = async e => {
    e.preventDefault();
    const num = Number(rating);
    if (isNaN(num) || num < 0 || num > 5) {
      setFormError('Rating must be a number between 0 and 5.');
      return;
    }
    try {
      await postFeedback({ uid: userId, iid: movieId, rating: num });
      getRecs(userId);             // refresh recommendations
      setMovieId('');              
      setRating('');               
      setFormError('');
    } catch {
      setFormError('Failed to submit feedback.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-blue-100 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
          <h2 className="text-3xl font-bold text-gray-800 mb-6">
            Recommendations for User {userId}
          </h2>

          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600"></div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 text-red-700 p-4 rounded-lg mb-6">
              {error}
            </div>
          )}

          {recs.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {recs.map((movie) => (
                <div 
                  key={movie.id}
                  className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-shadow"
                >
                  <div className="p-6">
                    <h3 className="text-xl font-semibold text-gray-800 mb-2">
                      {movie.title}
                    </h3>
                    {/* <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">Rating:</span>
                      <span className="text-indigo-600 font-medium">
                        {movie.rating}/5
                      </span>
                    </div> */}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {watchlist.length > 0 && <WatchlistTable watchlist={watchlist} />}

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h3 className="text-2xl font-semibold text-gray-800 mb-6">
            Submit Feedback
          </h3>
          {/* Feedback form remains similar with updated styling */}
        </div>
      </div>
    </div>
  );
}
