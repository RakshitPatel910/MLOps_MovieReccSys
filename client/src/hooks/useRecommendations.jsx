// client/src/hooks/useRecommendations.js
import { useState } from 'react';

const recommendations = {
  1: [101, 102, 103],
  2: [104, 105],
  3: [106],
  4: [],
  5: [107, 108, 109, 110]
};

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
