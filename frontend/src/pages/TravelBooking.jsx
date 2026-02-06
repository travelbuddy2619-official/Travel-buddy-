import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    Plane, Train, Bus, Search, Calendar, Users, IndianRupee, 
    Clock, Star, ArrowRight, ExternalLink, Loader2, MapPin,
    Luggage, CheckCircle, AlertCircle, Home, Hotel, Car, Ship,
    Palmtree, Gift, Phone, ChevronRight, TrendingUp, ArrowLeftRight,
    Shield, Tag, Award
} from 'lucide-react';
import { Link } from 'react-router-dom';

const TravelBooking = () => {
    const [searchParams, setSearchParams] = useState({
        origin: '',
        destination: '',
        travel_date: '',
        travel_type: 'all',
        budget: '',
        passengers: 1
    });
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('all');
    const [error, setError] = useState(null);

    const handleSearch = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResults(null);

        try {
            const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_URL}/api/search/travel`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...searchParams,
                    budget: searchParams.budget ? parseInt(searchParams.budget) : null,
                    travel_type: activeTab
                })
            });

            const data = await response.json();
            
            if (data.success) {
                setResults(data);
            } else {
                setError('Failed to fetch travel options. Please try again.');
            }
        } catch (err) {
            console.error('Search error:', err);
            setError('An error occurred while searching. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const formatPrice = (price) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(price);
    };

    const FlightCard = ({ flight, index }) => (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-xl transition-all"
        >
            {/* Deal Banner */}
            {flight.deal && (
                <div className="bg-gradient-to-r from-green-500 to-emerald-500 text-white text-sm px-4 py-1.5 font-medium flex items-center justify-between">
                    <span>🎉 {flight.deal}</span>
                    {flight.is_real_data && (
                        <span className="flex items-center gap-1 bg-red-500 px-2 py-0.5 rounded-full text-xs">
                            <span className="w-2 h-2 bg-white rounded-full animate-pulse"></span>
                            LIVE
                        </span>
                    )}
                </div>
            )}
            
            {/* Show LIVE badge even without deal */}
            {!flight.deal && flight.is_real_data && (
                <div className="bg-gradient-to-r from-red-500 to-pink-500 text-white text-sm px-4 py-1.5 font-medium flex items-center gap-2">
                    <span className="w-2 h-2 bg-white rounded-full animate-pulse"></span>
                    Live Price from Booking.com
                </div>
            )}
            
            {/* Badge */}
            {flight.badge && (
                <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm px-4 py-1.5 font-medium">
                    {flight.badge}
                </div>
            )}
            
            <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center">
                            <Plane className="w-6 h-6 text-indigo-600" />
                        </div>
                        <div>
                            <h3 className="font-bold text-gray-800">{flight.airline}</h3>
                            <p className="text-sm text-gray-500">{flight.flight_number}</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <p className="text-2xl font-bold text-indigo-600">{formatPrice(flight.price_per_person)}</p>
                        <p className="text-xs text-gray-500">per person</p>
                        {flight.passengers > 1 && (
                            <p className="text-sm text-gray-600">
                                Total: {formatPrice(flight.total_price)} ({flight.passengers} pax)
                            </p>
                        )}
                    </div>
                </div>

                {/* Flight Times */}
                <div className="flex items-center justify-between py-4 border-t border-b border-gray-100">
                    <div className="text-center">
                        <p className="text-xl font-bold text-gray-800">{flight.departure_time}</p>
                        <p className="text-sm text-gray-500">{searchParams.origin}</p>
                    </div>
                    <div className="flex-1 px-4">
                        <div className="flex items-center gap-2">
                            <div className="flex-1 h-0.5 bg-gray-200"></div>
                            <div className="text-center">
                                <Clock className="w-4 h-4 text-gray-400 mx-auto" />
                                <p className="text-xs text-gray-500 mt-1">{flight.duration}</p>
                                <p className="text-xs text-gray-400">{flight.stops}</p>
                            </div>
                            <div className="flex-1 h-0.5 bg-gray-200"></div>
                        </div>
                    </div>
                    <div className="text-center">
                        <p className="text-xl font-bold text-gray-800">{flight.arrival_time}</p>
                        <p className="text-sm text-gray-500">{searchParams.destination}</p>
                    </div>
                </div>

                {/* Details */}
                <div className="mt-4 flex flex-wrap gap-2">
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full flex items-center gap-1">
                        <Luggage className="w-3 h-3" /> {flight.baggage}
                    </span>
                    <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                        {flight.class}
                    </span>
                    {flight.rating && (
                        <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded-full flex items-center gap-1">
                            <Star className="w-3 h-3" /> {flight.rating}
                        </span>
                    )}
                </div>

                {/* Why Recommended */}
                {flight.why_recommended && (
                    <p className="mt-3 text-sm text-green-600 flex items-center gap-1">
                        <CheckCircle className="w-4 h-4" /> {flight.why_recommended}
                    </p>
                )}

                {/* Book Button */}
                <a
                    href={flight.booking_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-4 w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-colors"
                >
                    Book Now <ExternalLink className="w-4 h-4" />
                </a>
            </div>
        </motion.div>
    );

    const TrainCard = ({ train, index }) => (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-xl transition-all"
        >
            {train.deal && (
                <div className="bg-gradient-to-r from-orange-500 to-amber-500 text-white text-sm px-4 py-1.5 font-medium">
                    🚂 {train.deal}
                </div>
            )}
            
            <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                            <Train className="w-6 h-6 text-orange-600" />
                        </div>
                        <div>
                            <h3 className="font-bold text-gray-800">{train.train_name}</h3>
                            <p className="text-sm text-gray-500">#{train.train_number}</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <p className="text-2xl font-bold text-orange-600">{formatPrice(train.price_per_person)}</p>
                        <p className="text-xs text-gray-500">per person</p>
                    </div>
                </div>

                {/* Train Times */}
                <div className="flex items-center justify-between py-4 border-t border-b border-gray-100">
                    <div className="text-center">
                        <p className="text-xl font-bold text-gray-800">{train.departure_time}</p>
                        <p className="text-sm text-gray-500">{searchParams.origin}</p>
                    </div>
                    <div className="flex-1 px-4 text-center">
                        <Clock className="w-4 h-4 text-gray-400 mx-auto" />
                        <p className="text-xs text-gray-500 mt-1">{train.duration}</p>
                    </div>
                    <div className="text-center">
                        <p className="text-xl font-bold text-gray-800">{train.arrival_time}</p>
                        <p className="text-sm text-gray-500">{searchParams.destination}</p>
                    </div>
                </div>

                {/* Details */}
                <div className="mt-4 flex flex-wrap gap-2">
                    <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded-full">
                        {train.class}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                        train.availability === 'Available' 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-amber-100 text-amber-700'
                    }`}>
                        {train.availability}
                    </span>
                    {train.pantry && (
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                            🍽️ Pantry
                        </span>
                    )}
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                        {train.days_running}
                    </span>
                </div>

                {train.why_recommended && (
                    <p className="mt-3 text-sm text-green-600 flex items-center gap-1">
                        <CheckCircle className="w-4 h-4" /> {train.why_recommended}
                    </p>
                )}

                <a
                    href={train.booking_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-4 w-full bg-orange-600 hover:bg-orange-700 text-white py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-colors"
                >
                    Book on IRCTC <ExternalLink className="w-4 h-4" />
                </a>
            </div>
        </motion.div>
    );

    const BusCard = ({ bus, index }) => (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-xl transition-all"
        >
            {bus.deal && (
                <div className="bg-gradient-to-r from-red-500 to-pink-500 text-white text-sm px-4 py-1.5 font-medium">
                    🎫 {bus.deal}
                </div>
            )}
            
            <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                            <Bus className="w-6 h-6 text-red-600" />
                        </div>
                        <div>
                            <h3 className="font-bold text-gray-800">{bus.operator}</h3>
                            <p className="text-sm text-gray-500">{bus.bus_type}</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <p className="text-2xl font-bold text-red-600">{formatPrice(bus.price_per_person)}</p>
                        <p className="text-xs text-gray-500">per person</p>
                    </div>
                </div>

                {/* Bus Times */}
                <div className="flex items-center justify-between py-4 border-t border-b border-gray-100">
                    <div className="text-center">
                        <p className="text-xl font-bold text-gray-800">{bus.departure_time}</p>
                        <p className="text-sm text-gray-500">{bus.boarding_point}</p>
                    </div>
                    <div className="flex-1 px-4 text-center">
                        <Clock className="w-4 h-4 text-gray-400 mx-auto" />
                        <p className="text-xs text-gray-500 mt-1">{bus.duration}</p>
                    </div>
                    <div className="text-center">
                        <p className="text-xl font-bold text-gray-800">{bus.arrival_time}</p>
                        <p className="text-sm text-gray-500">{bus.dropping_point}</p>
                    </div>
                </div>

                {/* Details */}
                <div className="mt-4 flex flex-wrap gap-2">
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                        {bus.seats_available} seats left
                    </span>
                    {bus.rating && (
                        <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded-full flex items-center gap-1">
                            <Star className="w-3 h-3" /> {bus.rating} ({bus.reviews_count})
                        </span>
                    )}
                </div>

                {/* Amenities */}
                {bus.amenities?.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-1">
                        {bus.amenities.map((amenity, idx) => (
                            <span key={idx} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                                {amenity}
                            </span>
                        ))}
                    </div>
                )}

                {bus.why_recommended && (
                    <p className="mt-3 text-sm text-green-600 flex items-center gap-1">
                        <CheckCircle className="w-4 h-4" /> {bus.why_recommended}
                    </p>
                )}

                <a
                    href={bus.booking_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-4 w-full bg-red-600 hover:bg-red-700 text-white py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-colors"
                >
                    Book on RedBus <ExternalLink className="w-4 h-4" />
                </a>
            </div>
        </motion.div>
    );

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Header with Service Tabs - MakeMyTrip Style */}
            <header className="bg-gradient-to-r from-[#041E42] to-[#0D47A1] sticky top-0 z-50">
                {/* Top Bar */}
                <div className="container mx-auto px-4 py-3 flex items-center justify-between border-b border-white/10">
                    <Link to="/" className="flex items-center gap-2">
                        <div className="bg-white rounded-lg p-1.5">
                            <span className="text-xl font-black text-[#041E42]">Travel</span>
                            <span className="text-xl font-black text-orange-500">AI</span>
                        </div>
                    </Link>
                    <div className="flex items-center gap-4 text-white/90 text-sm">
                        <button className="flex items-center gap-2 hover:text-white transition-colors">
                            <Gift className="w-4 h-4" /> Offers
                        </button>
                        <button className="flex items-center gap-2 hover:text-white transition-colors">
                            <Phone className="w-4 h-4" /> Support
                        </button>
                        <button className="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg transition-colors">
                            Login / Sign Up
                        </button>
                    </div>
                </div>
                
                {/* Service Tabs */}
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-center gap-1 md:gap-3 overflow-x-auto">
                        {[
                            { icon: Plane, label: 'Flights', path: '/travel', active: true },
                            { icon: Hotel, label: 'Hotels', path: '/hotels', active: false },
                            { icon: Train, label: 'Trains', path: '/travel', active: false },
                            { icon: Bus, label: 'Buses', path: '/travel', active: false },
                            { icon: Car, label: 'Cabs', path: '#', active: false },
                            { icon: Palmtree, label: 'Holidays', path: '#', active: false },
                        ].map((item, idx) => (
                            <Link 
                                key={idx}
                                to={item.path}
                                className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-all min-w-[80px] ${
                                    item.active 
                                        ? 'bg-white text-[#041E42]' 
                                        : 'text-white/80 hover:bg-white/10 hover:text-white'
                                }`}
                            >
                                <item.icon className="w-5 h-5" />
                                <span className="text-xs font-medium whitespace-nowrap">{item.label}</span>
                                {item.active && <div className="w-full h-0.5 bg-orange-500 rounded-full mt-1"></div>}
                            </Link>
                        ))}
                    </div>
                </div>
            </header>

            {/* Hero Section with Background Image */}
            <section className="relative min-h-[420px] flex items-center">
                {/* Background Image */}
                <div className="absolute inset-0 z-0">
                    <img 
                        src="https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1920&q=80" 
                        alt="Travel"
                        className="w-full h-full object-cover"
                    />
                    <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/70"></div>
                </div>
                
                {/* Content */}
                <div className="container mx-auto px-4 relative z-10 py-12">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-center mb-8"
                    >
                        <h1 className="text-4xl md:text-5xl font-bold text-white mb-3">
                            Book Flights, Trains & Buses
                        </h1>
                        <p className="text-white/80 text-lg">
                            Lowest prices guaranteed. Compare and book instantly.
                        </p>
                    </motion.div>

                    {/* Search Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="bg-white rounded-2xl shadow-2xl p-6 max-w-5xl mx-auto"
                    >
                        {/* Trip Type Toggle */}
                        <div className="flex items-center gap-6 mb-6 border-b border-gray-100 pb-4">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="radio" name="tripType" defaultChecked className="w-4 h-4 text-blue-600" />
                                <span className="text-sm font-medium text-gray-700">One Way</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="radio" name="tripType" className="w-4 h-4 text-blue-600" />
                                <span className="text-sm font-medium text-gray-700">Round Trip</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="radio" name="tripType" className="w-4 h-4 text-blue-600" />
                                <span className="text-sm font-medium text-gray-700">Multi City</span>
                            </label>
                        </div>

                        {/* Transport Type Tabs */}
                        <div className="flex gap-3 mb-6">
                            {[
                                { id: 'all', label: 'All', icon: Search },
                                { id: 'flight', label: 'Flights', icon: Plane },
                                { id: 'train', label: 'Trains', icon: Train },
                                { id: 'bus', label: 'Buses', icon: Bus }
                            ].map(tab => (
                                <button
                                    key={tab.id}
                                    type="button"
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-all ${
                                        activeTab === tab.id
                                            ? 'bg-blue-600 text-white shadow-lg shadow-blue-200'
                                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                                >
                                    <tab.icon className="w-4 h-4" />
                                    {tab.label}
                                </button>
                            ))}
                        </div>

                        <form onSubmit={handleSearch} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                                {/* From */}
                                <div className="group relative">
                                    <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">
                                        From
                                    </label>
                                    <input
                                        type="text"
                                        value={searchParams.origin}
                                        onChange={(e) => setSearchParams({ ...searchParams, origin: e.target.value })}
                                        placeholder="City or Airport"
                                        className="w-full text-xl font-bold text-gray-900 border-b-2 border-gray-200 focus:border-blue-500 py-2 outline-none transition-colors bg-transparent"
                                        required
                                    />
                                    <p className="text-sm text-gray-500 mt-1">India</p>
                                    
                                    {/* Swap Button */}
                                    <button 
                                        type="button"
                                        className="absolute right-[-20px] top-1/2 transform -translate-y-1/2 z-10 bg-white border-2 border-blue-500 rounded-full p-1.5 text-blue-500 hover:bg-blue-50 transition-colors hidden lg:block"
                                        onClick={() => setSearchParams({
                                            ...searchParams,
                                            origin: searchParams.destination,
                                            destination: searchParams.origin
                                        })}
                                    >
                                        <ArrowLeftRight className="w-4 h-4" />
                                    </button>
                                </div>

                                {/* To */}
                                <div className="group">
                                    <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">
                                        To
                                    </label>
                                    <input
                                        type="text"
                                        value={searchParams.destination}
                                        onChange={(e) => setSearchParams({ ...searchParams, destination: e.target.value })}
                                        placeholder="City or Airport"
                                        className="w-full text-xl font-bold text-gray-900 border-b-2 border-gray-200 focus:border-blue-500 py-2 outline-none transition-colors bg-transparent"
                                        required
                                    />
                                    <p className="text-sm text-gray-500 mt-1">India</p>
                                </div>

                                {/* Travel Date */}
                                <div className="group">
                                    <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">
                                        Departure
                                    </label>
                                    <input
                                        type="date"
                                        value={searchParams.travel_date}
                                        onChange={(e) => setSearchParams({ ...searchParams, travel_date: e.target.value })}
                                        className="w-full text-lg font-bold text-gray-900 border-b-2 border-gray-200 focus:border-blue-500 py-2 outline-none transition-colors bg-transparent cursor-pointer"
                                        required
                                    />
                                </div>

                                {/* Passengers */}
                                <div className="group">
                                    <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">
                                        Travellers & Class
                                    </label>
                                    <div className="flex items-baseline gap-1 border-b-2 border-gray-200 py-2">
                                        <span className="text-2xl font-bold text-gray-900">{searchParams.passengers}</span>
                                        <span className="text-sm text-gray-500">Traveller{searchParams.passengers > 1 ? 's' : ''}</span>
                                        <span className="text-sm text-gray-500 ml-2">Economy</span>
                                    </div>
                                </div>
                            </div>

                            {/* Trending Routes */}
                            <div className="flex items-center gap-3 pt-2 flex-wrap">
                                <span className="text-sm text-gray-500 flex items-center gap-1">
                                    <TrendingUp className="w-4 h-4" /> Popular:
                                </span>
                                {[
                                    { from: 'Delhi', to: 'Mumbai' },
                                    { from: 'Bangalore', to: 'Delhi' },
                                    { from: 'Mumbai', to: 'Goa' },
                                    { from: 'Chennai', to: 'Hyderabad' }
                                ].map((route, idx) => (
                                    <button
                                        key={idx}
                                        type="button"
                                        onClick={() => setSearchParams({ 
                                            ...searchParams, 
                                            origin: route.from,
                                            destination: route.to 
                                        })}
                                        className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-blue-50 hover:text-blue-600 transition-colors flex items-center gap-1"
                                    >
                                        {route.from} <ArrowRight className="w-3 h-3" /> {route.to}
                                    </button>
                                ))}
                            </div>

                            {/* Search Button */}
                            <div className="flex justify-center pt-4">
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white px-16 py-4 rounded-full font-bold text-lg shadow-lg shadow-orange-200 hover:shadow-xl transition-all disabled:opacity-50 uppercase tracking-wide"
                                >
                                    {loading ? (
                                        <span className="flex items-center gap-2">
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                            Searching...
                                        </span>
                                    ) : (
                                        'SEARCH'
                                    )}
                                </button>
                            </div>
                        </form>
                    </motion.div>
                </div>
            </section>

            {/* Offers Section */}
            <section className="container mx-auto px-4 py-12">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-6">
                        <h2 className="text-2xl font-bold text-gray-900">Offers</h2>
                        <div className="flex items-center gap-2 overflow-x-auto">
                            {['Flights', 'Trains', 'Buses', 'All Offers'].map((tab, idx) => (
                                <button 
                                    key={idx}
                                    className={`px-4 py-2 text-sm font-medium rounded-full transition-colors ${
                                        idx === 0 
                                            ? 'text-blue-600 border-b-2 border-blue-600' 
                                            : 'text-gray-600 hover:text-blue-600'
                                    }`}
                                >
                                    {tab}
                                </button>
                            ))}
                        </div>
                    </div>
                    <button className="text-blue-600 font-medium flex items-center gap-1 hover:gap-2 transition-all">
                        VIEW ALL <ChevronRight className="w-4 h-4" />
                    </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[
                        {
                            title: 'Up to ₹2000 OFF',
                            subtitle: 'on Domestic Flights',
                            code: 'FLYDEAL',
                            color: 'from-blue-600 to-indigo-600',
                            image: 'https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=300'
                        },
                        {
                            title: 'FLAT 10% OFF',
                            subtitle: 'on Train Tickets',
                            code: 'TRAINEXPRESS',
                            color: 'from-orange-500 to-red-500',
                            image: 'https://images.unsplash.com/photo-1474487548417-781cb71495f3?w=300'
                        },
                        {
                            title: 'Save ₹300',
                            subtitle: 'on Bus Bookings',
                            code: 'BUSRIDE',
                            color: 'from-emerald-500 to-teal-600',
                            image: 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=300'
                        }
                    ].map((offer, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow cursor-pointer group"
                        >
                            <div className="h-32 overflow-hidden">
                                <img 
                                    src={offer.image} 
                                    alt={offer.title}
                                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                                />
                            </div>
                            <div className="p-4">
                                <h3 className={`text-lg font-bold bg-gradient-to-r ${offer.color} bg-clip-text text-transparent`}>
                                    {offer.title}
                                </h3>
                                <p className="text-gray-600 text-sm">{offer.subtitle}</p>
                                <div className="flex items-center justify-between mt-3">
                                    <span className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
                                        Code: {offer.code}
                                    </span>
                                    <span className="text-xs text-gray-400">T&C's Apply</span>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </section>

            {/* Error Message */}
            {error && (
                <div className="container mx-auto px-4 mt-6">
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl flex items-center gap-2">
                        <AlertCircle className="w-5 h-5" />
                        {error}
                    </div>
                </div>
            )}

            {/* Loading State */}
            {loading && (
                <div className="container mx-auto px-4 py-16 text-center">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-100 rounded-full mb-4">
                        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
                    </div>
                    <p className="text-xl font-semibold text-gray-800">Finding Best Deals...</p>
                    <p className="text-gray-500 mt-2">Our AI is comparing prices across platforms</p>
                </div>
            )}

            {/* Results */}
            {results && !loading && (
                <section className="container mx-auto px-4 py-8">
                    {/* Summary */}
                    {results.search_summary && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-4 mb-6 text-center"
                        >
                            <p className="text-gray-700 font-medium">{results.search_summary}</p>
                        </motion.div>
                    )}

                    {/* Flights */}
                    {(activeTab === 'all' || activeTab === 'flight') && results.flights?.length > 0 && (
                        <div className="mb-10">
                            <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                                <Plane className="w-6 h-6 text-indigo-600" /> 
                                Flights ({results.flights.length} options)
                            </h2>
                            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {results.flights.map((flight, idx) => (
                                    <FlightCard key={idx} flight={flight} index={idx} />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Trains */}
                    {(activeTab === 'all' || activeTab === 'train') && results.trains?.length > 0 && (
                        <div className="mb-10">
                            <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                                <Train className="w-6 h-6 text-orange-600" /> 
                                Trains ({results.trains.length} options)
                            </h2>
                            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {results.trains.map((train, idx) => (
                                    <TrainCard key={idx} train={train} index={idx} />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Buses */}
                    {(activeTab === 'all' || activeTab === 'bus') && results.buses?.length > 0 && (
                        <div className="mb-10">
                            <h2 className="text-2xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                                <Bus className="w-6 h-6 text-red-600" /> 
                                Buses ({results.buses.length} options)
                            </h2>
                            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {results.buses.map((bus, idx) => (
                                    <BusCard key={idx} bus={bus} index={idx} />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* No Results */}
                    {!results.flights?.length && !results.trains?.length && !results.buses?.length && (
                        <div className="text-center py-16">
                            <p className="text-xl text-gray-600">No travel options found. Try different search criteria.</p>
                        </div>
                    )}
                </section>
            )}

            {/* Info Section */}
            <section className="container mx-auto px-4 py-12">
                <div className="bg-gradient-to-br from-[#041E42] to-[#0D47A1] rounded-3xl p-8 text-white">
                    <h3 className="text-2xl font-bold mb-8 text-center">
                        Why Book With TravelAI?
                    </h3>
                    <div className="grid md:grid-cols-4 gap-6">
                        <div className="text-center">
                            <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                                <Search className="w-7 h-7 text-white" />
                            </div>
                            <h4 className="font-bold text-lg mb-2">Smart Search</h4>
                            <p className="text-white/70 text-sm">AI compares prices across 100+ providers</p>
                        </div>
                        <div className="text-center">
                            <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                                <IndianRupee className="w-7 h-7 text-white" />
                            </div>
                            <h4 className="font-bold text-lg mb-2">Best Prices</h4>
                            <p className="text-white/70 text-sm">Guaranteed lowest fares or we refund the difference</p>
                        </div>
                        <div className="text-center">
                            <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                                <Clock className="w-7 h-7 text-white" />
                            </div>
                            <h4 className="font-bold text-lg mb-2">Instant Booking</h4>
                            <p className="text-white/70 text-sm">Confirm your tickets in seconds</p>
                        </div>
                        <div className="text-center">
                            <div className="w-14 h-14 bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                                <Award className="w-7 h-7 text-white" />
                            </div>
                            <h4 className="font-bold text-lg mb-2">Trusted Service</h4>
                            <p className="text-white/70 text-sm">10M+ happy travellers and counting</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Trust Badges */}
            <section className="container mx-auto px-4 pb-12">
                <div className="flex flex-wrap items-center justify-center gap-8 text-gray-500">
                    <div className="flex items-center gap-2">
                        <Shield className="w-5 h-5 text-green-500" />
                        <span className="text-sm">Secure Payments</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-blue-500" />
                        <span className="text-sm">Verified Operators</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Clock className="w-5 h-5 text-orange-500" />
                        <span className="text-sm">24/7 Support</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Tag className="w-5 h-5 text-purple-500" />
                        <span className="text-sm">Best Price Guarantee</span>
                    </div>
                </div>
            </section>
        </div>
    );
};

export default TravelBooking;
