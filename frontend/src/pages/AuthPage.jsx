import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Compass, ShieldCheck, Sparkles } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const AuthPage = ({ onAuthSuccess }) => {
  const navigate = useNavigate();
  const [mode, setMode] = useState('login');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const isSignup = mode === 'signup';

  useEffect(() => {
    window.scrollTo(0, 0);
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    const id = window.requestAnimationFrame(() => {
      window.scrollTo(0, 0);
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
    });
    return () => window.cancelAnimationFrame(id);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = isSignup ? '/api/auth/signup' : '/api/auth/login';
      const payload = isSignup
        ? { name: name.trim(), email: email.trim(), password }
        : { email: email.trim(), password };

      const response = await axios.post(`${API_URL}${endpoint}`, payload, {
        headers: { 'Content-Type': 'application/json' },
      });

      onAuthSuccess(response.data.token, response.data.user);
      navigate('/dashboard');
    } catch (err) {
      const message = err?.response?.data?.detail || 'Authentication failed. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="travel-page-shell h-screen min-h-0 px-4 relative overflow-hidden flex items-center justify-center">
      <div className="pointer-events-none absolute -top-16 -left-16 h-64 w-64 rounded-full bg-sky-300/30 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-12 -right-12 h-64 w-64 rounded-full bg-emerald-300/20 blur-3xl" />

      <section className="travel-glass w-full max-w-lg rounded-3xl p-6 md:p-8 shadow-xl border border-white/70 my-0">
        <div className="flex items-center justify-center mb-5">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-sky-100 text-sky-700">
            <Compass className="w-6 h-6" />
          </div>
        </div>

        <div className="text-center mb-6">
          <p className="inline-flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500 bg-white/80 border border-slate-200 rounded-full px-3 py-1 mb-3">
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            TravelAI Account
          </p>
          <h1 className="text-3xl font-black text-slate-900 mb-2">
            {isSignup ? 'Create your travel profile' : 'Welcome back, traveler'}
          </h1>
          <p className="text-slate-600 text-sm md:text-base">
            {isSignup
              ? 'Save itineraries and revisit them anytime from your dashboard.'
              : 'Log in to manage your active and previous itineraries.'}
          </p>
        </div>

        <div className="inline-flex rounded-xl border border-slate-200 bg-white p-1 mb-6 w-full">
          <button
            onClick={() => setMode('login')}
            className={`flex-1 px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
              !isSignup ? 'bg-slate-900 text-white' : 'text-slate-700'
            }`}
          >
            Log In
          </button>
          <button
            onClick={() => setMode('signup')}
            className={`flex-1 px-4 py-2 rounded-lg text-sm font-semibold transition-colors ${
              isSignup ? 'bg-slate-900 text-white' : 'text-slate-700'
            }`}
          >
            Sign Up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {isSignup && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-sky-300"
                placeholder="Your name"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-sky-300"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={6}
              required
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-sky-300"
              placeholder="Minimum 6 characters"
            />
          </div>

          {error && (
            <div className="rounded-xl bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full travel-cta rounded-xl py-3 font-semibold text-white disabled:opacity-60"
          >
            {loading ? 'Please wait...' : isSignup ? 'Create Account' : 'Log In'}
          </button>
        </form>

        <div className="mt-5 text-sm text-slate-600 text-center">
          {isSignup ? 'Already have an account?' : 'New here?'}{' '}
          <button
            onClick={() => setMode(isSignup ? 'login' : 'signup')}
            className="text-slate-900 font-semibold underline"
          >
            {isSignup ? 'Log in' : 'Create an account'}
          </button>
        </div>

        <div className="mt-5 rounded-xl bg-slate-900 text-white px-4 py-3 text-sm flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-300" />
          Your saved itineraries are tied to your account dashboard.
        </div>
      </section>
    </div>
  );
};

export default AuthPage;
