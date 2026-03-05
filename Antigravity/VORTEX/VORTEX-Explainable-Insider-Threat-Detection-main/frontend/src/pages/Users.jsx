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
            if (sortBy === 'risk') return (b.baseline_score || 0) - (a.baseline_score || 0);
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
            <Layout title="User Behavioral Directory" subtitle="Monitoring 50 unique behavioral fingerprints">
                <div className="flex flex-col items-center justify-center h-96">
                    <LoadingSpinner size={48} />
                    <p className="text-gray-400 mt-4 animate-pulse">Syncing organizational baselines...</p>
                </div>
            </Layout>
        );
    }

    return (
        <Layout title="User Behavioral Directory" subtitle="Comprehensive monitoring of individualized risk baselines">
            {/* Top Stats & Search */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
                <div className="lg:col-span-3 card bg-gray-900/50 backdrop-blur-md border-gray-800 flex items-center px-6 py-4 shadow-xl">
                    <Search size={22} className="text-vortex-accent mr-4" />
                    <input
                        type="text"
                        placeholder="Search organizational identity (e.g. user_025)..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="bg-transparent border-none focus:ring-0 text-lg w-full placeholder:text-gray-600"
                    />
                    <div className="hidden md:flex items-center gap-2 ml-4 px-3 py-1 bg-gray-800 rounded-full border border-gray-700">
                        <UsersIcon size={14} className="text-gray-400" />
                        <span className="text-xs font-bold whitespace-nowrap">{filteredUsers.length} Results</span>
                    </div>

                    <div className="ml-4 flex items-center gap-2">
                        <span className="text-xs text-gray-500 font-bold uppercase whitespace-nowrap">Sort By:</span>
                        <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value)}
                            className="bg-gray-800 border border-gray-700 text-xs rounded-lg px-2 py-1 focus:ring-vortex-accent focus:border-vortex-accent text-white"
                        >
                            <option value="risk">Highest Risk</option>
                            <option value="confidence">Confidence</option>
                            <option value="events">Activity</option>
                            <option value="id">User ID</option>
                        </select>
                    </div>
                </div>

                <div className="card bg-vortex-accent/10 border-vortex-accent/30 flex items-center justify-center p-4">
                    <ShieldAlert size={20} className="text-vortex-accent mr-3" />
                    <div>
                        <div className="text-[10px] text-vortex-accent font-bold uppercase tracking-wider">High Risk Count</div>
                        <div className="text-2xl font-bold">{users.filter(u => u.baseline_risk_level === 'High' || u.baseline_risk_level === 'Critical').length}</div>
                    </div>
                </div>
            </div>

            {/* Users Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredUsers.map((user) => (
                    <div
                        key={user.user_id}
                        className="group relative bg-gray-900 rounded-xl border border-gray-800 hover:border-vortex-accent/50 transition-all duration-300 overflow-hidden hover:shadow-[0_0_30px_rgba(124,58,237,0.15)] shadow-xl flex flex-col cursor-pointer"
                        onClick={() => navigate(`/user/${user.user_id}`)}
                    >
                        {/* Background subtle glow */}
                        <div className="absolute top-0 right-0 w-32 h-32 bg-vortex-accent/5 blur-[50px] -z-10 group-hover:bg-vortex-accent/10 transition-all"></div>

                        <div className="p-5 flex-1">
                            <div className="flex items-start justify-between mb-4">
                                <div className="w-12 h-12 rounded-lg bg-gray-800 flex items-center justify-center group-hover:bg-vortex-accent/20 transition-colors">
                                    <UsersIcon className="w-6 h-6 text-gray-400 group-hover:text-vortex-accent" />
                                </div>
                                <RiskBadge level={user.baseline_risk_level} />
                            </div>

                            <div className="mb-6">
                                <h3 className="text-xl font-bold mb-1 tracking-tight text-white group-hover:text-vortex-accent transition-colors">
                                    {user.user_id}
                                </h3>
                                <div className="flex items-center gap-2 text-xs text-gray-500">
                                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-500"></span>
                                    <span>{user.event_count} activity events</span>
                                </div>
                            </div>

                            <div className="space-y-4 mb-2">
                                <div>
                                    <div className="flex items-center justify-between text-xs mb-1.5 uppercase font-bold tracking-widest text-gray-500">
                                        <span>Baseline Deviation</span>
                                        <span className={user.baseline_score > 0.5 ? 'text-vortex-accent' : 'text-gray-400'}>
                                            {((user.baseline_score || 0) * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                    <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-blue-500 to-vortex-accent transition-all duration-1000"
                                            style={{ width: `${Math.min(user.baseline_score * 100, 100)}%` }}
                                        />
                                    </div>
                                </div>

                                <div className="flex items-center justify-between py-2 border-t border-gray-800/50">
                                    <div className="flex items-center gap-1.5 text-xs text-gray-400">
                                        <TrendingUp size={14} className="text-purple-500" />
                                        <span>Confidence</span>
                                    </div>
                                    <span className="text-xs font-mono font-bold text-gray-300">{((user.confidence || 0) * 100).toFixed(0)}%</span>
                                </div>
                            </div>
                        </div>

                        {/* Action Overlay */}
                        <div className="px-5 pb-5">
                            <button
                                className="w-full bg-gray-800 hover:bg-vortex-accent hover:text-white text-gray-300 py-2.5 rounded-lg text-sm font-bold flex items-center justify-center gap-2 transition-all"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    navigate(`/user/${user.user_id}`);
                                }}
                            >
                                <Eye size={16} />
                                Observe Agent Profile
                            </button>
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
