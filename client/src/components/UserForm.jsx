// client/src/components/UserForm.jsx
import React, { useState } from 'react';

export function UserForm({ onSubmit }) {
  const [userId, setUserId] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (userId.trim() !== '') {
      onSubmit(userId.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center mb-4">
      <input
        type="number"
        placeholder="User ID"
        value={userId}
        onChange={e => setUserId(e.target.value)}
        className="border p-2 mr-2"
      />
      <button
        type="submit"
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Recommend
      </button>
    </form>
  );
}
