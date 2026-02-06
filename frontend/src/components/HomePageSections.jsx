import React from 'react';
import { motion } from 'framer-motion';
import { 
  MapPin, Plane, Hotel, Utensils, Cloud, Brain, Shield, Clock, 
  Star, ChevronRight, Globe, Zap, Users, Award, Heart
} from 'lucide-react';
import { Link } from 'react-router-dom';

// How It Works Section
export const HowItWorks = () => {
  const steps = [
    {
      number: "01",
      title: "Enter Your Details",
      description: "Tell us where you want to go, your travel dates, budget, and preferences.",
      icon: <MapPin className="w-8 h-8" />,
      color: "from-blue-500 to-cyan-500"
    },
    {
      number: "02", 
      title: "AI Plans Your Trip",
      description: "Our multi-agent AI system researches, plans, and creates a personalized itinerary.",
      icon: <Brain className="w-8 h-8" />,
      color: "from-purple-500 to-pink-500"
    },
    {
      number: "03",
      title: "Review & Customize",
      description: "Get a detailed day-by-day plan with real-time weather, restaurants, and activities.",
      icon: <Zap className="w-8 h-8" />,
      color: "from-orange-500 to-red-500"
    },
    {
      number: "04",
      title: "Book & Travel",
      description: "Book flights, hotels, and experiences directly. Your dream trip is ready!",
      icon: <Plane className="w-8 h-8" />,
      color: "from-green-500 to-emerald-500"
    }
  ];

  return (
    <section className="py-20 bg-white">
      <div className="container mx-auto px-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="text-blue-600 font-semibold text-sm uppercase tracking-wider">How It Works</span>
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mt-3 mb-4">
            Plan Your Trip in <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">4 Easy Steps</span>
          </h2>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Our AI-powered platform makes travel planning effortless and enjoyable
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="relative group"
            >
              {/* Connector Line */}
              {index < steps.length - 1 && (
                <div className="hidden lg:block absolute top-16 left-[60%] w-full h-0.5 bg-gradient-to-r from-gray-200 to-transparent" />
              )}
              
              <div className="bg-gray-50 rounded-2xl p-8 hover:bg-white hover:shadow-xl transition-all duration-300 border border-gray-100 relative z-10">
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${step.color} flex items-center justify-center text-white mb-6 group-hover:scale-110 transition-transform`}>
                  {step.icon}
                </div>
                <span className="text-5xl font-bold text-gray-100 absolute top-4 right-4">{step.number}</span>
                <h3 className="text-xl font-bold text-gray-900 mb-3">{step.title}</h3>
                <p className="text-gray-600">{step.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Features Section
export const Features = () => {
  const features = [
    {
      icon: <Brain className="w-6 h-6" />,
      title: "AI-Powered Planning",
      description: "6 specialized AI agents work together to create the perfect itinerary",
      color: "bg-purple-100 text-purple-600"
    },
    {
      icon: <Cloud className="w-6 h-6" />,
      title: "Real-Time Weather",
      description: "Get accurate weather forecasts and packing recommendations",
      color: "bg-cyan-100 text-cyan-600"
    },
    {
      icon: <Utensils className="w-6 h-6" />,
      title: "Restaurant Discovery",
      description: "Find the best local restaurants with ratings and reviews",
      color: "bg-orange-100 text-orange-600"
    },
    {
      icon: <Hotel className="w-6 h-6" />,
      title: "Live Hotel Prices",
      description: "Compare prices from Booking.com with real-time availability",
      color: "bg-green-100 text-green-600"
    },
    {
      icon: <Plane className="w-6 h-6" />,
      title: "Flight Booking",
      description: "Search and compare flights from multiple providers",
      color: "bg-blue-100 text-blue-600"
    },
    {
      icon: <MapPin className="w-6 h-6" />,
      title: "Local Insights",
      description: "Discover hidden gems, festivals, and local experiences",
      color: "bg-pink-100 text-pink-600"
    }
  ];

  return (
    <section className="py-20 bg-gradient-to-b from-gray-50 to-white">
      <div className="container mx-auto px-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="text-blue-600 font-semibold text-sm uppercase tracking-wider">Features</span>
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mt-3 mb-4">
            Everything You Need to <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">Travel Smart</span>
          </h2>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Powered by cutting-edge AI technology to make your travel planning seamless
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.05 }}
              className="bg-white rounded-2xl p-6 border border-gray-100 hover:shadow-lg hover:border-blue-200 transition-all group cursor-pointer"
            >
              <div className={`w-12 h-12 rounded-xl ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                {feature.icon}
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-gray-600 text-sm">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Popular Destinations Section
export const PopularDestinations = () => {
  const destinations = [
    {
      name: "Goa",
      image: "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=600",
      tagline: "Beach Paradise",
      rating: 4.8,
      trips: "12K+ trips"
    },
    {
      name: "Jaipur",
      image: "https://images.unsplash.com/photo-1477587458883-47145ed94245?w=600",
      tagline: "Pink City Heritage",
      rating: 4.7,
      trips: "8K+ trips"
    },
    {
      name: "Manali",
      image: "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=600",
      tagline: "Mountain Escape",
      rating: 4.9,
      trips: "10K+ trips"
    },
    {
      name: "Kerala",
      image: "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=600",
      tagline: "God's Own Country",
      rating: 4.8,
      trips: "15K+ trips"
    },
    {
      name: "Udaipur",
      image: "https://images.unsplash.com/photo-1568495248636-6432b97bd949?w=600",
      tagline: "City of Lakes",
      rating: 4.7,
      trips: "6K+ trips"
    },
    {
      name: "Varanasi",
      image: "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?w=600",
      tagline: "Spiritual Capital",
      rating: 4.6,
      trips: "9K+ trips"
    }
  ];

  return (
    <section className="py-20 bg-white">
      <div className="container mx-auto px-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="flex justify-between items-end mb-12"
        >
          <div>
            <span className="text-blue-600 font-semibold text-sm uppercase tracking-wider">Popular Destinations</span>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mt-3">
              Trending <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">Destinations</span>
            </h2>
          </div>
          <Link to="/" className="hidden md:flex items-center gap-2 text-blue-600 font-semibold hover:gap-3 transition-all">
            View All <ChevronRight className="w-5 h-5" />
          </Link>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {destinations.map((dest, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="group relative rounded-3xl overflow-hidden h-80 cursor-pointer"
            >
              <img 
                src={dest.image} 
                alt={dest.name}
                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
              
              <div className="absolute bottom-0 left-0 right-0 p-6">
                <div className="flex items-center gap-2 mb-2">
                  <span className="bg-white/20 backdrop-blur-sm text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
                    <Star className="w-3 h-3 fill-yellow-400 text-yellow-400" /> {dest.rating}
                  </span>
                  <span className="bg-white/20 backdrop-blur-sm text-white text-xs px-2 py-1 rounded-full">
                    {dest.trips}
                  </span>
                </div>
                <h3 className="text-2xl font-bold text-white mb-1">{dest.name}</h3>
                <p className="text-white/80 text-sm">{dest.tagline}</p>
              </div>
              
              <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-lg">
                  <ChevronRight className="w-5 h-5 text-gray-800" />
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Stats Section
export const Stats = () => {
  const stats = [
    { value: "50K+", label: "Happy Travelers", icon: <Users className="w-6 h-6" /> },
    { value: "100+", label: "Destinations", icon: <Globe className="w-6 h-6" /> },
    { value: "4.9", label: "User Rating", icon: <Star className="w-6 h-6" /> },
    { value: "99%", label: "Satisfaction", icon: <Heart className="w-6 h-6" /> }
  ];

  return (
    <section className="py-16 bg-gradient-to-r from-blue-600 to-purple-600">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="text-center text-white"
            >
              <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
                {stat.icon}
              </div>
              <div className="text-4xl md:text-5xl font-bold mb-2">{stat.value}</div>
              <div className="text-white/80">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

// Testimonials Section
export const Testimonials = () => {
  const testimonials = [
    {
      name: "Priya Sharma",
      role: "Solo Traveler",
      image: "https://randomuser.me/api/portraits/women/44.jpg",
      text: "TravelAI planned my entire Goa trip perfectly! The restaurant recommendations were spot on and the weather alerts saved my beach day.",
      rating: 5
    },
    {
      name: "Rahul Verma",
      role: "Family Trip",
      image: "https://randomuser.me/api/portraits/men/32.jpg",
      text: "We used TravelAI for our Kerala family vacation. The detailed itinerary with kids-friendly activities was amazing!",
      rating: 5
    },
    {
      name: "Anita Desai",
      role: "Adventure Seeker",
      image: "https://randomuser.me/api/portraits/women/68.jpg",
      text: "The AI found hidden gems in Manali that weren't in any guidebook. Best trip planning experience ever!",
      rating: 5
    }
  ];

  return (
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <span className="text-blue-600 font-semibold text-sm uppercase tracking-wider">Testimonials</span>
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mt-3 mb-4">
            What Our <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">Travelers Say</span>
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100"
            >
              <div className="flex items-center gap-1 mb-4">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                ))}
              </div>
              <p className="text-gray-600 mb-6 italic">"{testimonial.text}"</p>
              <div className="flex items-center gap-4">
                <img 
                  src={testimonial.image} 
                  alt={testimonial.name}
                  className="w-12 h-12 rounded-full object-cover"
                />
                <div>
                  <h4 className="font-bold text-gray-900">{testimonial.name}</h4>
                  <p className="text-sm text-gray-500">{testimonial.role}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};

// CTA Section
export const CTASection = () => {
  return (
    <section className="py-20 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-10 left-10 w-40 h-40 bg-white rounded-full blur-3xl" />
        <div className="absolute bottom-10 right-10 w-60 h-60 bg-white rounded-full blur-3xl" />
      </div>
      
      <div className="container mx-auto px-4 relative z-10">
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto"
        >
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to Start Your Adventure?
          </h2>
          <p className="text-white/90 text-lg mb-8">
            Let our AI plan your perfect trip. No more hours of research - just tell us where you want to go!
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="#home" 
              className="bg-white text-blue-600 px-8 py-4 rounded-full font-bold hover:shadow-xl hover:scale-105 transition-all inline-flex items-center justify-center gap-2"
            >
              Start Planning <ChevronRight className="w-5 h-5" />
            </a>
            <Link 
              to="/travel" 
              className="bg-white/20 text-white px-8 py-4 rounded-full font-bold hover:bg-white/30 transition-all inline-flex items-center justify-center gap-2 backdrop-blur-sm"
            >
              <Plane className="w-5 h-5" /> Search Flights
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
};

// Footer Component
export const Footer = () => {
  return (
    <footer className="bg-gray-900 text-white py-16">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          <div>
            <h3 className="text-2xl font-bold mb-4">TravelAI</h3>
            <p className="text-gray-400 mb-6">
              AI-powered travel planning that makes your dream trips a reality.
            </p>
            <div className="flex gap-4">
              <a href="#" className="w-10 h-10 bg-gray-800 rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
              </a>
              <a href="#" className="w-10 h-10 bg-gray-800 rounded-full flex items-center justify-center hover:bg-pink-600 transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>
              </a>
              <a href="#" className="w-10 h-10 bg-gray-800 rounded-full flex items-center justify-center hover:bg-blue-400 transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/></svg>
              </a>
            </div>
          </div>
          
          <div>
            <h4 className="font-bold mb-4">Quick Links</h4>
            <ul className="space-y-2 text-gray-400">
              <li><a href="#" className="hover:text-white transition-colors">Home</a></li>
              <li><Link to="/travel" className="hover:text-white transition-colors">Flights & Trains</Link></li>
              <li><Link to="/hotels" className="hover:text-white transition-colors">Hotels</Link></li>
              <li><a href="#" className="hover:text-white transition-colors">About Us</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-bold mb-4">Popular Destinations</h4>
            <ul className="space-y-2 text-gray-400">
              <li><a href="#" className="hover:text-white transition-colors">Goa</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Kerala</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Rajasthan</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Himachal</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-bold mb-4">Support</h4>
            <ul className="space-y-2 text-gray-400">
              <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Contact Us</a></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-800 mt-12 pt-8 text-center text-gray-400">
          <p>© 2026 TravelAI. All rights reserved. Made with ❤️ for travelers.</p>
        </div>
      </div>
    </footer>
  );
};
