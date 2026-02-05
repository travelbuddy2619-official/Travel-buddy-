import { useState } from 'react';
import { motion } from 'framer-motion';
import { MapPin, CalendarRange, Users, Plane, Send, Wallet } from 'lucide-react';

const ItineraryForm = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    source: '',
    destination: '',
    startDate: '',
    endDate: '',
    people: '',
    budget: '', // Changed to empty string for number input
    transport: 'Flight', // Added back
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.5, ease: "easeOut" }}
      className="w-full max-w-6xl bg-white p-4 sm:p-6 rounded-2xl shadow-2xl"
    >
      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-8 gap-4 items-center">
        {/* Source */}
        <div className="relative md:col-span-1">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input type="text" name="source" placeholder="Source" value={formData.source} onChange={handleChange} required className="w-full pl-10 pr-3 py-3 text-sm text-gray-700 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>

        {/* Destination */}
        <div className="relative md:col-span-1">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input type="text" name="destination" placeholder="Destination" value={formData.destination} onChange={handleChange} required className="w-full pl-10 pr-3 py-3 text-sm text-gray-700 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        
        {/* Start Date */}
        <div className="relative md:col-span-1">
            <CalendarRange className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input type="date" name="startDate" value={formData.startDate} onChange={handleChange} required className="w-full pl-10 pr-3 py-3 text-sm text-gray-700 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" title="Start Date" />
        </div>

        {/* End Date */}
        <div className="relative md:col-span-1">
            <CalendarRange className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input type="date" name="endDate" value={formData.endDate} onChange={handleChange} required className="w-full pl-10 pr-3 py-3 text-sm text-gray-700 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" title="End Date" />
        </div>

        {/* People */}
        <div className="relative md:col-span-1">
          <Users className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input type="number" name="people" placeholder="People" min="1" value={formData.people} onChange={handleChange} required className="w-full pl-10 pr-3 py-3 text-sm text-gray-700 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>

        {/* Budget */}
        <div className="relative md:col-span-1">
            <Wallet className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input type="number" name="budget" placeholder="Budget (₹)" min="0" value={formData.budget} onChange={handleChange} required className="w-full pl-10 pr-3 py-3 text-sm text-gray-700 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        
        {/* Mode of Transport */}
        <div className="relative md:col-span-1">
          <Plane className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <select
            name="transport"
            value={formData.transport}
            onChange={handleChange}
            className="w-full pl-10 pr-3 py-3 text-sm text-gray-700 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 appearance-none bg-white"
          >
            <option className="text-black">Flight</option>
            <option className="text-black">Train</option>
            <option className="text-black">Car</option>
            <option className="text-black">Bus</option>
          </select>
        </div>

        {/* Submit Button */}
        <button type="submit" className="md:col-span-1 w-full bg-blue-600 text-white font-semibold py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors duration-300 flex items-center justify-center gap-2">
          <Send size={18} />
          <span>Generate</span>
        </button>
      </form>
    </motion.div>
  );
};

export default ItineraryForm;

