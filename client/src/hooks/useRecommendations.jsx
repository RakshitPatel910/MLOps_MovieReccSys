// client/src/hooks/useRecommendations.js
import { useState } from 'react';
import { recommendations } from '../data/dummyRecs';

export const useRecommendations = () => {
  const [recs, setRecs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getRecs = (userId) => {
    setLoading(true);
    setError(null);
    try {
      const items = recommendations[userId] || [];
      setRecs(items);
    } catch (err) {
      setError('Failed to load recommendations.');
    } finally {
      setLoading(false);
    }
  };

  return { recs, loading, error, getRecs };
};
