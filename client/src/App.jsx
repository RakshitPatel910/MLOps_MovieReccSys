/*
Project Structure:

src/
├── components/
│   ├── UserForm.js
│   └── RecommendationList.js
├── hooks/
│   └── useRecommendations.js
├── services/
│   └── api.js
├── App.js
└── index.js
*/


// import { useState } from 'react'
// import reactLogo from './assets/react.svg'
// import viteLogo from '/vite.svg'
// import './App.css'

// function App() {
//   const [count, setCount] = useState(0)

//   return (
//     <>
      
//     </>
//   )
// }


// import React from 'react';
// import { UserForm } from './components/UserForm';
// import { RecommendationList } from './components/RecommendationList';
// import { useRecommendations } from './hooks/useRecommendations';

// function App() {
//   const { recs, loading, error, getRecs } = useRecommendations();

//   return (
//     <>
//       <div className="header">
//         <h1>Movie Recommender</h1>
//       </div>
//       <div className="main-content">
//         <UserForm onSubmit={getRecs} />
//         {loading && <p>Loading...</p>}
//         {error && <p className="text-red-500">Error: {error}</p>}
//         <RecommendationList recs={recs} />
//       </div>
//     </>
//   );
// }


// export default App;

import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import LoginPage from './components/LoginPage';
import SignupPage from './components/SignupPage';
import RecsPage from './components/RecsPage';
import Header from './components/Header';

function App() {
  const location = useLocation();
  const [isLoggedIn, setIsLoggedIn] = useState(
    !!localStorage.getItem('userId')
  );

  // Listen for storage changes
  useEffect(() => {
    const checkAuth = () => {
      const loggedIn = !!localStorage.getItem('userId');
      if (loggedIn !== isLoggedIn) {
        setIsLoggedIn(loggedIn);
      }
    };

    window.addEventListener('storage', checkAuth);
    return () => window.removeEventListener('storage', checkAuth);
  }, [isLoggedIn]);

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      <Routes location={location} key={location.pathname}>
        <Route
          path="/login"
          element={!isLoggedIn ? <LoginPage /> : <Navigate to="/recs" replace />}
        />
        <Route
          path="/signup"
          element={!isLoggedIn ? <SignupPage /> : <Navigate to="/recs" replace />}
        />
        <Route
          path="/recs"
          element={isLoggedIn ? <RecsPage /> : <Navigate to="/login" replace />}
        />
        <Route
          path="*"
          element={<Navigate to={isLoggedIn ? "/recs" : "/login"} replace />}
        />
      </Routes>
    </div>
  );
}

export default App;