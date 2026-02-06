import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import ItineraryResult from './components/ItineraryResult';
import ChatBox from './components/ChatBox';
import FloatingChatbot from './components/FloatingChatbot';
import { 
  HowItWorks, 
  Features, 
  PopularDestinations, 
  Stats, 
  Testimonials, 
  CTASection, 
  Footer 
} from './components/HomePageSections';
import TravelBooking from './pages/TravelBooking';
import HotelBooking from './pages/HotelBooking';
import axios from 'axios';

// Main Home Page Component
function HomePage() {
  const [itinerary, setItinerary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tripRequest, setTripRequest] = useState(null);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  const handleFormSubmit = async (formData) => {
    setLoading(true);
    setItinerary(null);
    setError(null);
    setTripRequest(formData);

    // Generate session ID for chat
    const newSessionId = `${formData.destination}_${formData.startDate}`;
    setSessionId(newSessionId);

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

  // Handle itinerary updates from chat
  const handleItineraryUpdate = (updatedItinerary) => {
    setItinerary(updatedItinerary);
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans flex flex-col">
      <Navbar />
      <main className="flex-grow">
        <section id="hero" data-section="hero">
          <Hero onItinerarySubmit={handleFormSubmit} />
        </section>
        
        <div id="itinerary-result" data-section="itinerary-result" className="container mx-auto px-4 py-12">
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

          {itinerary && <ItineraryResult data={itinerary} />}
        </div>

        {/* Additional Home Page Sections */}
        {!itinerary && !loading && (
          <>
            <HowItWorks />
            <Features />
            <PopularDestinations />
            <Stats />
            <Testimonials />
            <CTASection />
          </>
        )}
      </main>
      
      {/* Chat Box - Only show when itinerary exists */}
      {itinerary && sessionId && (
        <ChatBox 
          sessionId={sessionId} 
          onItineraryUpdate={handleItineraryUpdate}
        />
      )}
      
      <Footer />
    </div>
  );
}

function App() {
  return (
    <Router>
      <FloatingChatbot />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/travel" element={<TravelBooking />} />
        <Route path="/hotels" element={<HotelBooking />} />
      </Routes>
    </Router>
  );
}

export default App;