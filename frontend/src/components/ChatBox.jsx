import { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, X, Bot, User, RefreshCw, Sparkles, ExternalLink, Navigation, Utensils, Cloud, MapPin } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ChatBox = ({ sessionId, onItineraryUpdate }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: "Hi! I'm your AI travel assistant powered by multiple specialized agents. I can:\n\n🗺️ **Navigate** - \"Go to about section\"\n✏️ **Modify** - \"Add more temples to day 2\"\n🌤️ **Weather** - \"What's the weather like?\"\n🍽️ **Restaurants** - \"Find dinner options\"\n🏙️ **City Info** - \"What's famous here?\"\n✈️ **Book** - \"Book flights\" or \"Find hotels\"\n\nHow can I help you today?"
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Execute actions received from backend
    const executeAction = (action, actionData) => {
        if (!action) return;
        
        console.log('Executing action:', action, actionData);
        
        switch (action) {
            case 'scroll_to_section':
                const section = actionData?.section;
                if (section) {
                    // Try multiple selector strategies
                    const element = document.getElementById(section) || 
                                   document.querySelector(`[data-section="${section}"]`) ||
                                   document.querySelector(`.${section}`) ||
                                   document.querySelector(`#${section.replace(/-/g, '')}`);
                    
                    if (element) {
                        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    } else {
                        // Fallback: try to scroll to common section names
                        const sectionMap = {
                            'hero': 0,
                            'itinerary-form': 500,
                            'itinerary-result': 800,
                            'weather': 600,
                            'city-highlights': 1000,
                            'famous-food': 1200,
                            'restaurants': 1400,
                            'about': 2000,
                            'contact': 2500
                        };
                        const offset = sectionMap[section] || 0;
                        window.scrollTo({ top: offset, behavior: 'smooth' });
                    }
                }
                break;
                
            case 'open_external':
                const url = actionData?.url;
                if (url) {
                    window.open(url, '_blank', 'noopener,noreferrer');
                }
                break;
                
            case 'update_itinerary':
                if (actionData?.itinerary && onItineraryUpdate) {
                    onItineraryUpdate(actionData.itinerary);
                    // Scroll to itinerary after update
                    setTimeout(() => {
                        const resultSection = document.getElementById('itinerary-result') || 
                                             document.querySelector('[data-section="itinerary-result"]');
                        if (resultSection) {
                            resultSection.scrollIntoView({ behavior: 'smooth' });
                        }
                    }, 500);
                }
                break;
                
            default:
                console.log('Unknown action:', action);
        }
    };

    // Get agent icon based on agent used
    const getAgentIcon = (agentUsed) => {
        switch (agentUsed) {
            case 'weather_agent': return <Cloud className="w-3 h-3 text-cyan-600" />;
            case 'dining_agent': return <Utensils className="w-3 h-3 text-orange-600" />;
            case 'navigation_handler': return <Navigation className="w-3 h-3 text-indigo-600" />;
            case 'place_research_agent': return <MapPin className="w-3 h-3 text-red-600" />;
            case 'booking_handler': return <ExternalLink className="w-3 h-3 text-green-600" />;
            default: return <Bot className="w-3 h-3 text-indigo-600" />;
        }
    };

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        setInput('');
        
        // Add user message
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            // Send to chat endpoint
            const chatResponse = await fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMessage,
                    session_id: sessionId,
                    chat_history: messages.slice(-10).map(m => ({ role: m.role, content: m.content }))
                })
            });

            const chatData = await chatResponse.json();
            
            // Add assistant response
            setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: chatData.reply,
                agentUsed: chatData.agent_used,
                hasAction: !!chatData.action
            }]);

            // Execute any action from backend
            if (chatData.action) {
                setTimeout(() => {
                    executeAction(chatData.action, chatData.action_data);
                }, 300);
            }

            // If itinerary was updated, notify user
            if (chatData.action === 'update_itinerary' && chatData.action_data?.itinerary) {
                setMessages(prev => [...prev, {
                    role: 'system',
                    content: '🔄 Itinerary updated! Scrolling to show your changes...'
                }]);
            }

        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error. Please try again.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleModify = async (modification) => {
        setIsLoading(true);
        
        try {
            const response = await fetch('http://localhost:8000/api/modify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    modification: modification
                })
            });

            const data = await response.json();
            
            if (data.success && data.modified_itinerary) {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: `✅ Changes applied!\n\n**What changed:**\n${data.changes_made.map(c => `• ${c}`).join('\n')}\n\n${data.explanation || ''}`
                }]);
                
                // Update the itinerary in parent component
                if (onItineraryUpdate) {
                    onItineraryUpdate(data.modified_itinerary);
                }
            } else {
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: `❌ Couldn't apply changes: ${data.explanation || 'Unknown error'}`
                }]);
            }

        } catch (error) {
            console.error('Modify error:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I couldn\'t apply the changes. Please try again.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <>
            {/* Floating Chat Button */}
            <motion.button
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsOpen(true)}
                className={`fixed bottom-6 right-6 z-50 w-14 h-14 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full shadow-lg flex items-center justify-center text-white ${isOpen ? 'hidden' : ''}`}
            >
                <MessageCircle className="w-6 h-6" />
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white"></span>
            </motion.button>

            {/* Chat Window */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 100, scale: 0.8 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 100, scale: 0.8 }}
                        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                        className="fixed bottom-6 right-6 z-50 w-96 h-[32rem] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-gray-200"
                    >
                        {/* Header */}
                        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-3 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                                    <Sparkles className="w-4 h-4 text-white" />
                                </div>
                                <div>
                                    <h3 className="text-white font-semibold text-sm">Travel Assistant</h3>
                                    <p className="text-white/70 text-xs">Powered by Multi-Agent AI</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="text-white/80 hover:text-white transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
                            {messages.map((msg, idx) => (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                >
                                    <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                                        msg.role === 'user'
                                            ? 'bg-indigo-600 text-white rounded-br-md'
                                            : msg.role === 'system'
                                            ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                            : 'bg-white text-gray-800 shadow-sm border border-gray-100 rounded-bl-md'
                                    }`}>
                                        <div className="flex items-start gap-2">
                                            {msg.role !== 'user' && (
                                                <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                                                    msg.role === 'system' ? 'bg-amber-200' : 'bg-indigo-100'
                                                }`}>
                                                    {msg.role === 'system' ? (
                                                        <RefreshCw className="w-3 h-3 text-amber-600" />
                                                    ) : msg.agentUsed ? (
                                                        getAgentIcon(msg.agentUsed)
                                                    ) : (
                                                        <Bot className="w-3 h-3 text-indigo-600" />
                                                    )}
                                                </div>
                                            )}
                                            <div className="flex-1">
                                                <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                                                {msg.agentUsed && (
                                                    <p className="text-[10px] text-gray-400 mt-1 flex items-center gap-1">
                                                        {getAgentIcon(msg.agentUsed)}
                                                        <span>{msg.agentUsed.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                                                    </p>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                            
                            {isLoading && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="flex justify-start"
                                >
                                    <div className="bg-white rounded-2xl rounded-bl-md px-4 py-3 shadow-sm border border-gray-100">
                                        <div className="flex items-center gap-2">
                                            <div className="w-5 h-5 bg-indigo-100 rounded-full flex items-center justify-center">
                                                <Bot className="w-3 h-3 text-indigo-600" />
                                            </div>
                                            <div className="flex gap-1">
                                                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                                                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                                                <span className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                            
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input */}
                        <div className="p-3 bg-white border-t border-gray-100">
                            <div className="flex items-center gap-2">
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    placeholder="Ask a question or request changes..."
                                    className="flex-1 px-4 py-2.5 bg-gray-100 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
                                    disabled={isLoading}
                                />
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={handleSend}
                                    disabled={!input.trim() || isLoading}
                                    className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-indigo-700 transition-colors"
                                >
                                    <Send className="w-4 h-4" />
                                </motion.button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
};

export default ChatBox;
