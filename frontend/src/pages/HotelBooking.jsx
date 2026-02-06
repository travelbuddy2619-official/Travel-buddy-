import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    Search, Calendar, Users, IndianRupee, Star, ExternalLink, Loader2, 
    MapPin, Wifi, Coffee, Dumbbell, Car, Waves, CheckCircle, AlertCircle, 
    Home, ThumbsUp, ThumbsDown, Award, Building2, Bed, UtensilsCrossed,
    Shield, Clock, Phone, Plane, Train, Bus, Hotel, Gift, CreditCard, 
    Palmtree, Ship, ChevronRight, TrendingUp, Percent, Tag
} from 'lucide-react';
import { Link } from 'react-router-dom';

const HotelBooking = () => {
    const [searchParams, setSearchParams] = useState({
        destination: '',
        check_in: '',
        check_out: '',
        guests: 2,
        rooms: 1,
        budget_per_night: '',
        hotel_type: 'all'
    });
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [selectedHotel, setSelectedHotel] = useState(null);

    const handleSearch = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResults(null);
        setSelectedHotel(null);

        try {
            const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_URL}/api/search/hotels`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...searchParams,
                    budget_per_night: searchParams.budget_per_night ? parseInt(searchParams.budget_per_night) : null
                })
            });

            const data = await response.json();
            
            if (data.success) {
                setResults(data);
            } else {
                setError('Failed to fetch hotels. Please try again.');
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

    const getAmenityIcon = (amenity) => {
        const iconMap = {
            'WiFi': <Wifi className="w-4 h-4" />,
            'wifi': <Wifi className="w-4 h-4" />,
            'Breakfast': <Coffee className="w-4 h-4" />,
            'breakfast': <Coffee className="w-4 h-4" />,
            'Pool': <Waves className="w-4 h-4" />,
            'pool': <Waves className="w-4 h-4" />,
            'Gym': <Dumbbell className="w-4 h-4" />,
            'gym': <Dumbbell className="w-4 h-4" />,
            'Parking': <Car className="w-4 h-4" />,
            'parking': <Car className="w-4 h-4" />,
            'Restaurant': <UtensilsCrossed className="w-4 h-4" />,
            'restaurant': <UtensilsCrossed className="w-4 h-4" />
        };
        return iconMap[amenity] || <CheckCircle className="w-4 h-4" />;
    };

    const StarRating = ({ rating }) => {
        return (
            <div className="flex items-center gap-1">
                {[...Array(5)].map((_, i) => (
                    <Star
                        key={i}
                        className={`w-4 h-4 ${
                            i < rating ? 'text-amber-400 fill-amber-400' : 'text-gray-300'
                        }`}
                    />
                ))}
            </div>
        );
    };

    const ScoreBar = ({ label, score, color = 'bg-green-500' }) => (
        <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 w-24">{label}</span>
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                    className={`h-full ${color} rounded-full transition-all`}
                    style={{ width: `${(score / 5) * 100}%` }}
                />
            </div>
            <span className="text-sm font-medium text-gray-800 w-8">{score?.toFixed(1)}</span>
        </div>
    );

    const HotelCard = ({ hotel, index }) => (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-xl transition-all"
        >
            {/* Badge */}
            {hotel.badge && (
                <div className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm px-4 py-1.5 font-medium">
                    {hotel.badge}
                </div>
            )}

            {/* Hotel Image */}
            <div className="relative h-48 overflow-hidden bg-gray-200">
                <img 
                    src={hotel.main_image || hotel.images?.[0] || 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600'}
                    alt={hotel.name}
                    className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                    onError={(e) => {
                        e.target.src = 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600';
                    }}
                />
                {/* Real-time data badge */}
                {hotel.is_real_data && (
                    <div className="absolute top-3 left-3 bg-red-500 text-white text-xs px-2 py-1 rounded-full font-medium flex items-center gap-1">
                        <span className="w-2 h-2 bg-white rounded-full animate-pulse"></span>
                        LIVE
                    </div>
                )}
                {/* Star rating overlay */}
                <div className="absolute bottom-3 left-3 bg-black/60 text-white px-2 py-1 rounded-lg flex items-center gap-1">
                    <StarRating rating={hotel.star_rating || 0} />
                </div>
                {/* Deal badge */}
                {hotel.deal && hotel.deal !== 'Best available rate' && (
                    <div className="absolute top-3 right-3 bg-amber-500 text-white text-xs px-2 py-1 rounded-full font-medium">
                        {hotel.deal.slice(0, 30)}{hotel.deal.length > 30 ? '...' : ''}
                    </div>
                )}
            </div>

            {/* Image gallery thumbnails */}
            {hotel.images && hotel.images.length > 1 && (
                <div className="flex gap-1 p-2 bg-gray-50 overflow-x-auto">
                    {hotel.images.slice(1, 5).map((img, idx) => (
                        <img 
                            key={idx}
                            src={img}
                            alt={`${hotel.name} ${idx + 2}`}
                            className="w-16 h-12 object-cover rounded cursor-pointer hover:opacity-80 transition-opacity"
                            onError={(e) => e.target.style.display = 'none'}
                        />
                    ))}
                    {hotel.images.length > 5 && (
                        <div className="w-16 h-12 bg-gray-200 rounded flex items-center justify-center text-xs text-gray-600 font-medium">
                            +{hotel.images.length - 5}
                        </div>
                    )}
                </div>
            )}

            <div className="p-5">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-bold text-gray-800 text-lg">{hotel.name}</h3>
                        </div>
                        <p className="text-sm text-gray-500 flex items-center gap-1">
                            <MapPin className="w-4 h-4" /> {hotel.location}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">{hotel.distance_to_center}</p>
                    </div>
                    <div className="text-right">
                        {hotel.original_price && hotel.original_price > hotel.price_per_night && (
                            <p className="text-sm text-gray-400 line-through">
                                {formatPrice(hotel.original_price)}
                            </p>
                        )}
                        <p className="text-2xl font-bold text-indigo-600">{formatPrice(hotel.price_per_night)}</p>
                        <p className="text-xs text-gray-500">per night</p>
                        {hotel.nights > 1 && hotel.price_total && (
                            <p className="text-sm text-gray-600 mt-1">
                                Total: {formatPrice(hotel.price_total)}
                                <span className="text-xs text-gray-400"> ({hotel.nights} nights)</span>
                            </p>
                        )}
                        <p className="text-xs text-gray-400 mt-1">+ taxes & fees</p>
                    </div>
                </div>

                {/* Room Type */}
                <div className="flex items-center gap-2 mb-3">
                    <Bed className="w-4 h-4 text-gray-500" />
                    <span className="text-sm text-gray-700">{hotel.room_type}</span>
                </div>

                {/* Ratings */}
                <div className="flex items-center gap-4 mb-4">
                    {(hotel.review_score || hotel.google_rating) && (
                        <div className="flex items-center gap-1 bg-green-100 text-green-700 px-2 py-1 rounded-lg">
                            <Star className="w-4 h-4 fill-current" />
                            <span className="font-semibold">{hotel.review_score || hotel.google_rating}/10</span>
                            <span className="text-xs text-green-600">
                                {hotel.review_word || 'Good'} ({hotel.total_reviews?.toLocaleString()} reviews)
                            </span>
                        </div>
                    )}
                    {hotel.composite_score && (
                        <div className="flex items-center gap-1 bg-purple-100 text-purple-700 px-2 py-1 rounded-lg">
                            <Award className="w-4 h-4" />
                            <span className="font-semibold">{hotel.composite_score}</span>
                            <span className="text-xs">AI Score</span>
                        </div>
                    )}
                    {hotel.is_preferred && (
                        <div className="flex items-center gap-1 bg-blue-100 text-blue-700 px-2 py-1 rounded-lg">
                            <Shield className="w-4 h-4" />
                            <span className="text-xs font-medium">Preferred</span>
                        </div>
                    )}
                </div>

                {/* Amenities */}
                <div className="flex flex-wrap gap-2 mb-4">
                    {hotel.amenities?.slice(0, 6).map((amenity, idx) => (
                        <span
                            key={idx}
                            className="flex items-center gap-1 text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full"
                        >
                            {getAmenityIcon(amenity)} {amenity}
                        </span>
                    ))}
                </div>

                {/* Review Analysis */}
                {hotel.review_analysis && (
                    <div className="bg-gray-50 rounded-xl p-4 mb-4">
                        <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                            <Shield className="w-4 h-4 text-indigo-600" /> AI Review Analysis
                        </h4>
                        
                        <p className="text-sm text-gray-600 mb-3 italic">
                            "{hotel.review_analysis.summary}"
                        </p>

                        {/* Score Bars */}
                        <div className="space-y-2 mb-3">
                            <ScoreBar 
                                label="Cleanliness" 
                                score={hotel.review_analysis.cleanliness_score} 
                                color="bg-blue-500"
                            />
                            <ScoreBar 
                                label="Service" 
                                score={hotel.review_analysis.service_score} 
                                color="bg-green-500"
                            />
                            <ScoreBar 
                                label="Value" 
                                score={hotel.review_analysis.value_score} 
                                color="bg-amber-500"
                            />
                        </div>

                        {/* Pros & Cons */}
                        <div className="grid grid-cols-2 gap-3 mt-3">
                            <div>
                                <p className="text-xs font-semibold text-green-700 mb-1 flex items-center gap-1">
                                    <ThumbsUp className="w-3 h-3" /> Pros
                                </p>
                                {hotel.review_analysis.pros?.slice(0, 2).map((pro, idx) => (
                                    <p key={idx} className="text-xs text-gray-600">• {pro}</p>
                                ))}
                            </div>
                            <div>
                                <p className="text-xs font-semibold text-red-700 mb-1 flex items-center gap-1">
                                    <ThumbsDown className="w-3 h-3" /> Cons
                                </p>
                                {hotel.review_analysis.cons?.slice(0, 2).map((con, idx) => (
                                    <p key={idx} className="text-xs text-gray-600">• {con}</p>
                                ))}
                            </div>
                        </div>

                        {/* Best For */}
                        {hotel.review_analysis.best_for?.length > 0 && (
                            <div className="mt-3">
                                <p className="text-xs text-gray-500">Best for: 
                                    <span className="font-medium text-gray-700">
                                        {' '}{hotel.review_analysis.best_for.join(', ')}
                                    </span>
                                </p>
                            </div>
                        )}

                        {/* Standout Feature */}
                        {hotel.review_analysis.standout_feature && (
                            <div className="mt-2 bg-indigo-50 text-indigo-700 text-xs px-3 py-2 rounded-lg">
                                ✨ {hotel.review_analysis.standout_feature}
                            </div>
                        )}
                    </div>
                )}

                {/* Why Recommended */}
                {hotel.why_recommended && (
                    <p className="text-sm text-green-600 flex items-center gap-1 mb-4">
                        <CheckCircle className="w-4 h-4" /> {hotel.why_recommended}
                    </p>
                )}

                {/* Good Value Badge */}
                {hotel.is_good_value && (
                    <div className="bg-green-50 text-green-700 text-sm px-3 py-2 rounded-lg mb-4 flex items-center gap-2">
                        <Award className="w-4 h-4" />
                        <span className="font-medium">Great Value for Money</span>
                    </div>
                )}

                {/* Book Button */}
                <a
                    href={hotel.booking_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-colors"
                >
                    Book Now <ExternalLink className="w-4 h-4" />
                </a>
            </div>
        </motion.div>
    );

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-purple-50">
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
                            { icon: Plane, label: 'Flights', path: '/travel', active: false },
                            { icon: Hotel, label: 'Hotels', path: '/hotels', active: true },
                            { icon: Palmtree, label: 'Holiday Packages', path: '#', active: false },
                            { icon: Train, label: 'Trains', path: '/travel', active: false },
                            { icon: Bus, label: 'Buses', path: '/travel', active: false },
                            { icon: Car, label: 'Cabs', path: '#', active: false },
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
            <section className="relative min-h-[400px] flex items-center">
                {/* Background Image */}
                <div className="absolute inset-0 z-0">
                    <img 
                        src="https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=1920&q=80" 
                        alt="Luxury Hotel"
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
                            Find the Best Hotels
                        </h1>
                        <p className="text-white/80 text-lg">
                            OYO, Treebo, FabHotel & more at lowest prices
                        </p>
                    </motion.div>

                    {/* Search Card */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="bg-white rounded-2xl shadow-2xl p-6 max-w-5xl mx-auto"
                    >
                        {/* Room Options Toggle */}
                        <div className="flex items-center gap-4 mb-6 border-b border-gray-100 pb-4">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="radio" name="roomType" defaultChecked className="w-4 h-4 text-blue-600" />
                                <span className="text-sm font-medium text-gray-700">Upto 4 Rooms</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="radio" name="roomType" className="w-4 h-4 text-blue-600" />
                                <span className="text-sm font-medium text-gray-700">Group Deals</span>
                                <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">new</span>
                            </label>
                        </div>

                        <form onSubmit={handleSearch} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                                {/* Destination */}
                                <div className="lg:col-span-2 group">
                                    <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">
                                        City, Property Name Or Location
                                    </label>
                                    <div className="relative">
                                        <input
                                            type="text"
                                            value={searchParams.destination}
                                            onChange={(e) => setSearchParams({ ...searchParams, destination: e.target.value })}
                                            placeholder="Enter destination"
                                            className="w-full text-xl font-bold text-gray-900 border-b-2 border-gray-200 focus:border-blue-500 py-2 outline-none transition-colors bg-transparent"
                                            required
                                        />
                                        <p className="text-sm text-gray-500 mt-1">India</p>
                                    </div>
                                </div>

                                {/* Check-in */}
                                <div className="group">
                                    <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">
                                        Check-In
                                    </label>
                                    <input
                                        type="date"
                                        value={searchParams.check_in}
                                        onChange={(e) => setSearchParams({ ...searchParams, check_in: e.target.value })}
                                        className="w-full text-lg font-bold text-gray-900 border-b-2 border-gray-200 focus:border-blue-500 py-2 outline-none transition-colors bg-transparent cursor-pointer"
                                        required
                                    />
                                </div>

                                {/* Check-out */}
                                <div className="group">
                                    <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">
                                        Check-Out
                                    </label>
                                    <input
                                        type="date"
                                        value={searchParams.check_out}
                                        onChange={(e) => setSearchParams({ ...searchParams, check_out: e.target.value })}
                                        className="w-full text-lg font-bold text-gray-900 border-b-2 border-gray-200 focus:border-blue-500 py-2 outline-none transition-colors bg-transparent cursor-pointer"
                                        required
                                    />
                                </div>

                                {/* Rooms & Guests */}
                                <div className="group">
                                    <label className="block text-xs font-medium text-gray-500 mb-1 uppercase tracking-wide">
                                        Rooms & Guests
                                    </label>
                                    <div className="flex items-baseline gap-1 border-b-2 border-gray-200 py-2">
                                        <span className="text-2xl font-bold text-gray-900">{searchParams.rooms}</span>
                                        <span className="text-sm text-gray-500">Room{searchParams.rooms > 1 ? 's' : ''}</span>
                                        <span className="text-2xl font-bold text-gray-900 ml-2">{searchParams.guests}</span>
                                        <span className="text-sm text-gray-500">Guest{searchParams.guests > 1 ? 's' : ''}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Price Range (Optional) */}
                            <div className="flex items-center gap-4 pt-2">
                                <label className="block text-xs font-medium text-gray-500 uppercase tracking-wide">
                                    Price Per Night
                                </label>
                                <div className="flex items-center gap-2">
                                    {['₹0-₹1500', '₹1500-₹2500', '₹2500-₹5000', '₹5000+'].map((range, idx) => (
                                        <button
                                            key={idx}
                                            type="button"
                                            className="px-3 py-1 text-sm border border-gray-300 rounded-full hover:border-blue-500 hover:text-blue-600 transition-colors"
                                        >
                                            {range}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Trending Searches */}
                            <div className="flex items-center gap-3 pt-2 flex-wrap">
                                <span className="text-sm text-gray-500 flex items-center gap-1">
                                    <TrendingUp className="w-4 h-4" /> Trending:
                                </span>
                                {['Goa, India', 'Mumbai, India', 'Delhi, India', 'Jaipur, India', 'Bangalore, India'].map((place, idx) => (
                                    <button
                                        key={idx}
                                        type="button"
                                        onClick={() => setSearchParams({ ...searchParams, destination: place.split(',')[0] })}
                                        className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-blue-50 hover:text-blue-600 transition-colors"
                                    >
                                        {place}
                                    </button>
                                ))}
                            </div>

                            {/* Search Button */}
                            <div className="flex justify-center pt-4">
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-16 py-4 rounded-full font-bold text-lg shadow-lg shadow-blue-200 hover:shadow-xl transition-all disabled:opacity-50 uppercase tracking-wide"
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
                            {['Hotels', 'All Offers', 'Flights', 'Holidays', 'Trains'].map((tab, idx) => (
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
                            title: 'Flat 25% OFF',
                            subtitle: 'on Domestic Hotels',
                            code: 'STAYDEAL',
                            color: 'from-purple-600 to-indigo-600',
                            image: 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=300'
                        },
                        {
                            title: 'Grab FLAT 15% OFF*',
                            subtitle: 'on International Hotels',
                            code: 'INTLSTAY',
                            color: 'from-orange-500 to-red-500',
                            image: 'https://images.unsplash.com/photo-1582719508461-905c673771fd?w=300'
                        },
                        {
                            title: 'Up to 20% OFF',
                            subtitle: 'For First-Time Users',
                            code: 'WELCOME20',
                            color: 'from-emerald-500 to-teal-600',
                            image: 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=300'
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
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-4">
                        <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
                    </div>
                    <p className="text-xl font-semibold text-gray-800">Finding Perfect Hotels...</p>
                    <p className="text-gray-500 mt-2">Our AI is analyzing reviews and comparing prices</p>
                    <div className="mt-6 flex flex-wrap justify-center gap-2 text-xs">
                        <span className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full animate-pulse">📊 Analyzing Reviews</span>
                        <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full animate-pulse">⭐ Checking Ratings</span>
                        <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full animate-pulse">💰 Comparing Prices</span>
                    </div>
                </div>
            )}

            {/* Results */}
            {results && !loading && (
                <section className="container mx-auto px-4 py-8">
                    {/* Summary */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="mb-6"
                    >
                        <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 mb-4">
                            <div className="flex flex-wrap items-center justify-between gap-4">
                                <div>
                                    <h2 className="text-xl font-bold text-gray-800">
                                        Hotels in {results.destination}
                                    </h2>
                                    <p className="text-gray-500">
                                        {results.nights} night{results.nights > 1 ? 's' : ''} • {results.guests} guest{results.guests > 1 ? 's' : ''} • {results.rooms} room{results.rooms > 1 ? 's' : ''}
                                    </p>
                                </div>
                                {results.search_summary && (
                                    <p className="text-sm text-gray-600 bg-gray-50 px-4 py-2 rounded-lg">
                                        {results.search_summary}
                                    </p>
                                )}
                            </div>
                        </div>
                    </motion.div>

                    {/* Hotel Cards */}
                    {results.hotels?.length > 0 ? (
                        <div className="grid lg:grid-cols-3 gap-6">
                            {results.hotels.map((hotel, idx) => (
                                <HotelCard key={idx} hotel={hotel} index={idx} />
                            ))}
                        </div>
                    ) : (
                        <div className="text-center py-16">
                            <p className="text-xl text-gray-600">No hotels found. Try different search criteria.</p>
                        </div>
                    )}
                </section>
            )}

            {/* Info Section */}
            <section className="container mx-auto px-4 py-12">
                <div className="bg-gradient-to-br from-[#041E42] to-[#0D47A1] rounded-3xl p-8 text-white">
                    <h3 className="text-2xl font-bold mb-8 text-center">
                        How Our AI Hotel Agent Works
                    </h3>
                    <div className="grid md:grid-cols-3 gap-8">
                        <div className="text-center">
                            <div className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                                <Search className="w-8 h-8 text-white" />
                            </div>
                            <h4 className="font-bold text-lg mb-2">1. Search Hotels</h4>
                            <p className="text-white/70">Finds all available hotels with real-time pricing from multiple providers</p>
                        </div>
                        <div className="text-center">
                            <div className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                                <Star className="w-8 h-8 text-white" />
                            </div>
                            <h4 className="font-bold text-lg mb-2">2. Analyze Reviews</h4>
                            <p className="text-white/70">AI reads thousands of reviews to identify pros, cons & hidden gems</p>
                        </div>
                        <div className="text-center">
                            <div className="w-16 h-16 bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                                <Award className="w-8 h-8 text-white" />
                            </div>
                            <h4 className="font-bold text-lg mb-2">3. Smart Ranking</h4>
                            <p className="text-white/70">Scores hotels based on value, ratings & your preferences</p>
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
                        <span className="text-sm">Verified Properties</span>
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

export default HotelBooking;
