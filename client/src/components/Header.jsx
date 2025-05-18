import React from 'react';
import { Link, useNavigate } from 'react-router-dom';

export default function Header() {
  const navigate = useNavigate();
  const isLoggedIn = !!localStorage.getItem('userId');

  const handleLogout = () => {
    localStorage.removeItem('userId');
    localStorage.removeItem('userProfile');
    
    window.dispatchEvent(new Event('storage'));
    navigate('/login', { replace: true });
  };

  return (
    <header className="bg-white shadow-sm">
      <nav className="max-w-6xl mx-auto px-4 py-3 flex justify-between items-center">
        <Link to="/" className="text-xl font-bold text-gray-800">
          Movie Recommender
        </Link>
        
        <div className="flex items-center gap-4">
          {isLoggedIn ? (
            <>
              <Link to="/recs" className="text-gray-600 hover:text-blue-600">
                Recommendations
              </Link>
              <button
                onClick={handleLogout}
                className="text-gray-600 hover:text-blue-600"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-gray-600 hover:text-blue-600">
                Login
              </Link>
              <Link to="/signup" className="text-gray-600 hover:text-blue-600">
                Sign Up
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}