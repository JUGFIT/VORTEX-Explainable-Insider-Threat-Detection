import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout/Layout';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import { TrendingUp, Users, AlertTriangle, ArrowRight, ShieldAlert } from 'lucide-react';
import { getTrendingUsers, getAllUsers } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import RiskBadge from '../components/Common/RiskBadge';

const Trajectories = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [trendingUsers, setTrendingUsers] = useState([]);
    const [stats, setStats] = useState({
        totalMonitored: 0,
        escalatingCount: 0,
        criticalEscalation: 0
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [trending, allUsers] = await Promise.all([
                getTrendingUsers({ limit: 20 }),
                getAllUsers()
            ]);

            const trendingList = Array.isArray(trending) ? trending : trending.trending_users || [];
            setTrendingUsers(trendingList);

            setStats({
                totalMonitored: allUsers.length || 0,
                escalatingCount: trendingList.length,
                criticalEscalation: trendingList.filter(u => u.escalation_severity === 'Critical').length
            });
        } catch (error) {
            console.error('Error fetching trajectory data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Layout title="Risk Trajectories">
                <LoadingSpinner size={48} className="h-96" />
            </Layout>
        );
    }

    return (
        <Layout title="Risk Trajectories">
            {/* Overview Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="card border-l-4 border-blue-500">
                    <div className="flex items-center gap-3 mb-2">
                        <Users className="text-blue-400 w-5 h-5" />
                        <span className="text-sm text-gray-400 font-bold uppercase">Total Monitored Baselines</span>
                    </div>
                    <div className="text-3xl font-black">{stats.totalMonitored}</div>
                </div>
                <div className="card border-l-4 border-red-500">
                    <div className="flex items-center gap-3 mb-2">
                        <TrendingUp className="text-red-400 w-5 h-5" />
                        <span className="text-sm text-gray-400 font-bold uppercase">Escalating Identities</span>
                    </div>
                    <div className="text-3xl font-black">{stats.escalatingCount}</div>
                </div>
                <div className="card border-l-4 border-red-500">
                    <div className="flex items-center gap-3 mb-2">
                        <ShieldAlert className="text-red-400 w-5 h-5" />
                        <span className="text-sm text-gray-400 font-bold uppercase">Critical Rate Shifts</span>
                    </div>
                    <div className="text-3xl font-black text-red-500">{stats.criticalEscalation}</div>
                </div>
            </div>

            {/* Main Content */}
            <div className="grid grid-cols-1 gap-8">
                {/* Escalation Leaderboard */}
                <div className="card">
                    <div className="flex items-center justify-between mb-6">
                        <h3 className="text-xl font-black uppercase tracking-tighter">Velocity Leaderboard</h3>
                        <div className="text-xs text-gray-500 font-bold px-3 py-1 bg-gray-800 rounded-full">
                            SORTED BY RISK VELOCITY (7D)
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b border-gray-800 text-left">
                                    <th className="py-4 px-4 text-2xs font-black text-gray-500 uppercase">Organizational Identity</th>
                                    <th className="py-4 px-4 text-2xs font-black text-gray-500 uppercase">Current Risk</th>
                                    <th className="py-4 px-4 text-2xs font-black text-gray-500 uppercase">Recent Activity</th>
                                    <th className="py-4 px-4 text-2xs font-black text-gray-500 uppercase">Velocity Shift</th>
                                    <th className="py-4 px-4 text-2xs font-black text-gray-500 uppercase">Severity</th>
                                    <th className="py-4 px-4 text-2xs font-black text-gray-500 uppercase">Analysis</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-800/50">
                                {trendingUsers.map((user) => (
                                    <tr key={user.user_id} className="hover:bg-gray-800/30 transition-colors group">
                                        <td className="py-4 px-4">
                                            <div
                                                className="font-bold text-vortex-accent cursor-pointer hover:underline"
                                                onClick={() => navigate(`/user/${user.user_id}`)}
                                            >
                                                {user.user_id}
                                            </div>
                                        </td>
                                        <td className="py-4 px-4 font-mono font-bold">
                                            {(user.current_risk || 0).toFixed(3)}
                                        </td>
                                        <td className="py-4 px-4 text-sm text-gray-400">
                                            {user.recent_event_count} events (7d)
                                        </td>
                                        <td className="py-4 px-4">
                                            <div className="flex items-center gap-1">
                                                <TrendingUp className={`w-4 h-4 ${user.percent_change > 25 ? 'text-red-500' : 'text-yellow-500'}`} />
                                                <span className={`font-black ${user.percent_change > 25 ? 'text-red-500' : 'text-yellow-500'}`}>
                                                    +{(user.percent_change || 0).toFixed(0)}%
                                                </span>
                                            </div>
                                        </td>
                                        <td className="py-4 px-4">
                                            <RiskBadge level={user.escalation_severity} />
                                        </td>
                                        <td className="py-4 px-4">
                                            <button
                                                onClick={() => navigate(`/user/${user.user_id}`)}
                                                className="p-2 bg-gray-800 rounded hover:bg-vortex-accent hover:text-white transition-all"
                                            >
                                                <ArrowRight className="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Perspective Section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="card overflow-hidden relative">
                        <div className="absolute top-0 right-0 p-4 opacity-10">
                            <TrendingUp className="w-24 h-24" />
                        </div>
                        <h3 className="text-lg font-black uppercase mb-4">Trajectory Insights</h3>
                        <p className="text-sm text-gray-400 leading-relaxed mb-6">
                            Risk trajectories identify "Low and Slow" behavioral shifts that evade traditional real-time alerts.
                            The velocity shift represents the increase in anomaly density over the last 7 days compared to the established baseline.
                        </p>
                        <div className="space-y-4">
                            <div className="p-4 bg-gray-900/50 rounded-lg border border-gray-800">
                                <div className="text-xs font-bold text-red-400 uppercase mb-1">Critical Insight</div>
                                <div className="text-sm text-gray-200">
                                    {stats.criticalEscalation} users are currently exhibiting exponential risk acceleration patterns.
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="card">
                        <h3 className="text-lg font-black uppercase mb-4">Escalation Distribution</h3>
                        <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={trendingUsers.slice(0, 7).map(u => ({ name: u.user_id, risk: u.current_risk, velocity: u.percent_change }))}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                                    <XAxis dataKey="name" stroke="#4a5568" fontSize={10} />
                                    <YAxis stroke="#4a5568" fontSize={10} />
                                    <Tooltip contentStyle={{ backgroundColor: '#1a202c', border: 'none', borderRadius: '8px' }} />
                                    <Area type="monotone" dataKey="velocity" stroke="#7c3aed" fill="#7c3aed" fillOpacity={0.2} strokeWidth={3} />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default Trajectories;
