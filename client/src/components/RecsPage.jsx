import React, { useEffect, useState } from 'react';
import { useRecommendations } from '../hooks/useRecommendations';
import { postFeedback } from '../services/api';

export default function RecsPage() {
  const userId = localStorage.getItem('userId');
  const { recs, loading, error, getRecs } = useRecommendations();
  const [movieId, setMovieId] = useState('');
  const [rating, setRating] = useState('');
  const [formError, setFormError] = useState('');

  // load recommendations on mount
  useEffect(() => {
    if (userId) getRecs(userId);
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
    <div className="max-w-xl mx-auto p-6">
      <h2 className="text-xl mb-4">Recommendations for User {userId}</h2>
      {loading && <p>Loading…</p>}
      {error && <p className="text-red-500">{error}</p>}

      {recs.length > 0 && (
        <ul className="mb-6">
          {recs.map(id => (
            <li key={id}>Movie ID: {id}</li>
          ))}
        </ul>
      )}

      <h3 className="text-lg mb-2">Submit Feedback</h3>
      {formError && <p className="text-red-500 mb-2">{formError}</p>}
      <form onSubmit={handleFeedback} className="space-y-4">
        <div>
          <label>Movie ID</label>
          <input
            value={movieId}
            onChange={e => setMovieId(e.target.value)}
            className="w-full border px-2 py-1"
          />
        </div>
        <div>
          <label>Rating (0–5)</label>
          <input
            type="number"
            value={rating}
            step="0.1"
            min="0"
            max="5"
            onChange={e => setRating(e.target.value)}
            className="w-full border px-2 py-1"
          />
        </div>
        <button
          type="submit"
          className="bg-green-600 text-white py-2 px-4 rounded"
        >
          Send Feedback
        </button>
      </form>
    </div>
  );
}
