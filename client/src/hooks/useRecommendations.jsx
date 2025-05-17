// client/src/hooks/useRecommendations.js
import { useState } from 'react';
import { fetchRecommendations } from '../services/api'; // Adjust path if needed

export const useRecommendations = () => {
  const [recs, setRecs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getRecs = async (userId) => {
    setLoading(true);
    setError(null);
    try {
      const items = await fetchRecommendations(userId);

      console.log(items);

      setRecs(items);
    } catch (err) {
      console.error(err);
      setError('Failed to load recommendations.');
    } finally {
      setLoading(false);
    }
  };

  return { recs, loading, error, getRecs };
};
