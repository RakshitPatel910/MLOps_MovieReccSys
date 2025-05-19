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
      const res = await postFeedback({ uid: userId, iid: movieId, rating: num });

      console.log(res);

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
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (Scrollable) */}
        <div className="lg:col-span-2 space-y-8">
          {/* Recommendations Section */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
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
                      <div className="flex items-baseline gap-5"> {/* Changed from gap-2 to gap-3 */}
                        <span className="text-sm font-medium text-indigo-600">#{movie.item_id}</span>
                        <h3 className="text-xl font-semibold text-gray-800">
                          {movie.title}
                        </h3>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Watchlist Section */}
          {watchlist.length > 0 && <WatchlistTable watchlist={watchlist} />}
        </div>

        {/* Right Column (Sticky Feedback Form) */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-2xl shadow-xl p-8 sticky top-8 h-fit">
            <h3 className="text-2xl font-semibold text-gray-800 mb-6">
              Submit Feedback
            </h3>
            
            <form onSubmit={handleFeedback} className="space-y-4">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Movie ID
                  </label>
                  <input
                    type="number"
                    value={movieId}
                    onChange={(e) => setMovieId(e.target.value)}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="Enter movie ID"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rating (0-5)
                  </label>
                  <input
                    type="number"
                    value={rating}
                    min="0"
                    max="5"
                    step="0.5"
                    onChange={(e) => setRating(e.target.value)}
                    className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="Enter rating"
                    required
                  />
                </div>
              </div>

              {formError && (
                <div className="text-red-600 text-sm mt-2">{formError}</div>
              )}

              <button
                type="submit"
                className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors"
              >
                Submit Feedback
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
