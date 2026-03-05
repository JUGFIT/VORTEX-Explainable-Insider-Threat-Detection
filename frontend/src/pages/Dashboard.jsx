import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout/Layout';
import StatsCard from '../components/Dashboard/StatsCard';
import TrendingUsersWidget from '../components/Dashboard/TrendingUsersWidget';
import GlobalAlertFeed from '../components/Dashboard/GlobalAlertFeed';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import RiskBadge from '../components/Common/RiskBadge';
import { AlertTriangle, Users, Activity, TrendingUp, Eye } from 'lucide-react';
import { getRiskEvents, getRiskCounts, getAllUsers } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Treemap, Cell } from 'recharts';

const Dashboard = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({
        totalEvents: 0,
        highRiskEvents: 0,
        totalUsers: 0,
        escalatingUsers: 0,
    });
    const [recentEvents, setRecentEvents] = useState([]);
    const [riskDistribution, setRiskDistribution] = useState([]);
    const [activeIndex, setActiveIndex] = useState(null);

    const trendData = [
        { day: 'Mon', critical: 2, high: 10, medium: 28, low: 45 },
        { day: 'Tue', critical: 3, high: 12, medium: 32, low: 42 },
        { day: 'Wed', critical: 1, high: 17, medium: 35, low: 38 },
        { day: 'Thu', critical: 4, high: 10, medium: 30, low: 41 },
        { day: 'Fri', critical: 5, high: 15, medium: 38, low: 35 },
        { day: 'Sat', critical: 6, high: 16, medium: 40, low: 32 },
        { day: 'Sun', critical: 3, high: 16, medium: 36, low: 37 },
    ];

    useEffect(() => {
        fetchDashboardData();

        const handleRefresh = () => fetchDashboardData();
        window.addEventListener('refreshDashboard', handleRefresh);
        return () => window.removeEventListener('refreshDashboard', handleRefresh);
    }, []);

    const fetchDashboardData = async () => {
        try {
            setLoading(true);

            // Fetch counts (full dataset breakdown — much more accurate than health endpoint)
            const [countData, users, events] = await Promise.allSettled([
                getRiskCounts(),
                getAllUsers(),
                getRiskEvents({ limit: 5, sort_by: 'timestamp', sort_order: 'desc' }),
            ]);

            const counts = countData.status === 'fulfilled' ? countData.value : null;
            const userList = users.status === 'fulfilled' ? users.value : [];
            const eventList = events.status === 'fulfilled' ? events.value : [];

            const criticalCount = counts?.by_risk_level?.Critical ?? 0;
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
                { name: 'Critical', value: criticalCount, color: '#fb2c36' },
                { name: 'High', value: highCount, color: '#ff6900' },
                { name: 'Medium', value: mediumCount, color: '#f0b100' },
                { name: 'Low', value: lowCount, color: '#00c950' },
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

    const getBarOpacity = (index) => {
        return 1;
    };

    const CustomizedTreemapContent = (props) => {
        const { x, y, width, height, index, name, value, color } = props;
        return (
            <g>
                <rect
                    x={x + 2}
                    y={y + 2}
                    width={width - 4}
                    height={height - 4}
                    rx={6}
                    ry={6}
                    className="transition-all duration-300 hover:fill-opacity-80 hover:brightness-110 cursor-pointer"
                    style={{
                        fill: color,
                        stroke: 'none',
                        transformOrigin: `${x + width / 2}px ${y + height / 2}px`,
                    }}
                />
                {width > 60 && height > 40 && (
                    <text
                        x={x + width / 2}
                        y={y + height / 2 - 5}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="#fff"
                        className="text-[12px] font-black uppercase tracking-wider"
                    >
                        {name}
                    </text>
                )}
                {width > 60 && height > 40 && (
                    <text
                        x={x + width / 2}
                        y={y + height / 2 + 10}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="#fff"
                        fillOpacity={0.7}
                        className="text-[10px] font-mono"
                    >
                        {value.toLocaleString()}
                    </text>
                )}
            </g>
        );
    };

    if (loading) {
        return (
            <Layout title="Dashboard">
                <LoadingSpinner size={48} className="h-96" />
            </Layout>
        );
    }

    return (
        <Layout title="Dashboard">
            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <StatsCard
                    title="Total Processed Events"
                    value={stats.totalEvents.toLocaleString()}
                    change="+12.5%"
                    changeType="increase"
                    icon={Activity}
                    color="vortex-accent"
                />
                <StatsCard
                    title="High Risk Anomalies"
                    value={stats.highRiskEvents.toLocaleString()}
                    change="+8.3%"
                    changeType="increase"
                    icon={AlertTriangle}
                    color="risk-critical"
                />
                <StatsCard
                    title="Active Behavioral Identities"
                    value={stats.totalUsers.toLocaleString()}
                    change="+2.1%"
                    changeType="increase"
                    icon={Users}
                    color="indigo-500"
                />
                <StatsCard
                    title="Escalating Risk Vectors"
                    value={stats.escalatingUsers.toLocaleString()}
                    change="-5.2%"
                    changeType="decrease"
                    icon={TrendingUp}
                    color="risk-high"
                />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
                {/* Risk Distribution */}
                <div className="card">
                    <h3 className="text-lg font-semibold mb-6">Risk Magnitude Distribution</h3>
                    <div className="h-[260px] w-full flex items-center">
                        {/* Left Side: Distribution Legend & Metrics */}
                        <div className="flex-1 h-full flex flex-col justify-center space-y-5 pr-6">
                            {riskDistribution.map((item) => (
                                <div key={item.name} className="flex items-center group cursor-default">
                                    <div className="flex items-center gap-3">
                                        <div
                                            className="w-1.5 h-4 rounded-full transition-transform group-hover:scale-x-150 origin-left"
                                            style={{ backgroundColor: item.color }}
                                        />
                                        <p className="text-[10px] text-gray-400 font-bold uppercase tracking-[0.15em]">
                                            {item.name}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Right Side: Distribution Treemap */}
                        <div className="w-[75%] h-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <Treemap
                                    data={riskDistribution}
                                    dataKey="value"
                                    content={<CustomizedTreemapContent />}
                                    isAnimationActive={true}
                                    animationDuration={1200}
                                    animationEasing="ease-out"
                                >
                                    <Tooltip
                                        content={({ active, payload }) => {
                                            if (active && payload && payload.length) {
                                                const data = payload[0].payload;
                                                return (
                                                    <div className="bg-[#0b0e14] border border-[#30363d] rounded-lg p-3 shadow-2xl">
                                                        <p className="text-gray-400 font-bold text-[10px] uppercase mb-1">{data.name} Risk</p>
                                                        <p className="text-lg font-black font-mono" style={{ color: data.color }}>
                                                            {data.value.toLocaleString()} <span className="text-xs font-normal text-gray-500">Events</span>
                                                        </p>
                                                    </div>
                                                );
                                            }
                                            return null;
                                        }}
                                    />
                                </Treemap>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>

                {/* Risk Trend */}
                <div className="card">
                    <h3 className="text-lg font-semibold mb-4">Risk Trend (Last 7 Days)</h3>
                    <div className="h-[260px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                                barSize={30}
                                data={trendData}
                                onMouseMove={(state) => {
                                    if (state && state.activeTooltipIndex !== undefined) {
                                        setActiveIndex(state.activeTooltipIndex);
                                    } else {
                                        setActiveIndex(null);
                                    }
                                }}
                                onMouseLeave={() => setActiveIndex(null)}
                            >
                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                                <XAxis dataKey="day" stroke="#9ca3af" axisLine={false} tickLine={false} />
                                <YAxis stroke="#9ca3af" axisLine={false} tickLine={false} />
                                <Tooltip
                                    content={({ active, payload, label }) => {
                                        if (active && payload && payload.length) {
                                            // Sort payload to show Critical at top, then High, then Medium, then Low
                                            const sortedPayload = [...payload].sort((a, b) => {
                                                const order = { critical: 0, high: 1, medium: 2, low: 3 };
                                                return order[a.dataKey] - order[b.dataKey];
                                            });

                                            const colorMap = {
                                                critical: '#fb2c36',
                                                high: '#ff6900',
                                                medium: '#f0b100',
                                                low: '#00c950'
                                            };

                                            return (
                                                <div className="bg-[#0b0e14] border border-[#30363d] rounded-lg p-3 shadow-2xl min-w-[120px]">
                                                    <p className="text-gray-400 font-bold text-[10px] uppercase mb-2 tracking-widest border-b border-gray-800 pb-1.5">{label} Report</p>
                                                    {sortedPayload.map((entry, index) => (
                                                        <div key={index} className="flex justify-between items-center gap-4 py-1">
                                                            <span className="text-[11px] font-bold uppercase tracking-tight" style={{ color: colorMap[entry.dataKey] }}>
                                                                {entry.dataKey}:
                                                            </span>
                                                            <span className="text-[12px] font-mono font-black border-l border-gray-800 pl-2" style={{ color: colorMap[entry.dataKey] }}>
                                                                {entry.value}
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            );
                                        }
                                        return null;
                                    }}
                                    cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }}
                                />
                                <Bar dataKey="low" stackId="a" isAnimationActive={true} animationDuration={1200} animationEasing="ease-out">
                                    {trendData.map((entry, index) => (
                                        <Cell
                                            key={`low-${index}`}
                                            fill="#00c950"
                                            fillOpacity={getBarOpacity(index)}
                                            radius={[0, 0, 4, 4]}
                                            stroke={activeIndex === index ? '#ffffff' : 'none'}
                                            strokeWidth={2}
                                        />
                                    ))}
                                </Bar>
                                <Bar dataKey="medium" stackId="a" isAnimationActive={true} animationDuration={1200} animationEasing="ease-out">
                                    {trendData.map((entry, index) => (
                                        <Cell
                                            key={`medium-${index}`}
                                            fill="#f0b100"
                                            fillOpacity={getBarOpacity(index)}
                                            stroke={activeIndex === index ? '#ffffff' : 'none'}
                                            strokeWidth={2}
                                        />
                                    ))}
                                </Bar>
                                <Bar dataKey="high" stackId="a" isAnimationActive={true} animationDuration={1200} animationEasing="ease-out">
                                    {trendData.map((entry, index) => (
                                        <Cell
                                            key={`high-${index}`}
                                            fill="#ff6900"
                                            fillOpacity={getBarOpacity(index)}
                                            stroke={activeIndex === index ? '#ffffff' : 'none'}
                                            strokeWidth={2}
                                        />
                                    ))}
                                </Bar>
                                <Bar dataKey="critical" stackId="a" isAnimationActive={true} animationDuration={1200} animationEasing="ease-out">
                                    {trendData.map((entry, index) => (
                                        <Cell
                                            key={`critical-${index}`}
                                            fill="#fb2c36"
                                            fillOpacity={getBarOpacity(index)}
                                            radius={[4, 4, 0, 0]}
                                            stroke={activeIndex === index ? '#ffffff' : 'none'}
                                            strokeWidth={2}
                                        />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Main Content: 2-Column Layout */}
            <div className="flex flex-col lg:flex-row gap-4 mb-8 items-start w-full">
                {/* Left Column - Global Alert Feed (50% width) */}
                <div className="flex-1 min-w-0 h-full">
                    <GlobalAlertFeed />
                </div>

                {/* Right Column - Trending Users (50% width) */}
                <div className="flex-1 min-w-0 h-full">
                    <TrendingUsersWidget />
                </div>
            </div>

            {/* Recent High-Risk Events - Full Width */}
            <div className="card mb-8">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">Recent Critical & High-Risk Events</h3>
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
                                    <td className="py-3 px-4 text-sm font-mono">
                                        <span className="truncate max-w-[120px] block" title={event.event_id}>
                                            {event.event_id}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-sm font-medium text-vortex-accent">{event.user_id}</td>
                                    <td className="py-3 px-4 text-sm text-gray-400">
                                        {new Date(event.timestamp).toLocaleString('en-GB')}
                                    </td>
                                    <td className="py-3 px-4">
                                        <RiskBadge level={event.risk_level} />
                                    </td>
                                    <td className="py-3 px-4 text-sm font-semibold">
                                        {event.anomaly_score.toFixed(3)}
                                    </td>
                                    <td className="py-3 px-4 text-right">
                                        <button
                                            onClick={() => navigate(`/event/${event.event_id}`)}
                                            className="btn-secondary py-0.5 px-2 text-[10px] font-bold flex items-center gap-1 ml-auto hover:bg-vortex-accent hover:border-vortex-accent hover:text-white group/btn"
                                        >
                                            <Eye size={10} className="text-vortex-accent group-hover/btn:text-white transition-colors" />
                                            <span>View</span>
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
        </Layout>
    );
};

export default Dashboard;
