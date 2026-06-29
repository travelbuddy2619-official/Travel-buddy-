import React from 'react';
import ItineraryForm from './ItineraryForm';
import { motion } from 'framer-motion';
import { Sparkles, Compass, Sunrise } from 'lucide-react';

const Hero = ({ onItinerarySubmit }) => {
  return (
    // The main container needs to be relative to position the video and overlay
    <section id="home" data-section="home" className="relative flex items-center justify-center min-h-screen bg-gray-900 text-white pt-24">
      {/* Background Video */}
      <video
        autoPlay
        loop
        muted
        className="absolute z-0 w-full h-full object-cover"
      >
        {/* You can replace this with any other video source */}
        <source
          src="/videos/hero.mp4"
          type="video/mp4"
        />
        Your browser does not support the video tag.
      </video>

      {/* Dark Overlay for Text Readability */}
      <div className="absolute z-10 w-full h-full bg-gradient-to-b from-slate-950/65 via-slate-900/55 to-sky-950/70"></div>

      {/* Floating Mood Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.5 }}
        className="absolute z-20 hidden xl:flex left-12 top-1/3 flex-col gap-3"
      >
      
      
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.65 }}
        className="absolute z-20 hidden xl:flex right-12 top-1/3"
      >
      
      </motion.div>

      {/* Content Container */}
      <div className="relative z-20 flex flex-col items-center w-full px-4 text-center">
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-4xl md:text-6xl lg:text-7xl font-bold mb-4 leading-tight travel-section-title text-white max-w-5xl"
        >
          Plan Journeys That Feel Cinematic, Not Generic
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
          className="text-lg md:text-xl lg:text-2xl mb-10 text-slate-100"
        >
          Modern trip planning with real booking data, local flavor, and day-wise intelligent flow.
        </motion.p>



        {/* The ItineraryForm is passed the onItinerarySubmit function */}
        <div id="itinerary-form" data-section="itinerary-form">
          <ItineraryForm onSubmit={onItinerarySubmit} />
        </div>
      </div>
    </section>
  );
};

export default Hero;

