import { useState } from 'react';
import { MapPin, Star, Sun, Thermometer, Utensils, Clock, Camera, Navigation, Lightbulb, Briefcase, Phone, Globe, IndianRupee, AlertTriangle, Info, Ticket, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Image Lightbox Modal Component
const ImageLightbox = ({ images, currentIndex, onClose, onNext, onPrev, placeName }) => {
    if (!images || images.length === 0) return null;
    
    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
                onClick={onClose}
            >
                {/* Close Button */}
                <button 
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors z-50"
                >
                    <X className="w-6 h-6" />
                </button>
                
                {/* Image Counter */}
                <div className="absolute top-4 left-4 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full text-white text-sm">
                    {currentIndex + 1} / {images.length}
                </div>
                
                {/* Place Name */}
                <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 bg-white/10 backdrop-blur-sm px-6 py-3 rounded-xl text-white text-center">
                    <p className="font-semibold">{placeName}</p>
                </div>
                
                {/* Navigation Arrows */}
                {images.length > 1 && (
                    <>
                        <button 
                            onClick={(e) => { e.stopPropagation(); onPrev(); }}
                            className="absolute left-4 p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
                        >
                            <ChevronLeft className="w-8 h-8" />
                        </button>
                        <button 
                            onClick={(e) => { e.stopPropagation(); onNext(); }}
                            className="absolute right-4 p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
                        >
                            <ChevronRight className="w-8 h-8" />
                        </button>
                    </>
                )}
                
                {/* Main Image */}
                <motion.img
                    key={currentIndex}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    src={images[currentIndex]}
                    alt={`${placeName} - Photo ${currentIndex + 1}`}
                    className="max-h-[85vh] max-w-[90vw] object-contain rounded-lg shadow-2xl"
                    onClick={(e) => e.stopPropagation()}
                />
                
                {/* Thumbnail Strip */}
                {images.length > 1 && (
                    <div className="absolute bottom-24 left-1/2 transform -translate-x-1/2 flex gap-2 px-4 py-2 bg-black/50 backdrop-blur-sm rounded-xl overflow-x-auto max-w-[80vw]">
                        {images.map((img, idx) => (
                            <button
                                key={idx}
                                onClick={(e) => { e.stopPropagation(); }}
                                className={`flex-shrink-0 w-16 h-12 rounded-lg overflow-hidden border-2 transition-all ${
                                    idx === currentIndex ? 'border-white scale-110' : 'border-transparent opacity-60 hover:opacity-100'
                                }`}
                            >
                                <img 
                                    src={img} 
                                    alt={`Thumbnail ${idx + 1}`}
                                    className="w-full h-full object-cover"
                                />
                            </button>
                        ))}
                    </div>
                )}
            </motion.div>
        </AnimatePresence>
    );
};

// Budget is now in INR directly
const formatIndianCurrency = (amount) => {
    if (!amount) return '₹0';
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(amount);
};

const formatDateRange = (start, end) => {
    const formatter = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' });
    return `${formatter.format(new Date(start))} - ${formatter.format(new Date(end))}`;
};

const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
};

// Convert 24-hour time to 12-hour AM/PM format
const formatTime12hr = (time) => {
    if (!time) return '';
    
    // If already in AM/PM format, return as is
    if (time.toLowerCase().includes('am') || time.toLowerCase().includes('pm')) {
        return time;
    }
    
    // Handle formats like "09:00", "14:30", "9:00"
    const match = time.match(/^(\d{1,2}):(\d{2})$/);
    if (match) {
        let hours = parseInt(match[1], 10);
        const minutes = match[2];
        const period = hours >= 12 ? 'PM' : 'AM';
        
        if (hours === 0) {
            hours = 12;
        } else if (hours > 12) {
            hours = hours - 12;
        }
        
        return `${hours}:${minutes} ${period}`;
    }
    
    // Return original if format not recognized
    return time;
};

const WeatherChip = ({ day }) => (
    <div className="flex items-center gap-3 bg-cyan-50 rounded-xl px-4 py-2">
        <Sun className="w-5 h-5 text-cyan-500" />
        <div>
            <p className="text-xs font-semibold text-gray-500">{new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}</p>
            <p className="text-sm text-gray-700">{day.summary}</p>
            <div className="flex items-center gap-2 text-xs text-gray-500">
                <Thermometer className="w-3 h-3" />
                <span>{Math.round(day.tempMinC || day.temp_min_c)}° / {Math.round(day.tempMaxC || day.temp_max_c)}°C</span>
            </div>
        </div>
    </div>
);

const ReviewHighlights = ({ reviews }) => (
    <div className="space-y-2">
        {reviews?.highlights?.map((quote, idx) => (
            <p key={idx} className="text-sm text-gray-600 italic">"{quote}"</p>
        ))}
        {typeof reviews?.rating === 'number' && (
            <div className="flex items-center gap-2 text-sm text-amber-600">
                <Star className="w-4 h-4 fill-current" />
                <span>{reviews.rating} ({reviews.totalReviews?.toLocaleString() || reviews.total_reviews?.toLocaleString() || 'New'})</span>
            </div>
        )}
    </div>
);

