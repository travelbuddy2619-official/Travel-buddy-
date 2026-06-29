    import React, { useState } from 'react';
    import { motion } from 'framer-motion';
    import { Menu, X, Plane, Hotel, Compass, LayoutDashboard, LogOut, User } from 'lucide-react';
    import { Link } from 'react-router-dom';
    
    const Navbar = ({ user, onLogout }) => {
      const [isOpen, setIsOpen] = useState(false);
    
      const menuVariants = {
        hidden: { opacity: 0, y: -20 },
        visible: { opacity: 1, y: 0, transition: { staggerChildren: 0.1 } },
      };
    
      const linkVariants = {
        hidden: { opacity: 0, y: -10 },
        visible: { opacity: 1, y: 0 },
      };
    
      return (
        <header className="fixed top-0 left-0 right-0 z-30">
          <nav className="container mx-auto mt-4 px-4 md:px-6 py-3 flex justify-between items-center rounded-2xl travel-glass">
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
            >
              <Link to="/" className="inline-flex items-center gap-2 text-xl font-bold text-slate-900">
                <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-sky-100 text-sky-700">
                  <Compass className="w-5 h-5" />
                </span>
                TravelAI
              </Link>
            </motion.div>
    
            {/* Desktop Menu */}
            <motion.ul
              variants={menuVariants}
              initial="hidden"
              animate="visible"
              className="hidden md:flex items-center space-x-3"
            >
              <motion.li variants={linkVariants}>
                <Link 
                  to="/travel" 
                  className="flex items-center gap-2 text-slate-700 hover:text-slate-900 transition-colors bg-white px-4 py-2 rounded-full border border-slate-200"
                >
                  <Plane className="w-4 h-4" />
                  Flights & Trains
                </Link>
              </motion.li>
              <motion.li variants={linkVariants}>
                <Link 
                  to="/hotels" 
                  className="flex items-center gap-2 text-slate-700 hover:text-slate-900 transition-colors bg-white px-4 py-2 rounded-full border border-slate-200"
                >
                  <Hotel className="w-4 h-4" />
                  Hotels
                </Link>
              </motion.li>
              <motion.li variants={linkVariants}>
                <a 
                  href="#itinerary-form" 
                  className="travel-cta font-semibold px-5 py-2 rounded-full"
                >
                  Start Planning
                </a>
              </motion.li>
              {user ? (
                <>
                  <motion.li variants={linkVariants}>
                    <Link
                      to="/dashboard"
                      className="flex items-center gap-2 text-slate-700 hover:text-slate-900 transition-colors bg-white px-4 py-2 rounded-full border border-slate-200"
                    >
                      <LayoutDashboard className="w-4 h-4" />
                      Dashboard
                    </Link>
                  </motion.li>
                  <motion.li variants={linkVariants}>
                    <button
                      onClick={onLogout}
                      className="flex items-center gap-2 text-slate-700 hover:text-slate-900 transition-colors bg-white px-4 py-2 rounded-full border border-slate-200"
                    >
                      <LogOut className="w-4 h-4" />
                      Logout
                    </button>
                  </motion.li>
                </>
              ) : (
                <motion.li variants={linkVariants}>
                  <Link
                    to="/auth"
                    className="flex items-center gap-2 text-slate-700 hover:text-slate-900 transition-colors bg-white px-4 py-2 rounded-full border border-slate-200"
                  >
                    <User className="w-4 h-4" />
                    Login / Sign Up
                  </Link>
                </motion.li>
              )}
            </motion.ul>
    
            {/* Mobile Menu Button */}
            <div className="md:hidden">
              <button onClick={() => setIsOpen(!isOpen)} className="text-slate-700">
                {isOpen ? <X size={24} /> : <Menu size={24} />}
              </button>
            </div>
          </nav>
    
          {/* Mobile Menu */}
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="md:hidden mx-4 rounded-2xl mt-2 travel-glass"
            >
              <ul className="flex flex-col items-center space-y-4 py-6">
                <li>
                  <Link 
                    to="/travel" 
                    className="flex items-center gap-2 text-slate-700 hover:text-slate-900" 
                    onClick={() => setIsOpen(false)}
                  >
                    <Plane className="w-4 h-4" />
                    Flights & Trains
                  </Link>
                </li>
                <li>
                  <Link 
                    to="/hotels" 
                    className="flex items-center gap-2 text-slate-700 hover:text-slate-900" 
                    onClick={() => setIsOpen(false)}
                  >
                    <Hotel className="w-4 h-4" />
                    Hotels
                  </Link>
                </li>
                <li>
                  <a 
                    href="#itinerary-form" 
                    className="travel-cta font-semibold px-5 py-2 rounded-full"
                    onClick={() => setIsOpen(false)}
                  >
                    Start Planning
                  </a>
                </li>
                {user ? (
                  <>
                    <li>
                      <Link
                        to="/dashboard"
                        className="flex items-center gap-2 text-slate-700 hover:text-slate-900"
                        onClick={() => setIsOpen(false)}
                      >
                        <LayoutDashboard className="w-4 h-4" />
                        Dashboard
                      </Link>
                    </li>
                    <li>
                      <button
                        onClick={() => {
                          onLogout();
                          setIsOpen(false);
                        }}
                        className="flex items-center gap-2 text-slate-700 hover:text-slate-900"
                      >
                        <LogOut className="w-4 h-4" />
                        Logout
                      </button>
                    </li>
                  </>
                ) : (
                  <li>
                    <Link
                      to="/auth"
                      className="flex items-center gap-2 text-slate-700 hover:text-slate-900"
                      onClick={() => setIsOpen(false)}
                    >
                      <User className="w-4 h-4" />
                      Login / Sign Up
                    </Link>
                  </li>
                )}
              </ul>
            </motion.div>
          )}
        </header>
      );
    };
    
    export default Navbar;
    

