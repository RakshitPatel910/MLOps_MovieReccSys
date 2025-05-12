import React from 'react';

export function RecommendationList({ recs }) {
  if (!recs.length) {
    return <p>No recommendations yet.</p>;
  }

  return (
    <ul className="mt-4">
      {recs.map(id => (
        <li key={id}>Movie ID: {id}</li>
      ))}
    </ul>
  );
}