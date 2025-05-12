export const fetchRecommendations = async (userId) => {
    if (!userId) return [];
    const response = await fetch(`http://app:8000/recommend/${userId}`);
    if (!response.ok) {
      throw new Error(`Error fetching recommendations: ${response.statusText}`);
    }
    const data = await response.json();
    return data.recommended_items || [];
  };