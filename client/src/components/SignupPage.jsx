// components/SignupPage.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthForm } from './AuthForm';
import { signup } from '../services/api';

export default function SignupPage() {
  const navigate = useNavigate();
  const [error, setError] = React.useState('');

  const handleSubmit = async (formData) => {
    try {
      const { status, message, profile } = await signup(formData);

      if (status) {
        localStorage.setItem('userId', profile.ml_user_id);
        localStorage.setItem('userProfile', JSON.stringify(profile));

        window.dispatchEvent(new Event('storage'));  // Add this line
        navigate('/recs', { replace: true });  // Add replace: true
      } else {
        setError(message);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-blue-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 transition-all duration-300 hover:shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-indigo-600 mb-2">Get Started</h1>
          <p className="text-gray-600">Create your movie recommender account</p>
        </div>
        <AuthForm 
            type="signup" 
            onSubmit={handleSubmit} 
            error={error}
        />
        <div className="mt-6 text-center">
          <p className="text-gray-600">
            Already have an account?{' '}
            <button 
              onClick={() => navigate('/login')}
              className="text-indigo-600 font-semibold hover:text-indigo-800 transition-colors"
            >
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}