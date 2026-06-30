import { useEffect, useRef, useState, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Bot, ChevronDown, MessageCircle, Send, Sparkles, X,
  Plane, Train, Bus, Star, Clock, MapPin,
  ExternalLink, ArrowRight, Loader2, CheckCircle2, Zap,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const SESSION_KEY = 'travelai_chat_session';

const getSessionId = () => {
  const existing = localStorage.getItem(SESSION_KEY);
  if (existing) return existing;
  const next = globalThis.crypto?.randomUUID?.() || `chat_${Date.now()}`;
  localStorage.setItem(SESSION_KEY, next);
  return next;
};

// ─── Agent Status Labels ───────────────────────────────────────────────────
const AGENT_LABELS = {
  travel_booking_agent: '✈️ Travel Agent searching...',
  hotel_booking_agent: '🏨 Hotel Agent searching...',
  weather_agent: '🌤️ Weather Agent fetching...',
  replanning_agent: '✏️ Replanning itinerary...',
  dining_agent: '🍽️ Dining Agent searching...',
  place_research_agent: '🔍 Researching place...',
  city_explorer_agent: '🏙️ Exploring city...',
  booking_handler: '🔗 Routing to booking...',
  navigation_handler: '🧭 Navigating...',
  itinerary_qa: '📋 Reading itinerary...',
};

// ─── Markdown-light text renderer ─────────────────────────────────────────
function RichText({ text }) {
  if (!text) return null;
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <span>
      {parts.map((part, i) =>
        part.startsWith('**') && part.endsWith('**') ? (
          <strong key={i}>{part.slice(2, -2)}</strong>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </span>
  );
}

function MessageText({ text }) {
  if (!text) return null;
  return (
    <p className="text-sm whitespace-pre-wrap leading-relaxed">
      {text.split('\n').map((line, i, arr) => (
        <span key={i}>
          <RichText text={line} />
          {i < arr.length - 1 && <br />}
        </span>
      ))}
    </p>
  );
}

// ─── Flight Result Card ────────────────────────────────────────────────────
function FlightCard({ flight, onBook }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden text-xs">
      <div className="flex items-center justify-between px-3 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-slate-100">
        <div className="flex items-center gap-1.5">
          {flight.airline_logo && (
            <img src={flight.airline_logo} alt="" className="h-4 w-4 object-contain rounded" onError={e => e.target.style.display='none'} />
          )}
          <span className="font-semibold text-slate-800 text-xs">{flight.airline || 'Flight'}</span>
          {flight.flight_number && <span className="text-slate-400 text-[10px]">{flight.flight_number}</span>}
        </div>
        {flight.badge && (
          <span className="text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full font-medium">{flight.badge}</span>
        )}
      </div>
      <div className="px-3 py-2 space-y-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-900 text-sm">{flight.departure_time || '—'}</span>
            <div className="flex items-center gap-1 text-slate-400">
              <div className="w-6 h-px bg-slate-300" />
              <Plane className="w-3 h-3" />
              <div className="w-6 h-px bg-slate-300" />
            </div>
            <span className="font-bold text-slate-900 text-sm">{flight.arrival_time || '—'}</span>
          </div>
          <span className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">{flight.stops || 'Non-stop'}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1 text-slate-500">
            <Clock className="w-3 h-3" />
            <span>{flight.duration || '—'}</span>
            {flight.data_source && <span className="text-slate-400">· {flight.data_source}</span>}
          </div>
          <div className="text-right">
            <span className="font-bold text-green-700 text-sm">₹{(flight.price_per_person || 0).toLocaleString('en-IN')}</span>
            <span className="text-slate-400 text-[10px] ml-0.5">/person</span>
          </div>
        </div>
        {flight.deal && <p className="text-[10px] text-orange-600">{flight.deal}</p>}
      </div>
      <div className="px-3 pb-2">
        <button
          onClick={() => onBook('/travel')}
          className="w-full text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-lg py-1.5 font-medium transition-colors flex items-center justify-center gap-1"
        >
          Book Flight <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}

// ─── Hotel Result Card ─────────────────────────────────────────────────────
function HotelCard({ hotel, onBook }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden text-xs">
      {hotel.main_image && (
        <div className="relative h-24 overflow-hidden bg-slate-100">
          <img
            src={hotel.main_image}
            alt={hotel.name}
            className="w-full h-full object-cover"
            onError={e => { e.target.style.display = 'none'; }}
          />
          {hotel.deal && hotel.deal !== 'Best available rate' && (
            <span className="absolute top-1.5 left-1.5 text-[10px] bg-orange-500 text-white px-1.5 py-0.5 rounded font-medium">{hotel.deal}</span>
          )}
        </div>
      )}
      <div className="px-3 py-2 space-y-1.5">
        <div className="flex items-start justify-between gap-1">
          <h4 className="font-semibold text-slate-900 leading-tight text-xs">{hotel.name}</h4>
          {hotel.star_rating > 0 && (
            <div className="flex items-center gap-0.5 shrink-0">
              {Array.from({ length: Math.min(hotel.star_rating, 5) }).map((_, i) => (
                <Star key={i} className="w-2.5 h-2.5 text-yellow-400 fill-yellow-400" />
              ))}
            </div>
          )}
        </div>
        <div className="flex items-center gap-1 text-slate-500">
          <MapPin className="w-3 h-3" />
          <span>{hotel.location}</span>
          {hotel.review_score > 0 && (
            <span className="ml-auto bg-green-100 text-green-700 px-1.5 py-0.5 rounded font-medium">
              {hotel.review_score}/10
            </span>
          )}
        </div>
        <div className="flex items-center justify-between">
          <div className="text-[10px] text-slate-500">
            {hotel.check_in_time && `Check-in: ${hotel.check_in_time}`}
          </div>
          <div className="text-right">
            <span className="font-bold text-green-700 text-sm">₹{(hotel.price_per_night || hotel.price_total || 0).toLocaleString('en-IN')}</span>
            <span className="text-slate-400 text-[10px] ml-0.5">/night</span>
          </div>
        </div>
      </div>
      <div className="px-3 pb-2">
        <button
          onClick={() => onBook('/hotels')}
          className="w-full text-xs bg-purple-600 hover:bg-purple-700 text-white rounded-lg py-1.5 font-medium transition-colors flex items-center justify-center gap-1"
        >
          Book Hotel <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}

// ─── Train/Bus Result Card ─────────────────────────────────────────────────
function TransportCard({ item, type, onBook }) {
  const isTrainType = type === 'trains';
  const Icon = isTrainType ? Train : Bus;
  const name = item.train_name || item.operator || item.name || (isTrainType ? 'Train' : 'Bus');
  const number = item.train_number || item.bus_number || '';
  const dep = item.departure_time || item.start_time || '—';
  const arr = item.arrival_time || item.end_time || '—';
  const price = item.price_per_person || 0;
  const duration = item.duration || '—';
  const badge = item.badge || '';

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden text-xs">
      <div className={`flex items-center justify-between px-3 py-2 border-b border-slate-100 ${isTrainType ? 'bg-gradient-to-r from-orange-50 to-amber-50' : 'bg-gradient-to-r from-green-50 to-teal-50'}`}>
        <div className="flex items-center gap-1.5">
          <Icon className={`w-3.5 h-3.5 ${isTrainType ? 'text-orange-600' : 'text-green-600'}`} />
          <span className="font-semibold text-slate-800">{name}</span>
          {number && <span className="text-slate-400 text-[10px]">#{number}</span>}
        </div>
        {badge && <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">{badge}</span>}
      </div>
      <div className="px-3 py-2 space-y-1.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-900 text-sm">{dep}</span>
            <div className="flex items-center gap-1 text-slate-400">
              <div className="w-4 h-px bg-slate-300" />
              <Icon className="w-3 h-3" />
              <div className="w-4 h-px bg-slate-300" />
            </div>
            <span className="font-bold text-slate-900 text-sm">{arr}</span>
          </div>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1 text-slate-500">
            <Clock className="w-3 h-3" />
            <span>{duration}</span>
          </div>
          <div className="text-right">
            <span className="font-bold text-green-700 text-sm">₹{price.toLocaleString('en-IN')}</span>
            <span className="text-slate-400 text-[10px] ml-0.5">/person</span>
          </div>
        </div>
      </div>
      <div className="px-3 pb-2">
        <button
          onClick={() => onBook('/travel')}
          className={`w-full text-xs text-white rounded-lg py-1.5 font-medium transition-colors flex items-center justify-center gap-1 ${isTrainType ? 'bg-orange-600 hover:bg-orange-700' : 'bg-green-600 hover:bg-green-700'}`}
        >
          Book {isTrainType ? 'Train' : 'Bus'} <ArrowRight className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}

// ─── Results Panel ─────────────────────────────────────────────────────────
function ResultsPanel({ actionData, onBook }) {
  if (!actionData) return null;
  const { type, results = [], summary, origin, destination, booking_page } = actionData;

  return (
    <div className="mt-2 space-y-2">
      {summary && (
        <p className="text-[11px] text-slate-500 italic">{summary}</p>
      )}
      {type === 'flights' && results.map((f, i) => (
        <FlightCard key={i} flight={f} onBook={onBook} />
      ))}
      {type === 'hotels' && results.map((h, i) => (
        <HotelCard key={i} hotel={h} onBook={onBook} />
      ))}
      {(type === 'trains' || type === 'buses') && results.map((t, i) => (
        <TransportCard key={i} item={t} type={type} onBook={onBook} />
      ))}
      {booking_page && (
        <button
          onClick={() => onBook(booking_page)}
          className="w-full text-xs text-slate-600 border border-slate-200 hover:bg-slate-50 rounded-lg py-1.5 flex items-center justify-center gap-1 transition-colors"
        >
          <ExternalLink className="w-3 h-3" />
          View all on booking page
        </button>
      )}
    </div>
  );
}

// ─── Main Chatbot Component ────────────────────────────────────────────────
const FloatingChatbot = ({ currentItinerary = null, onItineraryUpdate = null }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [sessionId] = useState(getSessionId);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '✨ Hi! I\'m your AI travel assistant. I can:\n• 🗺️ **Plan a full itinerary** via chat\n• ✏️ **Modify your current itinerary**\n• ✈️ **Search flights** in real-time\n• 🏨 **Find hotels** with live pricing\n• 🚂 **Search trains & buses**\n\nWhat can I help you with?',
      suggestions: ['Plan a trip from Mumbai to Goa', 'Find flights to Delhi', 'Find hotels in Jaipur', 'Modify my itinerary'],
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [agentStatus, setAgentStatus] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) inputRef.current.focus();
  }, [isOpen]);

  const appendAssistantMessage = useCallback((content, suggestions = [], actionData = null, action = null) => {
    setMessages(prev => [...prev, { role: 'assistant', content, suggestions, actionData, action }]);
  }, []);

  const handleSuggestionClick = useCallback((suggestion) => {
    setInput(suggestion);
    handleSend(suggestion);
  }, []);

  const handleBook = useCallback((path) => {
    navigate(path);
    setIsOpen(false);
  }, [navigate]);

  const applyBackendAction = useCallback((data) => {
    if (!data) return;

    if ((data.action === 'update_itinerary' || data.action === 'create_itinerary') && data.action_data?.itinerary) {
      onItineraryUpdate?.(data.action_data.itinerary);
    }

    if (data.action === 'scroll_to_section' && data.action_data?.section) {
      const target = document.querySelector(`[data-section="${data.action_data.section}"]`);
      target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    if (data.action === 'navigate_to_page' && data.action_data?.path) {
      navigate(data.action_data.path);
    }

    if (data.action === 'navigate' && data.action_data?.path) {
      navigate(data.action_data.path);
    }

    if (data.action === 'open_external' && data.action_data?.url) {
      window.open(data.action_data.url, '_blank', 'noreferrer');
    }
  }, [navigate, onItineraryUpdate]);

  const handleSend = useCallback(async (messageText = input) => {
    const trimmed = messageText.trim();
    if (!trimmed) return;

    const userMessage = { role: 'user', content: trimmed };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput('');
    setIsLoading(true);
    setAgentStatus('');

    try {
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const chatHistory = nextMessages.slice(-10).map(msg => ({
        role: msg.role,
        content: msg.content,
      }));

      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          session_id: sessionId,
          chat_history: chatHistory,
          current_itinerary: currentItinerary,
        }),
      });

      const data = response.ok ? await response.json() : null;
      const reply = data?.reply || 'I could not process that request right now.';
      const agent = data?.agent_used || '';
      if (agent) setAgentStatus(AGENT_LABELS[agent] || '');

      const isResultsAction = data?.action === 'show_results';
      const actionData = isResultsAction ? data.action_data : null;

      const suggestions = data?.suggestions?.length
        ? data.suggestions
        : data?.needs_clarification
          ? ['From Mumbai', 'To Goa', '2 travelers', 'Budget ₹15000']
          : ['Plan a trip', 'Modify itinerary', 'Find flights', 'Find hotels'];

      appendAssistantMessage(reply, suggestions, actionData, data?.action);
      applyBackendAction(data);
    } catch (error) {
      console.error('Chat error:', error);
      appendAssistantMessage(
        'The assistant is unavailable right now. Please try again.',
        ['Plan a trip', 'Find flights', 'Find hotels']
      );
    } finally {
      setIsLoading(false);
      setTimeout(() => setAgentStatus(''), 2000);
    }
  }, [input, messages, sessionId, currentItinerary, appendAssistantMessage, applyBackendAction]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* ── Floating Trigger Button ── */}
      <AnimatePresence>
        {!isOpen && (
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            whileHover={{ scale: 1.08 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setIsOpen(true)}
            id="chatbot-trigger-btn"
            className="fixed bottom-6 right-6 z-50 w-16 h-16 rounded-full shadow-2xl flex items-center justify-center bg-gradient-to-br from-indigo-600 to-purple-700 text-white"
            style={{ boxShadow: '0 8px 32px rgba(99,102,241,0.45)' }}
          >
            <MessageCircle className="w-7 h-7" />
            <motion.span
              animate={{ scale: [1, 1.3, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white"
            />
          </motion.button>
        )}
      </AnimatePresence>

      {/* ── Chat Window ── */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 80, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 80, scale: 0.95 }}
            transition={{ type: 'spring', damping: 28, stiffness: 320 }}
            className="fixed bottom-6 right-6 z-50 w-[430px] max-h-[85vh] bg-white rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-slate-200"
            style={{ height: '700px', boxShadow: '0 24px 64px rgba(0,0,0,0.18)' }}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-indigo-700 to-purple-700 px-5 py-4 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-white/15 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="text-white font-semibold text-sm">AI Travel Assistant</h3>
                  <p className="text-white/70 text-xs flex items-center gap-1">
                    <span className="w-1.5 h-1.5 bg-green-400 rounded-full inline-block" />
                    Powered by multi-agent AI
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsMinimized(v => !v)}
                  className="w-8 h-8 rounded-full hover:bg-white/15 flex items-center justify-center transition-colors"
                >
                  <ChevronDown className={`w-5 h-5 text-white transition-transform ${isMinimized ? 'rotate-180' : ''}`} />
                </button>
                <button
                  onClick={() => setIsOpen(false)}
                  className="w-8 h-8 rounded-full hover:bg-white/15 flex items-center justify-center transition-colors"
                >
                  <X className="w-5 h-5 text-white" />
                </button>
              </div>
            </div>

            {!isMinimized && (
              <>
                {/* Capability chips strip */}
                <div className="flex gap-1.5 px-4 py-2 border-b border-slate-100 bg-slate-50 overflow-x-auto shrink-0 scrollbar-hide">
                  {[
                    { icon: '🗺️', label: 'Plan Trip' },
                    { icon: '✈️', label: 'Flights' },
                    { icon: '🏨', label: 'Hotels' },
                    { icon: '🚂', label: 'Trains' },
                    { icon: '🚌', label: 'Buses' },
                    { icon: '✏️', label: 'Modify' },
                  ].map(({ icon, label }) => (
                    <button
                      key={label}
                      onClick={() => {
                        const prompts = {
                          'Plan Trip': 'I want to plan a trip',
                          'Flights': 'Find me flights',
                          'Hotels': 'Find me hotels',
                          'Trains': 'Search for trains',
                          'Buses': 'Search for buses',
                          'Modify': 'Modify my itinerary',
                        };
                        handleSuggestionClick(prompts[label]);
                      }}
                      className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-600 text-[11px] whitespace-nowrap hover:border-indigo-300 hover:text-indigo-700 hover:bg-indigo-50 transition-colors shrink-0"
                    >
                      <span>{icon}</span>
                      <span>{label}</span>
                    </button>
                  ))}
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
                  {messages.map((msg, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className="max-w-[90%]">
                        {msg.role === 'assistant' && (
                          <div className="flex items-center gap-2 mb-1">
                            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-indigo-600 to-purple-700 flex items-center justify-center">
                              <Bot className="w-3.5 h-3.5 text-white" />
                            </div>
                            <span className="text-xs text-slate-400">Assistant</span>
                          </div>
                        )}

                        <div
                          className={`px-4 py-3 rounded-2xl ${
                            msg.role === 'user'
                              ? 'bg-gradient-to-br from-indigo-600 to-purple-700 text-white rounded-br-md'
                              : 'bg-white text-slate-800 border border-slate-200 rounded-bl-md shadow-sm'
                          }`}
                        >
                          <MessageText text={msg.content} />
                        </div>

                        {/* Rich Results Panel */}
                        {msg.role === 'assistant' && msg.actionData && (
                          <ResultsPanel actionData={msg.actionData} onBook={handleBook} />
                        )}

                        {/* Itinerary Updated Badge */}
                        {msg.role === 'assistant' && (msg.action === 'update_itinerary' || msg.action === 'create_itinerary') && (
                          <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="mt-2 flex items-center gap-1.5 text-xs text-green-700 bg-green-50 border border-green-200 px-3 py-1.5 rounded-full w-fit"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Itinerary updated on page
                          </motion.div>
                        )}

                        {/* Suggestion Chips */}
                        {msg.role === 'assistant' && msg.suggestions?.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            {msg.suggestions.map((suggestion, idx) => (
                              <button
                                key={idx}
                                onClick={() => handleSuggestionClick(suggestion)}
                                className="text-xs bg-white border border-slate-200 text-slate-700 px-3 py-1.5 rounded-full hover:bg-indigo-50 hover:border-indigo-300 hover:text-indigo-700 transition-colors"
                              >
                                {suggestion}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}

                  {/* Loading / Agent Status */}
                  {isLoading && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                      <div className="bg-white px-4 py-3 rounded-2xl rounded-bl-md border border-slate-200 shadow-sm">
                        <div className="flex items-center gap-2">
                          <div className="flex items-center gap-1">
                            <span className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" />
                            <span className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <span className="w-2 h-2 bg-indigo-300 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                          </div>
                          {agentStatus && (
                            <span className="text-xs text-slate-500 animate-pulse">{agentStatus}</span>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input Bar */}
                <div className="p-4 bg-white border-t border-slate-200 shrink-0">
                  {agentStatus && !isLoading && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="text-[11px] text-indigo-600 mb-2 flex items-center gap-1"
                    >
                      <Zap className="w-3 h-3" />
                      {agentStatus}
                    </motion.p>
                  )}
                  <div className="flex items-center gap-2 bg-slate-100 rounded-2xl px-4 py-2.5">
                    <input
                      ref={inputRef}
                      type="text"
                      value={input}
                      onChange={e => setInput(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Ask me anything about your trip..."
                      className="flex-1 bg-transparent text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
                    />
                    <button
                      onClick={() => handleSend()}
                      disabled={!input.trim() || isLoading}
                      className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-600 to-purple-700 flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-md transition-all"
                    >
                      {isLoading ? (
                        <Loader2 className="w-4 h-4 text-white animate-spin" />
                      ) : (
                        <Send className="w-4 h-4 text-white" />
                      )}
                    </button>
                  </div>
                  <p className="text-center text-[10px] text-slate-400 mt-2">
                    Powered by Groq LLaMA · Real-time data from Google Flights, Booking.com
                  </p>
                </div>
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default FloatingChatbot;
