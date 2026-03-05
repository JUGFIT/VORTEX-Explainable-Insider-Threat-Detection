import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Search, User, Settings, LogOut, Shield } from 'lucide-react';

const Header = ({ title, subtitle }) => {
    const navigate = useNavigate();
    const [searchQuery, setSearchQuery] = useState('');
    const [showNotifications, setShowNotifications] = useState(false);
    const [showUserMenu, setShowUserMenu] = useState(false);

    const notificationRef = useRef(null);
    const userMenuRef = useRef(null);

    // Close dropdowns on click outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (notificationRef.current && !notificationRef.current.contains(event.target)) {
                setShowNotifications(false);
            }
            if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
                setShowUserMenu(false);
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
        <header className="bg-vortex-dark/60 border-b border-gray-800 px-8 py-4 sticky top-0 z-40 backdrop-blur-xl">
            <div className="flex items-center justify-between">
                {/* Title Section */}
                <div>
                    <h1 className="text-2xl font-bold text-white tracking-tight">{title}</h1>
                    {subtitle && <p className="text-sm text-gray-400 mt-1 font-medium">{subtitle}</p>}
                </div>

                {/* Actions Section */}
                <div className="flex items-center space-x-4">
                    {/* Search */}
                    <div className="relative group">
                        <Search
                            className={`absolute left-3 top-1/2 transform -translate-y-1/2 transition-colors ${searchQuery ? 'text-vortex-accent' : 'text-gray-400'}`}
                            size={18}
                        />
                        <input
                            type="text"
                            placeholder="Find user or event..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            onKeyDown={handleSearch}
                            className="bg-vortex-darker/40 border border-gray-700 rounded-full py-2 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-vortex-accent focus:ring-1 focus:ring-vortex-accent transition-all w-64 md:w-80 backdrop-blur-md"
                        />
                    </div>

                    {/* Notifications */}
                    <div className="relative" ref={notificationRef}>
                        <button
                            onClick={() => {
                                setShowNotifications(!showNotifications);
                                setShowUserMenu(false);
                            }}
                            className={`relative p-2 rounded-lg transition-all duration-200 border backdrop-blur-md ${showNotifications ? 'bg-vortex-accent/20 border-vortex-accent text-vortex-accent shadow-lg shadow-vortex-accent/20 -translate-y-0.5' : 'bg-gray-800/30 border-gray-700/50 text-gray-400 hover:bg-gray-700/60 hover:text-white hover:border-gray-500 hover:-translate-y-0.5 hover:shadow-lg'}`}
                        >
                            <Bell size={20} />
                            <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-risk-critical border-2 border-vortex-dark rounded-full"></span>
                        </button>

                        {showNotifications && (
                            <div className="absolute right-0 mt-3 w-84 bg-vortex-dark/60 border border-gray-700/50 rounded-2xl shadow-2xl z-50 animate-fade-in overflow-hidden backdrop-blur-2xl ring-1 ring-white/10">
                                <div className="p-4 border-b border-gray-700/50 flex justify-between items-center bg-gray-900/40 backdrop-blur-md">
                                    <h3 className="font-bold text-white">Notifications</h3>
                                    <span className="text-[10px] bg-red-500/90 text-white px-2 py-0.5 rounded-full uppercase font-black tracking-widest">2 New</span>
                                </div>
                                <div className="max-h-[32rem] overflow-y-auto custom-scrollbar">
                                    <div className="p-4 border-b border-gray-800/30 hover:bg-vortex-accent/20 cursor-pointer transition-all hover:pl-5 group">
                                        <div className="flex gap-3">
                                            <div className="w-2 h-2 mt-1.5 bg-red-500 rounded-full shrink-0 group-hover:scale-125 transition-transform" />
                                            <div>
                                                <p className="text-sm text-white font-semibold group-hover:text-vortex-accent transition-colors">Critical threat detected</p>
                                                <p className="text-xs text-gray-300 mt-1 line-clamp-2 leading-relaxed">Potential data exfiltration chain matched for user_027 (12.5GB total).</p>
                                                <p className="text-[10px] text-vortex-accent mt-2 font-bold uppercase tracking-wider opacity-80">2 minutes ago</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="p-4 border-b border-gray-800/30 hover:bg-vortex-accent/20 cursor-pointer transition-all hover:pl-5 group">
                                        <div className="flex gap-3">
                                            <div className="w-2 h-2 mt-1.5 bg-yellow-500 rounded-full shrink-0 group-hover:scale-125 transition-transform" />
                                            <div>
                                                <p className="text-sm text-white font-semibold group-hover:text-vortex-accent transition-colors">Model retraining complete</p>
                                                <p className="text-xs text-gray-300 mt-1 line-clamp-2 leading-relaxed">Isolation Forest optimized with new behavioral feature set.</p>
                                                <p className="text-[10px] text-gray-400 mt-2 font-bold uppercase tracking-wider opacity-80">1 hour ago</p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div className="p-3 bg-gray-900/60 text-center backdrop-blur-md">
                                    <button
                                        onClick={() => { navigate('/alerts'); setShowNotifications(false); }}
                                        className="text-xs text-vortex-accent font-black uppercase tracking-widest hover:text-white transition-colors"
                                    >
                                        View All Alerts
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* User Profile */}
                    <div className="relative" ref={userMenuRef}>
                        <button
                            onClick={() => {
                                setShowUserMenu(!showUserMenu);
                                setShowNotifications(false);
                            }}
                            className={`flex items-center space-x-3 p-1.5 pl-3 rounded-full transition-all duration-200 border backdrop-blur-md ${showUserMenu ? 'bg-vortex-accent/20 border-vortex-accent shadow-lg shadow-vortex-accent/20 -translate-y-0.5' : 'bg-gray-800/30 border-gray-700/50 hover:border-gray-500 hover:-translate-y-0.5 hover:shadow-lg'}`}
                        >
                            <span className="text-sm text-white font-bold pr-1">Admin</span>
                            <div className="bg-vortex-accent p-1.5 rounded-full shadow-lg shadow-vortex-accent/20">
                                <User size={18} className="text-white" />
                            </div>
                        </button>

                        {showUserMenu && (
                            <div className="absolute right-0 mt-3 w-60 bg-vortex-dark/60 border border-gray-700/50 rounded-2xl shadow-2xl z-50 animate-fade-in overflow-hidden backdrop-blur-2xl ring-1 ring-white/10">
                                <div className="p-4 border-b border-gray-700/50 bg-gray-900/40 backdrop-blur-md">
                                    <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-1">Signed in as</p>
                                    <p className="text-sm text-white font-black italic tracking-tight">vortex_admin</p>
                                </div>
                                <div className="p-2 space-y-1">
                                    <button
                                        onClick={() => { navigate('/settings'); setShowUserMenu(false); }}
                                        className="w-full flex items-center space-x-3 px-3 py-2.5 text-sm text-gray-300 hover:bg-vortex-accent hover:text-white rounded-xl transition-all hover:translate-x-1 group"
                                    >
                                        <Settings size={18} className="group-hover:rotate-90 transition-transform" />
                                        <span className="font-medium">Settings</span>
                                    </button>
                                    <button
                                        className="w-full flex items-center space-x-3 px-3 py-2.5 text-sm text-gray-300 hover:bg-white/10 hover:text-white rounded-xl transition-all hover:translate-x-1 group"
                                    >
                                        <Shield size={18} />
                                        <span className="font-medium">Security Panel</span>
                                    </button>
                                    <div className="my-2 border-t border-gray-800/50" />
                                    <button
                                        className="w-full flex items-center space-x-3 px-3 py-2.5 text-sm text-red-400 hover:bg-red-500 hover:text-white rounded-xl transition-all hover:translate-x-1 group"
                                    >
                                        <LogOut size={18} />
                                        <span className="font-medium">Logout</span>
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
