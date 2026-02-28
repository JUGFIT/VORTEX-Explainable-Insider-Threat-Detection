import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout/Layout';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import RiskBadge from '../components/Common/RiskBadge';
import { Search, Eye, TrendingUp, Users as UsersIcon, ShieldAlert } from 'lucide-react';
import { getAllUsers } from '../services/api';

const Users = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [users, setUsers] = useState([]);
    const [filteredUsers, setFilteredUsers] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [sortBy, setSortBy] = useState('risk');

    useEffect(() => {
        fetchUsers();
    }, []);

    useEffect(() => {
        let filtered = [...users];

        if (searchTerm) {
            filtered = filtered.filter(user =>
                user.user_id.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }

        // Apply Sorting
        filtered.sort((a, b) => {
            if (sortBy === 'risk') {
                const riskOrder = { 'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3 };
                const riskA = riskOrder[(a.baseline_risk_level || 'LOW').toUpperCase()] ?? 4;
                const riskB = riskOrder[(b.baseline_risk_level || 'LOW').toUpperCase()] ?? 4;

                if (riskA !== riskB) return riskA - riskB;
                // If same level, use score as secondary sort
                return (b.baseline_score || 0) - (a.baseline_score || 0);
            }
            if (sortBy === 'confidence') return (b.confidence || 0) - (a.confidence || 0);
            if (sortBy === 'events') return (b.event_count || 0) - (a.event_count || 0);
            if (sortBy === 'id') return a.user_id.localeCompare(b.user_id);
            return 0;
        });

        setFilteredUsers(filtered);
    }, [users, searchTerm, sortBy]);

    const fetchUsers = async () => {
        try {
            setLoading(true);
            const data = await getAllUsers();
            setUsers(data);
        } catch (error) {
            console.error('Error fetching users:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Layout title="User Behavioral Directory">
                <div className="flex flex-col items-center justify-center h-96">
                    <LoadingSpinner size={48} />
                    <p className="text-gray-400 mt-4 animate-pulse">Syncing organizational baselines...</p>
                </div>
            </Layout>
        );
    }

    return (
        <Layout title="User Behavioral Directory">
            {/* Top Stats & Search */}
            {/* Top Stats & Search Bar Area */}
            <div className="flex flex-wrap lg:flex-nowrap gap-4 mb-8">
                {/* Search Bar - Main Focus */}
                <div className="flex-grow lg:w-1/2 card bg-gray-900 border-gray-800 flex items-center px-6 py-2 shadow-xl transition-all focus-within:border-vortex-accent/50 focus-within:ring-1 focus-within:ring-vortex-accent/20">
                    <Search size={18} className="text-vortex-accent mr-4" />
                    <input
                        type="text"
                        placeholder="Search organizational identity (e.g. user_025)..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="bg-transparent border-none focus:ring-0 text-sm w-full placeholder:text-gray-600"
                    />
                    <div className="hidden sm:flex items-center gap-2 ml-4 px-2 py-0.5 bg-gray-800 rounded-full border border-gray-700">
                        <UsersIcon size={10} className="text-gray-400" />
                        <span className="text-2xs font-bold whitespace-nowrap text-gray-300">{filteredUsers.length}</span>
                    </div>
                </div>

                {/* Filter/Sort Section - Secondary Container */}
                <div className="w-full lg:w-60 card bg-gray-900 border-gray-800 flex items-center px-4 py-2 shadow-xl">
                    <div className="flex items-center gap-3 w-full">
                        <span className="text-2xs text-gray-500 font-bold uppercase tracking-wider">Sort:</span>
                        <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value)}
                            className="input-field py-1 px-8 text-xs w-full"
                        >
                            <option value="risk">Highest Risk</option>
                            <option value="confidence">Confidence Score</option>
                            <option value="events">Activity Volume</option>
                            <option value="id">Alphabetical ID</option>
                        </select>
                    </div>
                </div>

                {/* High Risk Highlight - Outcome Card */}
                <div className="w-full lg:w-60 card bg-vortex-accent/10 border-vortex-accent/30 flex items-center justify-between px-6 py-2 shadow-lg">
                    <div className="flex items-center gap-3">
                        <ShieldAlert size={18} className="text-vortex-accent" />
                        <div className="text-2xs text-vortex-accent font-black uppercase tracking-widest">Risk Vectors</div>
                    </div>
                    <div className="text-xl font-black text-white leading-none">
                        {users.filter(u => {
                            const level = u.baseline_risk_level?.toUpperCase();
                            return level === 'HIGH' || level === 'CRITICAL';
                        }).length}
                    </div>
                </div>
            </div>

            {/* Users Grid */}
            {/* Users List (Horizontal Cards) */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredUsers.map((user) => (
                    <div
                        key={user.user_id}
                        className="group relative bg-[#1c2128] rounded-xl border border-gray-800 hover:border-vortex-accent/60 transition-all duration-300 overflow-hidden hover:shadow-[0_10px_30px_rgba(124,58,237,0.1)] flex flex-col p-4 cursor-pointer h-full"
                        onClick={() => navigate(`/user/${user.user_id}`)}
                    >
                        {/* Top Indicator Line */}
                        <div className={`absolute top-0 left-0 right-0 h-1.5 ${(user.baseline_risk_level || '').toLowerCase() === 'critical' ? 'bg-[#fb2c36]' :
                            (user.baseline_risk_level || '').toLowerCase() === 'high' ? 'bg-[#ff6900]' :
                                (user.baseline_risk_level || '').toLowerCase() === 'medium' ? 'bg-[#f0b100]' :
                                    'bg-[#00c950]'
                            }`}></div>

                        {/* Card Header */}
                        <div className="flex items-start justify-between mb-3 mt-1">
                            <div className="flex items-center gap-3">
                                <div className="relative shrink-0">
                                    <div className="w-10 h-10 rounded-lg bg-gray-800/50 flex items-center justify-center border border-gray-700/50 group-hover:border-vortex-accent/30 transition-all">
                                        <UsersIcon className="w-5 h-5 text-gray-400 group-hover:text-vortex-accent transition-colors duration-300" />
                                    </div>
                                    <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-green-500 border-2 border-[#1c2128]"></div>
                                </div>
                                <div>
                                    <h3 className="text-lg font-black text-white tracking-tight group-hover:text-vortex-accent transition-colors leading-tight">
                                        {user.user_id}
                                    </h3>
                                    <div className="text-[10px] text-vortex-accent font-black uppercase tracking-wider mt-0.5">
                                        Identity Node
                                    </div>
                                </div>
                            </div>
                            <div className="scale-90 origin-top-right">
                                <RiskBadge level={user.baseline_risk_level} />
                            </div>
                        </div>

                        {/* Mid Section: Stats */}
                        <div className="grid grid-cols-2 gap-3 my-3 py-3 border-y border-gray-800/50">
                            <div>
                                <p className="text-[9px] text-gray-500 font-bold uppercase mb-1">Total Events</p>
                                <p className="text-sm font-mono font-bold text-gray-200">{user.event_count.toLocaleString()}</p>
                            </div>
                            <div>
                                <p className="text-[9px] text-gray-500 font-bold uppercase mb-1">Confidence</p>
                                <p className="text-sm font-mono font-bold text-purple-400">{((user.confidence || 0) * 100).toFixed(0)}%</p>
                            </div>
                        </div>

                        {/* Deviation Bar */}
                        <div className="mb-4">
                            <div className="flex items-center justify-between text-[10px] mb-1.5 font-black uppercase tracking-wider">
                                <span className="text-gray-600">Deviation Score</span>
                                <span className={user.baseline_score > 0.5 ? 'text-vortex-accent' : 'text-gray-400 font-mono'}>
                                    {((user.baseline_score || 0) * 100).toFixed(1)}%
                                </span>
                            </div>
                            <div className="h-1.5 w-full bg-gray-800/50 rounded-full overflow-hidden p-[1px]">
                                <div
                                    className="h-full rounded-full bg-vortex-accent transition-all duration-1000 group-hover:shadow-[0_0_8px_rgba(124,58,237,0.4)]"
                                    style={{ width: `${Math.min(user.baseline_score * 100, 100)}%` }}
                                />
                            </div>
                        </div>

                    </div>
                ))}
            </div>

            {filteredUsers.length === 0 && (
                <div className="card border-dashed border-gray-700 bg-transparent flex flex-col items-center justify-center py-20">
                    <div className="p-4 bg-gray-800 rounded-full mb-4">
                        <Search size={32} className="text-gray-600" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-400">Identity Not Found</h3>
                    <p className="text-gray-500 max-w-xs text-center mt-2">
                        No behavioral profile matches the current organizational query. Try another user ID.
                    </p>
                </div>
            )}
        </Layout>
    );
};

export default Users;
