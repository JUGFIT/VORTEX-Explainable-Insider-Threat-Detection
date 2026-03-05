import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    AlertTriangle,
    Users,
    TrendingUp,
    GitBranch,
    Activity,
    Settings
} from 'lucide-react';

const Sidebar = () => {
    const location = useLocation();
    const navigate = useNavigate();

    const navItems = [
        { path: '/', icon: LayoutDashboard, label: 'Dashboard', exact: true },
        { path: '/alerts', icon: AlertTriangle, label: 'Alerts', subPaths: ['/event'] },
        { path: '/users', icon: Users, label: 'Users', subPaths: ['/user'] },
        { path: '/trajectories', icon: TrendingUp, label: 'Risk Trajectories' },
        { path: '/chains', icon: GitBranch, label: 'Attack Chains' },
        { path: '/analytics', icon: Activity, label: 'Analytics' },
    ];

    const isNavItemActive = (item) => {
        if (item.exact) return location.pathname === item.path;
        if (location.pathname.startsWith(item.path)) return true;
        if (item.subPaths) {
            return item.subPaths.some(sub => location.pathname.startsWith(sub));
        }
        return false;
    };

    const renderNavLink = (item) => {
        const active = isNavItemActive(item);
        return (
            <NavLink
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-4 px-5 py-3 rounded-2xl transition-all duration-300 group relative border ${active
                    ? 'bg-white/10 text-white border-white/10 shadow-[0_4px_12px_rgba(0,0,0,0.2)]'
                    : 'text-gray-400 hover:bg-white/5 hover:text-white border-transparent'
                    }`}
            >
                {/* Active Focus Indicator (Glow Dot) */}
                {active && (
                    <div className="absolute left-1.5 w-1 h-1 rounded-full bg-vortex-accent shadow-[0_0_12px_rgba(31,111,235,1)]" />
                )}

                <div className={`transition-all duration-300 ${active ? 'text-vortex-accent scale-110' : 'group-hover:text-gray-200'}`}>
                    <item.icon size={20} />
                </div>

                <span className={`transition-all duration-300 tracking-tight ${active
                    ? 'text-base font-bold translate-x-1'
                    : 'text-sm font-medium group-hover:translate-x-0.5'
                    }`}>
                    {item.label}
                </span>
            </NavLink>
        );
    };

    return (
        <div className="w-64 bg-vortex-dark border-r border-gray-800 h-screen fixed left-0 top-0 overflow-y-auto z-50">
            {/* Logo */}
            <div className="py-4 border-b border-gray-800 flex flex-col items-center justify-center h-[73px] relative overflow-hidden">
                {/* Ambient glow behind logo */}
                <div className="absolute inset-0 bg-gradient-to-b from-vortex-accent/5 to-transparent pointer-events-none" />

                {/* Golden Ratio lockup: icon=28px (17×φ), text=17px, gap=10.5px (17/φ) */}
                <div className="flex items-center relative z-10" style={{ gap: '10.5px' }}>
                    {/* Icon Mark — 28px = 17 × φ */}
                    <svg width="28" height="28" viewBox="0 0 26 26" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <defs>
                            <linearGradient id="vortex-icon-grad" x1="0" y1="0" x2="26" y2="26" gradientUnits="userSpaceOnUse">
                                <stop offset="0%" stopColor="#388bfd" />
                                <stop offset="100%" stopColor="#1f6feb" />
                            </linearGradient>
                            <filter id="glow">
                                <feGaussianBlur stdDeviation="1.5" result="coloredBlur" />
                                <feMerge>
                                    <feMergeNode in="coloredBlur" />
                                    <feMergeNode in="SourceGraphic" />
                                </feMerge>
                            </filter>
                        </defs>
                        {/* Shield base */}
                        <path
                            d="M13 2L3 6.5V13C3 18.25 7.4 23.15 13 24.5C18.6 23.15 23 18.25 23 13V6.5L13 2Z"
                            fill="url(#vortex-icon-grad)"
                            fillOpacity="0.15"
                            stroke="url(#vortex-icon-grad)"
                            strokeWidth="1.5"
                            strokeLinejoin="round"
                            filter="url(#glow)"
                        />
                        {/* Inner vortex spiral */}
                        <path
                            d="M13 8C10.24 8 8 10.24 8 13C8 15.76 10.24 18 13 18C15.76 18 18 15.76 18 13"
                            stroke="url(#vortex-icon-grad)"
                            strokeWidth="1.8"
                            strokeLinecap="round"
                            filter="url(#glow)"
                        />
                        <circle cx="13" cy="13" r="2" fill="url(#vortex-icon-grad)" filter="url(#glow)" />
                    </svg>

                    {/* Wordmark — 17px */}
                    <span
                        className="font-black tracking-[0.25em] text-transparent bg-clip-text leading-none"
                        style={{
                            fontSize: '17px',
                            backgroundImage: 'linear-gradient(135deg, #ffffff 0%, #388bfd 50%, #1f6feb 100%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                        }}
                    >
                        VORTEX
                    </span>
                </div>

                {/* Glowing accent line at bottom */}
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-16 h-px bg-gradient-to-r from-transparent via-vortex-accent to-transparent opacity-60" />
            </div>

            {/* Navigation */}
            <nav className="p-4 space-y-1">
                {navItems.map(renderNavLink)}
            </nav>

            {/* Bottom Section */}
            <div className="absolute bottom-0 w-full p-4 border-t border-gray-800 bg-vortex-dark/80 backdrop-blur-md">
                {renderNavLink({ path: '/settings', icon: Settings, label: 'Settings' })}
            </div>
        </div>
    );
};

export default Sidebar;
