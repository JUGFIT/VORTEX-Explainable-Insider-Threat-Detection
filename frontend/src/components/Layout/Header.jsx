import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Bell, Search, User, Settings, LogOut, Shield } from 'lucide-react';

const Header = ({ title, subtitle }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const [searchQuery, setSearchQuery] = useState('');
    const [showNotifications, setShowNotifications] = useState(false);

    const isDemoMode = location.pathname === '/demo';

    const notificationRef = useRef(null);

    // Close dropdowns on click outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (notificationRef.current && !notificationRef.current.contains(event.target)) {
                setShowNotifications(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const handleSearch = (e) => {
        if (e.key === 'Enter' && searchQuery.trim()) {
            if (searchQuery.toLowerCase().startsWith('user_')) {
                navigate(`/user/${searchQuery.trim()}`);
            } else {
                navigate(`/alerts?search=${searchQuery.trim()}`);
            }
            setSearchQuery('');
        }
    };

    return (
        <header className="bg-black/90 border-b border-gray-800 px-8 sticky top-0 z-40 backdrop-blur-2xl shadow-2xl h-[73px] flex items-center">
            <div className="flex items-center justify-between w-full">
                {/* Title Section */}
                <div>
                    <h1 className="font-bold text-white tracking-tight" style={{ fontSize: '22px' }}>{title}</h1>
                    {subtitle && <p className="text-gray-400 font-medium" style={{ fontSize: '13px', marginTop: '2px' }}>{subtitle}</p>}
                </div>

                {/* Actions Section */}
                <div className="flex items-center space-x-6">
                    {/* Demo Mode Toggle */}
                    <button
                        onClick={() => navigate(isDemoMode ? '/' : '/demo')}
                        className={`group relative flex items-center gap-3 px-5 py-2.5 rounded-full overflow-hidden transition-all duration-500 ease-out cursor-pointer ${isDemoMode
                            ? 'bg-gradient-to-r from-vortex-accent/20 to-purple-600/20 border border-vortex-accent/40 shadow-[0_0_20px_rgba(31,111,235,0.2)]'
                            : 'bg-[#12151a]/80 border border-gray-700/60 hover:border-gray-500 hover:bg-gray-800/80 shadow-lg'
                            }`}
                    >
                        <span className={`text-sm font-bold tracking-wide transition-colors duration-300 z-10 ${isDemoMode ? 'text-white' : 'text-gray-400 group-hover:text-gray-200'
                            }`}>
                            Test Mode
                        </span>

                        {/* Custom Toggle Graphic */}
                        <div className={`relative w-14 h-7 rounded-full transition-colors duration-500 ease-out z-10 shadow-inner ${isDemoMode ? 'bg-gradient-to-r from-vortex-accent to-purple-500' : 'bg-gray-700/80'
                            }`}>
                            <div className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow-[0_2px_8px_rgba(0,0,0,0.5)] transition-all duration-500 ease-[cubic-bezier(0.34,1.56,0.64,1)] ${isDemoMode ? 'left-8' : 'left-1'
                                }`}></div>
                        </div>

                        {/* Background ambient effect when active */}
                        {isDemoMode && (
                            <div className="absolute inset-0 bg-gradient-to-r from-vortex-accent to-purple-600 opacity-10 animate-pulse"></div>
                        )}
                    </button>
                </div>
            </div>
        </header>
    );
};

export default Header;
