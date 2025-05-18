// components/AuthForm.jsx
import React, { useState } from 'react';
import { Link } from 'react-router-dom';

export function AuthForm({ type, onSubmit }) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    username: '',
    age: '',
    gender: 'M',
    occupation: 'other',
    zipCode: '00000'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const occupations = [
    'administrator', 'artist', 'doctor', 'educator', 'engineer',
    'entertainment', 'executive', 'healthcare', 'homemaker', 'lawyer',
    'librarian', 'marketing', 'none', 'other', 'programmer', 'retired',
    'salesman', 'scientist', 'student', 'technician', 'writer'
  ];

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(''); // Clear previous errors
        try {
            await onSubmit(formData);
        } catch (err) {
            setError(err.message || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {type === 'signup' && (
        <>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Username
              </label>
              <input
                type="text"
                required
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Age
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  max="120"
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  value={formData.age}
                  onChange={(e) => setFormData({...formData, age: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Gender
                </label>
                <select
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  value={formData.gender}
                  onChange={(e) => setFormData({...formData, gender: e.target.value})}
                >
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Occupation
              </label>
              <select
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                value={formData.occupation}
                onChange={(e) => setFormData({...formData, occupation: e.target.value})}
              >
                {occupations.map(occ => (
                  <option key={occ} value={occ}>
                    {occ.charAt(0).toUpperCase() + occ.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Zip Code
              </label>
              <input
                type="text"
                required
                pattern="(\d{5}|[A-Za-z]\d[A-Za-z] ?\d[A-Za-z]\d)"
                className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                value={formData.zipCode}
                onChange={(e) => setFormData({...formData, zipCode: e.target.value})}
              />
            </div>
          </div>
        </>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email
          </label>
          <input
            type="email"
            required
            className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Password
          </label>
          <input
            type="password"
            required
            minLength="5"
            className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className={`w-full bg-indigo-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-indigo-700 transition-colors shadow-sm ${
            loading ? 'opacity-50 cursor-not-allowed' : ''
        }`}
        >
        {loading ? (
            <span className="flex items-center justify-center">
            <svg className="animate-spin h-5 w-5 mr-3 ..." viewBox="0 0 24 24">
                {/* Add spinner SVG */}
            </svg>
            Processing...
            </span>
        ) : (
            type === 'login' ? 'Sign In' : 'Create Account'
        )}
    </button>

      {error && (
        <p className="text-red-500 text-sm text-center mt-4">{error}</p>
      )}

    </form>
  );
}