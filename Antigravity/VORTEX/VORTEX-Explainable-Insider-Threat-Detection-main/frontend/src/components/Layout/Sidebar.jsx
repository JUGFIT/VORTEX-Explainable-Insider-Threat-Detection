import React from 'react';
import { NavLink } from 'react-router-dom';
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
    const navItems = [
        { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
        { path: '/alerts', icon: AlertTriangle, label: 'Alerts' },
        { path: '/users', icon: Users, label: 'Users' },
        { path: '/trajectories', icon: TrendingUp, label: 'Risk Trajectories' },
        { path: '/chains', icon: GitBranch, label: 'Attack Chains' },
        { path: '/analytics', icon: Activity, label: 'Analytics' },
    ];

    return (
        <div className="w-64 bg-vortex-dark border-r border-gray-800 h-screen fixed left-0 top-0 overflow-y-auto">
            {/* Logo */}
            <div className="p-6 border-b border-gray-800">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-vortex-accent to-purple-500 bg-clip-text text-transparent">
                    VORTEX
                </h1>
                <p className="text-xs text-gray-400 mt-1">Insider Threat Detection</p>
            </div>

            {/* Navigation */}
            <nav className="p-4 space-y-2">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${isActive
                                ? 'bg-vortex-accent text-white shadow-lg'
                                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                            }`
                        }
                    >
                        <item.icon size={20} />
                        <span className="font-medium">{item.label}</span>
                    </NavLink>
                ))}
            </nav>

            {/* Bottom Section */}
            <div className="absolute bottom-0 w-64 p-4 border-t border-gray-800">
                <NavLink
                    to="/settings"
                    className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-gray-800 hover:text-white transition-all duration-200"
                >
                    <Settings size={20} />
                    <span className="font-medium">Settings</span>
                </NavLink>
            </div>
        </div>
    );
};

export default Sidebar;
