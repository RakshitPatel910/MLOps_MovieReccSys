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


import React from 'react';
import { UserForm } from './components/UserForm';
import { RecommendationList } from './components/RecommendationList';
import { useRecommendations } from './hooks/useRecommendations';

function App() {
  const { recs, loading, error, getRecs } = useRecommendations();

  return (
    <>
      <div className="header">
        <h1>Movie Recommender</h1>
      </div>
      <div className="main-content">
        <UserForm onSubmit={getRecs} />
        {loading && <p>Loading...</p>}
        {error && <p className="text-red-500">Error: {error}</p>}
        <RecommendationList recs={recs} />
      </div>
    </>
  );
}


export default App;
