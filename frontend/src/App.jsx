import { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import ItineraryResult from './components/ItineraryResult';
import FloatingChatbot from './components/FloatingChatbot';
import { 
  HowItWorks, 
  Features, 
  PopularDestinations, 
  CTASection, 
  Footer 
} from './components/HomePageSections';
import TravelBooking from './pages/TravelBooking';
import HotelBooking from './pages/HotelBooking';
import AuthPage from './pages/AuthPage';
import Dashboard from './pages/Dashboard';
import { clearAuth, loadAuth, saveAuth } from './utils/auth';
import axios from 'axios';

// Main Home Page Component
function HomePage({
  itinerary,
  loading,
  error,
  user,
  onLogout,
  onSubmit,
  onSaveItinerary,
  isSavingItinerary,
  saveMessage,
}) {
  const handleFormSubmit = async (formData) => {
    await onSubmit(formData);
  };

  return (
    <div className="travel-page-shell font-sans flex flex-col">
      <Navbar user={user} onLogout={onLogout} />
      <main className="flex-grow">
        <section id="hero" data-section="hero">
          <Hero onItinerarySubmit={handleFormSubmit} />
        </section>
        
        <div id="itinerary-result" data-section="itinerary-result" className="container mx-auto px-4 py-14">
          {loading && (
            <div className="text-center text-gray-700 py-20">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-100 rounded-full mb-6">
                <svg className="w-8 h-8 text-indigo-600 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <p className="text-2xl font-bold text-slate-800 mb-2">🤖 Multi-Agent System Active</p>
              <p className="text-gray-600 max-w-md mx-auto">
                Our specialized AI agents are working together to craft your perfect journey...
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-2 text-xs">
                <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full">🌤️ Weather Agent</span>
                <span className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full">🔍 Place Research</span>
                <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full">📸 Photo Agent</span>
                <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded-full">🍽️ Dining Agent</span>
                <span className="bg-pink-100 text-pink-700 px-3 py-1 rounded-full">🏙️ City Explorer</span>
              </div>
            </div>
          )}

          {error && (
            <div className="max-w-md mx-auto text-center bg-red-100 border border-red-300 text-red-800 px-4 py-3 rounded-lg">
              <strong className="font-bold">Oops! </strong>
              <span className="block sm:inline">{error}</span>
            </div>
          )}

          {itinerary && (
            <ItineraryResult
              data={itinerary}
              onSave={onSaveItinerary}
              canSave={Boolean(user)}
              isSaving={isSavingItinerary}
              saveMessage={saveMessage}
            />
          )}
        </div>

        {/* Additional Home Page Sections */}
        {!itinerary && !loading && (
          <>
            <HowItWorks />
            <Features />
            <PopularDestinations />
            <CTASection />
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}

function ScrollToTopOnRouteChange() {
  const location = useLocation();

  useEffect(() => {
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }
  }, []);

  useEffect(() => {
    window.scrollTo(0, 0);
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;

    // Some browsers restore scroll after paint; force one extra reset.
    const id = window.requestAnimationFrame(() => {
      window.scrollTo(0, 0);
      document.documentElement.scrollTop = 0;
      document.body.scrollTop = 0;
    });

    return () => window.cancelAnimationFrame(id);
  }, [location.pathname, location.search, location.hash, location.key]);

  return null;
}

function AppContent() {
  const navigate = useNavigate();
  const [itinerary, setItinerary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [isSavingItinerary, setIsSavingItinerary] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  useEffect(() => {
    const auth = loadAuth();
    setToken(auth.token);
    setUser(auth.user);
  }, []);

  const handleAuthSuccess = (newToken, newUser) => {
    saveAuth(newToken, newUser);
    setToken(newToken);
    setUser(newUser);
  };

  const handleLogout = () => {
    clearAuth();
    setToken(null);
    setUser(null);
    setSaveMessage('Logged out successfully.');
    navigate('/');
  };

  const handleFormSubmit = async (formData) => {
    setLoading(true);
    setItinerary(null);
    setError(null);
    setSaveMessage('');

    // Smooth scroll
    setTimeout(() => {
      const resultSection = document.getElementById('itinerary-result');
      if (resultSection) {
        resultSection.scrollIntoView({ behavior: 'smooth' });
      }
    }, 100);

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const response = await axios.post(`${API_URL}/api/itinerary`, formData, {
        headers: { 'Content-Type': 'application/json' }
      });

      setItinerary(response.data);

    } catch (err) {
      console.error('Failed to fetch itinerary:', err);

      let errorMessage = 'An unknown error occurred.';
      if (err.response && err.response.data && err.response.data.message) {
        errorMessage = err.response.data.message;
      } else if (err.response && err.response.data && err.response.data.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);

    } finally {
      setLoading(false);
    }
  };

  const handleItineraryUpdate = (updatedItinerary) => {
    setItinerary(updatedItinerary);
  };

  const handleSaveItinerary = async () => {
    if (!itinerary) return;
    if (!token) {
      setSaveMessage('Please login first to save itineraries.');
      navigate('/auth');
      return;
    }

    setIsSavingItinerary(true);
    setSaveMessage('');

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const title = itinerary?.title || `Trip to ${itinerary?.destination || 'Destination'}`;

      await axios.post(
        `${API_URL}/api/users/itineraries`,
        {
          title,
          status: 'active',
          itinerary,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      setSaveMessage('Itinerary saved to your dashboard.');
    } catch (err) {
      const message = err?.response?.data?.detail || 'Could not save itinerary.';
      setSaveMessage(message);
    } finally {
      setIsSavingItinerary(false);
    }
  };

  return (
    <>
      <ScrollToTopOnRouteChange />
      <FloatingChatbot />
      <Routes>
        <Route
          path="/"
          element={
            <HomePage
              itinerary={itinerary}
              loading={loading}
              error={error}
              user={user}
              onLogout={handleLogout}
              onSubmit={handleFormSubmit}
              onSaveItinerary={handleSaveItinerary}
              isSavingItinerary={isSavingItinerary}
              saveMessage={saveMessage}
            />
          }
        />
        <Route path="/travel" element={<TravelBooking />} />
        <Route path="/hotels" element={<HotelBooking />} />
        <Route path="/auth" element={<AuthPage onAuthSuccess={handleAuthSuccess} />} />
        <Route
          path="/dashboard"
          element={
            <Dashboard
              token={token}
              user={user}
              onOpenItinerary={handleItineraryUpdate}
            />
          }
        />
      </Routes>
    </>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;