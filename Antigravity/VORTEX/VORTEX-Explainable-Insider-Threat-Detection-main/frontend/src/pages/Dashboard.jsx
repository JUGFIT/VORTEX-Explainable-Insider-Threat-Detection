import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout/Layout';
import StatsCard from '../components/Dashboard/StatsCard';
import TrendingUsersWidget from '../components/Dashboard/TrendingUsersWidget';
import GlobalAlertFeed from '../components/Dashboard/GlobalAlertFeed';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import RiskBadge from '../components/Common/RiskBadge';
import SimulationFAB from '../components/Common/SimulationFAB';
import SimulationPanel from '../components/Simulation/SimulationPanel';
import { AlertTriangle, Users, Activity, TrendingUp, Eye } from 'lucide-react';
import { getRiskEvents, getRiskCounts, getAllUsers } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const Dashboard = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [showSimulation, setShowSimulation] = useState(false);
    const [stats, setStats] = useState({
        totalEvents: 0,
        highRiskEvents: 0,
        totalUsers: 0,
        escalatingUsers: 0,
    });
    const [recentEvents, setRecentEvents] = useState([]);
    const [riskDistribution, setRiskDistribution] = useState([]);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            setLoading(true);

            // Fetch counts (full dataset breakdown — much more accurate than health endpoint)
            const [countData, users, events] = await Promise.allSettled([
                getRiskCounts(),
                getAllUsers(),
                getRiskEvents({ limit: 5, sort_by: 'anomaly_score', sort_order: 'desc' }),
            ]);

            const counts = countData.status === 'fulfilled' ? countData.value : null;
            const userList = users.status === 'fulfilled' ? users.value : [];
            const eventList = events.status === 'fulfilled' ? events.value : [];

            const highCount = counts?.by_risk_level?.High ?? 0;
            const mediumCount = counts?.by_risk_level?.Medium ?? 0;
            const lowCount = counts?.by_risk_level?.Low ?? 0;
            const totalEvents = counts?.total_events ?? 0;

            const totalUsers = Array.isArray(userList) ? userList.length : 0;
            const escalatingUsers = Array.isArray(userList)
                ? userList.filter(u => u.baseline_risk_level === 'High' || u.baseline_risk_level === 'Critical').length
                : 0;

            // Pie chart — use real full-dataset counts
            const distribution = [
                { name: 'High', value: highCount, color: '#ef4444' },
                { name: 'Medium', value: mediumCount, color: '#f59e0b' },
                { name: 'Low', value: lowCount, color: '#10b981' },
            ].filter(d => d.value > 0);

            setStats({ totalEvents, highRiskEvents: highCount, totalUsers, escalatingUsers });
            setRecentEvents(Array.isArray(eventList) ? eventList.slice(0, 5) : []);
            setRiskDistribution(distribution);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Layout title="Dashboard" subtitle="Real-time insider threat monitoring">
                <LoadingSpinner size={48} className="h-96" />
            </Layout>
        );
    }

    return (
        <Layout title="Dashboard" subtitle="Real-time insider threat monitoring">
            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <StatsCard
                    title="Total Events"
                    value={stats.totalEvents.toLocaleString()}
                    change="+12.5%"
                    changeType="increase"
                    icon={Activity}
                    color="blue-500"
                />
                <StatsCard
                    title="High Risk Events"
                    value={stats.highRiskEvents.toLocaleString()}
                    change="+8.3%"
                    changeType="increase"
                    icon={AlertTriangle}
                    color="risk-critical"
                />
                <StatsCard
                    title="Monitored Users"
                    value={stats.totalUsers.toLocaleString()}
                    change="+2.1%"
                    changeType="increase"
                    icon={Users}
                    color="purple-500"
                />
                <StatsCard
                    title="Escalating Users"
                    value={stats.escalatingUsers.toLocaleString()}
                    change="-5.2%"
                    changeType="decrease"
                    icon={TrendingUp}
                    color="risk-high"
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* Risk Distribution */}
                <div className="card">
                    <h3 className="text-lg font-semibold mb-4">Risk Distribution</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={riskDistribution}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {riskDistribution.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Risk Trend (placeholder data) */}
                <div className="card">
                    <h3 className="text-lg font-semibold mb-4">Risk Trend (Last 7 Days)</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={[
                            { day: 'Mon', high: 12, medium: 28, low: 45 },
                            { day: 'Tue', high: 15, medium: 32, low: 42 },
                            { day: 'Wed', high: 18, medium: 35, low: 38 },
                            { day: 'Thu', high: 14, medium: 30, low: 41 },
                            { day: 'Fri', high: 20, medium: 38, low: 35 },
                            { day: 'Sat', high: 22, medium: 40, low: 32 },
                            { day: 'Sun', high: 19, medium: 36, low: 37 },
                        ]}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                            <XAxis dataKey="day" stroke="#9ca3af" />
                            <YAxis stroke="#9ca3af" />
                            <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none' }} />
                            <Bar dataKey="high" stackId="a" fill="#ef4444" />
                            <Bar dataKey="medium" stackId="a" fill="#fbbf24" />
                            <Bar dataKey="low" stackId="a" fill="#10b981" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Main Content: 2-Column Layout */}
            <div className="flex flex-col lg:flex-row gap-6 mb-8 items-start">
                {/* Left Column - Global Alert Feed (2/3 width) */}
                <div className="w-full lg:w-2/3">
                    <GlobalAlertFeed />
                </div>

                {/* Right Column - Trending Users (1/3 width) */}
                <div className="w-full lg:w-1/3">
                    <TrendingUsersWidget />
                </div>
            </div>

            {/* Recent High-Risk Events - Full Width */}
            <div className="card mb-8">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">Recent High-Risk Events</h3>
                    <button
                        onClick={() => navigate('/alerts')}
                        className="text-sm text-purple-400 hover:text-purple-300"
                    >
                        View All →
                    </button>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-800">
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Event ID</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">User ID</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Timestamp</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Risk Level</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Score</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {recentEvents.map((event) => (
                                <tr
                                    key={event.event_id}
                                    className="border-b border-gray-800 hover:bg-gray-800 transition-colors"
                                >
                                    <td className="py-3 px-4 text-sm font-mono">{event.event_id}</td>
                                    <td className="py-3 px-4 text-sm">{event.user_id}</td>
                                    <td className="py-3 px-4 text-sm text-gray-400">
                                        {new Date(event.timestamp).toLocaleString()}
                                    </td>
                                    <td className="py-3 px-4">
                                        <RiskBadge level={event.risk_level} />
                                    </td>
                                    <td className="py-3 px-4 text-sm font-semibold">
                                        {event.anomaly_score.toFixed(3)}
                                    </td>
                                    <td className="py-3 px-4">
                                        <button
                                            onClick={() => navigate(`/event/${event.event_id}`)}
                                            className="flex items-center space-x-1 text-vortex-accent hover:text-vortex-accent-hover"
                                        >
                                            <Eye size={16} />
                                            <span className="text-sm">View</span>
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            {recentEvents.length === 0 && (
                                <tr>
                                    <td colSpan="6" className="py-8 text-center text-gray-500">No high-risk events found</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Floating Action Button for Simulation */}
            <SimulationFAB onClick={() => setShowSimulation(true)} />

            {/* Simulation Panel Modal */}
            <SimulationPanel
                isOpen={showSimulation}
                onClose={() => setShowSimulation(false)}
                onShowReveal={() => {
                    // Refresh all dashboard data to show the new threat
                    fetchDashboardData();
                }}
            />
        </Layout>
    );
};

export default Dashboard;