const RestaurantCard = ({ restaurant }) => {
    if (!restaurant) return null;
    
    return (
        <div className="bg-white rounded-xl p-4 border border-emerald-100 hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                    <h4 className="font-bold text-slate-800 text-base">{restaurant.name}</h4>
                    {restaurant.cuisine && (
                        <p className="text-xs text-emerald-600 font-medium mt-0.5">{restaurant.cuisine}</p>
                    )}
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                    {restaurant.priceLevel && (
                        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full flex items-center gap-1">
                            <IndianRupee className="w-3 h-3" />
                            {restaurant.priceLevel}
                        </span>
                    )}
                    {restaurant.rating && (
                        <div className="flex items-center gap-1 bg-amber-100 px-2 py-0.5 rounded-full">
                            <Star className="w-3 h-3 text-amber-500 fill-current" />
                            <span className="text-xs font-semibold text-amber-700">{restaurant.rating}</span>
                            {restaurant.totalReviews && (
                                <span className="text-xs text-amber-600">({restaurant.totalReviews.toLocaleString()})</span>
                            )}
                        </div>
                    )}
                </div>
            </div>
            
            {restaurant.reviewSnippet && (
                <p className="text-xs text-gray-600 mt-2 italic line-clamp-2">"{restaurant.reviewSnippet}"</p>
            )}
            
            <div className="flex flex-wrap items-center gap-3 mt-3 text-xs text-gray-500">
                {restaurant.address && (
                    <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-emerald-500" />
                        <span className="line-clamp-1">{restaurant.address}</span>
                    </span>
                )}
            </div>
            
            <div className="flex items-center gap-3 mt-2">
                {restaurant.phone && (
                    <a href={`tel:${restaurant.phone}`} className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800">
                        <Phone className="w-3 h-3" />
                        <span>{restaurant.phone}</span>
                    </a>
                )}
                {restaurant.website && (
                    <a href={restaurant.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800">
                        <Globe className="w-3 h-3" />
                        <span>Website</span>
                    </a>
                )}
            </div>
        </div>
    );
};

const PlaceCard = ({ place }) => {
    const [lightboxOpen, setLightboxOpen] = useState(false);
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    
    if (!place) return null;
    
    // Check if we have real Google data (has rating AND reviews AND images)
    const hasRealData = place.rating && place.totalReviews && place.images?.length > 0;
    const practicalInfo = place.practicalInfo;
    
    const openLightbox = (index) => {
        setCurrentImageIndex(index);
        setLightboxOpen(true);
    };
    
    const closeLightbox = () => setLightboxOpen(false);
    
    const nextImage = () => {
        setCurrentImageIndex((prev) => (prev + 1) % place.images.length);
    };
    
    const prevImage = () => {
        setCurrentImageIndex((prev) => (prev - 1 + place.images.length) % place.images.length);
    };
    
    return (
        <div className="mt-3 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-4 border border-indigo-100">
            <div className="flex items-start gap-3">
                <div className="bg-indigo-100 p-2 rounded-lg">
                    <MapPin className="w-5 h-5 text-indigo-600" />
                </div>
                <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-bold text-slate-800">{place.name}</h4>
                        {hasRealData && (
                            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                                📍 Google
                            </span>
                        )}
                        {place.rating && (
                            <div className="flex items-center gap-1 bg-amber-100 px-2 py-0.5 rounded-full">
                                <Star className="w-3 h-3 text-amber-500 fill-current" />
                                <span className="text-xs font-semibold text-amber-700">{place.rating}</span>
                                {place.totalReviews && (
                                    <span className="text-xs text-amber-600">({place.totalReviews.toLocaleString()})</span>
                                )}
                            </div>
                        )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{place.description}</p>
                    
                    {/* Practical Information Section */}
                    {(place.openingHours || place.estimatedTime || practicalInfo) && (
                        <div className="mt-3 bg-blue-50 rounded-lg p-3 border border-blue-100">
                            <p className="text-xs text-blue-700 uppercase font-semibold mb-2 flex items-center gap-1">
                                <Info className="w-3 h-3" /> Practical Information
                            </p>
                            <div className="space-y-1.5 text-xs text-gray-700">
                                {place.openingHours && (
                                    <div className="flex items-start gap-2">
                                        <Clock className="w-3 h-3 text-blue-500 mt-0.5 flex-shrink-0" />
                                        <span><strong>Hours:</strong> {place.openingHours}</span>
                                    </div>
                                )}
                                {place.estimatedTime && (
                                    <div className="flex items-start gap-2">
                                        <Clock className="w-3 h-3 text-green-500 mt-0.5 flex-shrink-0" />
                                        <span><strong>Typical Duration:</strong> {place.estimatedTime}</span>
                                    </div>
                                )}
                                {practicalInfo?.ticketInfo && (
                                    <div className="flex items-start gap-2">
                                        <Ticket className="w-3 h-3 text-purple-500 mt-0.5 flex-shrink-0" />
                                        <span><strong>Tickets:</strong> {practicalInfo.ticketInfo}</span>
                                    </div>
                                )}
                                {practicalInfo?.bestTimeToVisit && (
                                    <div className="flex items-start gap-2">
                                        <Sun className="w-3 h-3 text-amber-500 mt-0.5 flex-shrink-0" />
                                        <span><strong>Best Time:</strong> {practicalInfo.bestTimeToVisit}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                    
                    {/* Crowd Predictions Section */}
                    {place.crowdPredictions && (
                        <div className="mt-3 bg-purple-50 rounded-lg p-3 border border-purple-200">
                            <p className="text-xs text-purple-700 uppercase font-semibold mb-2 flex items-center gap-1">
                                👥 Crowd Patterns
                            </p>
                            
                            {/* Peak Hours */}
                            {place.crowdPredictions.peakHours && Object.keys(place.crowdPredictions.peakHours).length > 0 && (
                                <div className="mb-2">
                                    <p className="text-xs font-semibold text-gray-700 mb-1.5">Peak Hours Today:</p>
                                    <div className="grid grid-cols-2 gap-1">
                                        {Object.entries(place.crowdPredictions.peakHours).map(([timeOfDay, hours]) => (
                                            <div key={timeOfDay} className="bg-white rounded p-2 border border-purple-100">
                                                <p className="text-xs font-semibold text-gray-700 capitalize">{timeOfDay}</p>
                                                <p className="text-xs text-gray-600">{hours.start} - {hours.end}</p>
                                                <div className="flex items-center gap-1 mt-1">
                                                    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${
                                                        hours.crowdLevel === 'light' ? 'bg-green-100 text-green-700' :
                                                        hours.crowdLevel === 'moderate' ? 'bg-yellow-100 text-yellow-700' :
                                                        'bg-red-100 text-red-700'
                                                    }`}>
                                                        {hours.crowdLevel.charAt(0).toUpperCase() + hours.crowdLevel.slice(1)} Crowd
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                            
                            {/* Best Times */}
                            {place.crowdPredictions.bestTimes?.length > 0 && (
                                <div className="mb-2">
                                    <p className="text-xs font-semibold text-gray-700 mb-1">✨ Best Times to Visit:</p>
                                    <div className="flex flex-wrap gap-1">
                                        {place.crowdPredictions.bestTimes.map((time, idx) => (
                                            <span key={idx} className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                                                {time}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                            
                            {/* Recommendations */}
                            {place.crowdPredictions.recommendations?.length > 0 && (
                                <div>
                                    <p className="text-xs font-semibold text-gray-700 mb-1">💡 Smart Tips:</p>
                                    <ul className="text-xs text-gray-700 space-y-1">
                                        {place.crowdPredictions.recommendations.slice(0, 2).map((rec, idx) => (
                                            <li key={idx} className="flex items-start gap-1">
                                                <span className="text-purple-500">→</span>
                                                <span>{rec}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}
                    
                    {/* Important Tips */}
                    {practicalInfo?.importantTips?.length > 0 && (
                        <div className="mt-2 bg-amber-50 rounded-lg p-2 border-l-4 border-amber-400">
                            <p className="text-xs text-amber-700 font-semibold mb-1 flex items-center gap-1">
                                <Lightbulb className="w-3 h-3" /> Tips from Visitors
                            </p>
                            <ul className="text-xs text-gray-700 space-y-1">
                                {practicalInfo.importantTips.slice(0, 2).map((tip, idx) => (
                                    <li key={idx} className="flex items-start gap-1">
                                        <span className="text-amber-500">•</span>
                                        <span>{tip}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                    
                    {/* Warnings */}
                    {practicalInfo?.warnings?.length > 0 && (
                        <div className="mt-2 bg-red-50 rounded-lg p-2 border-l-4 border-red-400">
                            <p className="text-xs text-red-700 font-semibold mb-1 flex items-center gap-1">
                                <AlertTriangle className="w-3 h-3" /> Important Notices
                            </p>
                            <ul className="text-xs text-gray-700 space-y-1">
                                {practicalInfo.warnings.slice(0, 2).map((warning, idx) => (
                                    <li key={idx} className="flex items-start gap-1">
                                        <span className="text-red-500">⚠️</span>
                                        <span>{warning}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                    
                    {place.reviewSummary && (
                        <div className="mt-2 bg-white/70 rounded-lg p-2 border-l-4 border-amber-400">
                            <p className="text-xs text-amber-600 uppercase font-semibold mb-1 flex items-center gap-1">
                                <Star className="w-3 h-3" /> Visitor Reviews
                            </p>
                            <p className="text-sm text-gray-700 italic">"{place.reviewSummary}"</p>
                        </div>
                    )}
                    
                    <div className="flex flex-wrap gap-2 mt-2 text-xs text-gray-500">
                        {place.address && (
                            <span className="flex items-center gap-1">
                                <Navigation className="w-3 h-3" /> {place.address}
                            </span>
                        )}
                    </div>
                    
                    {place.images?.length > 0 && (
                        <div className="mt-3">
                            <p className="text-xs text-gray-400 uppercase mb-2 flex items-center gap-1">
                                📷 Real Photos <span className="text-indigo-500 font-normal">(Click to enlarge)</span>
                            </p>
                            <div className="flex gap-2 overflow-x-auto pb-1">
                                {place.images.slice(0, 4).map((img, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => openLightbox(idx)}
                                        className="relative group flex-shrink-0"
                                    >
                                        <img 
                                            src={img} 
                                            alt={place.name} 
                                            className="h-24 w-32 object-cover rounded-lg shadow-sm hover:shadow-xl transition-all duration-300 group-hover:scale-105 cursor-pointer"
                                            onError={(e) => { e.currentTarget.parentElement.style.display = 'none'; }}
                                        />
                                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 rounded-lg transition-all flex items-center justify-center">
                                            <Camera className="w-5 h-5 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                                        </div>
                                        {idx === 3 && place.images.length > 4 && (
                                            <div className="absolute inset-0 bg-black/50 rounded-lg flex items-center justify-center">
                                                <span className="text-white font-semibold">+{place.images.length - 4}</span>
                                            </div>
                                        )}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                    
                    {/* Image Lightbox */}
                    {lightboxOpen && (
                        <ImageLightbox 
                            images={place.images}
                            currentIndex={currentImageIndex}
                            onClose={closeLightbox}
                            onNext={nextImage}
                            onPrev={prevImage}
                            placeName={place.name}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

// Restaurant card for meal schedule items
const MealRestaurantCard = ({ restaurant, mealType }) => {
    const [lightboxOpen, setLightboxOpen] = useState(false);
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    
    if (!restaurant) return null;
    
    const hasRealData = restaurant.rating && restaurant.images?.length > 0;
    
    const openLightbox = (index) => {
        setCurrentImageIndex(index);
        setLightboxOpen(true);
    };
    
    const closeLightbox = () => setLightboxOpen(false);
    
    const nextImage = () => {
        setCurrentImageIndex((prev) => (prev + 1) % restaurant.images.length);
    };
    
    const prevImage = () => {
        setCurrentImageIndex((prev) => (prev - 1 + restaurant.images.length) % restaurant.images.length);
    };
    
    // Meal type emoji
    const mealEmoji = {
        breakfast: '🍳',
        lunch: '🍽️',
        dinner: '🌙',
        snack: '☕',
        brunch: '🥐'
    }[mealType?.toLowerCase()] || '🍴';
    
    return (
        <div className="mt-3 bg-gradient-to-r from-orange-50 to-amber-50 rounded-xl p-4 border border-orange-200">
            <div className="flex items-start gap-3">
                <div className="bg-orange-100 p-2 rounded-lg text-2xl">
                    {mealEmoji}
                </div>
                <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-bold text-slate-800">{restaurant.name}</h4>
                        {hasRealData && (
                            <span className="text-xs bg-orange-200 text-orange-800 px-2 py-0.5 rounded-full">
                                📍 Google Verified
                            </span>
                        )}
                    </div>
                    
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                        {restaurant.cuisine && (
                            <span className="text-xs bg-white text-orange-700 px-2 py-0.5 rounded-full border border-orange-200">
                                {restaurant.cuisine}
                            </span>
                        )}
                        {restaurant.rating && (
                            <div className="flex items-center gap-1 bg-amber-100 px-2 py-0.5 rounded-full">
                                <Star className="w-3 h-3 text-amber-500 fill-current" />
                                <span className="text-xs font-semibold text-amber-700">{restaurant.rating}</span>
                                {restaurant.totalReviews && (
                                    <span className="text-xs text-amber-600">({restaurant.totalReviews.toLocaleString()})</span>
                                )}
                            </div>
                        )}
                        {restaurant.priceLevel && (
                            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                                {restaurant.priceLevel}
                            </span>
                        )}
                    </div>
                    
                    {restaurant.description && (
                        <p className="text-sm text-gray-600 mt-2">{restaurant.description}</p>
                    )}
                    
                    {/* Must Try Dishes */}
                    {restaurant.mustTry?.length > 0 && (
                        <div className="mt-2 bg-white/70 rounded-lg p-2">
                            <p className="text-xs text-orange-600 font-semibold mb-1">🍴 Must Try</p>
                            <div className="flex flex-wrap gap-1">
                                {restaurant.mustTry.map((dish, idx) => (
                                    <span key={idx} className="text-xs bg-orange-100 text-orange-800 px-2 py-0.5 rounded">
                                        {dish}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                    
                    {/* Review Snippet */}
                    {restaurant.reviewSnippet && (
                        <div className="mt-2 bg-white/70 rounded-lg p-2 border-l-4 border-amber-400">
                            <p className="text-xs text-amber-600 font-semibold mb-1 flex items-center gap-1">
                                <Star className="w-3 h-3" /> What diners say
                            </p>
                            <p className="text-sm text-gray-700 italic">"{restaurant.reviewSnippet}"</p>
                        </div>
                    )}
                    
                    {/* Address and Contact */}
                    <div className="flex flex-wrap items-center gap-3 mt-3 text-xs text-gray-500">
                        {restaurant.address && (
                            <span className="flex items-center gap-1">
                                <MapPin className="w-3 h-3 text-orange-500" />
                                <span className="line-clamp-1">{restaurant.address}</span>
                            </span>
                        )}
                        {restaurant.openingHours && (
                            <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3 text-blue-500" />
                                <span>{restaurant.openingHours}</span>
                            </span>
                        )}
                    </div>
                    
                    <div className="flex items-center gap-3 mt-2">
                        {restaurant.phone && (
                            <a href={`tel:${restaurant.phone}`} className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800">
                                <Phone className="w-3 h-3" />
                                <span>{restaurant.phone}</span>
                            </a>
                        )}
                        {restaurant.website && (
                            <a href={restaurant.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800">
                                <Globe className="w-3 h-3" />
                                <span>Website</span>
                            </a>
                        )}
                    </div>
                    
                    {/* Restaurant Photos */}
                    {restaurant.images?.length > 0 && (
                        <div className="mt-3">
                            <p className="text-xs text-gray-400 uppercase mb-2 flex items-center gap-1">
                                📷 Food & Ambiance <span className="text-orange-500 font-normal">(Click to view)</span>
                            </p>
                            <div className="flex gap-2 overflow-x-auto pb-1">
                                {restaurant.images.slice(0, 3).map((img, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => openLightbox(idx)}
                                        className="relative group flex-shrink-0"
                                    >
                                        <img 
                                            src={img} 
                                            alt={restaurant.name} 
                                            className="h-20 w-28 object-cover rounded-lg shadow-sm hover:shadow-xl transition-all duration-300 group-hover:scale-105 cursor-pointer"
                                            onError={(e) => { e.currentTarget.parentElement.style.display = 'none'; }}
                                        />
                                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 rounded-lg transition-all flex items-center justify-center">
                                            <Camera className="w-4 h-4 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                    
                    {/* Image Lightbox */}
                    {lightboxOpen && (
                        <ImageLightbox 
                            images={restaurant.images}
                            currentIndex={currentImageIndex}
                            onClose={closeLightbox}
                            onNext={nextImage}
                            onPrev={prevImage}
                            placeName={restaurant.name}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

const ScheduleItem = ({ item, isFirst, isLast }) => {
    // Check if this is a meal item
    const isMeal = item.isMeal || item.is_meal || 
        ['breakfast', 'lunch', 'dinner', 'brunch', 'snack', 'tea'].some(
            m => item.activity?.toLowerCase().includes(m)
        );
    
    return (
        <div className="relative pl-8 pb-6">
            {/* Timeline line */}
            {!isLast && (
                <div className="absolute left-[11px] top-8 bottom-0 w-0.5 bg-gradient-to-b from-cyan-300 to-cyan-100" />
            )}
            
            {/* Time dot - different color for meals */}
            <div className={`absolute left-0 top-1 w-6 h-6 ${isMeal ? 'bg-orange-500' : 'bg-cyan-500'} rounded-full flex items-center justify-center shadow-md`}>
                {isMeal ? (
                    <Utensils className="w-3 h-3 text-white" />
                ) : (
                    <Clock className="w-3 h-3 text-white" />
                )}
            </div>
            
            <div className={`bg-white rounded-xl border ${isMeal ? 'border-orange-100' : 'border-gray-100'} p-4 shadow-sm hover:shadow-md transition-shadow`}>
                <div className="flex items-center gap-3 mb-2">
                    <span className={`text-lg font-bold ${isMeal ? 'text-orange-600' : 'text-cyan-600'}`}>{formatTime12hr(item.time)}</span>
                    {item.duration && (
                        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                            {item.duration}
                        </span>
                    )}
                    {isMeal && (
                        <span className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full font-medium">
                            {item.mealType || item.meal_type || 'Meal'}
                        </span>
                    )}
                </div>
                <h4 className="text-lg font-semibold text-slate-800">{item.activity}</h4>
                <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                
                {item.tips && (
                    <div className="mt-2 flex items-start gap-2 bg-amber-50 rounded-lg p-2">
                        <Lightbulb className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                        <p className="text-xs text-amber-700">{item.tips}</p>
                    </div>
                )}
                
                {/* Show restaurant card for meals */}
                {item.restaurant && <MealRestaurantCard restaurant={item.restaurant} mealType={item.mealType || item.meal_type} />}
                
                {/* Show place card for attractions */}
                {item.place && <PlaceCard place={item.place} />}
            </div>
        </div>
    );
};

const ItineraryResult = ({ data }) => {
    if (!data) return null;

    const containerVariants = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.1 } } };
    const itemVariants = { hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0, transition: { duration: 0.5 } } };

    // Support both old and new data structure
    const details = data.details;
    const destination = data.destination || details?.destination;
    const startDate = data.startDate || details?.startDate;
    const endDate = data.endDate || details?.endDate;
    const tripRange = startDate && endDate ? formatDateRange(startDate, endDate) : '';
    const budgetPerPerson = details?.budgetPerPerson ?? 0;
    
    // New multi-agent data
    const weather = data.weather;
    const cityHighlights = data.cityHighlights;

    return (
        <div className="bg-slate-50 font-sans">
            <motion.div variants={containerVariants} initial="hidden" animate="visible" className="max-w-5xl mx-auto space-y-12 py-16 px-4">
                {/* Multi-Agent System Badge */}
                <motion.div variants={itemVariants} className="text-center">
                    <span className="inline-flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-xs font-semibold px-4 py-2 rounded-full">
                        <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                        Generated by Multi-Agent AI System
                    </span>
                </motion.div>

                {/* Header Card */}
                <motion.div variants={itemVariants} className="bg-white border border-gray-100 rounded-3xl shadow-sm p-8 relative overflow-hidden">
                    <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-fuchsia-500 via-cyan-400 to-emerald-400" />
                    <h1 className="text-4xl font-black text-slate-800 mb-4">{data.title || `Trip to ${destination}`}</h1>
                    <p className="text-lg text-gray-600 mb-6 max-w-3xl">{data.summary || `Your personalized ${data.days?.length || 0}-day itinerary for ${destination}`}</p>
                    
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm text-gray-600">
                        <div>
                            <p className="text-gray-400 uppercase text-xs">Destination</p>
                            <p className="font-semibold text-lg text-indigo-600">{destination}</p>
                        </div>
                        <div>
                            <p className="text-gray-400 uppercase text-xs">Dates</p>
                            <p className="font-semibold">{tripRange}</p>
                        </div>
                        <div>
                            <p className="text-gray-400 uppercase text-xs">Duration</p>
                            <p className="font-semibold">{data.days?.length || 0} Days</p>
                        </div>
                        {details?.travelers && (
                            <div>
                                <p className="text-gray-400 uppercase text-xs">Travelers</p>
                                <p className="font-semibold">{details.travelers}</p>
                            </div>
                        )}
                        {budgetPerPerson > 0 && (
                            <div>
                                <p className="text-gray-400 uppercase text-xs">Budget / Person</p>
                                <p className="font-semibold">{formatIndianCurrency(budgetPerPerson)}</p>
                            </div>
                        )}
                        {details?.transportPreference && (
                            <div>
                                <p className="text-gray-400 uppercase text-xs">Transport</p>
                                <p className="font-semibold">{details.transportPreference}</p>
                            </div>
                        )}
                    </div>
                </motion.div>

                {/* Weather Section from Weather Agent */}
                {weather && (weather.summary || weather.forecasts?.length > 0 || weather.recommendations?.length > 0) && (
                    <motion.div id="weather" data-section="weather" variants={itemVariants} className="bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-100 rounded-3xl shadow-sm p-6">
                        <div className="flex items-center gap-2 text-blue-600 mb-4">
                            <Sun className="w-6 h-6" />
                            <h3 className="font-bold text-lg">Weather Forecast</h3>
                            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full ml-2">from Weather Agent</span>
                        </div>
                        
                        {weather.summary && (
                            <p className="text-gray-700 mb-4">{weather.summary}</p>
                        )}
                        
                        {weather.forecasts?.length > 0 && (
                            <div className="flex flex-wrap gap-3 mb-4">
                                {weather.forecasts.map((day, idx) => (
                                    <WeatherChip key={idx} day={day} />
                                ))}
                            </div>
                        )}
                        
                        {weather.recommendations?.length > 0 && (
                            <div className="bg-white/70 rounded-xl p-4">
                                <p className="text-sm font-semibold text-blue-700 mb-2">Weather-based Recommendations:</p>
                                <ul className="space-y-1">
                                    {weather.recommendations.map((rec, idx) => (
                                        <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                                            <span className="text-blue-500">•</span> {rec}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </motion.div>
                )}

                {/* City Highlights from City Explorer Agent - REDESIGNED */}
                {cityHighlights && (cityHighlights.famousFood?.length > 0 || cityHighlights.famousRestaurants?.length > 0 || cityHighlights.localTips?.length > 0) && (
                    <motion.div id="city-highlights" data-section="city-highlights" variants={itemVariants} className="space-y-6">
                        {/* Header */}
                        <div className="text-center">
                            <h2 className="text-2xl font-bold text-gray-800 mb-2">
                                🏙️ Discover {destination}
                            </h2>
                            <p className="text-gray-500 text-sm">Local insights powered by City Explorer Agent</p>
                        </div>

                        {/* Festivals & Events - Prominent Banner */}
                        {cityHighlights.festivalsEvents?.length > 0 && (
                            <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl p-6 text-white shadow-lg">
                                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                                    🎉 Festivals & Events During Your Visit
                                </h3>
                                <div className="grid md:grid-cols-2 gap-4">
                                    {cityHighlights.festivalsEvents.map((event, idx) => (
                                        <div key={idx} className="bg-white/20 backdrop-blur-sm rounded-xl p-4">
                                            <p className="font-semibold text-white">{event.name}</p>
                                            <p className="text-white/90 text-sm mt-1">{event.description}</p>
                                            {event.period && (
                                                <span className="text-white/80 text-xs mt-2 inline-block bg-white/20 px-2 py-1 rounded-full">
                                                    📅 {event.period}
                                                </span>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Famous Food - Full Width Attractive Card */}
                        {cityHighlights.famousFood?.length > 0 && (
                            <div id="famous-food" data-section="famous-food" className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-2xl p-6 border border-orange-200 shadow-sm">
                                <h3 className="text-lg font-bold text-orange-800 mb-4 flex items-center gap-2">
                                    <Utensils className="w-5 h-5" />
                                    Must-Try Food in {destination}
                                </h3>
                                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {cityHighlights.famousFood.slice(0, 6).map((food, idx) => (
                                        <div key={idx} className="bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow border border-orange-100">
                                            <div className="flex items-start gap-3">
                                                {food.image ? (
                                                    <img 
                                                        src={food.image} 
                                                        alt={food.name} 
                                                        className="w-16 h-16 rounded-lg object-cover flex-shrink-0 shadow-sm"
                                                    />
                                                ) : (
                                                    <div className="w-16 h-16 bg-gradient-to-br from-orange-200 to-amber-200 rounded-lg flex items-center justify-center flex-shrink-0">
                                                        <span className="text-2xl">🍽️</span>
                                                    </div>
                                                )}
                                                <div className="flex-1 min-w-0">
                                                    <p className="font-bold text-gray-800 text-sm">{food.name || 'Local Specialty'}</p>
                                                    <p className="text-gray-600 text-xs mt-1 leading-relaxed">{food.description}</p>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Iconic Restaurants - Cards with Full Details */}
                        {cityHighlights.famousRestaurants?.length > 0 && (
                            <div id="restaurants" data-section="restaurants" className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl p-6 border border-emerald-200 shadow-sm">
                                <h3 className="text-lg font-bold text-emerald-800 mb-4 flex items-center gap-2">
                                    🍴 Iconic Restaurants in {destination}
                                </h3>
                                <div className="grid md:grid-cols-2 gap-4">
                                    {cityHighlights.famousRestaurants.slice(0, 4).map((rest, idx) => (
                                        <div key={idx} className="bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow border border-emerald-100">
                                            <div className="flex items-start justify-between gap-3">
                                                <div className="flex-1">
                                                    <p className="font-bold text-gray-800">{rest.name}</p>
                                                    {rest.category && (
                                                        <span className="text-xs text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full inline-block mt-1">
                                                            {rest.category}
                                                        </span>
                                                    )}
                                                </div>
                                                {rest.rating && (
                                                    <div className="flex items-center gap-1 bg-amber-100 px-2 py-1 rounded-lg">
                                                        <Star className="w-4 h-4 text-amber-500 fill-current" />
                                                        <span className="font-bold text-amber-700">{rest.rating}</span>
                                                    </div>
                                                )}
                                            </div>
                                            
                                            {rest.address && (
                                                <p className="text-sm text-gray-600 mt-3 flex items-start gap-2">
                                                    <MapPin className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                                                    <span>{rest.address}</span>
                                                </p>
                                            )}
                                            
                                            {rest.description && (
                                                <p className="text-sm text-gray-600 mt-2 italic">{rest.description}</p>
                                            )}
                                            
                                            <div className="flex items-center gap-4 mt-3 pt-3 border-t border-gray-100 flex-wrap">
                                                {rest.priceLevel && (
                                                    <span className="text-sm text-gray-600 flex items-center gap-1">
                                                        <IndianRupee className="w-4 h-4 text-emerald-500" />
                                                        {rest.priceLevel}
                                                    </span>
                                                )}
                                                {rest.phone && (
                                                    <a href={`tel:${rest.phone}`} className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1">
                                                        <Phone className="w-4 h-4" />
                                                        {rest.phone}
                                                    </a>
                                                )}
                                                {rest.googleMapsUrl && (
                                                    <a 
                                                        href={rest.googleMapsUrl} 
                                                        target="_blank" 
                                                        rel="noopener noreferrer" 
                                                        className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1 ml-auto"
                                                    >
                                                        <Navigation className="w-4 h-4" />
                                                        View on Map
                                                    </a>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Two Column Layout for Tips & Hidden Gems */}
                        <div className="grid md:grid-cols-2 gap-6">
                            {/* Local Tips & Getting Around */}
                            {(cityHighlights.localTips?.length > 0 || cityHighlights.transportTips?.length > 0) && (
                                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-200 shadow-sm">
                                    <h3 className="text-lg font-bold text-blue-800 mb-4 flex items-center gap-2">
                                        <Lightbulb className="w-5 h-5" />
                                        Traveler Tips
                                    </h3>
                                    
                                    {cityHighlights.localTips?.length > 0 && (
                                        <div className="space-y-2 mb-4">
                                            {cityHighlights.localTips.slice(0, 4).map((tip, idx) => (
                                                <div key={idx} className="bg-white rounded-lg p-3 text-sm text-gray-700 flex items-start gap-2 shadow-sm">
                                                    <span className="text-blue-500 font-bold">💡</span>
                                                    <span>{typeof tip === 'string' ? tip : JSON.stringify(tip)}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                    
                                    {cityHighlights.transportTips?.length > 0 && (
                                        <div className="mt-4 pt-4 border-t border-blue-200">
                                            <p className="text-sm font-semibold text-blue-700 mb-2 flex items-center gap-2">
                                                <Navigation className="w-4 h-4" /> Getting Around
                                            </p>
                                            <div className="space-y-2">
                                                {cityHighlights.transportTips.slice(0, 3).map((tip, idx) => (
                                                    <div key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                                                        <span className="text-blue-500">🚗</span>
                                                        <span>{typeof tip === 'string' ? tip : JSON.stringify(tip)}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {cityHighlights.safetyInfo && (
                                        <div className="mt-4 pt-4 border-t border-blue-200">
                                            <p className="text-sm font-semibold text-red-700 mb-2 flex items-center gap-2">
                                                <AlertTriangle className="w-4 h-4" /> Safety Note
                                            </p>
                                            <p className="text-sm text-gray-700 bg-red-50 p-3 rounded-lg border border-red-100">
                                                {cityHighlights.safetyInfo}
                                            </p>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Hidden Gems */}
                            {cityHighlights.hiddenGems?.length > 0 && (
                                <div className="bg-gradient-to-br from-violet-50 to-purple-50 rounded-2xl p-6 border border-violet-200 shadow-sm">
                                    <h3 className="text-lg font-bold text-violet-800 mb-4 flex items-center gap-2">
                                        💎 Hidden Gems
                                    </h3>
                                    <div className="space-y-3">
                                        {cityHighlights.hiddenGems.slice(0, 4).map((gem, idx) => (
                                            <div key={idx} className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                                                <p className="font-semibold text-gray-800 flex items-center gap-2">
                                                    <span className="text-violet-500">✨</span>
                                                    {gem.name}
                                                </p>
                                                <p className="text-sm text-gray-600 mt-1 leading-relaxed">{gem.description}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Shopping Areas - Horizontal Scroll Cards */}
                        {cityHighlights.shoppingAreas?.length > 0 && (
                            <div className="bg-gradient-to-br from-amber-50 to-yellow-50 rounded-2xl p-6 border border-amber-200 shadow-sm">
                                <h3 className="text-lg font-bold text-amber-800 mb-4 flex items-center gap-2">
                                    🛍️ Shopping Destinations
                                </h3>
                                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                                    {cityHighlights.shoppingAreas.slice(0, 4).map((shop, idx) => (
                                        <div key={idx} className="bg-white rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow border border-amber-100">
                                            <div className="flex items-start justify-between gap-2 mb-2">
                                                <p className="font-bold text-gray-800 text-sm">{shop.name}</p>
                                                {shop.rating && (
                                                    <div className="flex items-center gap-1 bg-amber-100 px-1.5 py-0.5 rounded">
                                                        <Star className="w-3 h-3 text-amber-500 fill-current" />
                                                        <span className="text-xs font-semibold text-amber-700">{shop.rating}</span>
                                                    </div>
                                                )}
                                            </div>
                                            {shop.category && (
                                                <span className="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">
                                                    {shop.category}
                                                </span>
                                            )}
                                            {shop.address && (
                                                <p className="text-xs text-gray-500 mt-2 flex items-start gap-1">
                                                    <MapPin className="w-3 h-3 text-amber-500 flex-shrink-0 mt-0.5" />
                                                    <span className="line-clamp-2">{shop.address}</span>
                                                </p>
                                            )}
                                            {shop.description && (
                                                <p className="text-xs text-gray-600 mt-2">{shop.description}</p>
                                            )}
                                            {shop.googleMapsUrl && (
                                                <a 
                                                    href={shop.googleMapsUrl} 
                                                    target="_blank" 
                                                    rel="noopener noreferrer" 
                                                    className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 mt-2"
                                                >
                                                    <Navigation className="w-3 h-3" />
                                                    View on Map
                                                </a>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                )}

                {/* Day Cards */}
                {data.days?.map((dayPlan) => (
                    <motion.div key={dayPlan.day} variants={itemVariants} className="bg-white border border-gray-100 rounded-3xl shadow-sm p-6 space-y-6">
                        {/* Day Header */}
                        <div className="flex items-center justify-between flex-wrap gap-4 border-b border-gray-100 pb-4">
                            <div>
                                <div className="flex items-center gap-3">
                                    <span className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white text-sm font-bold px-3 py-1 rounded-full">
                                        Day {dayPlan.day}
                                    </span>
                                    {dayPlan.date && (
                                        <span className="text-sm text-gray-500">{formatDate(dayPlan.date)}</span>
                                    )}
                                </div>
                                <h2 className="text-2xl font-bold text-slate-800 mt-2">{dayPlan.title || dayPlan.theme || `Day ${dayPlan.day} Activities`}</h2>
                                {dayPlan.summary && (
                                    <p className="text-gray-600 mt-1">{dayPlan.summary}</p>
                                )}
                            </div>
                            {dayPlan.estimatedCost && (
                                <div className="bg-emerald-50 px-4 py-2 rounded-xl">
                                    <p className="text-xs text-emerald-600 uppercase">Est. Cost</p>
                                    <p className="font-bold text-emerald-700">{dayPlan.estimatedCost}</p>
                                </div>
                            )}
                        </div>

                        {/* Weather */}
                        {dayPlan.locationInsight?.weather?.length > 0 && (
                            <div className="flex flex-wrap gap-3">
                                {dayPlan.locationInsight.weather.map((snapshot, idx) => (
                                    <WeatherChip key={`${snapshot.date}-${idx}`} day={snapshot} />
                                ))}
                            </div>
                        )}

                        {/* Time-based Schedule */}
                        {dayPlan.schedule?.length > 0 && (
                            <div className="mt-4">
                                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4 flex items-center gap-2">
                                    <Clock className="w-4 h-4" /> Day Schedule
                                </h3>
                                <div className="relative">
                                    {dayPlan.schedule.map((item, idx) => (
                                        <ScheduleItem 
                                            key={idx} 
                                            item={item} 
                                            isFirst={idx === 0}
                                            isLast={idx === dayPlan.schedule.length - 1}
                                        />
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Location Photos */}
                        {dayPlan.locationInsight?.photos?.length > 0 && (
                            <div>
                                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3 flex items-center gap-2">
                                    <Camera className="w-4 h-4" /> Destination Photos
                                </h3>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                    {dayPlan.locationInsight.photos.slice(0, 4).map((photo, idx) => (
                                        <img 
                                            key={idx} 
                                            src={photo} 
                                            alt={dayPlan.locationInsight.location} 
                                            className="h-32 w-full object-cover rounded-2xl" 
                                            onError={(e) => { e.currentTarget.src = 'https://placehold.co/600x400/e2e8f0/64748b?text=Photo'; }} 
                                        />
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Reviews */}
                        {dayPlan.locationInsight?.reviews && (
                            <div className="bg-slate-50 rounded-2xl p-4">
                                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">Reviews Snapshot</h3>
                                <ReviewHighlights reviews={dayPlan.locationInsight.reviews} />
                            </div>
                        )}

                        {/* Dining - Real Restaurants */}
                        {dayPlan.diningRecommendations?.restaurants?.length > 0 ? (
                            <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl p-5">
                                <div className="flex items-center gap-2 text-emerald-700 mb-4">
                                    <Utensils className="w-5 h-5" />
                                    <h3 className="text-sm font-bold uppercase tracking-wide">Real Restaurant Recommendations</h3>
                                    <span className="text-xs bg-emerald-200 text-emerald-800 px-2 py-0.5 rounded-full ml-2">from Google</span>
                                </div>
                                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                                    {dayPlan.diningRecommendations.restaurants.map((restaurant, idx) => (
                                        <RestaurantCard key={idx} restaurant={restaurant} />
                                    ))}
                                </div>
                            </div>
                        ) : dayPlan.dining?.length > 0 && (
                            <div className="bg-emerald-50 rounded-2xl p-4">
                                <div className="flex items-center gap-2 text-emerald-600 mb-3">
                                    <Utensils className="w-4 h-4" />
                                    <h3 className="text-sm font-semibold uppercase tracking-wide">Dining Suggestions</h3>
                                </div>
                                <div className="grid md:grid-cols-2 gap-2">
                                    {dayPlan.dining.map((spot, idx) => (
                                        <div key={idx} className="bg-white/70 rounded-lg px-3 py-2 text-sm text-gray-700">
                                            {spot}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                ))}

                {/* Travel Tips & Packing - supports both old and new data structure */}
                {(data.travelTips?.length > 0 || data.packingSuggestions?.length > 0 || data.packingList?.length > 0) && (
                    <motion.div variants={itemVariants} className="grid md:grid-cols-2 gap-6">
                        {data.travelTips?.length > 0 && (
                            <div className="bg-white border border-gray-100 rounded-3xl shadow-sm p-6">
                                <div className="flex items-center gap-2 text-cyan-600 mb-4">
                                    <Lightbulb className="w-5 h-5" />
                                    <h3 className="font-bold text-lg">Travel Tips</h3>
                                </div>
                                <ul className="space-y-2">
                                    {data.travelTips.map((tip, idx) => (
                                        <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                                            <span className="text-cyan-500 mt-1">•</span>
                                            {tip}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                        {/* Support both packingSuggestions and packingList */}
                        {(data.packingSuggestions?.length > 0 || data.packingList?.length > 0) && (
                            <div className="bg-white border border-gray-100 rounded-3xl shadow-sm p-6">
                                <div className="flex items-center gap-2 text-fuchsia-600 mb-4">
                                    <Briefcase className="w-5 h-5" />
                                    <h3 className="font-bold text-lg">Packing List</h3>
                                    {data.packingList?.length > 0 && (
                                        <span className="text-xs bg-fuchsia-100 text-fuchsia-700 px-2 py-0.5 rounded-full ml-2">from Weather Agent</span>
                                    )}
                                </div>
                                <ul className="space-y-2">
                                    {(data.packingList || data.packingSuggestions).map((item, idx) => (
                                        <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                                            <span className="text-fuchsia-500 mt-1">✓</span>
                                            {item}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </motion.div>
                )}

                {/* Budget Breakdown */}
                {data.budgetBreakdown && Object.keys(data.budgetBreakdown).length > 0 && (
                    <motion.div variants={itemVariants} className="bg-white border border-gray-100 rounded-3xl shadow-sm p-6">
                        <div className="flex items-center gap-2 text-emerald-600 mb-4">
                            <IndianRupee className="w-5 h-5" />
                            <h3 className="font-bold text-lg">Budget Breakdown</h3>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {data.budgetBreakdown.accommodation > 0 && (
                                <div className="bg-emerald-50 rounded-xl p-4 text-center">
                                    <p className="text-xs text-gray-500 uppercase">Accommodation</p>
                                    <p className="text-xl font-bold text-emerald-700">{formatIndianCurrency(data.budgetBreakdown.accommodation)}</p>
                                </div>
                            )}
                            {data.budgetBreakdown.food > 0 && (
                                <div className="bg-orange-50 rounded-xl p-4 text-center">
                                    <p className="text-xs text-gray-500 uppercase">Food</p>
                                    <p className="text-xl font-bold text-orange-700">{formatIndianCurrency(data.budgetBreakdown.food)}</p>
                                </div>
                            )}
                            {data.budgetBreakdown.transport > 0 && (
                                <div className="bg-blue-50 rounded-xl p-4 text-center">
                                    <p className="text-xs text-gray-500 uppercase">Transport</p>
                                    <p className="text-xl font-bold text-blue-700">{formatIndianCurrency(data.budgetBreakdown.transport)}</p>
                                </div>
                            )}
                            {data.budgetBreakdown.activities > 0 && (
                                <div className="bg-purple-50 rounded-xl p-4 text-center">
                                    <p className="text-xs text-gray-500 uppercase">Activities</p>
                                    <p className="text-xl font-bold text-purple-700">{formatIndianCurrency(data.budgetBreakdown.activities)}</p>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </motion.div>
        </div>
    );
};

export default ItineraryResult;
