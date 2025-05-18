// components/WatchlistTable.jsx
import React from 'react';

export function WatchlistTable({ watchlist }) {
  return (
    <div className="mt-8 bg-white rounded-xl shadow-md p-6">
      <h3 className="text-xl font-semibold text-gray-800 mb-4">Watched Movies</h3>
      <div className="overflow-x-auto">
        <table className="w-full table-auto">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Movie ID</th>
              <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Title</th>
              <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Rating</th>
              <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Date Watched</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {watchlist.map((item) => (
              <tr key={item.movie_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-gray-600">{item.movie_id}</td>
                <td className="px-4 py-3 text-gray-600">{item.title}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm">
                    {item.rating.toFixed(1) > 5 ? 5 : item.rating.toFixed(1)}/5
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-600">
                  {new Date(item.timestamp).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                  })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}