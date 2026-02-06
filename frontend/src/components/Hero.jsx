import React from 'react';
import ItineraryForm from './ItineraryForm';
import { motion } from 'framer-motion';

const Hero = ({ onItinerarySubmit }) => {
  return (
    // The main container needs to be relative to position the video and overlay
    <section id="home" data-section="home" className="relative flex items-center justify-center h-screen bg-gray-900 text-white">
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
      <div className="absolute z-10 w-full h-full bg-black opacity-50"></div>

      {/* Content Container */}
      <div className="relative z-20 flex flex-col items-center w-full px-4 text-center">
        <motion.h1
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-4xl md:text-6xl lg:text-7xl font-bold mb-4 leading-tight"
        >
          Let’s explore, create and manage trips with ease
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
          className="text-lg md:text-xl lg:text-2xl mb-12"
        >
          Plan your perfect journey with AI.
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

